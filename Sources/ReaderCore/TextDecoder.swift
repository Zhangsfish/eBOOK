import Foundation
import CoreFoundation

public struct DecodedText: Sendable {
    public let text: String
    public let encoding: TextEncoding
}

public enum TextDecoder {
    public static let maximumBytes = 32 * 1024 * 1024

    public static func decode(_ data: Data, hint: TextEncoding? = nil) throws -> DecodedText {
        guard !data.isEmpty else { throw ReaderError.invalid("TXT 文件为空。") }
        guard data.count <= maximumBytes else { throw ReaderError.tooLarge("TXT 超过 32 MiB，请先拆分文件。") }
        let bytes = [UInt8](data.prefix(4))
        // UTF-32 must not be mistaken for UTF-16.
        if bytes == [0xFF, 0xFE, 0, 0] || bytes == [0, 0, 0xFE, 0xFF] {
            throw ReaderError.unsupported("不支持 UTF-32，请转换为 UTF-8。")
        }
        let encoding: TextEncoding
        let payload: Data
        if data.starts(with: [0xEF, 0xBB, 0xBF]) {
            encoding = .utf8; payload = data.dropFirst(3)
        } else if data.starts(with: [0xFF, 0xFE]) {
            encoding = .utf16LE; payload = data.dropFirst(2)
        } else if data.starts(with: [0xFE, 0xFF]) {
            encoding = .utf16BE; payload = data.dropFirst(2)
        } else {
            payload = data
            if let hint { encoding = hint }
            else if looksLikeUTF16(data, littleEndian: true) { encoding = .utf16LE }
            else if looksLikeUTF16(data, littleEndian: false) { encoding = .utf16BE }
            else if String(data: data, encoding: .utf8) != nil { encoding = .utf8 }
            else { encoding = try validateLegacy(data) ? .gb18030 : .gbk }
        }
        let text: String
        switch encoding {
        case .utf8:
            guard let value = String(data: payload, encoding: .utf8) else {
                throw ReaderError.invalid("UTF-8 字节无效，请检查文件或手动选择编码。")
            }
            text = value
        case .utf16LE, .utf16BE:
            text = try decodeUTF16(payload, littleEndian: encoding == .utf16LE)
        case .gbk, .gb18030:
            let hasFourByte = try validateLegacy(payload)
            guard encoding != .gbk || !hasFourByte else {
                throw ReaderError.invalid("文件包含 GB18030 四字节字符，请选择 GB18030。")
            }
            let cfEncoding = CFStringEncoding(CFStringEncodings.GB_18030_2000.rawValue)
            let nsEncoding = String.Encoding(rawValue: CFStringConvertEncodingToNSStringEncoding(cfEncoding))
            guard let value = String(data: payload, encoding: nsEncoding),
                  value.data(using: nsEncoding, allowLossyConversion: false) == payload else {
                throw ReaderError.invalid("GBK/GB18030 解码失败，未使用有损替换。请检查编码。")
            }
            text = value
        }
        guard !text.unicodeScalars.contains(where: {
            $0.value == 0xFFFD || ($0.value < 32 && ![9, 10, 12, 13].contains($0.value))
        }) else { throw ReaderError.invalid("文件含有无效替换字符或二进制控制字符。") }
        guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            throw ReaderError.invalid("TXT 没有可阅读的正文。")
        }
        return DecodedText(text: text.replacingOccurrences(of: "\r\n", with: "\n")
            .replacingOccurrences(of: "\r", with: "\n"), encoding: encoding)
    }

    private static func looksLikeUTF16(_ data: Data, littleEndian: Bool) -> Bool {
        guard data.count >= 4, data.count.isMultiple(of: 2) else { return false }
        let sample = [UInt8](data.prefix(512))
        let pairs = sample.count / 2
        let highZeros = stride(from: littleEndian ? 1 : 0, to: pairs * 2, by: 2).filter { sample[$0] == 0 }.count
        let lowZeros = stride(from: littleEndian ? 0 : 1, to: pairs * 2, by: 2).filter { sample[$0] == 0 }.count
        return highZeros * 4 > pairs && lowZeros * 8 < pairs
    }

    private static func decodeUTF16(_ data: Data, littleEndian: Bool) throws -> String {
        guard data.count.isMultiple(of: 2) else { throw ReaderError.invalid("UTF-16 字节数不是偶数。") }
        let bytes = [UInt8](data)
        var units: [UInt16] = []
        units.reserveCapacity(bytes.count / 2)
        for index in stride(from: 0, to: bytes.count, by: 2) {
            let first = UInt16(bytes[index]), second = UInt16(bytes[index + 1])
            units.append(littleEndian ? first | second << 8 : first << 8 | second)
        }
        var index = 0
        while index < units.count {
            let unit = units[index]
            if (0xD800...0xDBFF).contains(unit) {
                guard index + 1 < units.count, (0xDC00...0xDFFF).contains(units[index + 1]) else {
                    throw ReaderError.invalid("UTF-16 代理对不完整。")
                }
                index += 2
            } else {
                guard !(0xDC00...0xDFFF).contains(unit) else { throw ReaderError.invalid("UTF-16 代理对无效。") }
                index += 1
            }
        }
        return String(decoding: units, as: UTF16.self)
    }

    // A strict structural check followed by a lossless system-codec round trip.
    private static func validateLegacy(_ data: Data) throws -> Bool {
        let bytes = [UInt8](data)
        var index = 0, fourByte = false
        while index < bytes.count {
            let first = bytes[index]
            if first <= 0x7F { index += 1; continue }
            guard (0x81...0xFE).contains(first), index + 1 < bytes.count else {
                throw ReaderError.invalid("无法严格识别 TXT 编码，请检查文件或手动选择编码。")
            }
            let second = bytes[index + 1]
            if (0x30...0x39).contains(second) {
                guard index + 3 < bytes.count, (0x81...0xFE).contains(bytes[index + 2]),
                      (0x30...0x39).contains(bytes[index + 3]) else {
                    throw ReaderError.invalid("GB18030 四字节序列不完整。")
                }
                fourByte = true; index += 4
            } else {
                guard (0x40...0xFE).contains(second), second != 0x7F else {
                    throw ReaderError.invalid("GBK 字节序列无效。")
                }
                index += 2
            }
        }
        return fourByte
    }
}
