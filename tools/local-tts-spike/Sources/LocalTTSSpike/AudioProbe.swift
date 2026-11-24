import Foundation
import AVFoundation

private final class RenderClock {
    let lock = NSLock()
    var first: Double?
}

public enum AudioProbe {
    /// Realtime mixer observation, not an acoustic microphone/speaker measurement.
    public static func firstRenderedSample(file: URL, requestStarted: Double) -> [String: Any] {
        #if os(iOS)
        let engine = AVAudioEngine()
        let player = AVAudioPlayerNode()
        let clock = RenderClock()
        var tapped = false
        defer {
            player.stop()
            engine.stop()
            if tapped { engine.mainMixerNode.removeTap(onBus: 0) }
        }
        do {
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(.playback, mode: .spokenAudio)
            try session.setActive(true)
            let outputFormat = engine.outputNode.outputFormat(forBus: 0)
            guard outputFormat.sampleRate > 0 && outputFormat.channelCount > 0 else {
                return ["status": "BLOCKED_SIMULATOR_OUTPUT_FORMAT", "physical_acoustic_audibility": "NOT_RUN"]
            }
            let audio = try AVAudioFile(forReading: file)
            engine.attach(player)
            engine.connect(player, to: engine.mainMixerNode, format: audio.processingFormat)
            engine.mainMixerNode.installTap(onBus: 0, bufferSize: 512, format: nil) { buffer, _ in
                guard let channels = buffer.floatChannelData else { return }
                let nonzero = (0..<Int(buffer.frameLength)).contains { abs(channels[0][$0]) > 0.00001 }
                if nonzero {
                    clock.lock.lock()
                    if clock.first == nil { clock.first = ProcessInfo.processInfo.systemUptime - requestStarted }
                    clock.lock.unlock()
                }
            }
            tapped = true
            player.scheduleFile(audio, at: nil)
            try engine.start()
            player.play()
            let deadline = ProcessInfo.processInfo.systemUptime + 5
            while ProcessInfo.processInfo.systemUptime < deadline {
                clock.lock.lock()
                let first = clock.first
                clock.lock.unlock()
                if let first {
                    return ["status": SpikePlatform.name == "IOS_SIMULATOR" ? "OBSERVED_SIMULATOR_REALTIME_MIXER" : "OBSERVED_IOS_DEVICE_REALTIME_MIXER", "first_output_render_seconds": first,
                        "measurement": "request start to nonzero main-mixer samples after real synthesis/playback",
                        "physical_acoustic_audibility": "NOT_MEASURED_NO_HARDWARE_LOOPBACK"]
                }
                RunLoop.current.run(until: Date().addingTimeInterval(0.01))
            }
            return ["status": "NOT_RUN_AUDIO_RENDER_TIMEOUT", "physical_acoustic_audibility": "NOT_RUN"]
        } catch {
            let problem = error as NSError
            return ["status": "BLOCKED_SIMULATOR_AUDIO_ROUTE", "error_domain": problem.domain,
                    "error_code": problem.code, "physical_acoustic_audibility": "NOT_RUN"]
        }
        #else
        return ["status": "NOT_RUN_NON_IOS", "physical_acoustic_audibility": "NOT_RUN"]
        #endif
    }
}
