import Foundation

/// Native Mandarin implementation of the pinned author's mixed frontend.
/// English/unknown symbols are explicit fallback cases, never silently removed.
public struct SuxinFrontend: Sendable {
    public enum Failure: Error { case unsupportedText, missingResource }
    private struct Lexicon: Decodable { let characters: [String: String]; let phrases: [String: [String]] }
    private struct Syllables: Decodable { let version: String; let syllables: [String: [String]] }
    private struct Model: Decodable { let phoneme_id_map: [String: [Int64]] }
    private let characters: [String: String]
    private let phrases: [String: [String]]
    private let syllables: [String: [String]]
    private let idMap: [String: [Int64]]
    private let maxPhrase: Int
    public let version: String

    public init(lexicon: Data, syllables: Data, modelConfig: Data) throws {
        let words = try JSONDecoder().decode(Lexicon.self, from: lexicon)
        let data = try JSONDecoder().decode(Syllables.self, from: syllables)
        let model = try JSONDecoder().decode(Model.self, from: modelConfig)
        guard model.phoneme_id_map["^"] != nil, model.phoneme_id_map["$"] != nil,
              model.phoneme_id_map["_"] != nil, !words.characters.isEmpty, !words.phrases.isEmpty else { throw Failure.missingResource }
        characters = words.characters; phrases = words.phrases; self.syllables = data.syllables
        idMap = model.phoneme_id_map; version = data.version
        maxPhrase = words.phrases.keys.map { $0.unicodeScalars.count }.max() ?? 1
    }

    public func prepare(_ text: String) throws -> [Int64] {
        let symbols = try phonemes(text)
        var ids = idMap["^"]!
        for symbol in symbols {
            guard let mapped = idMap[symbol] else { throw Failure.unsupportedText }
            ids += mapped
            if Self.groupEnds.contains(symbol) { ids += idMap["_"]! }
        }
        ids += idMap["$"]!
        guard ids.count > 2 else { throw Failure.unsupportedText }
        return ids
    }

    public func phonemes(_ input: String) throws -> [String] {
        // Markup is not an input language override in the reader; do not speak
        // or silently remove unknown tag bodies as if native English worked.
        guard !input.contains("<en>"), !input.contains("<zh>") else { throw Failure.unsupportedText }
        let text = input.replacingOccurrences(of: "％", with: "%").replacingOccurrences(of: "℃", with: "摄氏度")
        var segments: [(english: Bool, text: String)] = []
        var english = false, current = ""
        for scalar in text.unicodeScalars {
            let value = String(scalar)
            let next = Self.isHan(scalar) ? false : (Self.isASCIIAlphanumeric(scalar) ? true : english)
            if next != english, !current.isEmpty { segments.append((english, current)); current = "" }
            english = next; current += value
        }
        if !current.isEmpty { segments.append((english, current)) }
        // The author localizes numeric spans adjacent to Mandarin, before G2P.
        for index in segments.indices where segments[index].english {
            let before = index > 0 && !segments[index - 1].english
            let after = index + 1 < segments.count && !segments[index + 1].english
            guard before || after else { continue }
            let value = segments[index].text
            if after, value.count == 4, Self.asciiDigits(value), segments[index + 1].text.hasPrefix("年") {
                segments[index] = (false, value.map { Self.hanDigits[Int(String($0))!] }.joined())
            } else if let localized = Self.numberToHan(value) { segments[index] = (false, localized) }
        }
        var merged: [(english: Bool, text: String)] = []
        for part in segments {
            if let last = merged.last, last.english == part.english { merged[merged.count - 1].text += part.text }
            else { merged.append(part) }
        }
        var output: [String] = []
        for part in merged {
            guard !part.english else { throw Failure.unsupportedText }
            var han: [String] = []
            func flush() throws {
                guard !han.isEmpty else { return }
                output += try hanPhonemes(han); han = []
            }
            for scalar in part.text.unicodeScalars {
                if Self.isHan(scalar) { han.append(String(scalar)) }
                else {
                    try flush()
                    let char = String(scalar)
                    if let punctuation = Self.punctuation[char] { output.append(punctuation) }
                    else if CharacterSet.whitespacesAndNewlines.contains(scalar) { output.append(" ") }
                    else if !Self.ignored.contains(char) { throw Failure.unsupportedText }
                }
            }
            try flush()
        }
        return output
    }

    private func hanPhonemes(_ han: [String]) throws -> [String] {
        var resolved: [[String]] = []
        var index = 0
        while index < han.count {
            var found: [String]?, count = 1
            for length in stride(from: min(maxPhrase, han.count - index), through: 1, by: -1) {
                if let reading = phrases[han[index..<(index + length)].joined()] { found = reading; count = length; break }
            }
            if found == nil, let reading = characters[han[index]] { found = [reading] }
            guard let reading = found, reading.count == count else { throw Failure.unsupportedText }
            for offset in 0..<count {
                if han[index + offset] == "血" { resolved.append(["x", "ie", "3"]); continue }
                guard let symbols = syllables[reading[offset]], symbols.count == 3 else { throw Failure.unsupportedText }
                resolved.append(symbols)
            }
            index += count
        }
        for i in resolved.indices where i + 1 < resolved.count {
            let next = resolved[i + 1][2]
            if han[i] == "一" {
                if next == "4" { resolved[i][2] = "2" }
                else if ["1", "2", "3"].contains(next) { resolved[i][2] = "4" }
            } else if han[i] == "不", next == "4" { resolved[i][2] = "2" }
        }
        return resolved.flatMap { $0 }
    }

    private static let hanDigits = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
    private static let groupEnds: Set<String> = ["1", "2", "3", "4", "5", "。", "？", "！", "，", " ", ",", ".", "?", "!", ";", ":"]
    private static let ignored: Set<String> = Set("\"'“”‘’()（）《》【】[]{}<>·".map(String.init))
    private static let punctuation: [String: String] = ["。":"。", ".":"。", "？":"？", "?":"？", "！":"！", "!":"！", "、":"，", "，":"，", ",":"，", "：":"，", ":":"，", "；":"，", ";":"，", "—":"，", "…":"，"]
    private static func isHan(_ value: Unicode.Scalar) -> Bool {
        (0x4e00...0x9fff).contains(value.value) || (0x3400...0x4dbf).contains(value.value)
    }
    private static func isASCIIAlphanumeric(_ value: Unicode.Scalar) -> Bool {
        (48...57).contains(value.value) || (65...90).contains(value.value) || (97...122).contains(value.value)
    }
    private static func asciiDigits(_ value: String) -> Bool { !value.isEmpty && value.unicodeScalars.allSatisfy { (48...57).contains($0.value) } }
    private static func integerToHan(_ value: String) -> String? {
        guard asciiDigits(value), value.count <= 4, let number = Int(value) else { return nil }
        if number == 0 { return "零" }
        let units = ["", "十", "百", "千"]
        var output = "", zeroPending = false
        for (index, char) in value.enumerated() {
            let digit = Int(String(char))!, position = value.count - 1 - index
            if digit == 0 { zeroPending = true; continue }
            if zeroPending && !output.isEmpty { output += "零" }
            zeroPending = false
            if position == 1 && digit == 1 && output.isEmpty { output += "十" }
            else { output += hanDigits[digit] + units[position] }
        }
        return output
    }
    private static func numberToHan(_ input: String) -> String? {
        var value = input, suffix = ""
        if let last = value.last, "。？！，；：、".contains(last) { suffix = String(last); value.removeLast() }
        if value.contains(":") {
            let parts = value.components(separatedBy: ":")
            guard parts.count == 2, (1...2).contains(parts[0].count), parts[1].count == 2,
                  let hour = integerToHan(parts[0]), asciiDigits(parts[1]) else { return nil }
            if parts[1] == "00" { return hour + "点" + suffix }
            let minute = parts[1].hasPrefix("0") ? "零" + hanDigits[Int(String(parts[1].last!))!] : integerToHan(parts[1])!
            return hour + "点" + minute + "分" + suffix
        }
        let parts = value.components(separatedBy: ".")
        guard parts.count <= 2, let whole = integerToHan(parts[0]) else { return nil }
        if parts.count == 1 { return whole + suffix }
        guard asciiDigits(parts[1]) else { return nil }
        return whole + "点" + parts[1].map { hanDigits[Int(String($0))!] }.joined() + suffix
    }
}
