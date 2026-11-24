import Foundation
import Darwin
import SherpaOnnx

private final class MatchaCallbackClock {
    let start = ProcessInfo.processInfo.systemUptime
    var first: Double?
    var progress: Float = 0
}

/// Single speaker, CPU only, same bounded original corpus as the Kokoro spike.
public final class MatchaSpike {
    private let engine: SherpaOnnxOfflineTtsWrapper
    public let initializationSeconds: Double

    public init(modelDirectory: URL, threads: Int = 2) throws {
        guard (1...4).contains(threads) else { throw SpikeError.invalidRequest }
        func path(_ name: String) -> String { modelDirectory.appendingPathComponent(name).path }
        let matcha = sherpaOnnxOfflineTtsMatchaModelConfig(
            acousticModel: path("model-steps-3.onnx"), vocoder: path("vocos-22khz-univ.onnx"),
            lexicon: path("lexicon.txt"), tokens: path("tokens.txt"))
        var config = sherpaOnnxOfflineTtsConfig(model: sherpaOnnxOfflineTtsModelConfig(
            matcha: matcha, numThreads: threads, debug: 0, provider: "cpu"),
            ruleFsts: ["phone.fst", "date.fst", "number.fst"].map(path).joined(separator: ","),
            maxNumSentences: 1)
        let start = ProcessInfo.processInfo.systemUptime
        engine = SherpaOnnxOfflineTtsWrapper(config: &config)
        initializationSeconds = ProcessInfo.processInfo.systemUptime - start
        guard engine.tts != nil, engine.numSpeakers == 1, engine.sampleRate == 22050 else {
            throw SpikeError.initializationFailed
        }
    }

    public func synthesize(text: String, output: URL) throws -> ChunkMeasurement {
        guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
              text.unicodeScalars.count <= 240 else { throw SpikeError.invalidRequest }
        guard !FileManager.default.fileExists(atPath: output.path) else { throw SpikeError.saveFailed }
        let clock = MatchaCallbackClock()
        let callback: TtsProgressCallbackWithArg = { _, count, progress, raw in
            guard let raw else { return 0 }
            let state = Unmanaged<MatchaCallbackClock>.fromOpaque(raw).takeUnretainedValue()
            if count > 0 && state.first == nil {
                state.first = ProcessInfo.processInfo.systemUptime - state.start
            }
            state.progress = progress
            return 1
        }
        let audio = engine.generateWithConfig(text: text,
            config: SherpaOnnxGenerationConfigSwift(speed: 1, sid: 0), callback: callback,
            arg: Unmanaged.passUnretained(clock).toOpaque())
        let elapsed = ProcessInfo.processInfo.systemUptime - clock.start
        guard let first = clock.first, clock.progress >= 0.999 else { throw SpikeError.incompleteGeneration }
        let samples = audio.samples
        guard !samples.isEmpty, samples.allSatisfy({ $0.isFinite }), audio.sampleRate == 22050 else {
            throw SpikeError.invalidWaveform
        }
        let rms = sqrt(samples.reduce(0.0) { $0 + Double($1) * Double($1) } / Double(samples.count))
        guard rms > 0.001, audio.save(filename: output.path) == 1 else { throw SpikeError.invalidWaveform }
        var usage = rusage()
        guard getrusage(RUSAGE_SELF, &usage) == 0 else { throw SpikeError.invalidWaveform }
        return ChunkMeasurement(file: output, sampleRate: Int(audio.sampleRate), frames: samples.count,
            rms: rms, firstCallbackSeconds: first, generationSeconds: elapsed,
            peakProcessRSSBytes: UInt64(max(0, usage.ru_maxrss)))
    }
}
