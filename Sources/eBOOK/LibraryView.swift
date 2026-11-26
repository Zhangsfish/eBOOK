import SwiftUI
import UniformTypeIdentifiers
import UIKit

struct LibraryView: View {
    @EnvironmentObject private var library: LibraryModel
    @EnvironmentObject private var speech: SpeechController
    @State private var importing = false
    @State private var path: [UUID] = []
    @State private var removing: BookRecord?

    var body: some View {
        NavigationStack(path: $path) {
            Group {
                if library.state.books.isEmpty {
                    ContentUnavailableView {
                        Label("把好书留在手边", systemImage: "books.vertical")
                    } description: {
                        Text("从“文件”导入 EPUB 或 TXT。\n阅读与本机朗读，都从这里开始。")
                    } actions: { importButton }
                } else {
                    List {
                        ForEach(library.state.books) { book in
                            NavigationLink(value: book.id) {
                                HStack(spacing: 16) {
                                    Image(systemName: "book.closed.fill").font(.title).foregroundStyle(.brown)
                                        .frame(width: 44, height: 62).background(.brown.opacity(0.09), in: RoundedRectangle(cornerRadius: 8))
                                    VStack(alignment: .leading, spacing: 7) {
                                        Text(book.title).font(.headline).lineLimit(2)
                                        Text(book.author ?? book.format).font(.subheadline).foregroundStyle(.secondary)
                                        ProgressView(value: book.readingProgress).tint(.brown)
                                        Text("已读 \(Int(book.readingProgress * 100))%").font(.caption).foregroundStyle(.secondary)
                                    }
                                }.padding(.vertical, 7)
                            }.accessibilityIdentifier("library.book.\(book.title)")
                                .listRowBackground(Color(shelfBackground))
                                .swipeActions { Button("移除", role: .destructive) { removing = book } }
                        }
                        Section { Text("书籍保存在本机，仅导入你有权使用的文件。").font(.footnote).foregroundStyle(.secondary) }
                    }.listStyle(.plain).scrollContentBackground(.hidden)
                }
            }
            .background(Color(shelfBackground))
            .navigationDestination(for: UUID.self) { ReaderView(bookID: $0) }
            .navigationTitle("书架")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Menu {
                        Section("翻页方式") {
                            ForEach(ReadingMode.allCases, id: \.self) { mode in
                                Button { setMode(mode) } label: {
                                    if library.state.preferences.readingMode == mode { Label(mode.title, systemImage: "checkmark") }
                                    else { Text(mode.title) }
                                }.accessibilityIdentifier("library.mode.\(mode.rawValue)")
                            }
                        }
                        Section("书架外观") {
                            ForEach(ShelfAppearance.allCases, id: \.self) { appearance in
                                Button { setShelf(appearance) } label: {
                                    if library.state.preferences.shelfAppearance == appearance { Label(appearance.title, systemImage: "checkmark") }
                                    else { Text(appearance.title) }
                                }.accessibilityIdentifier("library.appearance.\(appearance.rawValue)")
                            }
                        }
                    } label: { Label("翻页与书架外观", systemImage: "slider.horizontal.3") }
                    .accessibilityIdentifier("library.preferences")
                    .accessibilityValue("\(library.state.preferences.readingMode.title)，书架\(library.state.preferences.shelfAppearance.title)")
                }
                ToolbarItem(placement: .topBarTrailing) { importButton }
            }
            .safeAreaInset(edge: .bottom) {
                if let book = speech.book {
                    HStack {
                        VStack(alignment: .leading) {
                            Text(book.title).font(.subheadline).lineLimit(1)
                            Text(speech.status.rawValue).font(.caption).foregroundStyle(.secondary)
                        }
                        Spacer()
                        Button { speech.status == .playing ? speech.pause() : speech.play() } label: {
                            Image(systemName: speech.status == .playing ? "pause.fill" : "play.fill").frame(width: 44, height: 44)
                        }.accessibilityLabel(speech.status == .playing ? "暂停朗读" : "继续朗读")
                        Button { speech.clearBook() } label: { Image(systemName: "xmark").frame(width: 44, height: 44) }.accessibilityLabel("关闭播放器")
                    }.padding(.horizontal).background(.regularMaterial)
                }
            }
            .overlay {
                if library.importing {
                    ProgressView("正在导入并建立索引…").padding(24).background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))
                }
            }
            .sheet(isPresented: $importing) {
                BookDocumentPicker { url in
                    importing = false
                    if let url { Task { await library.importFile(url, encoding: nil) } }
                }
            }
            .alert("无法完成操作", isPresented: Binding(get: { library.error != nil }, set: { if !$0 { library.error = nil } })) {
                Button("好") { library.error = nil }
            } message: { Text(library.error ?? "") }
            .alert("移除这本书？", isPresented: Binding(get: { removing != nil }, set: { if !$0 { removing = nil } })) {
                Button("取消", role: .cancel) { removing = nil }
                Button("移除", role: .destructive) {
                    if let removing {
                        if speech.book?.id == removing.id { speech.clearBook() }
                        library.remove(removing)
                    }
                    removing = nil
                }
            } message: { Text("将移除本机书架副本和进度，原始文件保留。") }
        }
        .tint(.brown)
        // The navigation destination explicitly uses the READER theme. Shelf
        // appearance controls only the root; neither preference overwrites the other.
        .preferredColorScheme(path.isEmpty ? shelfScheme : (library.state.preferences.theme == .dark ? .dark : .light))
    }
    private var shelfScheme: ColorScheme? {
        switch library.state.preferences.shelfAppearance {
        case .system: return nil
        case .dark: return .dark
        case .light, .warm: return .light
        }
    }
    private var shelfBackground: UIColor {
        switch library.state.preferences.shelfAppearance {
        case .system: return .systemBackground
        case .light: return ReaderTheme.light.background
        case .warm: return ReaderTheme.warm.background
        case .dark: return ReaderTheme.dark.background
        }
    }
    private func setMode(_ mode: ReadingMode) {
        var value = library.state.preferences; value.readingMode = mode; library.setPreferences(value)
    }
    private func setShelf(_ appearance: ShelfAppearance) {
        var value = library.state.preferences; value.shelfAppearance = appearance; library.setPreferences(value)
    }
    private var importButton: some View {
        Button { importing = true } label: { Label("导入书籍", systemImage: "plus") }
            .accessibilityIdentifier("library.import").disabled(library.importing || library.persistenceBlocked || library.storage == nil)
    }
}
