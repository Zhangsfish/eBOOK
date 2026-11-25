import Foundation
import CryptoKit

struct SuxinResources: Sendable {
    struct Manifest: Decodable {
        struct File: Decodable { let path: String; let bytes: Int; let sha256: String }
        let schema: Int; let modelRevision: String; let frontendVersion: String
        let sampleRate: Int; let files: [File]
    }
    let root: URL
    let fingerprint: String
    let frontend: SuxinFrontend

    static func bundledURL() throws -> URL {
        guard let url = Bundle.main.url(forResource: "Suxin", withExtension: nil) else {
            throw ReaderError.invalid("苏心资源缺失，请改用系统语音或更新应用。")
        }
        return url
    }
    init(root: URL) throws {
        let manifestData = try Data(contentsOf: root.appendingPathComponent("manifest.json"))
        let value = try JSONDecoder().decode(Manifest.self, from: manifestData)
        guard value.schema == 1, value.sampleRate == 22050, value.files.count == 6,
              Set(value.files.map(\.path)) == Set(["model.onnx", "config.json", "lexicon.json", "syllables.json", "author-LICENSE.txt", "pypinyin-LICENSE.txt"]) else {
            throw ReaderError.invalid("苏心资源版本不完整，请更新应用。")
        }
        for file in value.files {
            let url = root.appendingPathComponent(file.path)
            let properties = try url.resourceValues(forKeys: [.isRegularFileKey, .isSymbolicLinkKey, .fileSizeKey])
            guard properties.isRegularFile == true, properties.isSymbolicLink != true,
                  properties.fileSize == file.bytes, try Self.digest(url) == file.sha256 else {
                throw ReaderError.invalid("苏心资源校验失败，请改用系统语音或更新应用。")
            }
        }
        self.root = root
        fingerprint = SHA256.hash(data: manifestData).map { String(format: "%02x", $0) }.joined()
        frontend = try SuxinFrontend(lexicon: Data(contentsOf: root.appendingPathComponent("lexicon.json")),
            syllables: Data(contentsOf: root.appendingPathComponent("syllables.json")),
            modelConfig: Data(contentsOf: root.appendingPathComponent("config.json")))
    }
    private static func digest(_ url: URL) throws -> String {
        let file = try FileHandle(forReadingFrom: url); defer { try? file.close() }
        var hash = SHA256()
        while let bytes = try file.read(upToCount: 1024 * 1024), !bytes.isEmpty { hash.update(data: bytes) }
        return hash.finalize().map { String(format: "%02x", $0) }.joined()
    }
}

/// Only signals cancellation cross-thread. Construction, Run and destruction are
/// serialized by SuxinModel; its lock protects the handle's lifetime for signal().
private final class SuxinHandle: @unchecked Sendable {
    private let lock = NSLock()
    private var pointer: UnsafeMutableRawPointer?
    func install(_ value: UnsafeMutableRawPointer) { lock.lock(); pointer = value; lock.unlock() }
    func cancel() { lock.lock(); if let pointer { EBookSuxinCancel(pointer) }; lock.unlock() }
    func close() { lock.lock(); if let pointer { EBookSuxinDestroy(pointer) }; pointer = nil; lock.unlock() }
}

struct SuxinWave: Sendable {
    let samples: [Float]
    let generationSeconds: Double
    let cacheHit: Bool
    var duration: Double { Double(samples.count) / 22050 }
}

actor SuxinModel {
    static var runtimeVersion: String { String(cString: EBookSuxinRuntimeVersion()) }
    static var processLifetimePeakRSS: UInt64 { EBookSuxinPeakResidentBytes() }
    private let root: URL
    private var resources: SuxinResources?
    private var pointer: UnsafeMutableRawPointer?
    private nonisolated let handle = SuxinHandle()
    private let cache: SuxinAudioCache
    private(set) var initializationSeconds: Double = 0
    init(root: URL, cacheRoot: URL? = nil) {
        self.root = root
        let caches = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask).first!
        cache = SuxinAudioCache(root: cacheRoot ?? caches.appendingPathComponent("SuxinPCM-v1", isDirectory: true))
    }
    deinit { handle.close() }
    nonisolated func cancel() { handle.cancel() }
    func prepare(_ text: String) throws -> [Int64] {
        if resources == nil { resources = try SuxinResources(root: root) }
        return try resources!.frontend.prepare(text)
    }
    func identity() throws -> String {
        if resources == nil { resources = try SuxinResources(root: root) }
        return resources!.fingerprint
    }
    func preflight(_ text: String) throws -> [SpeechChunk] {
        guard text.unicodeScalars.contains(where: { CharacterSet.alphanumerics.contains($0) }) else {
            throw SuxinFrontend.Failure.unsupportedText
        }
        _ = try prepare(text)
        let parts = SuxinSegmentation.chunks(text)
        for part in parts {
            let ids = try prepare(part.text)
            guard ids.count <= 512 else { throw SuxinFrontend.Failure.unsupportedText }
        }
        return parts
    }
    func wave(text: String, speed: Float) throws -> SuxinWave {
        try Task.checkCancellation()
        let ids = try prepare(text)
        let key = SuxinAudioCache.key(text: text, speed: speed, resources: try identity())
        if let samples = cache.load(key) { return SuxinWave(samples: samples, generationSeconds: 0, cacheHit: true) }
        let value = try synthesize(ids, speed: speed)
        try Task.checkCancellation()
        // A full cache/disk is not a reason to interrupt otherwise valid speech.
        try? cache.store(value.samples, key: key)
        return value
    }
    func synthesize(_ ids: [Int64], speed: Float) throws -> SuxinWave {
        try Task.checkCancellation()
        if resources == nil { resources = try SuxinResources(root: root) }
        if pointer == nil {
            var error: UnsafeMutablePointer<CChar>?
            let created = root.appendingPathComponent("model.onnx").path.withCString {
                EBookSuxinCreate($0, 4, &initializationSeconds, &error)
            }
            defer { if let error { EBookSuxinFree(error) } }
            guard let created else { throw ReaderError.invalid("苏心模型未能加载，请改用系统语音。") }
            pointer = created; handle.install(created)
        }
        try Task.checkCancellation()
        var audio: UnsafeMutablePointer<Float>?, count = 0, seconds = 0.0
        var error: UnsafeMutablePointer<CChar>?
        let result = ids.withUnsafeBufferPointer {
            EBookSuxinRun(pointer, $0.baseAddress, $0.count, speed, &audio, &count, &seconds, &error)
        }
        defer { if let audio { EBookSuxinFree(audio) }; if let error { EBookSuxinFree(error) } }
        try Task.checkCancellation()
        guard result == 1, let audio else { throw ReaderError.invalid("苏心朗读暂时不可用，请重试或改用系统语音。") }
        return SuxinWave(samples: Array(UnsafeBufferPointer(start: audio, count: count)), generationSeconds: seconds, cacheHit: false)
    }
}
