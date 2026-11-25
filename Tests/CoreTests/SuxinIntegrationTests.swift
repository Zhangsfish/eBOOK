import XCTest
import AVFoundation
import CryptoKit
@testable import EBook

private final class OutputProbe: @unchecked Sendable {
    private let lock = NSLock()
    private var first: Double?
    func receive(_ buffer: AVAudioPCMBuffer) {
        guard let audio = buffer.floatChannelData?[0] else { return }
        for index in 0..<Int(buffer.frameLength) where abs(audio[index]) > 0.001 {
            lock.lock(); if first == nil { first = ProcessInfo.processInfo.systemUptime }; lock.unlock(); break
        }
    }
    var firstTime: Double? { lock.lock(); defer { lock.unlock() }; return first }
}

@MainActor final class SuxinIntegrationTests: XCTestCase {
    private var temporary: URL!
    override func setUpWithError() throws {
        temporary = FileManager.default.temporaryDirectory.appendingPathComponent("SuxinTest-" + UUID().uuidString)
        try FileManager.default.createDirectory(at: temporary, withIntermediateDirectories: true)
    }
    override func tearDownWithError() throws { try FileManager.default.removeItem(at: temporary) }
    private func request(_ text: String, rate: Float = 1) -> SpeechRequest {
        SpeechRequest(stableID: UUID().uuidString, chunk: SpeechChunk(text: text, startUTF16: 0, endUTF16: text.utf16.count),
                      voiceID: SuxinSpeechProvider.voiceID, rate: rate)
    }
    private func activateAudio() throws {
        try AVAudioSession.sharedInstance().setCategory(.playback, mode: .spokenAudio)
        try AVAudioSession.sharedInstance().setActive(true)
    }
    func testRealNativeTextToWaveAtTwoRatesAndVerifiedCache() async throws {
        let model = SuxinModel(root: try SuxinResources.bundledURL(), cacheRoot: temporary.appendingPathComponent("cache"))
        let text = "二零二六年的清晨，小船缓缓驶过石桥。"
        let start = ProcessInfo.processInfo.systemUptime
        let normal = try await model.wave(text: text, speed: 1)
        let wall = ProcessInfo.processInfo.systemUptime - start
        let faster = try await model.wave(text: text, speed: 1.5)
        XCTAssertFalse(normal.cacheHit); XCTAssertFalse(faster.cacheHit)
        XCTAssertGreaterThan(normal.duration, 1); XCTAssertLessThan(faster.duration, normal.duration * 0.85)
        let cached = try await model.wave(text: text, speed: 1)
        XCTAssertTrue(cached.cacheHit); XCTAssertEqual(cached.samples, normal.samples)
        let format = try XCTUnwrap(AVAudioFormat(standardFormatWithSampleRate: 22050, channels: 1))
        let buffer = try XCTUnwrap(AVAudioPCMBuffer(pcmFormat: format, frameCapacity: AVAudioFrameCount(normal.samples.count)))
        buffer.frameLength = buffer.frameCapacity
        normal.samples.withUnsafeBufferPointer { source in buffer.floatChannelData![0].update(from: source.baseAddress!, count: source.count) }
        let wave = temporary.appendingPathComponent("actual-native-original.wav")
        var file: AVAudioFile? = try AVAudioFile(forWriting: wave, settings: format.settings)
        try file!.write(from: buffer)
        file = nil // Close/finalize the WAV header before independently reopening.
        let reopened = try AVAudioFile(forReading: wave)
        XCTAssertEqual(reopened.length, AVAudioFramePosition(normal.samples.count))
        let digest = SHA256.hash(data: try Data(contentsOf: wave)).map { String(format: "%02x", $0) }.joined()
        let initialization = await model.initializationSeconds
        let runtime = SuxinModel.runtimeVersion
        print("S02B_METRIC " + String(data: try JSONSerialization.data(withJSONObject: [
            "case": "native_text_real_graph", "end_to_end_native_text": true, "runtime": runtime,
            "initialization_seconds": initialization, "cold_wave_wall_seconds": wall,
            "normal_generation_seconds": normal.generationSeconds, "normal_audio_seconds": normal.duration,
            "normal_rtf": normal.generationSeconds / normal.duration,
            "faster_generation_seconds": faster.generationSeconds, "faster_audio_seconds": faster.duration,
            "faster_rtf": faster.generationSeconds / faster.duration,
            "process_lifetime_peak_rss_bytes": SuxinModel.processLifetimePeakRSS, "wav_sha256": digest,
            "physical_device": false
        ], options: [.sortedKeys]), encoding: .utf8)!)
    }
    func testActualPCMQueuePauseResumeAndMixerOutput() async throws {
        try activateAudio()
        let provider = SuxinSpeechProvider(cacheRoot: temporary.appendingPathComponent("playback-cache"))
        let finished = expectation(description: "real multi-buffer playback finished")
        let probe = OutputProbe()
        provider.installTestOutputProbe { buffer, _ in probe.receive(buffer) }
        defer { provider.cancel(); provider.removeTestOutputProbe(); try? AVAudioSession.sharedInstance().setActive(false) }
        let text = "清晨的风很轻，小船经过石桥。她收起书，向岸边挥了挥手。远处的钟声响了，今天的故事才刚刚开始。她回头看了一眼熟悉的街道，又想起昨晚没有读完的那一页。"
        var playedOffsets: [Int] = []
        provider.onEvent = { event in
            if case .range(let start, _) = event { playedOffsets.append(start) }
            if case .failed(let message) = event { XCTFail(message); finished.fulfill() }
            if event == .finished { finished.fulfill() }
        }
        let start = ProcessInfo.processInfo.systemUptime
        try provider.speak(request(text, rate: 1.5)); provider.pause()
        try await Task.sleep(for: .milliseconds(500))
        XCTAssertNil(probe.firstTime, "Pause during loading must prevent late speech")
        XCTAssertTrue(playedOffsets.isEmpty || playedOffsets == [0])
        try provider.resume()
        await fulfillment(of: [finished], timeout: 100)
        XCTAssertNotNil(probe.firstTime)
        XCTAssertEqual(playedOffsets.last, text.utf16.count)
        XCTAssertEqual(playedOffsets, playedOffsets.sorted())
        XCTAssertGreaterThan(provider.measurement.chunks, 2)
        XCTAssertLessThanOrEqual(provider.measurement.peakQueuedBuffers, 3)
        let data: [String: Any] = ["case": "actual_pcm_queue", "rate": 1.5,
            "simulator_first_nonzero_mixer_seconds_including_requested_pause": (probe.firstTime ?? start) - start,
            "first_scheduled_seconds": provider.measurement.firstScheduledSeconds ?? -1,
            "chunks": provider.measurement.chunks, "chunk_rtf": provider.measurement.rtf,
            "underflows_within_request": provider.measurement.underflows,
            "peak_queued_buffers": provider.measurement.peakQueuedBuffers,
            "process_lifetime_peak_rss_bytes": SuxinModel.processLifetimePeakRSS, "physical_device": false]
        print("S02B_METRIC " + String(data: try JSONSerialization.data(withJSONObject: data, options: [.sortedKeys]), encoding: .utf8)!)
    }
    func testCancelDuringInferenceDropsAllStaleCallbacksAndCanRestart() async throws {
        let provider = SuxinSpeechProvider(cacheRoot: temporary.appendingPathComponent("cancel-cache"))
        var stale: [SpeechEvent] = []
        provider.onEvent = { stale.append($0) }
        try provider.speak(request(String(repeating: "窗外的树影轻轻晃动。", count: 8)))
        try await Task.sleep(for: .milliseconds(30))
        provider.cancel(); let count = stale.count
        try await Task.sleep(for: .milliseconds(200))
        XCTAssertEqual(stale.count, count)
        let unsupported = expectation(description: "new unsupported request delivered once")
        provider.onUnsupported = { unsupported.fulfill() }
        try provider.speak(request("请按Play开始。"))
        await fulfillment(of: [unsupported], timeout: 30)
        provider.cancel()
    }
    func testMixedEnglishUsesVisibleWholeSpanAppleFallback() async throws {
        let apple = RecordingSystemSpeech()
        let router = LocalSpeechProvider(apple: apple, suxin: SuxinSpeechProvider(cacheRoot: temporary.appendingPathComponent("fallback")))
        let shown = expectation(description: "explicit fallback notice")
        var notices: [String] = []
        router.onEvent = { if case .notice(let message) = $0, let message { notices.append(message); shown.fulfill() } }
        let mixed = request("请按Play开始，明天再听。", rate: 1.5)
        try router.speak(mixed); router.pause()
        await fulfillment(of: [shown], timeout: 30)
        XCTAssertEqual(apple.requests.first?.chunk, mixed.chunk)
        XCTAssertEqual(apple.pauses, 1); XCTAssertEqual(notices.count, 1)
        router.cancel()
    }
    func testMissingModelResourcesFailWithoutPretendingToSynthesize() async throws {
        let model = SuxinModel(root: temporary.appendingPathComponent("missing"))
        do { _ = try await model.wave(text: "今天有微风。", speed: 1); XCTFail("Missing resources must fail") }
        catch { /* real absence, not a mock waveform */ }
    }
}

@MainActor private final class RecordingSystemSpeech: SpeechProvider {
    var voices: [VoiceDescriptor] = []
    var onEvent: ((SpeechEvent) -> Void)?
    var requests: [SpeechRequest] = []; var pauses = 0
    func speak(_ request: SpeechRequest) throws { requests.append(request) }
    func pause() { pauses += 1 }
    func resume() throws {}
    func cancel() {}
}
