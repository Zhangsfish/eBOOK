import Foundation
import Combine
import AVFoundation
import MediaPlayer

@MainActor final class SpeechController: ObservableObject {
    enum Status: String { case stopped = "已停止", playing = "正在朗读", paused = "已暂停" }
    @Published private(set) var status: Status = .stopped
    @Published private(set) var book: BookRecord?
    @Published private(set) var position = TextPosition()
    @Published private(set) var document: BookDocument?
    @Published var error: String?
    @Published private(set) var preparing = false
    @Published private(set) var notice: String?
    let provider: SpeechProvider
    private weak var library: LibraryModel?
    private var storage: BookStorage?
    private var hasUtterance = false
    private var generation = 0
    private var lastSave = Date.distantPast
    private var wasPlayingBeforeInterruption = false
    private let managesAudio: Bool
    private var observers: [NSObjectProtocol] = []
    private var commands: [(MPRemoteCommand, Any)] = []

    init(provider: SpeechProvider? = nil, managesAudio: Bool = true) {
        self.provider = provider ?? LocalSpeechProvider()
        self.managesAudio = managesAudio
        if managesAudio { configureSystemControls() }
    }

    func attach(_ library: LibraryModel) { self.library = library }

    func load(_ book: BookRecord, document: BookDocument, storage: BookStorage) {
        if self.book?.id == book.id { return }
        stop()
        self.book = book; self.document = document; self.storage = storage
        position = document.clamped(book.listening); status = .paused
        updateNowPlaying()
    }

    func play() {
        guard let document, book != nil else { return }
        do {
            if managesAudio {
                let session = AVAudioSession.sharedInstance()
                try session.setCategory(.playback, mode: .spokenAudio, options: [])
                try session.setActive(true)
            }
            status = .playing
            if hasUtterance { try provider.resume() }
            else {
                if position.block == document.blocks.count - 1, position.utf16Offset >= document.blocks.last!.utf16Count {
                    position = TextPosition()
                }
                try speakNext()
            }
            updateNowPlaying()
        } catch { fail(error) }
    }

    func pause(deactivate: Bool = true) {
        guard book != nil else { return }
        provider.pause(); status = .paused; persist(); updateNowPlaying()
        if managesAudio && deactivate { try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation) }
    }

    func stop() {
        persist(); generation += 1; provider.cancel(); hasUtterance = false; status = .stopped; preparing = false; notice = nil
        if managesAudio { try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation) }
        updateNowPlaying()
    }

    func clearBook() {
        stop(); book = nil; document = nil; storage = nil
        if managesAudio { MPNowPlayingInfoCenter.default().nowPlayingInfo = nil }
    }

    func seek(_ target: TextPosition) {
        guard let document else { return }
        let shouldPlay = status == .playing
        generation += 1; provider.cancel(); hasUtterance = false; preparing = false; notice = nil
        position = document.clamped(target); persist()
        if shouldPlay {
            do { try speakNext() } catch { fail(error) }
        }
        updateNowPlaying()
    }

    func skipParagraph(_ delta: Int) {
        guard let document, let storage, let book, document.blocks.indices.contains(position.block) else { return }
        do {
            let text = try storage.text(for: document.blocks[position.block], book: book.id)
            let expression = try NSRegularExpression(pattern: "\\n{2,}")
            let length = text.utf16.count
            let starts = [0] + expression.matches(in: text, range: NSRange(location: 0, length: length))
                .map { $0.range.location + $0.range.length }.filter { $0 < length }
            if delta > 0 {
                if let next = starts.first(where: { $0 > position.utf16Offset }) {
                    seek(TextPosition(block: position.block, utf16Offset: next))
                } else {
                    var next = position.block + 1
                    while next < document.blocks.count {
                        let candidate = try storage.text(for: document.blocks[next], book: book.id)
                        if !candidate.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                            seek(TextPosition(block: next)); return
                        }
                        next += 1
                    }
                    seek(TextPosition(block: position.block, utf16Offset: length))
                }
            } else {
                let currentStart = starts.last(where: { $0 <= position.utf16Offset }) ?? 0
                if position.utf16Offset > currentStart { seek(TextPosition(block: position.block, utf16Offset: currentStart)) }
                else if let previous = starts.last(where: { $0 < currentStart }) {
                    seek(TextPosition(block: position.block, utf16Offset: previous))
                } else if position.block > 0 {
                    var previous = position.block - 1
                    while previous >= 0 {
                        let previousText = try storage.text(for: document.blocks[previous], book: book.id)
                        if !previousText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                            let previousLength = previousText.utf16.count
                            let starts = expression.matches(in: previousText, range: NSRange(location: 0, length: previousLength))
                                .map { $0.range.location + $0.range.length }.filter { $0 < previousLength }
                            seek(TextPosition(block: previous, utf16Offset: starts.last ?? 0)); return
                        }
                        previous -= 1
                    }
                }
            }
        } catch { fail(error) }
    }
    func skipChapter(_ delta: Int) {
        guard let document, !document.chapters.isEmpty else { return }
        let current = document.chapters.lastIndex(where: { $0.firstBlock <= position.block }) ?? 0
        if delta > 0 && current == document.chapters.count - 1 { return }
        let target = min(document.chapters.count - 1, max(0, current + delta))
        seek(TextPosition(block: document.chapters[target].firstBlock))
    }

    func preferencesChanged() {
        if book != nil { seek(position) }
    }

    func interruptionBegan() {
        wasPlayingBeforeInterruption = status == .playing
        if wasPlayingBeforeInterruption { pause(deactivate: false) }
    }
    func interruptionEnded(shouldResume: Bool) {
        if wasPlayingBeforeInterruption && shouldResume { play() }
        wasPlayingBeforeInterruption = false
    }
    func headphonesDisconnected() { if status == .playing { pause() } }
    func persist() {
        if let book { library?.updateListening(book.id, position: position) }
        lastSave = Date()
    }

    private func speakNext() throws {
        guard let document, let storage, let book else { return }
        while position.block < document.blocks.count {
            let block = document.blocks[position.block]
            let text = try storage.text(for: block, book: book.id)
            let preferences = library?.state.preferences ?? ReaderPreferences()
            let candidates = speechChunks(text, preferences: preferences, start: position.utf16Offset)
            if let chunk = candidates.first(where: { !$0.text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }) {
                generation += 1
                let token = generation, blockIndex = position.block
                provider.onEvent = { [weak self] event in
                    guard let self, self.generation == token, self.position.block == blockIndex else { return }
                    switch event {
                    case .preparing(let value): self.preparing = value
                    case .notice(let value): self.notice = value
                    case .started: break
                    case .range(let start, _):
                        self.position.utf16Offset = min(block.utf16Count, chunk.startUTF16 + start)
                        if Date().timeIntervalSince(self.lastSave) >= 1 { self.persist() }
                    case .finished:
                        self.hasUtterance = false; self.preparing = false
                        self.position.utf16Offset = chunk.endUTF16
                        self.persist()
                        if self.status == .playing {
                            do { try self.speakNext() } catch { self.fail(error) }
                        }
                    case .cancelled: self.hasUtterance = false; self.status = .paused; self.persist(); self.updateNowPlaying()
                    case .failed(let message): self.fail(ReaderError.invalid(message))
                    }
                }
                hasUtterance = true
                try provider.speak(request(chunk, block: blockIndex, book: book, preferences: preferences, context: text))
                // Read at most the next non-empty bounded block/chunk. Only a
                // single lookahead hint is retained by the local provider.
                if let next = candidates.dropFirst().first {
                    provider.prefetch(request(next, block: blockIndex, book: book, preferences: preferences, context: text))
                } else if blockIndex + 1 < document.blocks.count {
                    let index = blockIndex + 1
                    let nextText = try storage.text(for: document.blocks[index], book: book.id)
                    if let next = speechChunks(nextText, preferences: preferences, start: 0).first {
                        provider.prefetch(request(next, block: index, book: book, preferences: preferences, context: nextText))
                    }
                }
                updateNowPlaying(); return
            }
            if position.block + 1 < document.blocks.count { position = TextPosition(block: position.block + 1) }
            else {
                position = TextPosition(block: position.block, utf16Offset: block.utf16Count)
                status = .stopped; hasUtterance = false; persist()
                if managesAudio { try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation) }
                updateNowPlaying(); return
            }
        }
    }

    private func request(_ chunk: SpeechChunk, block: Int, book: BookRecord, preferences: ReaderPreferences, context: String) -> SpeechRequest {
        let rate = preferences.voiceIdentifier == SuxinSpeechProvider.voiceID ? preferences.suxinRate : preferences.speechRate
        let stableID = "\(book.fingerprint):\(block):\(chunk.startUTF16):\(preferences.voiceIdentifier ?? "zh-CN"):\(rate)"
        return SpeechRequest(stableID: stableID, chunk: chunk, voiceID: preferences.voiceIdentifier, rate: rate, contextText: context)
    }
    private func speechChunks(_ text: String, preferences: ReaderPreferences, start: Int) -> [SpeechChunk] {
        let model = preferences.voiceIdentifier == SuxinSpeechProvider.voiceID
        return model ? SuxinSegmentation.windows(text, startUTF16: start)
            : TextChunker.chunks(text, maximumUTF16: 280, startUTF16: start)
    }

    private func fail(_ error: Error) {
        self.error = error.localizedDescription
        provider.cancel(); hasUtterance = false; status = .paused; preparing = false; persist(); updateNowPlaying()
        if managesAudio { try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation) }
    }

    private func updateNowPlaying() {
        guard managesAudio, let book else { return }
        var info: [String: Any] = [MPMediaItemPropertyTitle: book.title,
                                  MPMediaItemPropertyArtist: book.author ?? "朗读",
                                  MPNowPlayingInfoPropertyPlaybackRate: status == .playing ? 1.0 : 0.0]
        if let document, position.block < document.blocks.count {
            let chapter = document.blocks[position.block].chapter
            if chapter < document.chapters.count { info[MPMediaItemPropertyAlbumTitle] = document.chapters[chapter].title }
        }
        MPNowPlayingInfoCenter.default().nowPlayingInfo = info
    }

    private func configureSystemControls() {
        let center = MPRemoteCommandCenter.shared()
        func bind(_ command: MPRemoteCommand, _ action: @escaping @MainActor () -> Void) {
            let token = command.addTarget { _ in Task { @MainActor in action() }; return .success }
            commands.append((command, token))
        }
        bind(center.playCommand) { [weak self] in self?.play() }
        bind(center.pauseCommand) { [weak self] in self?.pause() }
        bind(center.togglePlayPauseCommand) { [weak self] in
            if self?.status == .playing { self?.pause() } else { self?.play() }
        }
        bind(center.nextTrackCommand) { [weak self] in self?.skipChapter(1) }
        bind(center.previousTrackCommand) { [weak self] in self?.skipChapter(-1) }
        center.changePlaybackPositionCommand.isEnabled = false // Speech has no truthful audio duration.
        observers.append(NotificationCenter.default.addObserver(forName: AVAudioSession.interruptionNotification, object: nil, queue: .main) { [weak self] notification in
            guard let raw = notification.userInfo?[AVAudioSessionInterruptionTypeKey] as? UInt,
                  let type = AVAudioSession.InterruptionType(rawValue: raw) else { return }
            Task { @MainActor in
                if type == .began { self?.interruptionBegan() }
                else {
                    let options = AVAudioSession.InterruptionOptions(rawValue: notification.userInfo?[AVAudioSessionInterruptionOptionKey] as? UInt ?? 0)
                    self?.interruptionEnded(shouldResume: options.contains(.shouldResume))
                }
            }
        })
        observers.append(NotificationCenter.default.addObserver(forName: AVAudioSession.routeChangeNotification, object: nil, queue: .main) { [weak self] notification in
            if notification.userInfo?[AVAudioSessionRouteChangeReasonKey] as? UInt == AVAudioSession.RouteChangeReason.oldDeviceUnavailable.rawValue {
                Task { @MainActor in self?.headphonesDisconnected() }
            }
        })
    }
}
