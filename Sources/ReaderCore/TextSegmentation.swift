import Foundation

public struct SpeechChunk: Equatable, Sendable {
    public var text: String
    public var startUTF16: Int
    public var endUTF16: Int
}

public enum TextChunker {
    public static func chunks(_ text: String, maximumUTF16: Int = 280, startUTF16: Int = 0) -> [SpeechChunk] {
        let limit = max(8, maximumUTF16)
        var result: [SpeechChunk] = []
        var pending = "", size = 0, offset = 0, start = 0
        func flush() {
            if !pending.isEmpty {
                if offset > startUTF16 {
                    let trim = max(0, startUTF16 - start)
                    // Ranges reported by speech are UTF-16; do not split a surrogate.
                    var skipped = 0, suffix = ""
                    for scalar in pending.unicodeScalars {
                        let width = scalar.value > 0xFFFF ? 2 : 1
                        if skipped >= trim { suffix.unicodeScalars.append(scalar) }
                        skipped += width
                    }
                    let actualStart = offset - suffix.utf16.count
                    if !suffix.isEmpty { result.append(SpeechChunk(text: suffix, startUTF16: actualStart, endUTF16: offset)) }
                }
                pending = ""; size = 0; start = offset
            }
        }
        for scalar in text.unicodeScalars {
            let width = scalar.value > 0xFFFF ? 2 : 1
            if size + width > limit { flush() }
            pending.unicodeScalars.append(scalar); size += width; offset += width
            if "。！？!?；;\n".unicodeScalars.contains(scalar) { flush() }
        }
        flush()
        return result
    }
}

struct HeadingCandidate {
    let line: Int
    let title: String
    let number: Int?
    let strong: Bool
}

public enum TXTHeadings {
    private static let strong = try! NSRegularExpression(pattern: #"^(?:[0-9]{1,5}[.、]\s*)?第[0-9零〇一二三四五六七八九十百千万两壹贰叁肆伍陆柒捌玖拾佰仟]{1,12}[章节回卷部集](?:\s*[^。！？；]{0,40})?$"#)
    private static let bare = try! NSRegularExpression(pattern: #"^([0-9]{3,5})([\p{Han}][^\s。！？，、：；.?!,:;]{0,30})$"#)

    public static func detect(in text: String) -> [Int: String] {
        var candidates: [HeadingCandidate] = []
        var line = 0
        text.enumerateLines { value, _ in
            defer { line += 1 }
            let title = value.trimmingCharacters(in: .whitespaces)
            guard title.utf16.count <= 64 else { return }
            let range = NSRange(title.startIndex..., in: title)
            if strong.firstMatch(in: title, range: range) != nil || ["后记", "尾声", "序章", "序言"].contains(title) {
                candidates.append(HeadingCandidate(line: line, title: title, number: nil, strong: true))
            } else if let match = bare.firstMatch(in: title, range: range), let numberRange = Range(match.range(at: 1), in: title) {
                candidates.append(HeadingCandidate(line: line, title: title, number: Int(title[numberRange]), strong: false))
            }
        }
        // Bare numerical headings require a run of >=3 increasing numbers.
        // Strong headings alone remain useful, even for a short one-chapter book.
        var accepted: [Int: String] = [:]
        var run: [HeadingCandidate] = []
        func flush() {
            if run.count >= 3 { for item in run { accepted[item.line] = item.title } }
            run.removeAll(keepingCapacity: true)
        }
        for candidate in candidates {
            if candidate.strong { flush(); accepted[candidate.line] = candidate.title; continue }
            if let previous = run.last, candidate.number != previous.number.map({ $0 + 1 }) { flush() }
            run.append(candidate)
        }
        flush()
        return accepted
    }
}
