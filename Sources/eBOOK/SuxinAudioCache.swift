import Foundation
import CryptoKit

/// App-private, opaque identities. No book text, model or waveform in logs.
/// Used only from the model actor; at most 64 MiB on disk, no in-memory LRU.
struct SuxinAudioCache {
    let root: URL
    let maximumBytes: Int
    init(root: URL, maximumBytes: Int = 64 * 1024 * 1024) {
        self.root = root; self.maximumBytes = maximumBytes
    }
    static func key(text: String, speed: Float, resources: String, phonemeIDs: [Int64] = []) -> String {
        let textHash = SHA256.hash(data: Data(text.utf8)).map { String(format: "%02x", $0) }.joined()
        let inputHash = SHA256.hash(data: Data(phonemeIDs.map(String.init).joined(separator: ",").utf8))
            .map { String(format: "%02x", $0) }.joined()
        let identity = "pcm-f32le-v2-context:suxin.local.zh:\(resources):\(textHash):\(inputHash):\(speed.bitPattern)"
        return SHA256.hash(data: Data(identity.utf8)).map { String(format: "%02x", $0) }.joined()
    }
    private func url(_ key: String) -> URL { root.appendingPathComponent(key + ".pcm") }
    func load(_ key: String) -> [Float]? {
        let target = url(key)
        guard let size = try? target.resourceValues(forKeys: [.fileSizeKey]).fileSize,
              size > 32, size <= 22050 * 30 * 4 + 32, (size - 32) % 4 == 0,
              let data = try? Data(contentsOf: target) else { return nil }
        let payload = Data(data.dropFirst(32))
        guard Data(SHA256.hash(data: payload)) == data.prefix(32) else {
            try? FileManager.default.removeItem(at: target); return nil
        }
        var values = [Float](repeating: 0, count: payload.count / 4)
        _ = values.withUnsafeMutableBytes { payload.copyBytes(to: $0) }
        guard values.allSatisfy({ $0.isFinite }),
              values.reduce(0.0, { $0 + Double($1) * Double($1) }) / Double(values.count) > 0.000001 else {
            try? FileManager.default.removeItem(at: target); return nil
        }
        try? FileManager.default.setAttributes([.modificationDate: Date()], ofItemAtPath: target.path)
        return values
    }
    func store(_ samples: [Float], key: String) throws {
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        var directory = root; var flags = URLResourceValues(); flags.isExcludedFromBackup = true
        try directory.setResourceValues(flags)
        let payload = samples.withUnsafeBytes { Data($0) }
        let bytes = Data(SHA256.hash(data: payload)) + payload
        guard bytes.count <= maximumBytes else { return }
        try bytes.write(to: url(key), options: .atomic)
        let files = try FileManager.default.contentsOfDirectory(at: root, includingPropertiesForKeys: [.fileSizeKey, .contentModificationDateKey])
            .filter { $0.pathExtension == "pcm" }
            .compactMap { file -> (URL, Int, Date)? in
                guard let values = try? file.resourceValues(forKeys: [.fileSizeKey, .contentModificationDateKey]),
                      let size = values.fileSize else { return nil }
                return (file, size, values.contentModificationDate ?? .distantPast)
            }.sorted { $0.2 < $1.2 }
        var total = files.reduce(0) { $0 + $1.1 }
        for (file, size, _) in files where total > maximumBytes {
            try FileManager.default.removeItem(at: file); total -= size
        }
    }
}
