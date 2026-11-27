import XCTest
@testable import EBook

final class EPUBCompatibilityTests: XCTestCase {
    private var temporary: URL!
    override func setUpWithError() throws {
        temporary = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: temporary, withIntermediateDirectories: true)
    }
    override func tearDownWithError() throws { try FileManager.default.removeItem(at: temporary) }
    private func fixture(_ name: String) throws -> URL {
        try XCTUnwrap(Bundle(for: Self.self).resourceURL).appendingPathComponent("Fixtures/\(name)")
    }
    private func imported(_ name: String) throws -> (BookDocument, String) {
        let storage = try BookStorage(root: temporary.appendingPathComponent(name))
        let record = try BookImporter.importFile(fixture(name), storage: storage)
        let document = try storage.document(for: record.id)
        return (document, try document.blocks.map { try storage.text(for: $0, book: record.id) }.joined())
    }
    func testBareHTMLVoidElementsPreserveEveryChapterTextImageAndTOC() throws {
        let (document, text) = try imported("compat_void.epub")
        XCTAssertEqual(document.title, "合成的清晨"); XCTAssertEqual(document.author, "测试作者")
        XCTAssertEqual(document.chapters.count, 2)
        XCTAssertEqual(document.toc.map(\.title), ["晨光", "回声"])
        XCTAssertGreaterThan(document.toc[1].block, document.toc[0].block)
        for phrase in ["换行前", "换行后。", "原有闭合换行。", "她说：这段内容是我们自己写的。😀", "最后一段仍然保留。", "风从窗边经过。测试结束。"] {
            XCTAssertTrue(text.contains(phrase), "Missing original fixture phrase: \(phrase)")
        }
        XCTAssertEqual(document.blocks.filter { $0.imagePath != nil }.count, 1)
        XCTAssertTrue(document.blocks.allSatisfy { $0.utf16Count <= 1600 })
    }
    func testUTF16BothByteOrdersWithAndWithoutBOMRetainChineseAndEmoji() throws {
        for variant in ["le", "be", "le_nobom", "be_nobom"] {
            let (_, text) = try imported("compat_void_\(variant).epub")
            XCTAssertTrue(text.contains("换行前")); XCTAssertTrue(text.contains("换行后。"))
            XCTAssertTrue(text.contains("她说：这段内容是我们自己写的。😀"))
            XCTAssertFalse(text.contains("\u{FFFD}"))
        }
    }
    func testCommentsCDATAQuotedAttributesAndPairedTagsAreNotRewritten() throws {
        let (_, text) = try imported("compat_literals.epub")
        for phrase in ["字面 <br> 不应被改写。", "引号属性后的正文。", "成对内容保留。", "未闭合换行之后的原创句子。"] {
            XCTAssertTrue(text.contains(phrase))
        }
        XCTAssertFalse(text.contains("字面 <br/>")); XCTAssertFalse(text.contains("is a comment"))
    }
    func testMalformedNestingAndTruncationStillFailWithoutPartialBooks() throws {
        let storage = try BookStorage(root: temporary.appendingPathComponent("Library"))
        for name in ["compat_bad_nesting.epub", "compat_bad_attribute.epub", "compat_truncated.epub"] {
            XCTAssertThrowsError(try BookImporter.importFile(fixture(name), storage: storage))
        }
        XCTAssertTrue(try FileManager.default.contentsOfDirectory(atPath: storage.root.appendingPathComponent("Books").path).isEmpty)
    }
    func testEntityDeclarationsAndLimitsRemainForbiddenAfterCompatibilityRepair() throws {
        let storage = try BookStorage(root: temporary.appendingPathComponent("Library"))
        for variant in ["file", "remote", "internal", "le", "be"] {
            XCTAssertThrowsError(try BookImporter.importFile(fixture("compat_entity_\(variant).epub"), storage: storage)) { error in
                guard let readerError = error as? ReaderError, case .unsupported = readerError else {
                    return XCTFail("Entity refusal must not be a recoverable XML error")
                }
            }
        }
        XCTAssertTrue(try FileManager.default.contentsOfDirectory(atPath: storage.root.appendingPathComponent("Books").path).isEmpty)
        XCTAssertNil(XHTMLVoidRepair.repair(Data(repeating: 32, count: 8 * 1024 * 1024 + 1)))
        let tooDeep = "<html>" + String(repeating: "<div>", count: 129) + "<br>" + String(repeating: "</div>", count: 129) + "</html>"
        XCTAssertNil(XHTMLVoidRepair.repair(Data(tooDeep.utf8)))
        let tooMany = "<html>" + String(repeating: "<br>", count: 100_001) + "</html>"
        XCTAssertNil(XHTMLVoidRepair.repair(Data(tooMany.utf8)))
    }
}
