import Foundation
import CryptoKit
import Darwin
import SherpaOnnx

public enum SpikeError: Error {
    case invalidRequest, invalidManifest, invalidAsset(String), initializationFailed
    case invalidWaveform, incompleteGeneration, saveFailed
}

public enum SpikePlatform {
    public static var name: String {
        #if os(iOS) && targetEnvironment(simulator)
        return "IOS_SIMULATOR"
        #elseif os(iOS)
        return "IOS_PHYSICAL_DEVICE"
        #else
        return "MACOS_DESKTOP_NOT_IOS"
        #endif
    }
}

public struct AssetManifest: Decodable {
    public struct Entry: Decodable {
        public let path: String
        public let bytes: Int64
        public let sha256: String
    }
    public let files: [Entry]

    public static func validate(directory: URL, manifestURL: URL) throws {
        let manifest = try JSONDecoder().decode(AssetManifest.self, from: Data(contentsOf: manifestURL))
        guard !manifest.files.isEmpty else { throw SpikeError.invalidManifest }
        let root = directory.resolvingSymlinksInPath().standardizedFileURL
        for item in manifest.files {
            let parts = item.path.split(separator: "/")
            guard !item.path.hasPrefix("/"), !item.path.contains("\\"),
                  !item.path.contains(":"), !parts.contains("..") else { throw SpikeError.invalidManifest }
            let file = root.appendingPathComponent(item.path).resolvingSymlinksInPath().standardizedFileURL
            guard file.path.hasPrefix(root.path + "/") else { throw SpikeError.invalidManifest }
            let attributes = try FileManager.default.attributesOfItem(atPath: file.path)
            guard (attributes[.size] as? NSNumber)?.int64Value == item.bytes,
                  try digest(file) == item.sha256 else { throw SpikeError.invalidAsset(item.path) }
        }
    }

    public static func digest(_ file: URL) throws -> String {
        guard let stream = InputStream(url: file) else { throw SpikeError.invalidAsset(file.lastPathComponent) }
        stream.open()
        defer { stream.close() }
        var hash = SHA256()
        var buffer = [UInt8](repeating: 0, count: 1024 * 1024)
        while true {
            let count = stream.read(&buffer, maxLength: buffer.count)
            if count < 0 { throw stream.streamError ?? SpikeError.invalidAsset(file.lastPathComponent) }
            if count == 0 { break }
            hash.update(data: Data(buffer.prefix(count)))
        }
        return hash.finalize().map { String(format: "%02x", $0) }.joined()
    }
}

public struct ChunkMeasurement {
    public let file: URL
    public let sampleRate: Int
    public let frames: Int
    public let rms: Double
    public let firstCallbackSeconds: Double
    public let generationSeconds: Double
    public let peakProcessRSSBytes: UInt64
    public var durationSeconds: Double { Double(frames) / Double(sampleRate) }
    public var rtf: Double { generationSeconds / durationSeconds }
}

private final class CallbackClock {
    let start = ProcessInfo.processInfo.systemUptime
    var first: Double?
    var progress: Float = 0
}

/// Isolated synchronous spike. Caller must serialize this work off the UI thread.
/// One engine, <=240 Unicode scalars per request, one returned waveform per call.
public final class KokoroSpike {
    public static let speakers = ["zf_001": 3, "zf_002": 4, "zm_009": 58]
    public let initializationSeconds: Double
    private let engine: SherpaOnnxOfflineTtsWrapper
    private let lock = NSLock()

    public init(modelDirectory: URL) throws {
        func path(_ name: String) -> String { modelDirectory.appendingPathComponent(name).path }
        let kokoro = sherpaOnnxOfflineTtsKokoroModelConfig(
            model: path("model.int8.onnx"), voices: path("voices.bin"), tokens: path("tokens.txt"),
            lexicon: ["lexicon-us-en.txt", "lexicon-zh.txt"].map(path).joined(separator: ","))
        // v2.0.3 lexicon frontend: do not invoke deprecated eSpeak/dataDir path.
        let model = sherpaOnnxOfflineTtsModelConfig(kokoro: kokoro, numThreads: 4, debug: 0, provider: "cpu")
        var config = sherpaOnnxOfflineTtsConfig(model: model,
            ruleFsts: ["date-zh.fst", "number-zh.fst", "phone-zh.fst"].map(path).joined(separator: ","),
            maxNumSentences: 1)
        let start = ProcessInfo.processInfo.systemUptime
        engine = SherpaOnnxOfflineTtsWrapper(config: &config)
        initializationSeconds = ProcessInfo.processInfo.systemUptime - start
        guard engine.tts != nil, engine.numSpeakers == 103, engine.sampleRate == 24000 else {
            throw SpikeError.initializationFailed
        }
    }

    public func synthesize(text: String, voice: String, speed: Float, output: URL) throws -> ChunkMeasurement {
        guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
              text.unicodeScalars.count <= 240, speed.isFinite, (0.5...2.0).contains(speed),
              let sid = Self.speakers[voice] else { throw SpikeError.invalidRequest }
        guard !FileManager.default.fileExists(atPath: output.path) else { throw SpikeError.saveFailed }
        lock.lock()
        defer { lock.unlock() }
        let clock = CallbackClock()
        let callback: TtsProgressCallbackWithArg = { _, count, progress, raw in
            guard let raw else { return 0 }
            let clock = Unmanaged<CallbackClock>.fromOpaque(raw).takeUnretainedValue()
            if count > 0 && clock.first == nil {
                clock.first = ProcessInfo.processInfo.systemUptime - clock.start
            }
            clock.progress = progress
            return 1
        }
        let audio = engine.generateWithConfig(text: text,
            config: SherpaOnnxGenerationConfigSwift(speed: speed, sid: sid), callback: callback,
            arg: Unmanaged.passUnretained(clock).toOpaque())
        let elapsed = ProcessInfo.processInfo.systemUptime - clock.start
        guard let first = clock.first, clock.progress >= 0.999 else { throw SpikeError.incompleteGeneration }
        let samples = audio.samples
        guard audio.sampleRate == 24000, !samples.isEmpty, samples.allSatisfy({ $0.isFinite }) else {
            throw SpikeError.invalidWaveform
        }
        let rms = sqrt(samples.reduce(0.0) { $0 + Double($1) * Double($1) } / Double(samples.count))
        guard rms > 0.001 else { throw SpikeError.invalidWaveform }
        guard audio.save(filename: output.path) == 1 else { throw SpikeError.saveFailed }
        var usage = rusage()
        guard getrusage(RUSAGE_SELF, &usage) == 0 else { throw SpikeError.invalidWaveform }
        return ChunkMeasurement(file: output, sampleRate: Int(audio.sampleRate), frames: samples.count, rms: rms,
            firstCallbackSeconds: first, generationSeconds: elapsed,
            peakProcessRSSBytes: UInt64(max(0, usage.ru_maxrss))) // Darwin reports bytes.
    }
}
