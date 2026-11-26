import XCTest
@testable import EBook

@MainActor final class SuxinProductionBoundaryTests: XCTestCase {
    private struct Oracle: Decodable {
        struct Item: Decodable { let id: String; let text: String; let ids: [Int64] }
        let cases: [Item]
    }
    private func model() throws -> SuxinModel { SuxinModel(root: try SuxinResources.bundledURL()) }
    private func production(_ text: String, model: SuxinModel) async throws -> [SuxinPreparedPart] {
        let windows = SuxinSegmentation.windows(text)
        XCTAssertEqual(windows.map(\.text).joined(), text)
        var all: [SuxinPreparedPart] = []
        for window in windows {
            let parts = try await model.plan(window.text, context: text, startUTF16: window.startUTF16)
            XCTAssertEqual(parts.map { $0.chunk.text }.joined(), window.text)
            var offset = 0
            for part in parts {
                XCTAssertEqual(part.chunk.startUTF16, offset)
                offset = part.chunk.endUTF16
                XCTAssertLessThanOrEqual(part.ids.count, 512)
            }
            XCTAssertEqual(offset, window.text.utf16.count)
            all += parts
        }
        return all
    }
    private func body(_ parts: [SuxinPreparedPart]) -> [Int64] {
        parts.flatMap { Array($0.ids.dropFirst().dropLast()) }
    }
    func testActualAuthorOracleMatchesInputsAcrossInnerAndOuterBoundaries() async throws {
        let url = try XCTUnwrap(Bundle(for: Self.self).url(forResource: "suxin-production-oracle", withExtension: "json", subdirectory: "Fixtures"))
        let oracle = try JSONDecoder().decode(Oracle.self, from: Data(contentsOf: url))
        XCTAssertEqual(oracle.cases.count, 12)
        let engine = try model()
        for row in oracle.cases {
            let parts = try await production(row.text, model: engine)
            XCTAssertEqual(body(parts), Array(row.ids.dropFirst().dropLast()), row.id)
        }
    }
    func testSupportedNumbersAndTimesMoveAcrossAllProductionLimits() async throws {
        let engine = try model()
        for prefix in Array(14...21) + Array(49...56) + Array(235...242) {
            for token in ["12:05", "2026年", "1234", "12.05"] {
                let text = String(repeating: "甲", count: prefix) + token + "。小宁走到门口，读完了这段故事。"
                let parts = try await production(text, model: engine)
                let reference = try await engine.prepare(text)
                XCTAssertEqual(body(parts), Array(reference.dropFirst().dropLast()), "\(prefix)/\(token)")
                XCTAssertTrue(parts.contains { $0.chunk.text.contains(token) })
            }
        }
    }
    func testContextOutsideCurrentWindowDoesNotForceUnrelatedEnglishFallback() async throws {
        let engine = try model()
        let text = String(repeating: "甲", count: 239) + "不是这样。Hello"
        let windows = SuxinSegmentation.windows(text)
        let first = try await engine.plan(windows[0].text, context: text, startUTF16: 0)
        XCTAssertFalse(first.isEmpty)
        do {
            _ = try await engine.plan(windows[1].text, context: text, startUTF16: windows[1].startUTF16)
            XCTFail("The actual English window must retain explicit fallback")
        } catch SuxinFrontend.Failure.unsupportedText { }
    }
    func testNormalizedUnitsKeepOriginalTextAndUTF16Positions() async throws {
        let engine = try model()
        let text = "（清晨）\n" + String(repeating: "甲", count: 15) + "12.05℃。不是这样，一个人走过重庆银行。"
        let parts = try await production(text, model: engine)
        let reference = try await engine.prepare(text)
        XCTAssertEqual(body(parts), Array(reference.dropFirst().dropLast()))
    }
    func testCacheIdentityIncludesActualContextualPhonemes() {
        let first = SuxinAudioCache.key(text: "不", speed: 1, resources: "fixed", phonemeIDs: [1, 7, 8, 2, 2])
        let other = SuxinAudioCache.key(text: "不", speed: 1, resources: "fixed", phonemeIDs: [1, 7, 8, 4, 2])
        XCTAssertNotEqual(first, other)
        XCTAssertNotEqual(first, SuxinAudioCache.key(text: "不", speed: 1, resources: "fixed"))
    }
    func testActualGraphConsumesContextualPartAndCachesThatInput() async throws {
        let cache = FileManager.default.temporaryDirectory.appendingPathComponent("SuxinBoundary-" + UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: cache) }
        let engine = SuxinModel(root: try SuxinResources.bundledURL(), cacheRoot: cache)
        let text = String(repeating: "甲", count: 17) + "不是这样。"
        let plan = try await engine.plan(text)
        let first = try XCTUnwrap(plan.first)
        XCTAssertTrue(first.chunk.text.hasSuffix("不"))
        let isolated = try await engine.prepare(first.chunk.text)
        XCTAssertNotEqual(first.ids, isolated, "Production must use 不2 from the complete context")
        let wave = try await engine.wave(part: first, speed: 1)
        XCTAssertFalse(wave.cacheHit); XCTAssertGreaterThan(wave.duration, 0.1)
        XCTAssertTrue(wave.samples.allSatisfy(\.isFinite))
        let cached = try await engine.wave(part: first, speed: 1)
        XCTAssertTrue(cached.cacheHit); XCTAssertEqual(cached.samples, wave.samples)
    }
}
