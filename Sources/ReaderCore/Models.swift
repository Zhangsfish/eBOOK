import Foundation

public enum ReaderError: Error, LocalizedError {
    case invalid(String)
    case unsupported(String)
    case tooLarge(String)
    public var errorDescription: String? {
        switch self {
        case .invalid(let message), .unsupported(let message), .tooLarge(let message): return message
        }
    }
}

public enum TextEncoding: String, Codable, CaseIterable, Sendable {
    case utf8 = "UTF-8", utf16LE = "UTF-16 LE", utf16BE = "UTF-16 BE"
    case gbk = "GBK", gb18030 = "GB18030"
}

public struct TextPosition: Codable, Equatable, Sendable {
    public var block: Int
    public var utf16Offset: Int
    public init(block: Int = 0, utf16Offset: Int = 0) {
        self.block = block; self.utf16Offset = utf16Offset
    }
}

public struct ReadingAnchor: Codable, Equatable, Sendable {
    public var block: Int
    public var fraction: Double
    public init(block: Int = 0, fraction: Double = 0) {
        self.block = block; self.fraction = fraction
    }
}

public struct BookBlock: Codable, Identifiable, Sendable {
    public var id: Int
    public var byteOffset: UInt64
    public var byteCount: Int
    public var utf16Count: Int
    public var textStart: Int
    public var chapter: Int
    public var imagePath: String?
    public var imageDescription: String?
}

public struct BookChapter: Codable, Identifiable, Sendable {
    public var id: Int
    public var title: String
    public var firstBlock: Int
}

public struct TOCEntry: Codable, Identifiable, Sendable {
    public var id: Int
    public var title: String
    public var block: Int
    public var depth: Int
    public init(id: Int, title: String, block: Int, depth: Int = 0) {
        self.id = id; self.title = title; self.block = block; self.depth = depth
    }
}

public struct BookDocument: Codable, Sendable {
    public var title: String
    public var author: String?
    public var encoding: TextEncoding?
    public var blocks: [BookBlock]
    public var chapters: [BookChapter]
    public var toc: [TOCEntry]
    public var totalUTF16: Int
    public var heuristicTOC: Bool

    public func clamped(_ position: TextPosition) -> TextPosition {
        guard !blocks.isEmpty else { return TextPosition() }
        let block = min(max(0, position.block), blocks.count - 1)
        return TextPosition(block: block, utf16Offset: min(max(0, position.utf16Offset), blocks[block].utf16Count))
    }

    /// The nearest preceding TOC destination, including the body of a chapter.
    /// EPUB navigation order need not match spine order; prefer the deepest
    /// entry when a section and its parent share the same destination.
    public func tocEntry(atBlock block: Int) -> TOCEntry? {
        guard !blocks.isEmpty else { return nil }
        let position = min(max(0, block), blocks.count - 1)
        return toc.lazy.filter { $0.block >= 0 && $0.block <= position }.max {
            $0.block == $1.block ? $0.depth < $1.depth : $0.block < $1.block
        }
    }

    public func progress(block: Int, fraction: Double = 0) -> Double {
        guard totalUTF16 > 0, !blocks.isEmpty else { return 0 }
        let item = blocks[min(max(0, block), blocks.count - 1)]
        return min(1, max(0, (Double(item.textStart) + Double(item.utf16Count) * min(1, max(0, fraction))) / Double(totalUTF16)))
    }

    public func block(atProgress progress: Double) -> Int {
        guard !blocks.isEmpty else { return 0 }
        let target = Int(Double(totalUTF16) * min(1, max(0, progress)))
        var low = 0, high = blocks.count
        while low < high {
            let mid = (low + high) / 2
            if blocks[mid].textStart <= target { low = mid + 1 } else { high = mid }
        }
        return max(0, low - 1)
    }
}

public struct BookRecord: Codable, Identifiable, Sendable {
    public var id: UUID
    public var title: String
    public var author: String?
    public var format: String
    public var fingerprint: String
    public var importedAt: Date
    public var reading: ReadingAnchor
    public var listening: TextPosition
    public var readingProgress: Double

    public init(id: UUID, title: String, author: String?, format: String, fingerprint: String) {
        self.id = id; self.title = title; self.author = author; self.format = format
        self.fingerprint = fingerprint; importedAt = Date()
        reading = ReadingAnchor(); listening = TextPosition(); readingProgress = 0
    }
}

public enum ReaderTheme: String, Codable, CaseIterable, Sendable {
    case light, warm, dark
    public var title: String {
        switch self { case .light: return "明亮"; case .warm: return "护眼"; case .dark: return "夜间" }
    }
}

public struct ReaderPreferences: Codable, Equatable, Sendable {
    public var fontSize: Double = 21
    public var lineSpacing: Double = 9
    public var theme: ReaderTheme = .warm
    public var speechRate: Float = 0.5
    public var suxinRate: Float = 1
    public var voiceIdentifier: String?
    public init() {}
    private enum CodingKeys: String, CodingKey { case fontSize, lineSpacing, theme, speechRate, suxinRate, voiceIdentifier }
    public init(from decoder: Decoder) throws {
        let fields = try decoder.container(keyedBy: CodingKeys.self)
        fontSize = try fields.decodeIfPresent(Double.self, forKey: .fontSize) ?? 21
        lineSpacing = try fields.decodeIfPresent(Double.self, forKey: .lineSpacing) ?? 9
        theme = try fields.decodeIfPresent(ReaderTheme.self, forKey: .theme) ?? .warm
        speechRate = try fields.decodeIfPresent(Float.self, forKey: .speechRate) ?? 0.5
        suxinRate = try fields.decodeIfPresent(Float.self, forKey: .suxinRate) ?? 1
        voiceIdentifier = try fields.decodeIfPresent(String.self, forKey: .voiceIdentifier)
        validate()
    }
    public mutating func validate() {
        fontSize = fontSize.isFinite ? min(36, max(14, fontSize)) : 21
        lineSpacing = lineSpacing.isFinite ? min(24, max(0, lineSpacing)) : 9
        speechRate = speechRate.isFinite ? min(0.65, max(0.35, speechRate)) : 0.5
        suxinRate = suxinRate.isFinite ? min(2, max(0.5, suxinRate)) : 1
    }
}

public struct LibraryState: Codable, Sendable {
    public var books: [BookRecord] = []
    public var preferences = ReaderPreferences()
    public init() {}
}
