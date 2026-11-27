import Foundation
import AVFoundation

@MainActor final class SuxinSpeechProvider: SpeechProvider {
    static let voiceID = "suxin.local.zh"
    let voices = [VoiceDescriptor(id: voiceID, name: "苏心", language: "zh-CN", requiresNetwork: false)]
    var onEvent: ((SpeechEvent) -> Void)?
    var onUnsupported: (() -> Void)?
    struct Measurement {
        var firstScheduledSeconds: Double?
        var generatedSeconds = 0.0, audioSeconds = 0.0
        var cacheHits = 0, chunks = 0, underflows = 0, peakQueuedBuffers = 0
        var rtf: [Double] = []
    }
    private(set) var measurement = Measurement()
    private let model: SuxinModel?
    private let engine = AVAudioEngine()
    private let player = AVAudioPlayerNode()
    private let format = AVAudioFormat(standardFormatWithSampleRate: 22050, channels: 1)!
    private var task: Task<Void, Never>?
    private var prefetchTask: Task<Void, Never>?
    private var lookahead: SpeechRequest?
    private var spaceWaiter: CheckedContinuation<Void, Never>?
    private var token = 0, queued = 0, completed = 0, planned = 0
    private var paused = false, hasStarted = false
    private var requestedAt = 0.0

    init(root: URL? = try? SuxinResources.bundledURL(), cacheRoot: URL? = nil) {
        model = root.map { SuxinModel(root: $0, cacheRoot: cacheRoot) }
        engine.attach(player)
        engine.connect(player, to: engine.mainMixerNode, format: format)
    }
    func speak(_ request: SpeechRequest) throws {
        invalidate(stopEngine: false)
        guard let model else { throw ReaderError.invalid("苏心资源缺失，请选择系统语音。") }
        paused = false; hasStarted = false; measurement = Measurement()
        let current = token
        requestedAt = ProcessInfo.processInfo.systemUptime
        onEvent?(.preparing(true))
        task = Task { [weak self] in
            guard let self else { return }
            do {
                // Validate the entire outer request before speaking any of it.
                // Mixed English/unknown symbols explicitly route the whole span.
                let parts = try await model.plan(request.chunk.text, context: request.contextText, startUTF16: request.chunk.startUTF16)
                try Task.checkCancellation()
                guard self.token == current else { return }
                self.planned = parts.count
                for part in parts {
                    while self.queued >= 3 {
                        await withCheckedContinuation { self.spaceWaiter = $0 }
                        try Task.checkCancellation()
                    }
                    let wave = try await model.wave(part: part, speed: request.rate)
                    try Task.checkCancellation()
                    guard self.token == current else { return }
                    try self.enqueue(wave, part: part.chunk, token: current)
                    self.startLookaheadIfUseful()
                }
                if parts.isEmpty, self.token == current { self.onEvent?(.preparing(false)); self.onEvent?(.finished) }
            } catch is CancellationError { /* explicit cancel owns the state */
            } catch SuxinFrontend.Failure.unsupportedText {
                guard self.token == current else { return }
                self.onEvent?(.preparing(false)); self.onUnsupported?()
            } catch {
                guard self.token == current else { return }
                self.onEvent?(.preparing(false)); self.onEvent?(.failed(error.localizedDescription))
            }
        }
    }
    private func enqueue(_ wave: SuxinWave, part: SpeechChunk, token current: Int) throws {
        guard token == current else { return }
        if !paused && !engine.isRunning { engine.prepare(); try engine.start() }
        guard let buffer = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: AVAudioFrameCount(wave.samples.count)),
              let destination = buffer.floatChannelData?[0] else { throw ReaderError.invalid("无法准备本地语音播放。") }
        buffer.frameLength = buffer.frameCapacity
        wave.samples.withUnsafeBufferPointer { source in destination.update(from: source.baseAddress!, count: source.count) }
        queued += 1
        measurement.chunks += 1
        measurement.generatedSeconds += wave.generationSeconds; measurement.audioSeconds += wave.duration
        measurement.rtf.append(wave.generationSeconds / wave.duration)
        if wave.cacheHit { measurement.cacheHits += 1 }
        measurement.peakQueuedBuffers = max(measurement.peakQueuedBuffers, queued)
        player.scheduleBuffer(buffer, completionCallbackType: .dataPlayedBack) { [weak self] _ in
            Task { @MainActor in self?.didPlay(part, token: current) }
        }
        if !hasStarted {
            hasStarted = true
            measurement.firstScheduledSeconds = ProcessInfo.processInfo.systemUptime - requestedAt
            onEvent?(.range(startUTF16: part.startUTF16, length: 0))
            onEvent?(.started)
        }
        onEvent?(.preparing(false))
        if !paused && !player.isPlaying { player.play() }
    }
    private func didPlay(_ part: SpeechChunk, token current: Int) {
        guard token == current else { return }
        queued -= 1; completed += 1
        // Commit only audio confirmed played, never a synthesized future buffer.
        onEvent?(.range(startUTF16: part.endUTF16, length: 0))
        signalSpace()
        if completed == planned { onEvent?(.preparing(false)); onEvent?(.finished) }
        else if queued == 0 && !paused { measurement.underflows += 1; onEvent?(.preparing(true)) }
    }
    func pause() { paused = true; player.pause() }
    func resume() throws {
        if queued > 0 {
            if !engine.isRunning { try engine.start() }
            player.play()
        }
        paused = false
    }
    func cancel() { invalidate(stopEngine: true) }
    private func invalidate(stopEngine: Bool) {
        token += 1; task?.cancel(); task = nil
        prefetchTask?.cancel(); prefetchTask = nil; lookahead = nil
        model?.cancel(); player.stop()
        if stopEngine { engine.stop() }
        queued = 0; completed = 0; planned = 0; signalSpace()
    }
    private func signalSpace() { let waiting = spaceWaiter; spaceWaiter = nil; waiting?.resume() }
    func prefetch(_ request: SpeechRequest) { lookahead = request; startLookaheadIfUseful() }
    private func startLookaheadIfUseful() {
        guard queued >= 2, let request = lookahead, let model else { return }
        lookahead = nil
        prefetchTask = Task(priority: .utility) {
            do {
                let parts = try await model.plan(request.chunk.text, context: request.contextText, startUTF16: request.chunk.startUTF16)
                // Only one next request and its first two short clauses, not a book.
                for part in parts.prefix(2) {
                    try Task.checkCancellation()
                    _ = try await model.wave(part: part, speed: request.rate)
                }
            } catch { /* opportunistic prefetch; foreground reports actual errors */ }
        }
    }
    // A mixer probe is used only by original-text native tests. A simulator probe
    // is not a physical microphone measurement or an iPhone latency claim.
    func installTestOutputProbe(_ block: @escaping AVAudioNodeTapBlock) {
        engine.mainMixerNode.installTap(onBus: 0, bufferSize: 512, format: nil, block: block)
    }
    func removeTestOutputProbe() { engine.mainMixerNode.removeTap(onBus: 0) }
}
