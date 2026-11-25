import Foundation

public struct VoiceDescriptor: Identifiable, Sendable {
    public let id: String
    public let name: String
    public let language: String
    public let requiresNetwork: Bool
    public init(id: String, name: String, language: String, requiresNetwork: Bool) {
        self.id = id; self.name = name; self.language = language; self.requiresNetwork = requiresNetwork
    }
}

public struct SpeechRequest: Sendable {
    public let stableID: String
    public let chunk: SpeechChunk
    public let voiceID: String?
    public let rate: Float
    public init(stableID: String, chunk: SpeechChunk, voiceID: String?, rate: Float) {
        self.stableID = stableID; self.chunk = chunk; self.voiceID = voiceID; self.rate = rate
    }
}

public enum SpeechEvent: Sendable, Equatable {
    case preparing(Bool)
    case notice(String?)
    case started
    case range(startUTF16: Int, length: Int)
    case finished
    case cancelled
    case failed(String)
}

/// Local speech emits timing events directly. A later backend-based provider may
/// return an audio asset and optional timings; transport/cache/player belong to
/// that adapter, never to the reader UI. There is no cloud adapter in S00.
@MainActor public protocol SpeechProvider: AnyObject {
    var voices: [VoiceDescriptor] { get }
    var onEvent: ((SpeechEvent) -> Void)? { get set }
    func speak(_ request: SpeechRequest) throws
    func pause()
    func resume() throws
    func cancel()
    func prefetch(_ request: SpeechRequest)
}

public extension SpeechProvider {
    func prefetch(_ request: SpeechRequest) {}
}

public struct FutureAudioAsset: Sendable {
    public let localURL: URL
    public let duration: TimeInterval?
    public let timings: [SpeechChunk]
    public init(localURL: URL, duration: TimeInterval?, timings: [SpeechChunk]) {
        self.localURL = localURL; self.duration = duration; self.timings = timings
    }
}

/// Design seam only. An implementation needs separately authorized backend,
/// disclosure, quotas and credentials held outside the client.
public protocol FutureSynthesisProvider: Sendable {
    var voices: [VoiceDescriptor] { get async throws }
    func synthesize(_ request: SpeechRequest) async throws -> FutureAudioAsset
    func cancel(requestID: String) async
}
