import XCTest
import AVFoundation
@testable import EBook

@MainActor private final class FakeSpeechProvider: SpeechProvider {
    var voices: [VoiceDescriptor] = []
    var onEvent: ((SpeechEvent) -> Void)?
    var requests: [SpeechRequest] = []
    var pauses = 0, resumes = 0, cancellations = 0
    var shouldFail = false
    func speak(_ request: SpeechRequest) throws {
        if shouldFail { throw ReaderError.invalid("synthetic failure") }
        requests.append(request); onEvent?(.started)
    }
    func pause() { pauses += 1 }
    func resume() throws { resumes += 1 }
    func cancel() { cancellations += 1 }
}

@MainActor final class SpeechControllerTests: XCTestCase {
    private var root: URL!
    override func setUpWithError() throws {
        root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
    }
    override func tearDownWithError() throws { try FileManager.default.removeItem(at: root) }
    private func context(text: String = "第一章 晨光\n你好，清晨。第二句。\n第二章 小路\n晚风吹来。\n第三章 回来\n故事结束。") throws -> (LibraryModel, BookRecord, BookDocument, BookStorage) {
        let storage = try BookStorage(root: root.appendingPathComponent("Library"))
        let input = root.appendingPathComponent("original.txt")
        try Data(text.utf8).write(to: input)
        let book = try BookImporter.importFile(input, storage: storage)
        var state = LibraryState(); state.books = [book]; try storage.saveLibrary(state)
        return (LibraryModel(root: storage.root), book, try storage.document(for: book.id), storage)
    }

    func testPauseResumeSeekChapterProgressAndSeparateReadingPosition() throws {
        let (library, book, doc, storage) = try context()
        let fake = FakeSpeechProvider()
        // The explicit fake is retained so test events pass through the real controller.
        let controller = SpeechController(provider: fake, managesAudio: false)
        controller.attach(library); controller.load(book, document: doc, storage: storage); controller.play()
        XCTAssertEqual(controller.status, .playing); XCTAssertEqual(fake.requests.count, 1)
        fake.onEvent?(.range(startUTF16: 3, length: 1))
        controller.pause()
        XCTAssertEqual(controller.status, .paused); XCTAssertEqual(fake.pauses, 1)
        XCTAssertEqual(library.record(book.id)?.listening.utf16Offset, 3)
        XCTAssertEqual(library.record(book.id)?.reading, ReadingAnchor())
        controller.play(); XCTAssertEqual(fake.resumes, 1)
        let oldEvent = fake.onEvent
        controller.skipChapter(1)
        XCTAssertEqual(controller.position.block, doc.chapters[1].firstBlock)
        oldEvent?(.finished) // A cancelled utterance cannot advance the new position.
        XCTAssertEqual(controller.position.block, doc.chapters[1].firstBlock)
        let expected = fake.requests.last!.chunk.endUTF16
        fake.onEvent?(.finished)
        XCTAssertGreaterThanOrEqual(controller.position.utf16Offset, expected)
        controller.pause()
        let reopened = try storage.loadLibrary()
        XCTAssertEqual(reopened.books[0].listening, controller.position)
    }

    func testInterruptionOnlyResumesWhenPermittedAndRouteLossPauses() throws {
        let (library, book, doc, storage) = try context()
        let controller = SpeechController(provider: FakeSpeechProvider(), managesAudio: false)
        controller.attach(library); controller.load(book, document: doc, storage: storage); controller.play()
        controller.interruptionBegan(); XCTAssertEqual(controller.status, .paused)
        controller.interruptionEnded(shouldResume: false); XCTAssertEqual(controller.status, .paused)
        controller.play(); controller.interruptionBegan(); controller.interruptionEnded(shouldResume: true)
        XCTAssertEqual(controller.status, .playing)
        controller.headphonesDisconnected(); XCTAssertEqual(controller.status, .paused)
        controller.interruptionBegan(); controller.interruptionEnded(shouldResume: true)
        XCTAssertEqual(controller.status, .paused)
    }

    func testFailureAndRateChangeDoNotDiscardSavedListeningPosition() throws {
        let (library, book, doc, storage) = try context()
        let fake = FakeSpeechProvider()
        let player = SpeechController(provider: fake, managesAudio: false)
        player.attach(library); player.load(book, document: doc, storage: storage)
        player.seek(TextPosition(block: 1, utf16Offset: 3))
        fake.shouldFail = true; player.play()
        XCTAssertNotNil(player.error); XCTAssertEqual(player.status, .paused)
        XCTAssertEqual(library.record(book.id)?.listening, TextPosition(block: 1, utf16Offset: 3))
        fake.shouldFail = false
        var preferences = library.state.preferences; preferences.speechRate = 0.6
        library.setPreferences(preferences); player.play()
        XCTAssertEqual(fake.requests.last?.rate, 0.6)
    }

    func testSuxinRateLookaheadAndCancelledSameBlockEventsDoNotMoveNewPosition() throws {
        let (library, book, doc, storage) = try context(text: String(repeating: "清晨的风吹过石桥，她把书轻轻合上。", count: 45))
        var preferences = library.state.preferences
        preferences.voiceIdentifier = SuxinSpeechProvider.voiceID; preferences.suxinRate = 1.5
        library.setPreferences(preferences)
        let fake = FakeSpeechProvider()
        let controller = SpeechController(provider: fake, managesAudio: false)
        controller.attach(library); controller.load(book, document: doc, storage: storage); controller.play()
        XCTAssertEqual(fake.requests.first?.rate, 1.5)
        XCTAssertLessThanOrEqual(fake.requests[0].chunk.text.utf16.count, 240)
        let old = fake.onEvent
        fake.onEvent?(.finished)
        let next = controller.position
        old?(.range(startUTF16: 1, length: 1)); old?(.failed("stale failure"))
        XCTAssertEqual(controller.position, next); XCTAssertNil(controller.error)
        controller.pause()
        XCTAssertEqual(library.record(book.id)?.reading, ReadingAnchor())
        XCTAssertEqual(try storage.loadLibrary().preferences.suxinRate, 1.5)
    }

    func testCorruptLibraryBlocksWritesRatherThanReplacingExistingState() throws {
        let storage = try BookStorage(root: root.appendingPathComponent("corrupt"))
        let url = storage.root.appendingPathComponent("library.json")
        let original = Data("original corrupt state retained for recovery".utf8)
        try original.write(to: url)
        let library = LibraryModel(root: storage.root)
        XCTAssertTrue(library.persistenceBlocked); XCTAssertNotNil(library.error)
        library.setPreferences(ReaderPreferences()); library.persist()
        XCTAssertEqual(try Data(contentsOf: url), original)
    }

    func testParagraphSeekWorksWithinABlockAndAcrossChapterBoundaries() throws {
        let (library, book, doc, storage) = try context()
        let controller = SpeechController(provider: FakeSpeechProvider(), managesAudio: false)
        controller.attach(library); controller.load(book, document: doc, storage: storage)
        controller.skipParagraph(1)
        XCTAssertEqual(controller.position.block, 0); XCTAssertGreaterThan(controller.position.utf16Offset, 0)
        controller.skipParagraph(-1); XCTAssertEqual(controller.position, TextPosition())
        controller.skipParagraph(1); controller.skipParagraph(1)
        XCTAssertEqual(controller.position.block, doc.chapters[1].firstBlock)
        controller.skipParagraph(-1)
        XCTAssertEqual(controller.position.block, 0); XCTAssertGreaterThan(controller.position.utf16Offset, 0)
    }

    func testPreviousParagraphSkipsTrailingBlockSeparators() throws {
        let text = "第一章 测试\n" + String(repeating: String(repeating: "甲", count: 57) + "。\n", count: 60)
        let (library, book, doc, storage) = try context(text: text)
        XCTAssertGreaterThan(doc.blocks.count, 1)
        let first = try storage.text(for: doc.blocks[0], book: book.id)
        XCTAssertTrue(first.hasSuffix("\n\n"))
        let controller = SpeechController(provider: FakeSpeechProvider(), managesAudio: false)
        controller.attach(library); controller.load(book, document: doc, storage: storage)
        controller.seek(TextPosition(block: 1)); controller.skipParagraph(-1)
        XCTAssertEqual(controller.position.block, 0)
        XCTAssertLessThan(controller.position.utf16Offset, first.utf16.count - 2)
        controller.play(); XCTAssertEqual(controller.position.block, 0)
    }

    func testParagraphSeekSkipsEPUBIllustrationsInBothDirections() throws {
        let storage = try BookStorage(root: root.appendingPathComponent("illustrated"))
        let fixture = try XCTUnwrap(Bundle(for: Self.self).resourceURL).appendingPathComponent("Fixtures/synthetic.epub")
        let book = try BookImporter.importFile(fixture, storage: storage)
        let doc = try storage.document(for: book.id)
        var state = LibraryState(); state.books = [book]; try storage.saveLibrary(state)
        let library = LibraryModel(root: storage.root)
        let controller = SpeechController(provider: FakeSpeechProvider(), managesAudio: false)
        controller.attach(library); controller.load(book, document: doc, storage: storage)
        let image = try XCTUnwrap(doc.blocks.firstIndex { $0.imagePath != nil })
        controller.seek(TextPosition(block: image + 1)); controller.skipParagraph(-1)
        XCTAssertLessThan(controller.position.block, image)
        let beforeImage = controller.position.block
        controller.seek(TextPosition(block: beforeImage, utf16Offset: doc.blocks[beforeImage].utf16Count))
        controller.skipParagraph(1)
        XCTAssertGreaterThan(controller.position.block, image)
    }

    func testActualAppleSynthesizerCallbacksWhenSimulatorHasVoiceAssets() async throws {
        guard AVSpeechSynthesisVoice.speechVoices().contains(where: { $0.language.hasPrefix("zh") }) else {
            throw XCTSkip("This simulator has no installed Mandarin voice; real speech remains a device check.")
        }
        let provider = AppleSpeechProvider()
        let finished = expectation(description: "real Apple speech finished")
        var sawRange = false
        provider.onEvent = { event in
            if case .range = event { sawRange = true }
            if event == .finished { finished.fulfill() }
        }
        try AVAudioSession.sharedInstance().setCategory(.playback, mode: .spokenAudio)
        try AVAudioSession.sharedInstance().setActive(true)
        defer { provider.cancel(); try? AVAudioSession.sharedInstance().setActive(false) }
        let text = "这是一段原创朗读测试。"
        let chunk = SpeechChunk(text: text, startUTF16: 0, endUTF16: text.utf16.count)
        try provider.speak(SpeechRequest(stableID: "synthetic-real-speech", chunk: chunk, voiceID: nil, rate: 0.5))
        await fulfillment(of: [finished], timeout: 30)
        XCTAssertTrue(sawRange)
    }
}
