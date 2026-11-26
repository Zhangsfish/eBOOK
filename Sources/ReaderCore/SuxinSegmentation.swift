import Foundation

/// Bounded clauses retain every scalar and its original UTF-16 address. Prefer
/// punctuation; never cut a contiguous ASCII number/date/time in the middle.
enum SuxinSegmentation {
    static func numberRanges(_ text: String) -> [Range<Int>] {
        let expression = try! NSRegularExpression(pattern: #"[0-9]+(?:[:.\-/][0-9]+)*(?:[年月日点分秒岁元度])?"#)
        return expression.matches(in: text, range: NSRange(location: 0, length: text.utf16.count))
            .map { $0.range.location..<($0.range.location + $0.range.length) }
    }
    static func chunks(_ text: String, protectedRanges: [Range<Int>] = []) -> [SpeechChunk] {
        let scalars = Array(text.unicodeScalars)
        var positions = [0]
        for scalar in scalars { positions.append(positions.last! + (scalar.value > 0xFFFF ? 2 : 1)) }
        let protected = numberRanges(text) + protectedRanges
        func inside(_ index: Int) -> Bool { protected.contains { $0.lowerBound < positions[index] && positions[index] < $0.upperBound } }
        var result: [SpeechChunk] = [], start = 0, offset = 0
        var leading = ""
        while start < scalars.count {
            let limit = result.isEmpty ? 18 : 36
            var end = min(scalars.count, start + limit)
            if let punctuation = (start..<end).last(where: { "，,。！？!?；;：:\n".unicodeScalars.contains(scalars[$0]) && !inside($0 + 1) }) {
                end = punctuation + 1
            }
            // Apply the same protection after punctuation and hard-limit choices.
            while end < scalars.count, inside(end) { end += 1 }
            var value = String(String.UnicodeScalarView(scalars[start..<end]))
            let spoken = value.unicodeScalars.contains { CharacterSet.alphanumerics.contains($0) }
            if !spoken && result.isEmpty {
                leading += value; start = end; continue
            }
            value = leading + value; leading = ""
            if !spoken, !result.isEmpty {
                result[result.count - 1].text += value
                result[result.count - 1].endUTF16 += value.utf16.count
            } else {
                result.append(SpeechChunk(text: value, startUTF16: offset, endUTF16: offset + value.utf16.count))
            }
            offset += value.utf16.count; start = end
        }
        if !leading.isEmpty { result.append(SpeechChunk(text: leading, startUTF16: offset, endUTF16: offset + leading.utf16.count)) }
        return result
    }
}
