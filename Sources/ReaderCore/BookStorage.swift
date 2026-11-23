import Foundation
import CryptoKit

public struct BookStorage: Sendable {
    public let root: URL
    public init(root: URL) throws {
        self.root = root
        try FileManager.default.createDirectory(at: root.appendingPathComponent("Books"), withIntermediateDirectories: true)
    }
    public func directory(for id: UUID) -> URL { root.appendingPathComponent("Books/\(id.uuidString)", isDirectory: true) }
    public func loadLibrary() throws -> LibraryState {
        let url = root.appendingPathComponent("library.json")
        guard FileManager.default.fileExists(atPath: url.path) else { return LibraryState() }
        var state = try JSONDecoder().decode(LibraryState.self, from: Data(contentsOf: url))
        state.preferences.validate()
        return state
    }
    public func saveLibrary(_ state: LibraryState) throws {
        try JSONEncoder().encode(state).write(to: root.appendingPathComponent("library.json"), options: .atomic)
    }
    public func document(for id: UUID) throws -> BookDocument {
        try JSONDecoder().decode(BookDocument.self, from: Data(contentsOf: directory(for: id).appendingPathComponent("index.json")))
    }
    public func text(for block: BookBlock, book id: UUID) throws -> String {
        guard block.byteCount >= 0, block.byteCount <= BookBuilder.maximumBlockUTF16 * 4 else {
            throw ReaderError.invalid("正文索引损坏。")
        }
        let handle = try FileHandle(forReadingFrom: directory(for: id).appendingPathComponent("content.utf8"))
        defer { try? handle.close() }
        try handle.seek(toOffset: block.byteOffset)
        let data = try handle.read(upToCount: block.byteCount) ?? Data()
        guard data.count == block.byteCount, let text = String(data: data, encoding: .utf8) else {
            throw ReaderError.invalid("正文文件损坏，请重新导入。")
        }
        return text
    }
    public func remove(_ id: UUID, from state: LibraryState) throws -> LibraryState {
        var next = state
        next.books.removeAll { $0.id == id }
        // Persist first. A failed write leaves the original book recoverable.
        try saveLibrary(next)
        do { try FileManager.default.removeItem(at: directory(for: id)) }
        catch {
            try saveLibrary(state)
            throw error
        }
        return next
    }
}

final class BookBuilder {
    static let maximumBlockUTF16 = 1600
    private let handle: FileHandle
    let directory: URL
    var blocks: [BookBlock] = []
    var chapters: [BookChapter] = []
    private var pending = ""
    private var byteOffset: UInt64 = 0
    private var textStart = 0
    private var chapterIndex = 0

    init(directory: URL) throws {
        self.directory = directory
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        let url = directory.appendingPathComponent("content.utf8")
        guard FileManager.default.createFile(atPath: url.path, contents: nil) else { throw ReaderError.invalid("无法创建正文文件。") }
        handle = try FileHandle(forWritingTo: url)
    }
    deinit { try? handle.close() }

    func beginChapter(_ title: String) throws {
        try flush()
        chapterIndex = chapters.count
        chapters.append(BookChapter(id: chapterIndex, title: title, firstBlock: blocks.count))
    }
    func append(_ text: String) throws {
        guard !text.isEmpty else { return }
        if !pending.isEmpty {
            if pending.utf16.count + 2 > Self.maximumBlockUTF16 { try flush() }
            else { pending += "\n\n" }
        }
        for part in TextChunker.chunks(text, maximumUTF16: Self.maximumBlockUTF16) {
            if pending.utf16.count + part.text.utf16.count > Self.maximumBlockUTF16 { try flush() }
            pending += part.text
        }
    }
    func flush() throws {
        guard !pending.isEmpty else { return }
        let data = Data(pending.utf8)
        try handle.write(contentsOf: data)
        blocks.append(BookBlock(id: blocks.count, byteOffset: byteOffset, byteCount: data.count,
                                utf16Count: pending.utf16.count, textStart: textStart, chapter: chapterIndex))
        byteOffset += UInt64(data.count); textStart += pending.utf16.count
        pending = ""
    }
    func appendImage(_ data: Data, extension suffix: String, description: String) throws {
        try flush()
        let path = "Images/\(blocks.count).\(suffix)"
        try FileManager.default.createDirectory(at: directory.appendingPathComponent("Images"), withIntermediateDirectories: true)
        try data.write(to: directory.appendingPathComponent(path))
        blocks.append(BookBlock(id: blocks.count, byteOffset: byteOffset, byteCount: 0,
                                utf16Count: 1, textStart: textStart, chapter: chapterIndex,
                                imagePath: path, imageDescription: description))
        textStart += 1
    }
    func finish(title: String, author: String?, encoding: TextEncoding?, toc: [TOCEntry], heuristic: Bool) throws -> BookDocument {
        try flush()
        try handle.synchronize()
        guard !blocks.isEmpty else { throw ReaderError.invalid("书籍没有可阅读的正文。") }
        let usableChapters = chapters.filter { $0.firstBlock < blocks.count }
        let usableTOC = toc.filter { $0.block >= 0 && $0.block < blocks.count }
        let document = BookDocument(title: title, author: author, encoding: encoding, blocks: blocks,
                                    chapters: usableChapters, toc: usableTOC, totalUTF16: textStart, heuristicTOC: heuristic)
        try JSONEncoder().encode(document).write(to: directory.appendingPathComponent("index.json"), options: .atomic)
        return document
    }
}

public enum BookImporter {
    public static func importFile(_ source: URL, storage: BookStorage, encoding: TextEncoding? = nil) throws -> BookRecord {
        let suffix = source.pathExtension.lowercased()
        guard ["txt", "epub"].contains(suffix) else { throw ReaderError.unsupported("仅支持 TXT 和 EPUB 文件。") }
        let values = try source.resourceValues(forKeys: [.fileSizeKey, .isRegularFileKey])
        let limit = suffix == "txt" ? TextDecoder.maximumBytes : 64 * 1024 * 1024
        guard values.isRegularFile == true, let size = values.fileSize, size > 0 else { throw ReaderError.invalid("请选择非空的普通文件。") }
        guard size <= limit else { throw ReaderError.tooLarge("文件过大：TXT 上限 32 MiB，EPUB 上限 64 MiB。") }
        let id = UUID(), fm = FileManager.default
        let staging = storage.root.appendingPathComponent(".import-\(id.uuidString)", isDirectory: true)
        try fm.createDirectory(at: staging, withIntermediateDirectories: true)
        do {
            let copy = staging.appendingPathComponent("source.\(suffix)")
            try fm.copyItem(at: source, to: copy)
            let copiedSize = try copy.resourceValues(forKeys: [.fileSizeKey]).fileSize ?? 0
            guard copiedSize > 0, copiedSize <= limit else { throw ReaderError.tooLarge("复制后的文件大小超出限制。") }
            let data = try Data(contentsOf: copy, options: .mappedIfSafe)
            let builder = try BookBuilder(directory: staging)
            let document: BookDocument
            if suffix == "txt" {
                let decoded = try TextDecoder.decode(data, hint: encoding)
                let headings = TXTHeadings.detect(in: decoded.text)
                var line = 0
                var failure: Error?
                if headings[0] == nil { try builder.beginChapter(headings.isEmpty ? "正文" : "开篇") }
                decoded.text.enumerateLines { value, stop in
                    do {
                        if let heading = headings[line] { try builder.beginChapter(heading) }
                        let paragraph = value.trimmingCharacters(in: .whitespaces)
                        if !paragraph.isEmpty { try builder.append(paragraph) }
                        line += 1
                    } catch { failure = error; stop = true }
                }
                if let failure { throw failure }
                try builder.flush()
                let toc = headings.isEmpty ? [] : builder.chapters.enumerated().map {
                    TOCEntry(id: $0.offset, title: $0.element.title, block: $0.element.firstBlock)
                }
                document = try builder.finish(title: source.deletingPathExtension().lastPathComponent,
                    author: nil, encoding: decoded.encoding, toc: toc, heuristic: !headings.isEmpty)
            } else {
                document = try EPUBParser.parse(data, builder: builder, fallbackTitle: source.deletingPathExtension().lastPathComponent)
            }
            let fingerprint = SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
            try fm.moveItem(at: staging, to: storage.directory(for: id))
            return BookRecord(id: id, title: document.title, author: document.author, format: suffix.uppercased(), fingerprint: fingerprint)
        } catch {
            try? fm.removeItem(at: staging)
            throw error
        }
    }
}
