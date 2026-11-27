import XCTest
@testable import EBook

final class SuxinStateTests: XCTestCase {
    func testOldPreferencesMigrateWithoutLosingAppleVoiceOrReaderSettings() throws {
        let old = Data(#"{"fontSize":27,"lineSpacing":12,"theme":"dark","speechRate":0.6,"voiceIdentifier":"saved.apple.voice"}"#.utf8)
        let migrated = try JSONDecoder().decode(ReaderPreferences.self, from: old)
        XCTAssertEqual(migrated.fontSize, 27); XCTAssertEqual(migrated.lineSpacing, 12)
        XCTAssertEqual(migrated.theme, .dark); XCTAssertEqual(migrated.speechRate, 0.6)
        XCTAssertEqual(migrated.voiceIdentifier, "saved.apple.voice"); XCTAssertEqual(migrated.suxinRate, 1)
        XCTAssertEqual(try JSONDecoder().decode(ReaderPreferences.self, from: JSONEncoder().encode(migrated)), migrated)
    }
    func testChunkRangesKeepAllTextAndDoNotSplitNumbers() {
        let text = "窗边的风吹动了厚厚的书页，现在是2026年，时间是12:05。\n\n她读完了这一章，再慢慢地合上书。"
        let parts = SuxinSegmentation.chunks(text)
        XCTAssertEqual(parts.map(\.text).joined(), text)
        XCTAssertTrue(parts.contains { $0.text.contains("2026") }); XCTAssertTrue(parts.contains { $0.text.contains("12:05") })
        XCTAssertLessThanOrEqual(parts[0].text.count, 18)
        var offset = 0
        for part in parts { XCTAssertEqual(part.startUTF16, offset); offset = part.endUTF16 }
        XCTAssertEqual(offset, text.utf16.count)
        for variant in ["\n\n" + text, "……\n" + text, text + "\n——\n" + text] {
            let chunks = SuxinSegmentation.chunks(variant)
            XCTAssertEqual(chunks.map(\.text).joined(), variant)
            XCTAssertTrue(chunks.allSatisfy { $0.text.unicodeScalars.contains { CharacterSet.alphanumerics.contains($0) } },
                          "No standalone whitespace/separator buffer may reach neural inference")
            var end = 0
            for chunk in chunks { XCTAssertEqual(chunk.startUTF16, end); end = chunk.endUTF16 }
            XCTAssertEqual(end, variant.utf16.count)
        }
    }
    func testCacheVersionSpeedCorruptionAndBoundedEviction() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let cache = SuxinAudioCache(root: root, maximumBytes: 1024)
        let key = SuxinAudioCache.key(text: "原创文本", speed: 1, resources: "one")
        XCTAssertNotEqual(key, SuxinAudioCache.key(text: "原创文本", speed: 1.5, resources: "one"))
        XCTAssertNotEqual(key, SuxinAudioCache.key(text: "原创文本", speed: 1, resources: "two"))
        let audio = [Float](repeating: 0.2, count: 120)
        try cache.store(audio, key: key); XCTAssertEqual(cache.load(key), audio)
        var bytes = try Data(contentsOf: root.appendingPathComponent(key + ".pcm")); bytes[40] ^= 1
        try bytes.write(to: root.appendingPathComponent(key + ".pcm"))
        XCTAssertNil(cache.load(key), "Even finite PCM bit corruption must invalidate the file")
        for index in 0..<8 { try cache.store(audio, key: String(index)) }
        let urls = try FileManager.default.contentsOfDirectory(at: root, includingPropertiesForKeys: [.fileSizeKey])
        let total = try urls.reduce(0) { try $0 + ($1.resourceValues(forKeys: [.fileSizeKey]).fileSize ?? 0) }
        XCTAssertLessThanOrEqual(total, 1024)
    }
}
