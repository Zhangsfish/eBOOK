import SwiftUI
import UIKit
import ImageIO

/// Small native line map shared with vertical anchors. No whole-book layout.
@MainActor struct ReaderLineMap {
    private var lines: [(offset: Int, y: CGFloat)] = []
    init(text: NSAttributedString, width: CGFloat) {
        var result: [(offset: Int, y: CGFloat)] = []
        let storage = NSTextStorage(attributedString: text), manager = NSLayoutManager()
        let container = NSTextContainer(size: CGSize(width: max(1, width), height: 1_000_000))
        container.lineFragmentPadding = 0
        storage.addLayoutManager(manager); manager.addTextContainer(container)
        manager.ensureLayout(for: container)
        manager.enumerateLineFragments(forGlyphRange: manager.glyphRange(for: container)) { rect, _, _, glyphs, _ in
            let chars = manager.characterRange(forGlyphRange: glyphs, actualGlyphRange: nil)
            result.append((chars.location, rect.minY))
        }
        lines = result
    }
    func offset(atY y: CGFloat) -> Int { lines.last(where: { $0.y <= y + 0.5 })?.offset ?? 0 }
    func y(for offset: Int) -> CGFloat { lines.last(where: { $0.offset <= offset })?.y ?? 0 }
}

struct ReaderPageSlice {
    let start: TextPosition
    let end: TextPosition
    let text: NSAttributedString
    let image: UIImage?
    let imageDescription: String?
}

/// Demand-driven, viewport-sized layout. At most four source blocks are offered
/// to TextKit; only eight small source strings and64 predecessor positions persist.
@MainActor final class ReaderPaginator {
    let document: BookDocument
    private let storage: BookStorage, bookID: UUID, preferences: ReaderPreferences
    let size: CGSize
    private var texts: [Int: String] = [:], order: [Int] = []
    private var predecessors: [TextPosition: TextPosition] = [:], history: [TextPosition] = []
    private let pictures = NSCache<NSString, UIImage>()
    private(set) var maximumSourceBlocksObserved = 0
    var cachedTextBlocks: Int { texts.count }
    var cachedPredecessors: Int { predecessors.count }

    init(document: BookDocument, storage: BookStorage, bookID: UUID, preferences: ReaderPreferences, size: CGSize) {
        self.document = document; self.storage = storage; self.bookID = bookID
        self.preferences = preferences; self.size = size
        pictures.countLimit = 2; pictures.totalCostLimit = 16 * 1024 * 1024
    }
    private func text(_ block: Int) throws -> String {
        if let value = texts[block] { return value }
        let value = try storage.text(for: document.blocks[block], book: bookID)
        texts[block] = value; order.append(block)
        if order.count > 8 { texts.removeValue(forKey: order.removeFirst()) }
        return value
    }
    private func before(_ a: TextPosition, _ b: TextPosition) -> Bool {
        a.block == b.block ? a.utf16Offset < b.utf16Offset : a.block < b.block
    }
    private func normalized(_ point: TextPosition) throws -> TextPosition? {
        var point = point
        point.block = max(0, point.block)
        while point.block < document.blocks.count {
            let block = document.blocks[point.block]
            if block.imagePath != nil, point.utf16Offset == 0 { return point }
            let length = block.utf16Count
            point.utf16Offset = min(length, max(0, point.utf16Offset))
            if point.utf16Offset < length {
                let value = try text(point.block) as NSString
                point.utf16Offset = value.rangeOfComposedCharacterSequence(at: point.utf16Offset).location
                return point
            }
            point = TextPosition(block: point.block + 1)
        }
        return nil
    }
    private func remember(_ page: ReaderPageSlice) {
        if predecessors[page.end] == nil { history.append(page.end) }
        predecessors[page.end] = page.start
        if history.count > 64 { predecessors.removeValue(forKey: history.removeFirst()) }
    }
    private func picture(_ block: BookBlock) throws -> UIImage {
        let name = block.imagePath! as NSString
        if let image = pictures.object(forKey: name) { return image }
        let url = storage.directory(for: bookID).appendingPathComponent(block.imagePath!)
        guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
              let p = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [CFString: Any],
              let width = (p[kCGImagePropertyPixelWidth] as? NSNumber)?.int64Value,
              let height = (p[kCGImagePropertyPixelHeight] as? NSNumber)?.int64Value,
              width > 0, height > 0, width <= 16_384, height <= 16_384, width * height <= 40_000_000,
              let thumbnail = CGImageSourceCreateThumbnailAtIndex(source, 0, [
                kCGImageSourceCreateThumbnailFromImageAlways: true,
                kCGImageSourceThumbnailMaxPixelSize: 1600,
                kCGImageSourceCreateThumbnailWithTransform: true] as CFDictionary) else {
            throw ReaderError.invalid("插图无法显示，尺寸过大或文件损坏。")
        }
        let image = UIImage(cgImage: thumbnail)
        pictures.setObject(image, forKey: name, cost: thumbnail.width * thumbnail.height * 4)
        return image
    }
    func page(at requested: TextPosition, stoppingAt stop: TextPosition? = nil) throws -> ReaderPageSlice? {
        guard let start = try normalized(requested), stop.map({ before(start, $0) }) ?? true else { return nil }
        let block = document.blocks[start.block]
        if block.imagePath != nil {
            let page = ReaderPageSlice(start: start, end: TextPosition(block: start.block + 1), text: NSAttributedString(string: ""),
                                       image: try picture(block), imageDescription: block.imageDescription)
            remember(page); return page
        }
        var source = "", spans: [(block: Int, start: Int, length: Int)] = []
        var blockIndex = start.block
        while blockIndex < min(document.blocks.count, start.block + 4) {
            let current = document.blocks[blockIndex]
            if current.imagePath != nil || current.chapter != block.chapter { break }
            if let stop, blockIndex > stop.block || (blockIndex == stop.block && stop.utf16Offset == 0) { break }
            let value = try text(blockIndex) as NSString
            let lower = blockIndex == start.block ? start.utf16Offset : 0
            let upper = (stop?.block == blockIndex) ? min(value.length, stop!.utf16Offset) : value.length
            guard upper >= lower else { break }
            source += value.substring(with: NSRange(location: lower, length: upper - lower))
            spans.append((blockIndex, lower, upper - lower)); blockIndex += 1
            if let stop, blockIndex - 1 == stop.block { break }
        }
        maximumSourceBlocksObserved = max(maximumSourceBlocksObserved, spans.count)
        let paragraph = NSMutableParagraphStyle(); paragraph.lineSpacing = preferences.lineSpacing; paragraph.paragraphSpacing = 5
        let font = UIFontMetrics(forTextStyle: .body).scaledFont(for: .systemFont(ofSize: preferences.fontSize))
        let attributed = NSAttributedString(string: source, attributes: [.font: font,
            .foregroundColor: preferences.theme.foreground, .paragraphStyle: paragraph])
        let textStorage = NSTextStorage(attributedString: attributed), manager = NSLayoutManager()
        let container = NSTextContainer(size: CGSize(width: max(1, size.width - 48), height: max(1, size.height - 16)))
        container.lineFragmentPadding = 0
        textStorage.addLayoutManager(manager); manager.addTextContainer(container); manager.ensureLayout(for: container)
        var visible = 0
        manager.enumerateLineFragments(forGlyphRange: manager.glyphRange(for: container)) { rect, _, _, glyphs, _ in
            if rect.maxY <= container.size.height + 0.5 {
                let chars = manager.characterRange(forGlyphRange: glyphs, actualGlyphRange: nil)
                visible = max(visible, chars.location + chars.length)
            }
        }
        if visible == 0, !source.isEmpty { visible = (source as NSString).rangeOfComposedCharacterSequence(at: 0).length }
        visible = min(visible, attributed.length)
        var remaining = visible, end = start
        for span in spans {
            if remaining < span.length { end = TextPosition(block: span.block, utf16Offset: span.start + remaining); break }
            remaining -= span.length; end = TextPosition(block: span.block + 1)
            if let stop, !before(end, stop) { end = stop; break }
        }
        guard before(start, end) else { throw ReaderError.invalid("当前页面无法排版，请调整字号或阅读方式。") }
        let page = ReaderPageSlice(start: start, end: end, text: attributed.attributedSubstring(from: NSRange(location: 0, length: visible)),
                                   image: nil, imageDescription: nil)
        remember(page); return page
    }
    func previous(before end: TextPosition) throws -> ReaderPageSlice? {
        guard end.block > 0 || end.utf16Offset > 0 else { return nil }
        if let known = predecessors[end] { return try page(at: known, stoppingAt: end) }
        var cursor = end, budget = 1600, blocks = 0
        if cursor.block >= document.blocks.count { cursor = TextPosition(block: document.blocks.count - 1, utf16Offset: document.blocks.last?.utf16Count ?? 0) }
        while budget > 0, blocks < 4 {
            let amount = min(budget, cursor.utf16Offset)
            cursor.utf16Offset -= amount; budget -= amount; blocks += 1
            if budget == 0 || cursor.block == 0 { break }
            cursor = TextPosition(block: cursor.block - 1, utf16Offset: document.blocks[cursor.block - 1].utf16Count)
        }
        var result: ReaderPageSlice?
        for _ in 0..<1605 {
            guard before(cursor, end), let page = try page(at: cursor, stoppingAt: end) else { break }
            result = page; cursor = page.end
        }
        return result
    }
}

private final class ReaderPageContent: UIViewController, UIGestureRecognizerDelegate {
    let page: ReaderPageSlice
    let theme: ReaderTheme
    var onTurn: ((Bool) -> Bool)?
    private weak var pageText: UITextView?
    init(_ page: ReaderPageSlice, theme: ReaderTheme) { self.page = page; self.theme = theme; super.init(nibName: nil, bundle: nil) }
    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
    override func loadView() {
        let root = UIView(); root.backgroundColor = theme.background; view = root
        let content: UIView
        if let image = page.image {
            let picture = UIImageView(image: image); picture.contentMode = .scaleAspectFit
            picture.isAccessibilityElement = true; picture.accessibilityLabel = page.imageDescription ?? "书中插图"
            content = picture
        } else {
            let storage = NSTextStorage(attributedString: page.text), manager = NSLayoutManager(), container = NSTextContainer()
            container.lineFragmentPadding = 0; storage.addLayoutManager(manager); manager.addTextContainer(container)
            let text = UITextView(frame: .zero, textContainer: container)
            text.isEditable = false; text.isScrollEnabled = false; text.textContainerInset = .zero
            text.contentInsetAdjustmentBehavior = .never; text.backgroundColor = theme.background
            #if DEBUG
            if ProcessInfo.processInfo.arguments.contains("--uitesting") {
                text.accessibilityLabel = page.text.string
                text.accessibilityValue = "block=\(page.start.block);offset=\(page.start.utf16Offset);visibleUTF16=\(page.text.length)"
            }
            #endif
            text.accessibilityIdentifier = "reader.page.text"; content = text
            pageText = text
        }
        content.translatesAutoresizingMaskIntoConstraints = false; root.addSubview(content)
        content.accessibilityCustomActions = [
            UIAccessibilityCustomAction(name: "下一页") { [weak self] _ in self?.onTurn?(true) ?? false },
            UIAccessibilityCustomAction(name: "上一页") { [weak self] _ in self?.onTurn?(false) ?? false }]
        NSLayoutConstraint.activate([content.leadingAnchor.constraint(equalTo: root.leadingAnchor, constant: 24),
            content.trailingAnchor.constraint(equalTo: root.trailingAnchor, constant: -24),
            content.topAnchor.constraint(equalTo: root.topAnchor, constant: 8), content.bottomAnchor.constraint(equalTo: root.bottomAnchor, constant: -8)])
        // Side taps share the paginator's existing next/previous path. Keep the
        // middle free, and let double-tap/long-press text selection take priority.
        let doubleTap = UITapGestureRecognizer(target: nil, action: nil)
        doubleTap.numberOfTapsRequired = 2
        let tap = UITapGestureRecognizer(target: self, action: #selector(turnPage(_:)))
        for gesture in [tap, doubleTap] {
            gesture.delegate = self; gesture.cancelsTouchesInView = false
            root.addGestureRecognizer(gesture)
        }
        tap.require(toFail: doubleTap)
    }
    func gestureRecognizer(_ gestureRecognizer: UIGestureRecognizer, shouldReceive touch: UITouch) -> Bool {
        guard !UIAccessibility.isVoiceOverRunning, (pageText?.selectedRange.length ?? 0) == 0 else { return false }
        let x = touch.location(in: view).x, width = view.bounds.width
        return x < width / 3 || x > width * 2 / 3
    }
    func gestureRecognizer(_ gestureRecognizer: UIGestureRecognizer,
                           shouldRecognizeSimultaneouslyWith otherGestureRecognizer: UIGestureRecognizer) -> Bool {
        otherGestureRecognizer is UITapGestureRecognizer || otherGestureRecognizer is UILongPressGestureRecognizer
    }
    @objc private func turnPage(_ gesture: UITapGestureRecognizer) {
        guard gesture.state == .ended, (pageText?.selectedRange.length ?? 0) == 0 else { return }
        let x = gesture.location(in: view).x, width = view.bounds.width
        if x < width / 3 { _ = onTurn?(false) }
        else if x > width * 2 / 3 { _ = onTurn?(true) }
    }
}

private final class ReaderPageController: UIPageViewController {
    var onSizeChange: (() -> Void)?
    private var lastSize: CGSize = .zero
    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        if abs(view.bounds.width - lastSize.width) > 0.5 || abs(view.bounds.height - lastSize.height) > 0.5 {
            lastSize = view.bounds.size; onSizeChange?()
        }
    }
}

struct ReaderPages: UIViewControllerRepresentable {
    let document: BookDocument, storage: BookStorage, bookID: UUID, preferences: ReaderPreferences, jump: ReaderJump
    let onPosition: (ReadingAnchor) -> Void
    let onError: (String) -> Void
    @Environment(\.dynamicTypeSize) private var typeSize
    func makeCoordinator() -> Coordinator { Coordinator(self) }
    func makeUIViewController(context: Context) -> UIPageViewController {
        let pager = ReaderPageController(transitionStyle: .scroll, navigationOrientation: .horizontal)
        pager.dataSource = context.coordinator; pager.delegate = context.coordinator
        pager.view.accessibilityIdentifier = "reader.pages"
        context.coordinator.pager = pager
        pager.onSizeChange = { [weak coordinator = context.coordinator] in coordinator?.scheduleLayout() }
        pager.view.accessibilityCustomActions = [
            UIAccessibilityCustomAction(name: "下一页") { [weak coordinator = context.coordinator] _ in coordinator?.turn(forward: true) ?? false },
            UIAccessibilityCustomAction(name: "上一页") { [weak coordinator = context.coordinator] _ in coordinator?.turn(forward: false) ?? false }]
        return pager
    }
    func updateUIViewController(_ pager: UIPageViewController, context: Context) {
        guard !document.blocks.isEmpty else { return }
        let c = context.coordinator
        let changed = c.parent.preferences != preferences || c.typeSize != typeSize
        c.parent = self; c.typeSize = typeSize
        if c.lastJump != jump.revision {
            c.lastJump = jump.revision
            let block = min(max(0, jump.block), document.blocks.count - 1)
            c.position = TextPosition(block: block, utf16Offset: jump.utf16Offset ?? Int(Double(document.blocks[block].utf16Count) * jump.fraction))
            c.scheduleLayout()
        } else if changed { c.scheduleLayout() }
    }
    @MainActor final class Coordinator: NSObject, UIPageViewControllerDataSource, UIPageViewControllerDelegate {
        var parent: ReaderPages
        weak var pager: UIPageViewController?
        var engine: ReaderPaginator?, position = TextPosition(), lastJump: UUID?, typeSize: DynamicTypeSize?
        private var layoutToken = UUID()
        private var isTransitioning = false
        init(_ parent: ReaderPages) { self.parent = parent }
        func scheduleLayout() {
            let token = UUID(); layoutToken = token
            DispatchQueue.main.async { [weak self] in
                guard let self, self.layoutToken == token, let pager = self.pager,
                      pager.view.bounds.width > 64, pager.view.bounds.height > 56 else { return }
                do {
                    self.engine = ReaderPaginator(document: self.parent.document, storage: self.parent.storage,
                        bookID: self.parent.bookID, preferences: self.parent.preferences, size: pager.view.bounds.size)
                    if let page = try self.engine?.page(at: self.position) {
                        if let content = self.content(page) { pager.setViewControllers([content], direction: .forward, animated: false) }
                        self.report(page)
                    }
                } catch { self.parent.onError(error.localizedDescription) }
            }
        }
        private func content(_ page: ReaderPageSlice?) -> UIViewController? {
            guard let page else { return nil }
            let view = ReaderPageContent(page, theme: parent.preferences.theme)
            view.onTurn = { [weak self] in self?.turn(forward: $0) ?? false }
            return view
        }
        func pageViewController(_ pageViewController: UIPageViewController, viewControllerBefore viewController: UIViewController) -> UIViewController? {
            guard let page = (viewController as? ReaderPageContent)?.page else { return nil }
            do { return content(try engine?.previous(before: page.start)) } catch { parent.onError(error.localizedDescription); return nil }
        }
        func pageViewController(_ pageViewController: UIPageViewController, viewControllerAfter viewController: UIViewController) -> UIViewController? {
            guard let page = (viewController as? ReaderPageContent)?.page else { return nil }
            do { return content(try engine?.page(at: page.end)) } catch { parent.onError(error.localizedDescription); return nil }
        }
        func pageViewController(_ pageViewController: UIPageViewController, willTransitionTo pendingViewControllers: [UIViewController]) {
            isTransitioning = true
        }
        func pageViewController(_ pageViewController: UIPageViewController, didFinishAnimating finished: Bool,
                                previousViewControllers: [UIViewController], transitionCompleted completed: Bool) {
            isTransitioning = false
            if completed, let page = (pageViewController.viewControllers?.first as? ReaderPageContent)?.page { report(page) }
        }
        func turn(forward: Bool) -> Bool {
            guard !isTransitioning, let pager, let current = pager.viewControllers?.first else { return false }
            let next = forward ? pageViewController(pager, viewControllerAfter: current) : pageViewController(pager, viewControllerBefore: current)
            guard let next, let page = (next as? ReaderPageContent)?.page else { return false }
            pager.setViewControllers([next], direction: forward ? .forward : .reverse, animated: false); report(page); return true
        }
        private func report(_ page: ReaderPageSlice) {
            position = page.start
            #if DEBUG
            if ProcessInfo.processInfo.arguments.contains("--uitesting") {
                pager?.view.accessibilityValue = "block=\(position.block);offset=\(position.utf16Offset);visibleUTF16=\(page.text.length);sourceBlocks=\(engine?.maximumSourceBlocksObserved ?? 0)"
            }
            #endif
            let count = parent.document.blocks[position.block].utf16Count
            parent.onPosition(ReadingAnchor(block: position.block, fraction: Double(position.utf16Offset) / Double(max(1, count)), utf16Offset: position.utf16Offset))
        }
    }
}
