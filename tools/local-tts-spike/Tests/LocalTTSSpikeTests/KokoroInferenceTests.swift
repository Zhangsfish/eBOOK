import XCTest
import Foundation
@testable import LocalTTSSpike

final class KokoroInferenceTests: XCTestCase {
    struct Corpus: Decodable {
        struct Case: Decodable { let id: String; let text: String }
        let cases: [Case]
    }

    func testActualOriginalMandarinInference() throws {
        // A macOS execution is explicitly rejected as an iOS proof.
        XCTAssertEqual(SpikePlatform.name, "IOS_SIMULATOR")
        guard SpikePlatform.name == "IOS_SIMULATOR" else { throw SpikeError.initializationFailed }
        let resources = try XCTUnwrap(Bundle.module.resourceURL).appendingPathComponent("Resources")
        let model = resources.appendingPathComponent("kokoro")
        try AssetManifest.validate(directory: model, manifestURL: resources.appendingPathComponent("model.json"))
        let corpus = try JSONDecoder().decode(Corpus.self, from: Data(contentsOf: resources.appendingPathComponent("corpus.json")))
        let context = try JSONSerialization.jsonObject(with: Data(contentsOf: resources.appendingPathComponent("run-context.json")))
        let provider = try KokoroSpike(modelDirectory: model)
        let destination = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: destination, withIntermediateDirectories: true)
        var records: [[String: Any]] = []
        var hashes = Set<String>()
        let voices = ["zf_001", "zf_002", "zm_009"]
        let jobs = voices.map { ($0, corpus.cases[0]) } + corpus.cases.dropFirst().map { (voices[0], $0) }
        for (index, job) in jobs.enumerated() {
            let result = try provider.synthesize(text: job.1.text, voice: job.0, speed: 1,
                output: destination.appendingPathComponent("original-\(index).wav"))
            XCTAssertGreaterThan(result.durationSeconds, 1)
            let digest = try AssetManifest.digest(result.file)
            if index < 3 { hashes.insert(digest) }
            records.append(["voice": job.0, "speaker_id": KokoroSpike.speakers[job.0]!,
                "fixture_id": job.1.id, "duration_seconds": result.durationSeconds,
                "generation_seconds": result.generationSeconds, "first_callback_seconds": result.firstCallbackSeconds,
                "rtf": result.rtf, "sample_rate": result.sampleRate, "frames": result.frames,
                "rms": result.rms, "process_peak_rss_cumulative_bytes": result.peakProcessRSSBytes,
                "wav_sha256": digest])
        }
        XCTAssertEqual(hashes.count, 3)
        let metadata: [String: Any] = ["environment": SpikePlatform.name, "genuine_ios_inference": true,
            "run_context": context, "model_initialization_seconds": provider.initializationSeconds,
            "cache_state": "Hash verified before initialization; filesystem cache not cold-controlled",
            "records": records, "session_10_min": "NOT_RUN", "physical_device": "NOT_RUN"]
        let data = try JSONSerialization.data(withJSONObject: metadata, options: [.sortedKeys])
        print("S02A_IOS_METRICS " + String(decoding: data, as: UTF8.self))
    }
}
