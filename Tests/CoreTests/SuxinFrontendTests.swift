import XCTest
@testable import EBook

final class SuxinFrontendTests: XCTestCase {
    private struct Oracle: Decodable {
        struct Item: Decodable { let id: String; let text: String; let ids: [Int64]; let phonemes: [String] }
        let cases: [Item]
    }
    private func frontend() throws -> SuxinFrontend {
        let root = try XCTUnwrap(Bundle.main.url(forResource: "Suxin", withExtension: nil))
        return try SuxinFrontend(lexicon: Data(contentsOf: root.appendingPathComponent("lexicon.json")),
            syllables: Data(contentsOf: root.appendingPathComponent("syllables.json")),
            modelConfig: Data(contentsOf: root.appendingPathComponent("config.json")))
    }
    func testNativeArbitraryTextMatchesPinnedAuthorOn92OriginalCases() throws {
        let url = try XCTUnwrap(Bundle(for: Self.self).url(forResource: "suxin-frontend-oracle", withExtension: "json", subdirectory: "Fixtures"))
        let oracle = try JSONDecoder().decode(Oracle.self, from: Data(contentsOf: url))
        XCTAssertEqual(oracle.cases.count, 92)
        let native = try frontend()
        for row in oracle.cases {
            XCTAssertEqual(try native.phonemes(row.text), row.phonemes, row.id)
            XCTAssertEqual(try native.prepare(row.text), row.ids, row.id)
        }
    }
    func testUnsupportedEnglishAndSymbolsRequireExplicitSystemFallback() throws {
        let native = try frontend()
        for text in ["请按Play开始。", "Reader与Wi-Fi", "123456", "前面有🙂", "新书Ω测试", "<en>hello</en>"] {
            XCTAssertThrowsError(try native.prepare(text))
        }
    }
    func testUnseenMandarinIsNotAStoredFiveCaseIDLookup() throws {
        let native = try frontend()
        let first = try native.prepare("春天到了，窗台上多了一盆小花。")
        let second = try native.prepare("春天到了，窗台上多了两盆小花。")
        XCTAssertGreaterThan(first.count, 30)
        XCTAssertNotEqual(first, second)
        XCTAssertEqual(first.first, 1)
        XCTAssertEqual(first.last, 2)
    }
}
