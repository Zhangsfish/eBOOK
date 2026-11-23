import Foundation

/// Keep the UIKit/accessibility tree bounded as well as the decoded text.
/// Absolute block IDs remain stable when the visible window moves.
public struct ReadingWindow: Equatable, Sendable {
    public static let maximumBlocks = 12
    public let total: Int
    public let lowerBound: Int
    public let upperBound: Int
    public var count: Int { upperBound - lowerBound }

    public init(total: Int, anchor: Int = 0) {
        self.total = max(0, total)
        let block = min(max(0, anchor), max(0, total - 1))
        lowerBound = min(max(0, block - 3), max(0, total - Self.maximumBlocks))
        upperBound = min(max(0, total), lowerBound + Self.maximumBlocks)
    }
    public func shouldMove(at block: Int) -> Bool {
        (block <= lowerBound + 2 && lowerBound > 0)
            || (block >= lowerBound + Self.maximumBlocks / 2 && upperBound < total)
    }
}
