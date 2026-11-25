import SwiftUI

struct ReaderView: View {
    let bookID: UUID
    @EnvironmentObject private var library: LibraryModel
    @EnvironmentObject private var speech: SpeechController
    @Environment(\.dismiss) private var dismiss
    @Environment(\.colorSchemeContrast) private var colorSchemeContrast
    @State private var document: BookDocument?
    @State private var jump = ReaderJump(block: 0)
    @State private var current = ReadingAnchor()
    @State private var showingTOC = false
    @State private var showingSettings = false
    @State private var showingSpeech = false
    @State private var showingControls = false
    @State private var loadError: String?
    @State private var tocQuery = ""

    var body: some View {
        Group {
            if let document, let storage = library.storage {
                ZStack(alignment: .bottomTrailing) {
                    ReaderTable(document: document, storage: storage, bookID: bookID,
                                preferences: library.state.preferences, jump: jump) { anchor in
                        current = anchor
                        library.updateReading(bookID, anchor: anchor, progress: document.progress(block: anchor.block, fraction: anchor.fraction))
                    } onError: { loadError = $0 }
                    // Keep the text viewport stable when controls appear/disappear.
                    // The quiet bottom margin also keeps the entry off the text.
                    .padding(.bottom, 44)
                    if showingControls {
                        readingControls(document)
                            .padding(12)
                            .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))
                            .padding(12)
                    } else {
                        Button { showingControls = true } label: {
                            Image(systemName: "ellipsis")
                                .font(.system(size: 16, weight: .regular))
                                .foregroundStyle(Color(library.state.preferences.theme.foreground)
                                    .opacity(colorSchemeContrast == .increased ? 1 : 0.60))
                                .frame(width: 44, height: 44)
                                .contentShape(Rectangle())
                        }
                        .buttonStyle(.plain)
                        .accessibilityLabel("阅读控制")
                        .accessibilityHint("打开返回、目录、字号、朗读和进度")
                        .accessibilityIdentifier("reader.controls")
                        .padding(.trailing, 8)
                    }
                }
                .background(Color(library.state.preferences.theme.background).ignoresSafeArea())
            } else if let loadError {
                ContentUnavailableView {
                    Label("无法打开书籍", systemImage: "exclamationmark.triangle")
                } description: {
                    Text(loadError)
                } actions: {
                    Button("返回书架") { dismiss() }.accessibilityIdentifier("reader.back")
                }
            } else {
                VStack(spacing: 16) {
                    ProgressView("正在打开…")
                    Button("返回书架") { dismiss() }.accessibilityIdentifier("reader.back")
                }
            }
        }
        .toolbar(.hidden, for: .navigationBar)
        .navigationBarBackButtonHidden(true)
        .statusBarHidden(true)
        .preferredColorScheme(library.state.preferences.theme == .dark ? .dark : .light)
        .sheet(isPresented: $showingTOC) { toc }
        .sheet(isPresented: $showingSettings) { ReaderSettings().environmentObject(library).environmentObject(speech) }
        .sheet(isPresented: $showingSpeech) {
            if let document, let storage = library.storage {
                NavigationStack {
                    ScrollView {
                        playback(document, storage: storage).padding(.vertical)
                    }
                    .navigationTitle("朗读")
                    .navigationBarTitleDisplayMode(.inline)
                    .toolbar {
                        ToolbarItem(placement: .topBarTrailing) {
                            Button("收起") { showingSpeech = false }
                                .accessibilityIdentifier("speech.dismiss")
                        }
                    }
                }
                .presentationDetents([.medium, .large])
                .presentationDragIndicator(.visible)
            }
        }
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
        .alert("正文读取失败", isPresented: Binding(get: { document != nil && loadError != nil }, set: { if !$0 { loadError = nil } })) {
            Button("好") { loadError = nil }
        } message: { Text(loadError ?? "") }
    }

    private func readingControls(_ document: BookDocument) -> some View {
        VStack(spacing: 12) {
            HStack {
                Button { dismiss() } label: {
                    Image(systemName: "chevron.left").frame(width: 44, height: 44)
                }.accessibilityLabel("返回书架").accessibilityIdentifier("reader.back")
                Text(library.record(bookID)?.title ?? "阅读").font(.headline).lineLimit(1)
                Spacer(minLength: 0)
                Button { showingControls = false } label: {
                    Image(systemName: "xmark").frame(width: 44, height: 44)
                }.accessibilityLabel("收起阅读控制").accessibilityIdentifier("reader.controls.dismiss")
            }
            HStack(spacing: 12) {
                Button {
                    showingControls = false; showingSpeech = true
                } label: {
                    Label("朗读", systemImage: speech.book?.id == bookID && speech.status == .playing ? "speaker.wave.2.fill" : "speaker.wave.2")
                        .frame(maxWidth: .infinity, minHeight: 44)
                }.accessibilityLabel("朗读控制").accessibilityIdentifier("reader.speech")
                Button {
                    tocQuery = ""
                    showingControls = false; showingTOC = true
                } label: {
                    Label("目录", systemImage: "list.bullet").frame(maxWidth: .infinity, minHeight: 44)
                }.accessibilityIdentifier("reader.toc")
                Button {
                    showingControls = false; showingSettings = true
                } label: {
                    Label("字号", systemImage: "textformat.size").frame(maxWidth: .infinity, minHeight: 44)
                }.accessibilityLabel("阅读设置").accessibilityIdentifier("reader.settings")
            }
            HStack {
                Text("\(Int(document.progress(block: current.block, fraction: current.fraction) * 100))%")
                    .monospacedDigit().accessibilityIdentifier("reader.progress")
                Slider(value: Binding(get: { document.progress(block: current.block, fraction: current.fraction) }, set: {
                    jump = ReaderJump(block: document.block(atProgress: $0))
                }), in: 0...1)
                .accessibilityLabel("阅读进度").accessibilityIdentifier("reader.seek")
                Text("\(current.block + 1)/\(document.blocks.count)")
                    .monospacedDigit().accessibilityIdentifier("reader.anchor")
            }.font(.caption)
        }
        .buttonStyle(.plain)
        .foregroundStyle(Color(library.state.preferences.theme.foreground))
    }

    private var toc: some View {
        let currentEntryID = document?.tocEntry(atBlock: current.block)?.id
        return NavigationStack {
            ScrollViewReader { proxy in
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
                                HStack {
                                    Text(entry.title)
                                        .fontWeight(entry.id == currentEntryID ? .semibold : .regular)
                                        .padding(.leading, CGFloat(entry.depth) * 14)
                                        .foregroundStyle(.primary)
                                    Spacer(minLength: 12)
                                    if entry.id == currentEntryID {
                                        Image(systemName: "checkmark").foregroundStyle(.tint)
                                            .accessibilityHidden(true)
                                    }
                                }
                            }
                            .id(entry.id)
                            .accessibilityIdentifier("toc.entry.\(entry.id)")
                            .accessibilityValue(entry.id == currentEntryID ? "当前阅读章节" : "")
                            .accessibilityAddTraits(entry.id == currentEntryID ? .isSelected : [])
                        }
                    }
                }
                .accessibilityIdentifier("toc.list")
                .task {
                    // Let the sheet's list register its rows before scrolling.
                    // Run once per presentation, so browsing the TOC stays free.
                    await Task.yield()
                    if let currentEntryID { proxy.scrollTo(currentEntryID, anchor: .center) }
                }
                .onChange(of: tocQuery) { _, query in
                    if query.isEmpty, let currentEntryID { proxy.scrollTo(currentEntryID, anchor: .center) }
                }
                .navigationTitle("目录")
                .searchable(text: $tocQuery, placement: .navigationBarDrawer(displayMode: .always), prompt: "查找章节")
                .toolbar { ToolbarItem(placement: .topBarTrailing) { Button("完成") { showingTOC = false } } }
            }
        }
    }

    private func playback(_ document: BookDocument, storage: BookStorage) -> some View {
        let active = speech.book?.id == bookID
        return VStack(spacing: 4) {
            if active && speech.preparing { ProgressView("正在准备本地语音…").font(.caption) }
            if active, let notice = speech.notice { Text(notice).font(.caption).foregroundStyle(.secondary) }
            HStack {
                Label(active ? speech.status.rawValue : "本机语音 · 不发送正文", systemImage: "waveform")
                    .font(.caption).foregroundStyle(.secondary)
                Spacer()
                if active {
                    Button("查看听书位置") {
                        jump = ReaderJump(block: speech.position.block)
                        showingSpeech = false
                    }.font(.caption)
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
                    Text("苏心在手机上合成中文；含英文或不支持字符的段落会提示并使用苹果系统语音。书籍正文不上传。").font(.footnote).foregroundStyle(.secondary)
                    if library.state.preferences.voiceIdentifier == SuxinSpeechProvider.voiceID {
                        LabeledContent("苏心语速", value: String(format: "%.2f×", library.state.preferences.suxinRate))
                        Slider(value: Binding(get: { Double(library.state.preferences.suxinRate) }, set: {
                            var value = library.state.preferences; value.suxinRate = Float($0); library.setPreferences(value); speech.preferencesChanged()
                        }), in: 0.5...2, step: 0.05).accessibilityLabel("苏心朗读语速")
                    } else {
                    LabeledContent("语速", value: String(format: "%.2f", library.state.preferences.speechRate))
                    Slider(value: Binding(get: { Double(library.state.preferences.speechRate) }, set: {
                        var value = library.state.preferences; value.speechRate = Float($0); library.setPreferences(value); speech.preferencesChanged()
                    }), in: 0.35...0.65, step: 0.025).accessibilityLabel("朗读语速")
                    }
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
