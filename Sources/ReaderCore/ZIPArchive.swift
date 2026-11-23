import Foundation
import zlib

/// Read-only, bounded EPUB container reader. Never extracts archive paths.
struct ZIPArchive {
    struct Entry {
        let name: String
        let flags: UInt16
        let method: UInt16
        let checksum: UInt32
        let compressed: Int
        let uncompressed: Int
        let localOffset: Int
    }
    let data: Data
    let entries: [String: Entry]
    private let centralOffset: Int

    init(data: Data) throws {
        guard data.count >= 22, data.count <= 64 * 1024 * 1024 else { throw ReaderError.invalid("EPUB ZIP 容器无效或过大。") }
        self.data = data
        var end: Int?
        for offset in stride(from: data.count - 22, through: max(0, data.count - 65_557), by: -1) {
            if try data.u32(offset) == 0x06054B50, offset + 22 + Int(try data.u16(offset + 20)) == data.count {
                end = offset; break
            }
        }
        guard let end else { throw ReaderError.invalid("找不到 EPUB ZIP 目录。") }
        let count = Int(try data.u16(end + 10))
        let central = Int(try data.u32(end + 16)), centralSize = Int(try data.u32(end + 12))
        guard try data.u16(end + 4) == 0, try data.u16(end + 6) == 0,
              try data.u16(end + 8) == UInt16(count), count > 0, count <= 4096,
              central >= 0, central + centralSize == end else {
            throw ReaderError.unsupported("不支持分卷、ZIP64 或超过 4096 项的 EPUB。")
        }
        centralOffset = central
        var items: [String: Entry] = [:], cursor = central, total: UInt64 = 0
        for _ in 0..<count {
            guard cursor + 46 <= end, try data.u32(cursor) == 0x02014B50 else { throw ReaderError.invalid("EPUB ZIP 目录损坏。") }
            let flags = try data.u16(cursor + 8), method = try data.u16(cursor + 10)
            let compressed = Int(try data.u32(cursor + 20)), uncompressed = Int(try data.u32(cursor + 24))
            let nameSize = Int(try data.u16(cursor + 28)), extra = Int(try data.u16(cursor + 30)), comment = Int(try data.u16(cursor + 32))
            let finish = cursor + 46 + nameSize + extra + comment
            guard finish <= end, nameSize > 0, nameSize <= 1024,
                  let name = String(data: data.subdata(in: cursor + 46..<cursor + 46 + nameSize), encoding: .utf8),
                  Self.safeName(name), items[name] == nil else { throw ReaderError.invalid("EPUB 路径无效、重复或不安全。") }
            guard flags & 0x41 == 0, [0, 8].contains(method) else { throw ReaderError.unsupported("EPUB 已加密或压缩方式不受支持。") }
            let attributes = try data.u32(cursor + 38)
            guard (attributes >> 16) & 0xF000 != 0xA000 else { throw ReaderError.unsupported("EPUB 不允许符号链接。") }
            guard try data.u16(cursor + 34) == 0, uncompressed <= 16 * 1024 * 1024,
                  compressed < Int(UInt32.max), uncompressed < Int(UInt32.max) else { throw ReaderError.tooLarge("EPUB 单个资源过大或使用 ZIP64。") }
            total += UInt64(uncompressed)
            guard total <= 96 * 1024 * 1024 else { throw ReaderError.tooLarge("EPUB 解压资源总量超过 96 MiB。") }
            let local = Int(try data.u32(cursor + 42))
            guard local >= 0, local + 30 <= central else { throw ReaderError.invalid("EPUB ZIP 文件偏移无效。") }
            items[name] = Entry(name: name, flags: flags, method: method, checksum: try data.u32(cursor + 16),
                                compressed: compressed, uncompressed: uncompressed, localOffset: local)
            cursor = finish
        }
        guard cursor == end else { throw ReaderError.invalid("EPUB ZIP 目录大小不一致。") }
        entries = items
    }

    private static func safeName(_ name: String) -> Bool {
        guard !name.hasPrefix("/"), !name.contains("\\"), !name.contains(":"), !name.contains("\0") else { return false }
        let parts = name.split(separator: "/", omittingEmptySubsequences: false)
        return parts.enumerated().allSatisfy { index, part in
            part != ".." && part != "." && (!part.isEmpty || index == parts.count - 1)
        }
    }

    func read(_ path: String, maximum: Int = 8 * 1024 * 1024) throws -> Data {
        guard let entry = entries[path], !path.hasSuffix("/") else { throw ReaderError.invalid("EPUB 缺少资源：\(path.prefix(120))") }
        guard entry.uncompressed <= maximum else { throw ReaderError.tooLarge("EPUB 资源超出解析上限。") }
        let local = entry.localOffset
        guard try data.u32(local) == 0x04034B50, try data.u16(local + 6) == entry.flags,
              try data.u16(local + 8) == entry.method else { throw ReaderError.invalid("EPUB ZIP 本地目录不一致。") }
        let nameSize = Int(try data.u16(local + 26)), extra = Int(try data.u16(local + 28))
        let start = local + 30 + nameSize + extra
        guard start <= centralOffset, start + entry.compressed <= centralOffset,
              local + 30 + nameSize <= centralOffset,
              String(data: data.subdata(in: local + 30..<local + 30 + nameSize), encoding: .utf8) == entry.name else {
            throw ReaderError.invalid("EPUB ZIP 正文范围无效。")
        }
        let compressed = data.subdata(in: start..<start + entry.compressed)
        let output: Data
        if entry.method == 0 {
            guard compressed.count == entry.uncompressed else { throw ReaderError.invalid("EPUB ZIP 资源长度不一致。") }
            output = compressed
        } else {
            var stream = z_stream()
            guard inflateInit2_(&stream, -MAX_WBITS, ZLIB_VERSION, Int32(MemoryLayout<z_stream>.size)) == Z_OK else {
                throw ReaderError.invalid("无法初始化 EPUB 解压器。")
            }
            defer { inflateEnd(&stream) }
            var buffer = Data(count: max(1, entry.uncompressed))
            let status = compressed.withUnsafeBytes { source in
                buffer.withUnsafeMutableBytes { destination in
                    stream.next_in = UnsafeMutablePointer(mutating: source.bindMemory(to: Bytef.self).baseAddress)
                    stream.avail_in = uInt(compressed.count)
                    stream.next_out = destination.bindMemory(to: Bytef.self).baseAddress
                    stream.avail_out = uInt(destination.count)
                    return inflate(&stream, Z_FINISH)
                }
            }
            guard status == Z_STREAM_END, stream.total_out == entry.uncompressed, stream.total_in == entry.compressed else {
                throw ReaderError.invalid("EPUB 压缩数据损坏或长度不一致。")
            }
            output = buffer.prefix(entry.uncompressed)
        }
        let checksum = output.withUnsafeBytes { bytes in crc32(0, bytes.bindMemory(to: Bytef.self).baseAddress, uInt(bytes.count)) }
        guard UInt32(checksum) == entry.checksum else { throw ReaderError.invalid("EPUB 资源 CRC 校验失败。") }
        return output
    }
}

private extension Data {
    func u16(_ offset: Int) throws -> UInt16 {
        guard offset >= 0, offset + 2 <= count else { throw ReaderError.invalid("EPUB ZIP 被截断。") }
        return UInt16(self[offset]) | UInt16(self[offset + 1]) << 8
    }
    func u32(_ offset: Int) throws -> UInt32 {
        UInt32(try u16(offset)) | UInt32(try u16(offset + 2)) << 16
    }
}
