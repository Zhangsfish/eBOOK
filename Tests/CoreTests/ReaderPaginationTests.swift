import XCTest
import UIKit
@testable import EBook

@MainActor final class ReaderPaginationTests: XCTestCase {
    private var root: URL!
    override func setUpWithError() throws {
        root = FileManager.default.temporaryDirectory.appendingPathComponent("Pagination-" + UUID().uuidString)
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
    }
    override func tearDownWithError() throws { try FileManager.default.removeItem(at: root) }
    private func book() throws -> (BookStorage, BookRecord, BookDocument) {
        let path = root.appendingPathComponent("原创分页.txt")
        let text = String(repeating: "清晨的小路很安静，小宁拿着一本旧书，慢慢走到窗边。她读完这一段，又望向远处的石桥。\n\n", count: 120)
        try Data(text.utf8).write(to: path)
        let storage = try BookStorage(root: root.appendingPathComponent("Library"))
        let record = try BookImporter.importFile(path, storage: storage)
        return (storage, record, try storage.document(for: record.id))
    }
    func testViewportPagesPreserveAllSourceAndBoundedCaches() throws {
        let (storage, book, document) = try book()
        let expected = try document.blocks.map { try storage.text(for: $0, book: book.id) }.joined()
        var prefs = ReaderPreferences(); prefs.fontSize = 24
        let paginator = ReaderPaginator(document: document, storage: storage, bookID: book.id, preferences: prefs, size: CGSize(width: 240, height: 220))
        var cursor = TextPosition(), output = "", pages = 0
        while let page = try paginator.page(at: cursor) {
            XCTAssertEqual(page.start, cursor)
            XCTAssertNotEqual(page.end, cursor)
            output += page.text.string; cursor = page.end; pages += 1
            if pages > 500 { XCTFail("Pagination must advance and terminate"); break }
        }
        XCTAssertEqual(output, expected)
        XCTAssertGreaterThan(pages, 64)
        XCTAssertLessThanOrEqual(paginator.maximumSourceBlocksObserved, 4)
        XCTAssertLessThanOrEqual(paginator.cachedTextBlocks, 8)
        XCTAssertLessThanOrEqual(paginator.cachedPredecessors, 64)
    }
    func testForwardBackwardAndUncachedJumpRemainContiguous() throws {
        let (storage, book, document) = try book()
        let paginator = ReaderPaginator(document: document, storage: storage, bookID: book.id, preferences: ReaderPreferences(), size: CGSize(width: 320, height: 500))
        let first = try XCTUnwrap(paginator.page(at: TextPosition()))
        let second = try XCTUnwrap(paginator.page(at: first.end))
        let previous = try XCTUnwrap(paginator.previous(before: second.start))
        XCTAssertEqual(previous.start, first.start); XCTAssertEqual(previous.end, second.start)
        XCTAssertEqual(previous.text.string, first.text.string)
        let target = TextPosition(block: 2, utf16Offset: 300)
        let before = try XCTUnwrap(paginator.previous(before: target))
        XCTAssertEqual(before.end, target)
        XCTAssertEqual(try paginator.page(at: before.end)?.start, target)
        XCTAssertNil(try paginator.previous(before: TextPosition()))
        XCTAssertNil(try paginator.page(at: TextPosition(block: document.blocks.count)))
    }
    func testTypographyAndViewportReflowKeepExactSourceStart() throws {
        let (storage, book, document) = try book()
        let small = ReaderPaginator(document: document, storage: storage, bookID: book.id, preferences: ReaderPreferences(), size: CGSize(width: 320, height: 500))
        let first = try XCTUnwrap(small.page(at: TextPosition()))
        let old = try XCTUnwrap(small.page(at: first.end))
        var prefs = ReaderPreferences(); prefs.fontSize = 32; prefs.lineSpacing = 15
        let large = ReaderPaginator(document: document, storage: storage, bookID: book.id, preferences: prefs, size: CGSize(width: 320, height: 500))
        let reflow = try XCTUnwrap(large.page(at: old.start))
        XCTAssertEqual(reflow.start, old.start)
        XCTAssertLessThan(reflow.text.length, old.text.length)
        let rotated = ReaderPaginator(document: document, storage: storage, bookID: book.id, preferences: prefs, size: CGSize(width: 600, height: 300))
        XCTAssertEqual(try rotated.page(at: old.start)?.start, old.start)
    }
    func testEPUBImageOwnPagePreservesFollowingPosition() throws {
        let storage = try BookStorage(root: root.appendingPathComponent("EPUB"))
        let fixture = try XCTUnwrap(Bundle(for: Self.self).url(forResource: "synthetic", withExtension: "epub", subdirectory: "Fixtures"))
        let book = try BookImporter.importFile(fixture, storage: storage)
        let document = try storage.document(for: book.id)
        let index = try XCTUnwrap(document.blocks.firstIndex { $0.imagePath != nil })
        let engine = ReaderPaginator(document: document, storage: storage, bookID: book.id, preferences: ReaderPreferences(), size: CGSize(width: 320, height: 500))
        let page = try XCTUnwrap(engine.page(at: TextPosition(block: index)))
        XCTAssertNotNil(page.image); XCTAssertEqual(page.text.length, 0)
        XCTAssertEqual(page.end, TextPosition(block: index + 1))
    }
    func testLegacyPreferencesAndAnchorsMigrateWithIndependentShelfAppearance() throws {
        let prefs = try JSONDecoder().decode(ReaderPreferences.self, from: Data(#"{"theme":"dark","fontSize":27,"speechRate":0.6}"#.utf8))
        XCTAssertEqual(prefs.theme, .dark); XCTAssertEqual(prefs.shelfAppearance, .system)
        XCTAssertEqual(prefs.readingMode, .vertical)
        let anchor = try JSONDecoder().decode(ReadingAnchor.self, from: Data(#"{"block":3,"fraction":0.4}"#.utf8))
        XCTAssertNil(anchor.utf16Offset)
        let library = LibraryModel(root: root.appendingPathComponent("Preferences"))
        var updated = prefs; updated.shelfAppearance = .light; updated.readingMode = .horizontal
        library.setPreferences(updated)
        let reopened = LibraryModel(root: root.appendingPathComponent("Preferences"))
        XCTAssertEqual(reopened.state.preferences.theme, .dark)
        XCTAssertEqual(reopened.state.preferences.shelfAppearance, .light)
        XCTAssertEqual(reopened.state.preferences.readingMode, .horizontal)
        let precise = ReadingAnchor(block: 3, fraction: 0.4, utf16Offset: 100)
        XCTAssertEqual(try JSONDecoder().decode(ReadingAnchor.self, from: JSONEncoder().encode(precise)), precise)
    }
}
