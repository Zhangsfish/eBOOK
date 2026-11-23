import AVFoundation

// Retain delegate payloads until the main-queue delivery. Only identity is used;
// the framework object is never inspected or mutated off the main actor.
private struct UtteranceReference: @unchecked Sendable { let value: AVSpeechUtterance }

@MainActor final class AppleSpeechProvider: NSObject, SpeechProvider, AVSpeechSynthesizerDelegate {
    private let synthesizer = AVSpeechSynthesizer()
    private var current: AVSpeechUtterance?
    private var wantsPause = false
    var onEvent: ((SpeechEvent) -> Void)?
    var voices: [VoiceDescriptor] {
        AVSpeechSynthesisVoice.speechVoices().map {
            VoiceDescriptor(id: $0.identifier, name: $0.name, language: $0.language, requiresNetwork: false)
        }.sorted { $0.language < $1.language }
    }
    override init() {
        super.init()
        synthesizer.delegate = self
        synthesizer.usesApplicationAudioSession = true
    }
    func speak(_ request: SpeechRequest) throws {
        cancel()
        let utterance = AVSpeechUtterance(string: request.chunk.text)
        let voice = request.voiceID.flatMap { AVSpeechSynthesisVoice(identifier: $0) }
            ?? AVSpeechSynthesisVoice(language: "zh-CN")
        guard let voice else { throw ReaderError.unsupported("未找到本机中文语音，请在 iOS 辅助功能的朗读内容中下载语音。") }
        utterance.voice = voice
        utterance.rate = min(AVSpeechUtteranceMaximumSpeechRate, max(AVSpeechUtteranceMinimumSpeechRate, request.rate))
        utterance.postUtteranceDelay = request.chunk.text.hasSuffix("\n") ? 0.18 : 0.05
        current = utterance; wantsPause = false
        synthesizer.speak(utterance)
    }
    func pause() { wantsPause = true; synthesizer.pauseSpeaking(at: .immediate) }
    func resume() throws {
        wantsPause = false
        if !synthesizer.continueSpeaking(), !synthesizer.isSpeaking {
            throw ReaderError.invalid("本机朗读已停止，请再次播放。")
        }
    }
    func cancel() { current = nil; wantsPause = false; synthesizer.stopSpeaking(at: .immediate) }

    nonisolated func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didStart utterance: AVSpeechUtterance) {
        let reference = UtteranceReference(value: utterance)
        DispatchQueue.main.async { [weak self] in
            guard let self, self.matches(reference) else { return }
            if self.wantsPause { self.synthesizer.pauseSpeaking(at: .immediate) }
            self.onEvent?(.started)
        }
    }
    nonisolated func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, willSpeakRangeOfSpeechString characterRange: NSRange, utterance: AVSpeechUtterance) {
        let reference = UtteranceReference(value: utterance)
        DispatchQueue.main.async { [weak self] in
            guard let self, self.matches(reference) else { return }
            self.onEvent?(.range(startUTF16: characterRange.location, length: characterRange.length))
        }
    }
    nonisolated func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        let reference = UtteranceReference(value: utterance)
        DispatchQueue.main.async { [weak self] in
            guard let self, self.matches(reference) else { return }
            self.current = nil; self.onEvent?(.finished)
        }
    }
    nonisolated func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didCancel utterance: AVSpeechUtterance) {
        let reference = UtteranceReference(value: utterance)
        DispatchQueue.main.async { [weak self] in
            guard let self, self.matches(reference) else { return }
            self.current = nil; self.onEvent?(.cancelled)
        }
    }
    private func matches(_ reference: UtteranceReference) -> Bool { reference.value === current }
}
