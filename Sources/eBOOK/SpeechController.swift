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
        self.provider = provider ?? AppleSpeechProvider()
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
        persist(); generation += 1; provider.cancel(); hasUtterance = false; status = .stopped
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
        generation += 1; provider.cancel(); hasUtterance = false
        position = document.clamped(target); persist()
        if shouldPlay {
            do { try speakNext() } catch { fail(error) }
        }
        updateNowPlaying()
    }

    func skipBlock(_ delta: Int) { seek(TextPosition(block: position.block + delta)) }
    func skipChapter(_ delta: Int) {
        guard let document, !document.chapters.isEmpty else { return }
        let current = document.chapters.lastIndex(where: { $0.firstBlock <= position.block }) ?? 0
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
            let candidates = TextChunker.chunks(text, startUTF16: position.utf16Offset)
            if let chunk = candidates.first(where: { !$0.text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }) {
                let token = generation, blockIndex = position.block
                let preferences = library?.state.preferences ?? ReaderPreferences()
                provider.onEvent = { [weak self] event in
                    guard let self, self.generation == token, self.position.block == blockIndex else { return }
                    switch event {
                    case .started: break
                    case .range(let start, _):
                        self.position.utf16Offset = min(block.utf16Count, chunk.startUTF16 + start)
                        if Date().timeIntervalSince(self.lastSave) >= 1 { self.persist() }
                    case .finished:
                        self.hasUtterance = false
                        self.position.utf16Offset = chunk.endUTF16
                        self.persist()
                        if self.status == .playing {
                            do { try self.speakNext() } catch { self.fail(error) }
                        }
                    case .cancelled: self.hasUtterance = false; self.status = .paused; self.persist()
                    case .failed(let message): self.fail(ReaderError.invalid(message))
                    }
                }
                hasUtterance = true
                let stableID = "\(book.fingerprint):\(blockIndex):\(chunk.startUTF16):\(preferences.voiceIdentifier ?? "zh-CN"):\(preferences.speechRate)"
                try provider.speak(SpeechRequest(stableID: stableID, chunk: chunk, voiceID: preferences.voiceIdentifier, rate: preferences.speechRate))
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

    private func fail(_ error: Error) {
        self.error = error.localizedDescription
        provider.cancel(); hasUtterance = false; status = .paused; persist(); updateNowPlaying()
        if managesAudio { try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation) }
    }

    private func updateNowPlaying() {
        guard managesAudio, let book else { return }
        var info: [String: Any] = [MPMediaItemPropertyTitle: book.title,
                                  MPMediaItemPropertyArtist: book.author ?? "本机中文朗读",
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
