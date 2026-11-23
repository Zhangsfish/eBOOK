import SwiftUI
import UniformTypeIdentifiers

struct LibraryView: View {
    @EnvironmentObject private var library: LibraryModel
    @EnvironmentObject private var speech: SpeechController
    @State private var importing = false
    @State private var encoding: TextEncoding?
    @State private var removing: BookRecord?

    var body: some View {
        NavigationStack {
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
                            NavigationLink { ReaderView(bookID: book.id) } label: {
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
                                .swipeActions { Button("移除", role: .destructive) { removing = book } }
                        }
                        Section { Text("书籍保存在本机，仅导入你有权使用的文件。").font(.footnote).foregroundStyle(.secondary) }
                    }.listStyle(.plain)
                }
            }
            .navigationTitle("书架")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Menu {
                        Picker("TXT 编码", selection: $encoding) {
                            Text("自动识别").tag(nil as TextEncoding?)
                            ForEach(TextEncoding.allCases, id: \.self) { Text($0.rawValue).tag(Optional($0)) }
                        }
                    } label: { Label("TXT 编码", systemImage: "textformat.abc") }
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
            .fileImporter(isPresented: $importing, allowedContentTypes: [.plainText, UTType(filenameExtension: "epub") ?? .data], allowsMultipleSelection: false) { result in
                switch result {
                case .success(let urls): if let url = urls.first { Task { await library.importFile(url, encoding: encoding) } }
                case .failure(let error): library.error = error.localizedDescription
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
    }
    private var importButton: some View {
        Button { importing = true } label: { Label("导入书籍", systemImage: "plus") }
            .accessibilityIdentifier("library.import").disabled(library.importing || library.persistenceBlocked || library.storage == nil)
    }
}
