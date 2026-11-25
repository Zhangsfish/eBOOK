import Foundation

/// Bounded clauses retain every scalar and its original UTF-16 address. Prefer
/// punctuation; never cut a contiguous ASCII number/date/time in the middle.
enum SuxinSegmentation {
    static func chunks(_ text: String) -> [SpeechChunk] {
        let scalars = Array(text.unicodeScalars)
        var result: [SpeechChunk] = [], start = 0, offset = 0
        var leading = ""
        while start < scalars.count {
            let limit = result.isEmpty ? 18 : 36
            var end = min(scalars.count, start + limit)
            if let punctuation = (start..<end).last(where: { "，,。！？!?；;：:\n".unicodeScalars.contains(scalars[$0]) }) {
                end = punctuation + 1
            } else {
                func numeric(_ scalar: Unicode.Scalar) -> Bool { "0123456789:.-/".unicodeScalars.contains(scalar) }
                while end < scalars.count, end > start, numeric(scalars[end - 1]), numeric(scalars[end]) { end += 1 }
                if end < scalars.count, numeric(scalars[end - 1]), "年月日点分秒岁元度".unicodeScalars.contains(scalars[end]) { end += 1 }
            }
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
