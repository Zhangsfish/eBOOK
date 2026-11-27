import Foundation

/// The selected local model is explicit. Unsupported English/symbol spans use
/// the existing Apple adapter with a visible notice; model failures never silently
/// swap voices. No network client or Python/Piper runtime is shipped in the App.
@MainActor final class LocalSpeechProvider: SpeechProvider {
    var voices: [VoiceDescriptor] { suxin.voices + apple.voices }
    var onEvent: ((SpeechEvent) -> Void)?
    private let apple: SpeechProvider
    private let suxin: SuxinSpeechProvider
    private var active: SpeechProvider?
    private var generation = 0
    private var paused = false
    init(apple: SpeechProvider? = nil, suxin: SuxinSpeechProvider? = nil) {
        self.apple = apple ?? AppleSpeechProvider(); self.suxin = suxin ?? SuxinSpeechProvider()
    }
    func speak(_ request: SpeechRequest) throws {
        generation += 1; let token = generation
        paused = false
        onEvent?(.notice(nil))
        let source: SpeechProvider = request.voiceID == SuxinSpeechProvider.voiceID ? suxin : apple
        if let active, active !== source { active.cancel() }
        active = source
        source.onEvent = { [weak self] event in
            guard let self, self.generation == token else { return }
            self.onEvent?(event)
        }
        suxin.onUnsupported = { [weak self] in
            guard let self, self.generation == token else { return }
            self.suxin.cancel(); self.active = self.apple
            self.onEvent?(.notice("本段使用系统语音"))
            self.apple.onEvent = { [weak self] event in
                guard let self, self.generation == token else { return }; self.onEvent?(event)
            }
            do {
                // Map the model's multiplier onto Apple's supported rate range.
                let rate = min(0.65, max(0.35, 0.5 * request.rate))
                try self.apple.speak(SpeechRequest(stableID: request.stableID, chunk: request.chunk, voiceID: nil, rate: rate))
                if self.paused { self.apple.pause() }
            } catch { self.onEvent?(.failed(error.localizedDescription)) }
        }
        try source.speak(request)
    }
    func pause() { paused = true; active?.pause() }
    func resume() throws { try active?.resume(); paused = false }
    func cancel() { generation += 1; active?.cancel(); active = nil; suxin.cancel() }
    func prefetch(_ request: SpeechRequest) {
        if request.voiceID == SuxinSpeechProvider.voiceID { suxin.prefetch(request) }
    }
}
