import Foundation
import SwiftUI

@MainActor final class LibraryModel: ObservableObject {
    @Published private(set) var state = LibraryState()
    @Published private(set) var importing = false
    @Published private(set) var persistenceBlocked = false
    @Published var error: String?
    let storage: BookStorage?

    init(root: URL? = nil) {
        do {
            var base = root ?? FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0].appendingPathComponent("eBOOK", isDirectory: true)
            #if DEBUG
            if ProcessInfo.processInfo.arguments.contains("--uitesting") {
                // Match the shipping app: imported/indexed books are private
                // support data, not a File Provider's shared Documents tree.
                base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0].appendingPathComponent(".ui-test-library", isDirectory: true)
                if ProcessInfo.processInfo.arguments.contains("--reset-library"), FileManager.default.fileExists(atPath: base.path) {
                    try FileManager.default.removeItem(at: base)
                }
            }
            #endif
            let storage = try BookStorage(root: base)
            self.storage = storage
            do { state = try storage.loadLibrary() }
            catch {
                persistenceBlocked = true
                self.error = "书架无法读取：\(error.localizedDescription)"
            }
        } catch { storage = nil; self.error = "书架存储无法访问：\(error.localizedDescription)" }
    }

    func importFile(_ url: URL, encoding: TextEncoding?) async {
        guard !importing, !persistenceBlocked, let storage else {
            NSLog("EBOOK_IMPORT ignored busy=%d blocked=%d storage=%d", importing ? 1 : 0, persistenceBlocked ? 1 : 0, storage == nil ? 0 : 1)
            return
        }
        importing = true
        NSLog("EBOOK_IMPORT started")
        defer { importing = false }
        let scoped = url.startAccessingSecurityScopedResource()
        defer { if scoped { url.stopAccessingSecurityScopedResource() } }
        do {
            let record = try await Task.detached(priority: .userInitiated) {
                try Self.importCoordinated(url, storage: storage, encoding: encoding)
            }.value
            var next = state
            next.books.insert(record, at: 0)
            do {
                try storage.saveLibrary(next); state = next
                NSLog("EBOOK_IMPORT saved books=%ld", state.books.count)
            }
            catch {
                try? FileManager.default.removeItem(at: storage.directory(for: record.id))
                throw error
            }
        } catch {
            NSLog("EBOOK_IMPORT failed code=%ld", (error as NSError).code)
            self.error = "导入失败：\(error.localizedDescription)"
        }
    }

    nonisolated private static func importCoordinated(_ url: URL, storage: BookStorage, encoding: TextEncoding?) throws -> BookRecord {
        // Files providers may hand out a placeholder or coordinated URL. Keep
        // the security scope open while materializing and copying the selection.
        let coordinator = NSFileCoordinator(filePresenter: nil)
        var coordinationError: NSError?
        var result: Result<BookRecord, Error>?
        NSLog("EBOOK_IMPORT coordination requested")
        coordinator.coordinate(readingItemAt: url, options: .withoutChanges, error: &coordinationError) { readableURL in
            NSLog("EBOOK_IMPORT coordination entered")
            result = Result { try BookImporter.importFile(readableURL, storage: storage, encoding: encoding) }
        }
        NSLog("EBOOK_IMPORT coordination returned")
        if let coordinationError { throw coordinationError }
        guard let result else { throw ReaderError.invalid("文件提供程序未返回可读取的文件。") }
        return try result.get()
    }

    func remove(_ book: BookRecord) {
        guard !persistenceBlocked, let storage else { return }
        do { state = try storage.remove(book.id, from: state) }
        catch { self.error = "移除失败：\(error.localizedDescription)" }
    }

    func record(_ id: UUID) -> BookRecord? { state.books.first { $0.id == id } }

    func updateReading(_ id: UUID, anchor: ReadingAnchor, progress: Double) {
        guard let index = state.books.firstIndex(where: { $0.id == id }) else { return }
        state.books[index].reading = anchor
        state.books[index].readingProgress = progress
        persist()
    }

    func updateListening(_ id: UUID, position: TextPosition) {
        guard let index = state.books.firstIndex(where: { $0.id == id }) else { return }
        state.books[index].listening = position
        persist()
    }

    func setPreferences(_ preferences: ReaderPreferences) {
        var validated = preferences; validated.validate()
        state.preferences = validated
        persist()
    }

    func persist() {
        guard !persistenceBlocked else { return }
        do { try storage?.saveLibrary(state) }
        catch { self.error = "更改未能保存：\(error.localizedDescription)" }
    }

    #if DEBUG
    func importUITestFixtureIfRequested() async {
        let arguments = ProcessInfo.processInfo.arguments
        guard arguments.contains("--uitesting"), state.books.isEmpty,
              let flag = arguments.firstIndex(of: "--test-import"), flag + 1 < arguments.count else { return }
        let name = arguments[flag + 1]
        guard !name.contains("/"), !name.contains("\\"), !name.contains("..") else { return }
        let url = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0].appendingPathComponent(name)
        await importFile(url, encoding: nil)
    }
    #endif
}
