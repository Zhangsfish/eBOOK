import XCTest
import Darwin
@testable import EBook

final class ReaderCoreTests: XCTestCase {
    private var temporary: URL!
    override func setUpWithError() throws {
        temporary = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: temporary, withIntermediateDirectories: true)
    }
    override func tearDownWithError() throws { try FileManager.default.removeItem(at: temporary) }
    private func fixture(_ name: String) throws -> URL {
        let root = try XCTUnwrap(Bundle(for: Self.self).resourceURL)
        let url = root.appendingPathComponent("Fixtures/\(name)")
        XCTAssertTrue(FileManager.default.fileExists(atPath: url.path), "Missing test fixture \(name)")
        return url
    }
    private func storage() throws -> BookStorage { try BookStorage(root: temporary.appendingPathComponent("Library")) }
    private func synthetic(_ text: String, name: String = "local.txt") throws -> URL {
        let url = temporary.appendingPathComponent(name)
        try Data(text.utf8).write(to: url); return url
    }

    func testEveryRequiredEncodingStrictlyDecodesChineseAndDialogue() throws {
        let variants: [(String, TextEncoding)] = [("utf8", .utf8), ("utf8_bom", .utf8), ("utf16le", .utf16LE), ("utf16be", .utf16BE), ("gbk", .gbk), ("gb18030", .gb18030)]
        for (name, encoding) in variants {
            let decoded = try TextDecoder.decode(Data(contentsOf: fixture("sample_\(name).txt")))
            XCTAssertEqual(decoded.encoding, encoding)
            XCTAssertTrue(decoded.text.contains("她说：‘今天读一段自己写的故事。’"))
            XCTAssertTrue(decoded.text.contains("\n\n002小路\n"))
            XCTAssertFalse(decoded.text.contains("\r")); XCTAssertFalse(decoded.text.contains("\u{FFFD}"))
            if encoding == .gb18030 { XCTAssertTrue(decoded.text.contains("𠀀与😀")) }
        }
    }

    func testUTF16WithAndWithoutBOMAndExplicitEncodingHint() throws {
        let text = "Hello 中文\n第二段。"
        for (ns, encoding) in [(String.Encoding.utf16LittleEndian, TextEncoding.utf16LE), (.utf16BigEndian, .utf16BE)] {
            let data = try XCTUnwrap(text.data(using: ns))
            XCTAssertEqual(try TextDecoder.decode(data).text, text)
            XCTAssertEqual(try TextDecoder.decode(data, hint: encoding).encoding, encoding)
        }
        let chineseOnly = "中文正文"
        let data = try XCTUnwrap(chineseOnly.data(using: .utf16BigEndian))
        XCTAssertEqual(try TextDecoder.decode(data, hint: .utf16BE).text, chineseOnly)
    }

    func testRejectsTruncationBinaryLossyReplacementAndWrongHint() throws {
        for data in [Data(), Data([0xFF]), Data([0x81, 0x30, 0x81]), Data([0xFF, 0xFE, 0x00]),
                     Data([0xFF, 0xFE, 0x00, 0xD8]), Data([0xFE, 0xFF, 0xDC, 0x00]),
                     Data([0xFF, 0xFE, 0, 0, 0, 0, 0, 0]), Data("hello\0binary".utf8), Data("坏\u{FFFD}字符".utf8)] {
            XCTAssertThrowsError(try TextDecoder.decode(data))
        }
        XCTAssertThrowsError(try TextDecoder.decode(Data([0xC0, 0xAF]), hint: .utf8))
        XCTAssertThrowsError(try TextDecoder.decode(Data(contentsOf: fixture("sample_gb18030.txt")), hint: .gbk))
    }

    func testMixedChapterFormsAndConservativeFallback() {
        let headings = TXTHeadings.detect(in: "001晨光\n正文。\n002小路\n正文。\n003归来\n正文。\n第4章 后来\n正文。\n5.第五章回声\n正文。\n后记\n结束。")
        XCTAssertEqual(headings.count, 6)
        XCTAssertEqual(headings[0], "001晨光")
        XCTAssertEqual(headings[8], "5.第五章回声")
        for text in ["1. 买纸\n2. 写字\n3. 读书", "001我只是一个项目。\n002另一个项目。", "001孤立的数字标题\n正文。", "001项目\n003不连续\n009不连续"] {
            XCTAssertTrue(TXTHeadings.detect(in: text).isEmpty)
        }
    }

    func testChunkingPreservesTextOffsetsAndSurrogateBoundaries() {
        let text = String(repeating: "她说：“你好😀。”\n第二段没有句号", count: 80)
        let chunks = TextChunker.chunks(text, maximumUTF16: 72)
        XCTAssertEqual(chunks.map(\.text).joined(), text)
        XCTAssertEqual(chunks.first?.startUTF16, 0)
        XCTAssertEqual(chunks.last?.endUTF16, text.utf16.count)
        for chunk in chunks {
            XCTAssertLessThanOrEqual(chunk.text.utf16.count, 72)
            XCTAssertEqual(chunk.text.utf16.count, chunk.endUTF16 - chunk.startUTF16)
            XCTAssertFalse(chunk.text.contains("\u{FFFD}"))
        }
        let resumed = TextChunker.chunks("😀你好。", startUTF16: 1)
        XCTAssertEqual(resumed.first?.startUTF16, 2)
        XCTAssertEqual(resumed.map(\.text).joined(), "你好。")
        let hugeGrapheme = "a" + String(repeating: "\u{0301}", count: 10_000)
        XCTAssertTrue(TextChunker.chunks(hugeGrapheme).allSatisfy { $0.text.utf16.count <= 280 })
    }

    func testTXTImportAtomicStorageReadingAndListeningPersistence() throws {
        let storage = try storage()
        let record = try BookImporter.importFile(fixture("sample_gbk.txt"), storage: storage)
        let document = try storage.document(for: record.id)
        XCTAssertEqual(document.encoding, .gbk); XCTAssertEqual(document.toc.count, 4)
        XCTAssertTrue(document.heuristicTOC)
        XCTAssertTrue(try storage.text(for: document.blocks[0], book: record.id).contains("001晨光"))
        var state = LibraryState(); state.books = [record]
        state.books[0].reading = ReadingAnchor(block: 2, fraction: 0.35)
        state.books[0].listening = TextPosition(block: 1, utf16Offset: 9)
        state.preferences.theme = .dark; state.preferences.fontSize = 27; state.preferences.lineSpacing = 12
        state.preferences.speechRate = 0.6; state.preferences.voiceIdentifier = "test-local-voice"
        try storage.saveLibrary(state)
        let reopened = try BookStorage(root: storage.root).loadLibrary()
        XCTAssertEqual(reopened.books[0].reading, state.books[0].reading)
        XCTAssertEqual(reopened.books[0].listening, state.books[0].listening)
        XCTAssertEqual(reopened.preferences, state.preferences)
        let removed = try storage.remove(record.id, from: reopened)
        XCTAssertTrue(removed.books.isEmpty)
        XCTAssertFalse(FileManager.default.fileExists(atPath: storage.directory(for: record.id).path))
        XCTAssertTrue(FileManager.default.fileExists(atPath: try fixture("sample_gbk.txt").path))
    }

    func testNoHeadingFallbackAndVeryLongSingleParagraphRemainBounded() throws {
        let storage = try storage()
        let url = try synthetic(String(repeating: "正文与😀，", count: 20_000))
        let record = try BookImporter.importFile(url, storage: storage)
        let doc = try storage.document(for: record.id)
        XCTAssertTrue(doc.toc.isEmpty); XCTAssertFalse(doc.heuristicTOC)
        XCTAssertGreaterThan(doc.blocks.count, 50)
        for block in doc.blocks { XCTAssertLessThanOrEqual(block.utf16Count, 1600) }
        let restored = try doc.blocks.map { try storage.text(for: $0, book: record.id) }.joined()
        XCTAssertEqual(restored, String(repeating: "正文与😀，", count: 20_000))
    }

    func testEPUB3MetadataSpineFragmentTOCAndLocalImages() throws {
        let storage = try storage()
        let book = try BookImporter.importFile(fixture("synthetic.epub"), storage: storage)
        let doc = try storage.document(for: book.id)
        XCTAssertEqual(doc.title, "合成的清晨"); XCTAssertEqual(doc.author, "测试作者")
        XCTAssertEqual(doc.chapters.count, 2)
        XCTAssertEqual(doc.toc.map(\.title), ["晨光", "对话", "回声"])
        XCTAssertGreaterThan(doc.toc[1].block, doc.toc[0].block)
        XCTAssertEqual(doc.toc[1].depth, 1)
        let text = try doc.blocks.map { try storage.text(for: $0, book: book.id) }.joined()
        XCTAssertTrue(text.contains("斜体中的文字也要保留。"))
        XCTAssertFalse(text.contains("不应显示的脚本")); XCTAssertFalse(text.contains("body{color:red}"))
        let image = try XCTUnwrap(doc.blocks.first { $0.imagePath != nil })
        XCTAssertTrue(FileManager.default.fileExists(atPath: storage.directory(for: book.id).appendingPathComponent(image.imagePath!).path))
        XCTAssertEqual(image.imageDescription, "原创测试像素")
    }

    func testEPUB2NCXNavigation() throws {
        let storage = try storage()
        let book = try BookImporter.importFile(fixture("synthetic_ncx.epub"), storage: storage)
        let doc = try storage.document(for: book.id)
        XCTAssertEqual(doc.toc.map(\.title), ["晨光", "回声"])
        XCTAssertGreaterThan(doc.toc[1].block, doc.toc[0].block)
    }

    func testMalformedEPUBTraversalEntitiesAndFailedImportLeaveNoPartialBook() throws {
        let storage = try storage()
        for name in ["unsafe_path.epub", "unsafe_entity.epub", "bad_spine.epub"] {
            XCTAssertThrowsError(try BookImporter.importFile(fixture(name), storage: storage))
        }
        let valid = try Data(contentsOf: fixture("synthetic.epub"))
        for length in [1, 20, valid.count / 2, valid.count - 4] {
            let url = temporary.appendingPathComponent("truncated.epub")
            try valid.prefix(length).write(to: url)
            XCTAssertThrowsError(try BookImporter.importFile(url, storage: storage))
        }
        let children = try FileManager.default.contentsOfDirectory(atPath: storage.root.path)
        XCTAssertEqual(children, ["Books"])
        XCTAssertTrue(try FileManager.default.contentsOfDirectory(atPath: storage.root.appendingPathComponent("Books").path).isEmpty)
    }

    func testZIPCRCAndDeclaredExpansionLimitsAreEnforced() throws {
        var data = try Data(contentsOf: fixture("synthetic.epub"))
        let signature = Data([0x50, 0x4B, 0x01, 0x02])
        let central = try XCTUnwrap(data.range(of: signature)).lowerBound
        data[central + 16] ^= 1
        let archive = try ZIPArchive(data: data)
        XCTAssertThrowsError(try archive.read("mimetype"))
        var oversized = try Data(contentsOf: fixture("synthetic.epub"))
        oversized.replaceSubrange(central + 24..<central + 28, with: [0, 0, 0, 0x20])
        XCTAssertThrowsError(try ZIPArchive(data: oversized))
    }

    func testOversizedUnsupportedAndCorruptLibraryErrors() throws {
        let storage = try storage()
        let url = try synthetic("text", name: "book.zip")
        XCTAssertThrowsError(try BookImporter.importFile(url, storage: storage))
        let large = temporary.appendingPathComponent("oversized.txt")
        FileManager.default.createFile(atPath: large.path, contents: nil)
        let handle = try FileHandle(forWritingTo: large)
        try handle.truncate(atOffset: UInt64(TextDecoder.maximumBytes + 1)); try handle.close()
        XCTAssertThrowsError(try BookImporter.importFile(large, storage: storage))
        try Data("not json".utf8).write(to: storage.root.appendingPathComponent("library.json"))
        XCTAssertThrowsError(try storage.loadLibrary())
    }

    func testGeneratedLongGB18030ImportNavigationReadMemoryAndReopen() throws {
        let url = try XCTUnwrap(Bundle(for: Self.self).url(forResource: "synthetic_long_gb18030", withExtension: "txt"))
        let data = try Data(contentsOf: url)
        XCTAssertEqual(data.count, 4_236_594)
        let decoded = try TextDecoder.decode(data)
        XCTAssertEqual(decoded.encoding, .gbk) // Fixture deliberately uses the shared GBK repertoire.
        XCTAssertEqual(decoded.text.count, 2_228_307) // CRLF -> LF removes 73,175 scalars.
        XCTAssertEqual(TXTHeadings.detect(in: decoded.text).count, 625)
        let storage = try storage()
        var before = rusage(); getrusage(RUSAGE_SELF, &before)
        let start = Date()
        let book = try BookImporter.importFile(url, storage: storage)
        let elapsed = Date().timeIntervalSince(start)
        let doc = try storage.document(for: book.id)
        XCTAssertEqual(doc.chapters.count, 625); XCTAssertEqual(doc.toc.count, 625)
        XCTAssertEqual(doc.toc[0].title, "001雾夜来信")
        XCTAssertTrue(doc.toc.contains { $0.title.hasPrefix("221.第221章") })
        XCTAssertEqual(doc.toc.last?.title, "第625章 后记")
        XCTAssertTrue(doc.blocks.allSatisfy { $0.utf16Count <= 1600 })
        XCTAssertGreaterThan(doc.blocks.count, 1000)
        XCTAssertLessThan(elapsed, 90)
        // Read the same bounded blocks many times; the storage layer retains no decoded book/cache.
        for pass in 0..<4 {
            for index in stride(from: pass, to: doc.blocks.count, by: 5) {
                let text = try storage.text(for: doc.blocks[index], book: book.id)
                XCTAssertLessThanOrEqual(text.utf16.count, 1600)
            }
        }
        var state = LibraryState(); state.books = [book]
        let target = doc.toc[623].block
        state.books[0].reading = ReadingAnchor(block: target, fraction: 0.42)
        state.books[0].listening = TextPosition(block: doc.toc[220].block, utf16Offset: 15)
        try storage.saveLibrary(state)
        let reopened = try BookStorage(root: storage.root).loadLibrary()
        XCTAssertEqual(reopened.books[0].reading, state.books[0].reading)
        XCTAssertEqual(reopened.books[0].listening, state.books[0].listening)
        XCTAssertTrue(try storage.text(for: doc.blocks[target], book: book.id).hasPrefix("第624章"))
        for progress in [0.0, 0.25, 0.5, 0.99, 1.0] {
            let index = doc.block(atProgress: progress)
            XCTAssertTrue(doc.blocks.indices.contains(index))
        }
        var after = rusage(); getrusage(RUSAGE_SELF, &after)
        let peakIncrease = max(0, after.ru_maxrss - before.ru_maxrss)
        XCTAssertLessThan(peakIncrease, 180 * 1024 * 1024)
        let metrics = "S00_LONG_METRICS import_seconds=\(elapsed) blocks=\(doc.blocks.count) chapters=\(doc.chapters.count) max_block_utf16=\(doc.blocks.map(\.utf16Count).max() ?? 0) process_peak_rss_bytes=\(after.ru_maxrss) peak_increase_bytes=\(peakIncrease)"
        print(metrics)
        let attachment = XCTAttachment(string: metrics); attachment.name = "long-book-metrics"; attachment.lifetime = .keepAlways; add(attachment)
    }
}
