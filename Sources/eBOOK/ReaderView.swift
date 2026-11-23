import SwiftUI

struct ReaderView: View {
    let bookID: UUID
    @EnvironmentObject private var library: LibraryModel
    @EnvironmentObject private var speech: SpeechController
    @State private var document: BookDocument?
    @State private var jump = ReaderJump(block: 0)
    @State private var current = ReadingAnchor()
    @State private var showingTOC = false
    @State private var showingSettings = false
    @State private var loadError: String?
    @State private var tocQuery = ""

    var body: some View {
        Group {
            if let document, let storage = library.storage {
                VStack(spacing: 0) {
                    ReaderTable(document: document, storage: storage, bookID: bookID,
                                preferences: library.state.preferences, jump: jump) { anchor in
                        current = anchor
                        library.updateReading(bookID, anchor: anchor, progress: document.progress(block: anchor.block, fraction: anchor.fraction))
                    } onError: { loadError = $0 }
                    HStack {
                        Text("\(Int(document.progress(block: current.block, fraction: current.fraction) * 100))%")
                            .monospacedDigit().accessibilityIdentifier("reader.progress")
                        Slider(value: Binding(get: { document.progress(block: current.block, fraction: current.fraction) }, set: {
                            jump = ReaderJump(block: document.block(atProgress: $0))
                        }), in: 0...1)
                        .accessibilityLabel("阅读进度")
                        Text("\(current.block + 1)/\(document.blocks.count)").monospacedDigit().accessibilityIdentifier("reader.anchor")
                    }.font(.caption).padding(.horizontal).padding(.vertical, 8).background(.bar)
                    playback(document, storage: storage)
                }
                .background(Color(library.state.preferences.theme.background))
            } else if let loadError {
                ContentUnavailableView("无法打开书籍", systemImage: "exclamationmark.triangle", description: Text(loadError))
            } else { ProgressView("正在打开…") }
        }
        .navigationTitle(library.record(bookID)?.title ?? "阅读")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItemGroup(placement: .topBarTrailing) {
                Button { showingTOC = true } label: { Image(systemName: "list.bullet") }.accessibilityLabel("目录").accessibilityIdentifier("reader.toc")
                Button { showingSettings = true } label: { Image(systemName: "textformat.size") }.accessibilityLabel("阅读设置").accessibilityIdentifier("reader.settings")
            }
        }
        .sheet(isPresented: $showingTOC) { toc }
        .sheet(isPresented: $showingSettings) { ReaderSettings().environmentObject(library).environmentObject(speech) }
        .task {
            guard document == nil, let storage = library.storage, let record = library.record(bookID) else { return }
            do {
                let loaded = try storage.document(for: bookID)
                current = record.reading
                jump = ReaderJump(block: current.block, fraction: current.fraction)
                document = loaded
            } catch { loadError = error.localizedDescription }
        }
        .onDisappear { library.persist() }
        .alert("朗读提示", isPresented: Binding(get: { speech.error != nil }, set: { if !$0 { speech.error = nil } })) {
            Button("好") { speech.error = nil }
        } message: { Text(speech.error ?? "") }
        .alert("正文读取失败", isPresented: Binding(get: { document != nil && loadError != nil }, set: { if !$0 { loadError = nil } })) {
            Button("好") { loadError = nil }
        } message: { Text(loadError ?? "") }
    }

    private var toc: some View {
        NavigationStack {
            List {
                if let document {
                    if document.heuristicTOC {
                        Text("TXT 目录由标题格式推测，可能有遗漏。").font(.footnote).foregroundStyle(.secondary)
                    }
                    if document.toc.isEmpty {
                        Text("未检测到可靠章节，可使用阅读进度浏览全文。").foregroundStyle(.secondary)
                    }
                    ForEach(document.toc.filter { tocQuery.isEmpty || $0.title.localizedCaseInsensitiveContains(tocQuery) }) { entry in
                        Button {
                            jump = ReaderJump(block: entry.block); showingTOC = false
                        } label: {
                            Text(entry.title).padding(.leading, CGFloat(entry.depth) * 14).foregroundStyle(.primary)
                        }.accessibilityIdentifier("toc.entry.\(entry.id)")
                    }
                }
            }.navigationTitle("目录").searchable(text: $tocQuery, prompt: "查找章节")
                .toolbar { ToolbarItem(placement: .topBarTrailing) { Button("完成") { showingTOC = false } } }
        }
    }

    private func playback(_ document: BookDocument, storage: BookStorage) -> some View {
        let active = speech.book?.id == bookID
        return VStack(spacing: 4) {
            HStack {
                Label(active ? speech.status.rawValue : "本机语音 · 不发送正文", systemImage: "waveform")
                    .font(.caption).foregroundStyle(.secondary)
                Spacer()
                if active {
                    Button("查看听书位置") { jump = ReaderJump(block: speech.position.block) }.font(.caption)
                }
            }
            HStack(spacing: 12) {
                Button { ensureSpeech(document, storage); speech.skipChapter(-1) } label: { Image(systemName: "backward.end.fill").frame(minWidth: 44, minHeight: 44) }.accessibilityLabel("上一章")
                Button { ensureSpeech(document, storage); speech.skipParagraph(-1) } label: { Image(systemName: "gobackward").frame(minWidth: 44, minHeight: 44) }.accessibilityLabel("上一段")
                Button {
                    ensureSpeech(document, storage)
                    if speech.status == .playing { speech.pause() } else { speech.play() }
                } label: {
                    Label(active && speech.status == .playing ? "暂停" : "朗读", systemImage: active && speech.status == .playing ? "pause.fill" : "play.fill")
                        .frame(maxWidth: .infinity, minHeight: 44)
                }.buttonStyle(.borderedProminent).accessibilityIdentifier("speech.play")
                Button { ensureSpeech(document, storage); speech.skipParagraph(1) } label: { Image(systemName: "goforward").frame(minWidth: 44, minHeight: 44) }.accessibilityLabel("下一段")
                Button { ensureSpeech(document, storage); speech.skipChapter(1) } label: { Image(systemName: "forward.end.fill").frame(minWidth: 44, minHeight: 44) }.accessibilityLabel("下一章")
            }
            Button("从当前阅读位置开始朗读") {
                ensureSpeech(document, storage)
                let length = document.blocks[current.block].utf16Count
                speech.seek(TextPosition(block: current.block, utf16Offset: Int(Double(length) * current.fraction)))
                speech.play()
            }.font(.caption).padding(.bottom, 4)
        }.padding(.horizontal).background(.bar)
    }
    private func ensureSpeech(_ document: BookDocument, _ storage: BookStorage) {
        if let record = library.record(bookID) { speech.load(record, document: document, storage: storage) }
    }
}

struct ReaderSettings: View {
    @EnvironmentObject private var library: LibraryModel
    @EnvironmentObject private var speech: SpeechController
    @Environment(\.dismiss) private var dismiss
    var body: some View {
        NavigationStack {
            Form {
                Section("阅读") {
                    LabeledContent("字号", value: "\(Int(library.state.preferences.fontSize))")
                    Slider(value: setting(\.fontSize), in: 14...36, step: 1).accessibilityLabel("字号").accessibilityIdentifier("settings.font")
                    LabeledContent("行距", value: "\(Int(library.state.preferences.lineSpacing))")
                    Slider(value: setting(\.lineSpacing), in: 0...24, step: 1).accessibilityLabel("行距")
                    Picker("主题", selection: setting(\.theme)) {
                        ForEach(ReaderTheme.allCases, id: \.self) { Text($0.title).tag($0) }
                    }.pickerStyle(.segmented).accessibilityIdentifier("settings.theme")
                }
                Section("本机朗读") {
                    Text("使用设备已有语音，不向云端发送书籍正文。语音质量取决于设备安装的语音。").font(.footnote).foregroundStyle(.secondary)
                    LabeledContent("语速", value: String(format: "%.2f", library.state.preferences.speechRate))
                    Slider(value: Binding(get: { Double(library.state.preferences.speechRate) }, set: {
                        var value = library.state.preferences; value.speechRate = Float($0); library.setPreferences(value); speech.preferencesChanged()
                    }), in: 0.35...0.65, step: 0.025).accessibilityLabel("朗读语速")
                    Picker("语音", selection: Binding(get: { library.state.preferences.voiceIdentifier ?? "" }, set: {
                        var value = library.state.preferences; value.voiceIdentifier = $0.isEmpty ? nil : $0; library.setPreferences(value); speech.preferencesChanged()
                    })) {
                        Text("默认中文语音").tag("")
                        ForEach(speech.provider.voices.filter { $0.language.hasPrefix("zh") }) { Text("\($0.name) · \($0.language)").tag($0.id) }
                    }
                }
            }.navigationTitle("阅读设置").toolbar { ToolbarItem(placement: .topBarTrailing) { Button("完成") { dismiss() } } }
        }
    }
    private func setting<T>(_ keyPath: WritableKeyPath<ReaderPreferences, T>) -> Binding<T> {
        Binding(get: { library.state.preferences[keyPath: keyPath] }, set: {
            var value = library.state.preferences; value[keyPath: keyPath] = $0; library.setPreferences(value)
        })
    }
}
