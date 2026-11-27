import Foundation

/// Bounded lexical repair of unclosed HTML void elements only. This does not
/// recover arbitrary XML, drop a chapter, decode entities or fetch a DTD.
enum XHTMLVoidRepair {
    private struct Element {
        let name: String
        let end: Int
        let isVoid: Bool
    }
    private static let voidNames: Set<String> = [
        "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "param", "source", "track", "wbr"
    ]

    static func repair(_ data: Data) -> Data? {
        guard data.count <= 8 * 1024 * 1024, let decoded = decode(data) else { return nil }
        let bytes = Array(decoded.text.utf8)
        var stack: [Element] = [], insertions: [Int] = []
        var cursor = 0, elements = 0, normalDepth = 0
        func starts(_ literal: String, at offset: Int) -> Bool {
            let pattern = Array(literal.utf8)
            return offset + pattern.count <= bytes.count && bytes[offset..<offset + pattern.count].elementsEqual(pattern)
        }
        func after(_ terminator: String, from start: Int) -> Int? {
            let pattern = Array(terminator.utf8)
            var index = start
            while index + pattern.count <= bytes.count {
                if bytes[index..<index + pattern.count].elementsEqual(pattern) { return index + pattern.count }
                index += 1
            }
            return nil
        }
        func isSpace(_ byte: UInt8) -> Bool { [9, 10, 13, 32].contains(byte) }
        func isName(_ byte: UInt8) -> Bool {
            (65...90).contains(byte) || (97...122).contains(byte) || (48...57).contains(byte)
                || [45, 46, 58, 95].contains(byte)
        }
        // Quotes and an internal DOCTYPE subset can contain a literal '>'.
        func tagEnd(from start: Int, declaration: Bool = false) -> Int? {
            var quote: UInt8?, brackets = 0, index = start
            while index < bytes.count {
                let byte = bytes[index]
                if let active = quote { if byte == active { quote = nil } }
                else if byte == 34 || byte == 39 { quote = byte }
                else if declaration && byte == 91 { brackets += 1 }
                else if declaration && byte == 93 { brackets = max(0, brackets - 1) }
                else if byte == 62 && brackets == 0 { return index }
                else if byte == 60 && !declaration { return nil }
                index += 1
            }
            return nil
        }
        while cursor < bytes.count {
            guard bytes[cursor] == 60 else { cursor += 1; continue }
            if starts("<!--", at: cursor) {
                guard let end = after("-->", from: cursor + 4) else { return nil }
                cursor = end; continue
            }
            if starts("<![CDATA[", at: cursor) {
                guard let end = after("]]>", from: cursor + 9) else { return nil }
                cursor = end; continue
            }
            if starts("<?", at: cursor) {
                guard let end = after("?>", from: cursor + 2) else { return nil }
                cursor = end; continue
            }
            if starts("<!", at: cursor) {
                guard let end = tagEnd(from: cursor + 2, declaration: true) else { return nil }
                cursor = end + 1; continue
            }
            let closing = starts("</", at: cursor)
            let nameStart = cursor + (closing ? 2 : 1)
            var nameEnd = nameStart
            while nameEnd < bytes.count && isName(bytes[nameEnd]) { nameEnd += 1 }
            guard nameEnd > nameStart, nameEnd < bytes.count,
                  isSpace(bytes[nameEnd]) || bytes[nameEnd] == 47 || bytes[nameEnd] == 62,
                  let end = tagEnd(from: nameEnd) else { return nil }
            let name = String(decoding: bytes[nameStart..<nameEnd], as: UTF8.self)
            if closing {
                guard bytes[nameEnd..<end].allSatisfy(isSpace) else { return nil }
                while let last = stack.last, last.name != name, last.isVoid {
                    insertions.append(last.end); stack.removeLast()
                }
                guard let last = stack.last, last.name == name else { return nil }
                stack.removeLast()
                if !last.isVoid { normalDepth -= 1 }
            } else {
                elements += 1
                guard elements <= 100_000 else { return nil }
                var last = end - 1
                while last > nameEnd && isSpace(bytes[last]) { last -= 1 }
                if bytes[last] != 47 {
                    let isVoid = voidNames.contains(name.split(separator: ":").last.map(String.init) ?? name)
                    if !isVoid { normalDepth += 1 }
                    guard normalDepth <= 128 else { return nil }
                    stack.append(Element(name: name, end: end, isVoid: isVoid))
                }
            }
            cursor = end + 1
        }
        guard stack.isEmpty, !insertions.isEmpty else { return nil }
        var output: [UInt8] = []; output.reserveCapacity(bytes.count + insertions.count)
        var previous = 0
        for index in insertions.sorted() {
            output.append(contentsOf: bytes[previous..<index]); output.append(47); previous = index
        }
        output.append(contentsOf: bytes[previous...])
        guard let encoded = String(decoding: output, as: UTF8.self).data(using: decoded.encoding) else { return nil }
        return decoded.bom + encoded
    }

    private static func decode(_ data: Data) -> (text: String, encoding: String.Encoding, bom: Data)? {
        var encoding = String.Encoding.utf8, prefix = 0
        if data.starts(with: [0xEF, 0xBB, 0xBF]) { prefix = 3 }
        else if data.starts(with: [0xFF, 0xFE]) { encoding = .utf16LittleEndian; prefix = 2 }
        else if data.starts(with: [0xFE, 0xFF]) { encoding = .utf16BigEndian; prefix = 2 }
        else if data.starts(with: [0x3C, 0]) { encoding = .utf16LittleEndian }
        else if data.starts(with: [0, 0x3C]) { encoding = .utf16BigEndian }
        guard let text = String(data: data.dropFirst(prefix), encoding: encoding) else { return nil }
        return (text, encoding, Data(data.prefix(prefix)))
    }
}
