import XCTest
import Foundation
@testable import LocalTTSSpike

final class KokoroBenchmarkTests: XCTestCase {
    struct Corpus: Decodable {
        struct Case: Decodable { let id: String; let text: String }
        let cases: [Case]
    }

    private func inputs() throws -> (URL, Corpus, Any, URL) {
        XCTAssertEqual(SpikePlatform.name, "IOS_SIMULATOR")
        guard SpikePlatform.name == "IOS_SIMULATOR" else { throw SpikeError.initializationFailed }
        let resources = try XCTUnwrap(Bundle.module.resourceURL).appendingPathComponent("Resources")
        let corpus = try JSONDecoder().decode(Corpus.self, from: Data(contentsOf: resources.appendingPathComponent("corpus.json")))
        let context = try JSONSerialization.jsonObject(with: Data(contentsOf: resources.appendingPathComponent("run-context.json")))
        let output = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
        return (resources, corpus, context, output)
    }

    private func jobs(_ corpus: Corpus) -> [(String, Corpus.Case)] {
        ["zf_001", "zf_002", "zm_009"].map { ($0, corpus.cases[0]) }
            + corpus.cases.dropFirst().map { ("zf_001", $0) }
    }

    private func emit(_ values: [String: Any]) throws {
        let data = try JSONSerialization.data(withJSONObject: values, options: [.sortedKeys])
        print("S02A_IOS_METRICS " + String(decoding: data, as: UTF8.self))
    }

    private func benchmark(threads: Int) throws {
        let (resources, corpus, context, destination) = try inputs()
        let model = resources.appendingPathComponent("kokoro")
        try AssetManifest.validate(directory: model, manifestURL: resources.appendingPathComponent("model.json"))
        let provider = try KokoroSpike(modelDirectory: model, threads: threads)
        print("S02A_IOS_INITIALIZED threads=\(threads) seconds=\(provider.initializationSeconds)")
        let warmup = try provider.synthesize(text: "清风吹过窗边。", voice: "zf_001", speed: 1,
            output: destination.appendingPathComponent("warmup.wav"))
        var records: [[String: Any]] = []
        var hashes = Set<String>()
        var playback: [String: Any] = ["status": "NOT_RUN"]
        for (index, job) in jobs(corpus).enumerated() {
            let requested = ProcessInfo.processInfo.systemUptime
            let result = try provider.synthesize(text: job.1.text, voice: job.0, speed: 1,
                output: destination.appendingPathComponent("original-\(index).wav"))
            XCTAssertGreaterThan(result.durationSeconds, 1)
            if index == 0 { playback = AudioProbe.firstRenderedSample(file: result.file, requestStarted: requested) }
            let digest = try AssetManifest.digest(result.file)
            if index < 3 { hashes.insert(digest) }
            records.append(["voice": job.0, "speaker_id": KokoroSpike.speakers[job.0]!,
                "fixture_id": job.1.id, "duration_seconds": result.durationSeconds,
                "generation_seconds": result.generationSeconds, "first_callback_seconds": result.firstCallbackSeconds,
                "rtf": result.rtf, "sample_rate": result.sampleRate, "frames": result.frames,
                "rms": result.rms, "process_peak_rss_cumulative_bytes": result.peakProcessRSSBytes,
                "wav_sha256": digest])
            print("S02A_IOS_CHUNK threads=\(threads) case=\(job.1.id) duration=\(result.durationSeconds) rtf=\(result.rtf)")
        }
        XCTAssertEqual(hashes.count, 3)
        try emit(["kind": "thread_benchmark", "environment": SpikePlatform.name, "genuine_ios_inference": true,
            "run_context": context, "threads": threads, "process_id": ProcessInfo.processInfo.processIdentifier,
            "ios_version": ProcessInfo.processInfo.operatingSystemVersionString,
            "model_initialization_seconds": provider.initializationSeconds,
            "warmup_generation_seconds": warmup.generationSeconds,
            "cache_state": "Fresh process, hash verified before init, OS cache not cold-controlled",
            "records": records, "playback_probe": playback, "physical_device": "NOT_RUN"])
    }

    func testThreads1() throws { try benchmark(threads: 1) }
    func testThreads2() throws { try benchmark(threads: 2) }
    func testThreads3() throws { try benchmark(threads: 3) }
    func testThreads4() throws { try benchmark(threads: 4) }

    func testMinimalEquivalence() throws {
        let (resources, corpus, context, destination) = try inputs()
        var runs: [[String]] = []
        var frameSets: [[Int]] = []
        for (pack, manifest) in [("kokoro", "model.json"), ("minimal", "minimal-model.json")] {
            let directory = resources.appendingPathComponent(pack)
            try AssetManifest.validate(directory: directory, manifestURL: resources.appendingPathComponent(manifest))
            let engine = try KokoroSpike(modelDirectory: directory, threads: 1)
            _ = try engine.synthesize(text: "清风吹过窗边。", voice: "zf_001", speed: 1,
                output: destination.appendingPathComponent("\(pack)-warmup.wav"))
            var hashes: [String] = []
            var frames: [Int] = []
            for (index, job) in jobs(corpus).enumerated() {
                let result = try engine.synthesize(text: job.1.text, voice: job.0, speed: 1,
                    output: destination.appendingPathComponent("\(pack)-\(index).wav"))
                hashes.append(try AssetManifest.digest(result.file))
                frames.append(result.frames)
            }
            runs.append(hashes)
            frameSets.append(frames)
        }
        let equivalent = runs[0] == runs[1] && frameSets[0] == frameSets[1]
        try emit(["kind": "minimal_equivalence", "environment": SpikePlatform.name, "genuine_ios_inference": true,
            "run_context": context, "threads": 1, "speed": 1, "provider": "cpu", "original_cases": 7,
            "full_wav_sha256": runs[0], "minimal_wav_sha256": runs[1],
            "full_frames": frameSets[0], "minimal_frames": frameSets[1],
            "bit_identical_pcm16_wav": equivalent,
            "status": equivalent ? "PASS_BIT_IDENTICAL_ORIGINAL_AUDIO" : "NOT_PROVEN_AUDIO_DIFFERENCES",
            "distribution_clearance": "UNRESOLVED_DATA_NOTICES"])
        XCTAssertTrue(equivalent, "Do not declare a minimal model equivalent when actual WAVs differ")
    }
}
