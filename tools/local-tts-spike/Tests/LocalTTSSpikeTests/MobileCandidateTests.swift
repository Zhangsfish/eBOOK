import XCTest
import Foundation
import Darwin
import LocalTTSSpike
import MobileOrtProbe

final class MobileCandidateTests: XCTestCase {
    struct Corpus: Decodable {
        struct Item: Decodable { let id: String; let text: String }
        let cases: [Item]
    }
    struct PreparedIDs: Decodable {
        struct Item: Decodable { let fixture_id: String; let text_sha256: String; let ids: [Int64] }
        let corpus_sha256: String
        let frontend_mode: String
        let records: [Item]
    }

    private func resources() throws -> URL {
        guard ["IOS_SIMULATOR", "IOS_PHYSICAL_DEVICE"].contains(SpikePlatform.name) else {
            throw SpikeError.initializationFailed
        }
        let root = try XCTUnwrap(Bundle.module.resourceURL)
        return try XCTUnwrap([root, root.appendingPathComponent("Resources")].first {
            FileManager.default.fileExists(atPath: $0.appendingPathComponent("s02a2-context.json").path)
        }, "Actual candidate resources/context missing")
    }

    private func corpus(_ root: URL) throws -> Corpus {
        try JSONDecoder().decode(Corpus.self, from: Data(contentsOf: root.appendingPathComponent("corpus.json")))
    }

    private func context(_ root: URL) throws -> Any {
        try JSONSerialization.jsonObject(with: Data(contentsOf: root.appendingPathComponent("s02a2-context.json")))
    }

    private func destination() throws -> URL {
        let result = FileManager.default.temporaryDirectory.appendingPathComponent("S02A2-" + UUID().uuidString)
        try FileManager.default.createDirectory(at: result, withIntermediateDirectories: true)
        return result
    }

    private func emit(_ value: [String: Any]) throws {
        let data = try JSONSerialization.data(withJSONObject: value, options: [.sortedKeys])
        print("S02A2_METRICS " + String(decoding: data, as: UTF8.self))
    }

    private func providers() throws -> [String: Any] {
        let value = try XCTUnwrap(MobileOrtProvidersJSON())
        defer { MobileOrtFreeString(value) }
        return try XCTUnwrap(JSONSerialization.jsonObject(with: Data(String(cString: value).utf8)) as? [String: Any])
    }

    func testRuntimeProviders() throws {
        let root = try resources()
        var value = try providers()
        value["kind"] = "runtime_providers"
        value["environment"] = SpikePlatform.name
        value["run_context"] = try context(root)
        try emit(value)
        XCTAssertEqual(value["status"] as? String, "RUNTIME_ENUMERATED")
    }

    private func row(_ result: ChunkMeasurement, fixture: String, firstOutput: [String: Any]?) throws -> [String: Any] {
        var values: [String: Any] = ["fixture_id": fixture, "generation_seconds": result.generationSeconds,
            "first_callback_seconds": result.firstCallbackSeconds, "sample_rate": result.sampleRate,
            "frames": result.frames, "duration_seconds": result.durationSeconds, "rtf": result.rtf,
            "rms": result.rms, "wav_sha256": try AssetManifest.digest(result.file),
            "process_peak_rss_cumulative_bytes": result.peakProcessRSSBytes]
        if let firstOutput { values["first_output_probe"] = firstOutput }
        return values
    }

    private func synthesizeKokoro(_ root: URL, output: URL, providerName: String) throws -> [String: Any] {
        let profile = output.appendingPathComponent("profile")
        let config = output.appendingPathComponent("provider.config")
        try "LogSeverityLevel=0\nProfilingFilePrefix=\(profile.path)\n".write(to: config, atomically: false, encoding: .utf8)
        let model = root.appendingPathComponent("kokoro")
        try AssetManifest.validate(directory: model, manifestURL: root.appendingPathComponent("model.json"))
        let engine = try KokoroSpike(modelDirectory: model, threads: 2,
            provider: providerName + ":" + config.path, diagnostics: true)
        print("S02A2_INITIALIZED kokoro provider=\(providerName) seconds=\(engine.initializationSeconds)")
        let warmup = try engine.synthesize(text: "清风吹过窗边。", voice: "zf_001", speed: 1,
            output: output.appendingPathComponent("warmup.wav"))
        var rows: [[String: Any]] = []
        for (index, item) in try corpus(root).cases.enumerated() {
            let started = ProcessInfo.processInfo.systemUptime
            let wave = try engine.synthesize(text: item.text, voice: "zf_001", speed: 1,
                output: output.appendingPathComponent(item.id + ".wav"))
            let first = index == 0 ? AudioProbe.firstRenderedSample(file: wave.file, requestStarted: started) : nil
            rows.append(try row(wave, fixture: item.id, firstOutput: first))
            print("S02A2_CHUNK kokoro provider=\(providerName) case=\(item.id) rtf=\(wave.rtf)")
        }
        return ["model_initialization_seconds": engine.initializationSeconds,
            "warmup_generation_seconds": warmup.generationSeconds, "records": rows]
        // engine destruction flushes ORT profiling before the caller inspects files.
    }

    private func profileSummary(_ output: URL) throws -> [String: Any] {
        let paths = try FileManager.default.contentsOfDirectory(at: output, includingPropertiesForKeys: nil)
            .filter { $0.lastPathComponent.hasPrefix("profile") && $0.pathExtension == "json" }
        var counts: [String: Int] = [:]
        var durations: [String: Double] = [:]
        var names: [String: Set<String>] = [:]
        for path in paths {
            let size = try FileManager.default.attributesOfItem(atPath: path.path)[.size] as? NSNumber
            guard (size?.int64Value ?? Int64.max) <= 256 * 1024 * 1024 else {
                return ["status": "NOT_PROVEN_PROFILE_EXCEEDS_BOUNDED_PARSER", "files": paths.count]
            }
            let events = try XCTUnwrap(JSONSerialization.jsonObject(with: Data(contentsOf: path)) as? [[String: Any]])
            for event in events {
                guard event["cat"] as? String == "Node",
                      let args = event["args"] as? [String: Any], let provider = args["provider"] as? String else { continue }
                counts[provider, default: 0] += 1
                durations[provider, default: 0] += (event["dur"] as? NSNumber)?.doubleValue ?? 0
                names[provider, default: []].insert(event["name"] as? String ?? "unknown")
            }
        }
        return ["status": paths.isEmpty ? "NOT_PROVEN_PROFILE_MISSING" : "ACTUAL_ORT_PROFILE_INSPECTED",
            "profile_files": paths.count, "provider_node_event_counts": counts,
            "provider_unique_executed_nodes": names.mapValues { $0.count }, "provider_node_duration_us": durations,
            "coreml_node_execution_observed": (counts["CoreMLExecutionProvider"] ?? 0) > 0,
            "ane_execution": "NOT_MEASURED_NO_ANE_DEVICE_COUNTERS",
            "scope": "Includes warmup; fused node events are not original graph operator counts."]
    }

    private func kokoro(provider: String) throws {
        let root = try resources()
        let availability = try providers()
        try emit(["kind": "runtime_providers", "environment": SpikePlatform.name,
            "run_context": try context(root), "runtime": availability])
        if provider == "coreml" {
            guard (availability["available_providers"] as? [String])?.contains("CoreMLExecutionProvider") == true else {
                try emit(["kind": "kokoro_pair", "environment": SpikePlatform.name,
                    "run_context": try context(root), "provider_requested": provider,
                    "status": "NOT_RUN_COREML_EP_NOT_REGISTERED", "genuine_ios_inference": false])
                throw SpikeError.initializationFailed
            }
        }
        let output = try destination()
        var result = try autoreleasepool { try synthesizeKokoro(root, output: output, providerName: provider) }
        result["kind"] = "kokoro_pair"
        result["environment"] = SpikePlatform.name
        result["run_context"] = try context(root)
        result["genuine_ios_inference"] = true
        result["provider_requested"] = provider
        result["threads"] = 2
        result["speed"] = 1
        result["profile"] = try profileSummary(output)
        result["provider_registration"] = availability
        result["ios_version"] = ProcessInfo.processInfo.operatingSystemVersionString
        result["physical_audibility"] = "NOT_MEASURED_NO_HARDWARE_LOOPBACK"
        result["profile_enabled_during_timing"] = true
        try emit(result)
    }

    func testKokoroCPUFinal() throws { try kokoro(provider: "cpu") }
    func testKokoroCoreMLFinal() throws { try kokoro(provider: "coreml") }

    private func matcha(threads: Int) throws {
        let root = try resources()
        let model = root.appendingPathComponent("matcha")
        try AssetManifest.validate(directory: model, manifestURL: root.appendingPathComponent("matcha-model.json"))
        let output = try destination()
        let engine = try MatchaSpike(modelDirectory: model, threads: threads)
        let warmup = try engine.synthesize(text: "清风吹过窗边。", output: output.appendingPathComponent("warmup.wav"))
        var rows: [[String: Any]] = []
        for (index, item) in try corpus(root).cases.enumerated() {
            let started = ProcessInfo.processInfo.systemUptime
            let wave = try engine.synthesize(text: item.text, output: output.appendingPathComponent(item.id + ".wav"))
            let first = index == 0 ? AudioProbe.firstRenderedSample(file: wave.file, requestStarted: started) : nil
            rows.append(try row(wave, fixture: item.id, firstOutput: first))
            print("S02A2_CHUNK matcha threads=\(threads) case=\(item.id) rtf=\(wave.rtf)")
        }
        try emit(["kind": "matcha", "environment": SpikePlatform.name, "run_context": try context(root),
            "genuine_ios_inference": true, "model_initialization_seconds": engine.initializationSeconds,
            "warmup_generation_seconds": warmup.generationSeconds, "records": rows, "threads": threads,
            "speed": 1, "speaker_id": 0, "speaker_count": 1,
            "ios_version": ProcessInfo.processInfo.operatingSystemVersionString,
            "language_limit": "Chinese-only; original mixed-English fixture remains unchanged, OOV may be skipped."])
    }

    func testMatchaThreads2() throws { try matcha(threads: 2) }
    func testMatchaThreads4() throws { try matcha(threads: 4) }

    private func writeWave(_ audio: UnsafePointer<Float>, count: Int, output: URL) throws -> Double {
        guard count > 22050, count < 22050 * 120 else { throw SpikeError.invalidWaveform }
        var sum = 0.0
        var data = Data()
        func text(_ value: String) { data.append(contentsOf: value.utf8) }
        func u32(_ value: UInt32) { var n = value.littleEndian; withUnsafeBytes(of: &n) { data.append(contentsOf: $0) } }
        func u16(_ value: UInt16) { var n = value.littleEndian; withUnsafeBytes(of: &n) { data.append(contentsOf: $0) } }
        text("RIFF"); u32(UInt32(36 + count * 2)); text("WAVEfmt "); u32(16)
        u16(1); u16(1); u32(22050); u32(44100); u16(2); u16(16); text("data"); u32(UInt32(count * 2))
        for index in 0..<count {
            let value = audio[index]
            guard value.isFinite else { throw SpikeError.invalidWaveform }
            sum += Double(value) * Double(value)
            let sample = Int16((max(-1, min(1, value)) * 32767).rounded())
            u16(UInt16(bitPattern: sample))
        }
        let rms = sqrt(sum / Double(count))
        guard rms > 0.001 else { throw SpikeError.invalidWaveform }
        try data.write(to: output, options: .withoutOverwriting)
        return rms
    }

    func testSuxinBackendOnly() throws {
        let root = try resources()
        let model = root.appendingPathComponent("suxin")
        try AssetManifest.validate(directory: model, manifestURL: root.appendingPathComponent("suxin-model.json"))
        let prepared = try JSONDecoder().decode(PreparedIDs.self, from: Data(contentsOf: root.appendingPathComponent("suxin-ids.json")))
        let cases = try corpus(root).cases
        XCTAssertEqual(prepared.frontend_mode, "AUTHOR_PYTHON_FRONTEND_PRECOMPUTED_IDS")
        XCTAssertEqual(prepared.corpus_sha256, try AssetManifest.digest(root.appendingPathComponent("corpus.json")))
        XCTAssertEqual(prepared.records.map { $0.fixture_id }, cases.map { $0.id })
        let output = try destination()
        var initialization = 0.0
        var error: UnsafeMutablePointer<CChar>?
        let handle = model.appendingPathComponent("zh_en-suxin-light.int8-excldec.onnx").path.withCString {
            MobileOrtCreateSuxin($0, 4, &initialization, &error)
        }
        defer { if let error { MobileOrtFreeString(error) } }
        guard let handle else { throw NSError(domain: "SuxinBackend", code: 1,
            userInfo: [NSLocalizedDescriptionKey: error.map { String(cString: $0) } ?? "Native session failed"]) }
        defer { MobileOrtDestroySuxin(handle) }
        var rows: [[String: Any]] = []
        for (index, item) in prepared.records.enumerated() {
            var samples: UnsafeMutablePointer<Float>?
            var count = 0
            var elapsed = 0.0
            var runError: UnsafeMutablePointer<CChar>?
            let started = ProcessInfo.processInfo.systemUptime
            let ok = item.ids.withUnsafeBufferPointer { MobileOrtRunSuxin(handle, $0.baseAddress, $0.count,
                &samples, &count, &elapsed, &runError) }
            defer { if let samples { MobileOrtFreeSamples(samples) }; if let runError { MobileOrtFreeString(runError) } }
            guard ok == 1, let samples else { throw NSError(domain: "SuxinBackend", code: 2,
                userInfo: [NSLocalizedDescriptionKey: runError.map { String(cString: $0) } ?? "Native graph run failed"]) }
            let path = output.appendingPathComponent(item.fixture_id + ".wav")
            let rms = try writeWave(UnsafePointer(samples), count: count, output: path)
            let first = index == 0 ? AudioProbe.firstRenderedSample(file: path, requestStarted: started) : nil
            var usage = rusage()
            guard getrusage(RUSAGE_SELF, &usage) == 0 else { throw SpikeError.invalidWaveform }
            var record: [String: Any] = ["fixture_id": item.fixture_id, "text_sha256": item.text_sha256,
                "generation_seconds": elapsed, "duration_seconds": Double(count) / 22050,
                "rtf": elapsed / (Double(count) / 22050), "frames": count, "sample_rate": 22050,
                "rms": rms, "wav_sha256": try AssetManifest.digest(path), "first_callback_seconds": NSNull(),
                "process_peak_rss_cumulative_bytes": UInt64(max(0, usage.ru_maxrss))]
            if let first { record["first_output_probe"] = first }
            rows.append(record)
        }
        try emit(["kind": "suxin_backend", "environment": SpikePlatform.name, "run_context": try context(root),
            "genuine_ios_graph_inference": true, "end_to_end_native_text": false,
            "frontend_mode": prepared.frontend_mode, "threads": 4, "records": rows,
            "model_initialization_seconds": initialization, "runtime": try providers(),
            "ios_version": ProcessInfo.processInfo.operatingSystemVersionString,
            "status": "BACKEND_ONLY_NATIVE_FRONTEND_NOT_IMPLEMENTED"])
    }
}
