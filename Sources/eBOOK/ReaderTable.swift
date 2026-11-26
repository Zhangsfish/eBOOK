import SwiftUI
import UIKit
import ImageIO
#if DEBUG
import Darwin
#endif

struct ReaderJump: Equatable {
    var block: Int
    var fraction: Double = 0
    var utf16Offset: Int? = nil
    var revision = UUID()
}

extension ReaderTheme {
    var background: UIColor {
        switch self {
        case .light: return UIColor(red: 0.99, green: 0.99, blue: 0.97, alpha: 1)
        case .warm: return UIColor(red: 0.96, green: 0.92, blue: 0.82, alpha: 1)
        case .dark: return UIColor(red: 0.09, green: 0.11, blue: 0.13, alpha: 1)
        }
    }
    var foreground: UIColor {
        self == .dark ? UIColor(red: 0.83, green: 0.84, blue: 0.82, alpha: 1)
            : UIColor(red: 0.19, green: 0.21, blue: 0.20, alpha: 1)
    }
}

private final class BookCell: UITableViewCell {
    let label = UILabel()
    let picture = UIImageView()
    private let stack = UIStackView()
    override init(style: UITableViewCell.CellStyle, reuseIdentifier: String?) {
        super.init(style: style, reuseIdentifier: reuseIdentifier)
        selectionStyle = .none
        label.numberOfLines = 0
        label.adjustsFontForContentSizeCategory = true
        label.accessibilityTraits = .staticText
        picture.contentMode = .scaleAspectFit
        picture.isAccessibilityElement = true
        stack.axis = .vertical; stack.spacing = 12
        stack.addArrangedSubview(label); stack.addArrangedSubview(picture)
        stack.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(stack)
        let pictureHeight = picture.heightAnchor.constraint(equalToConstant: 260)
        pictureHeight.priority = .defaultHigh // UIStackView may collapse a hidden image to zero.
        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 24),
            stack.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -24),
            stack.topAnchor.constraint(equalTo: contentView.topAnchor, constant: 8),
            stack.bottomAnchor.constraint(equalTo: contentView.bottomAnchor, constant: -8),
            pictureHeight
        ])
    }
    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
    override func prepareForReuse() { super.prepareForReuse(); picture.image = nil; label.attributedText = nil }
}

private final class BookTableView: UITableView {
    var widthDidChange: (() -> Void)?
    private var previousWidth: CGFloat = 0
    override func layoutSubviews() {
        let changed = abs(bounds.width - previousWidth) > 0.5
        previousWidth = bounds.width
        super.layoutSubviews()
        if changed { widthDidChange?() }
    }
}

/// UITableView reuses visible cells. Each text read is <=1600 UTF-16 units;
/// neither a whole chapter nor the whole book becomes one SwiftUI Text.
struct ReaderTable: UIViewRepresentable {
    let document: BookDocument
    let storage: BookStorage
    let bookID: UUID
    let preferences: ReaderPreferences
    let jump: ReaderJump
    let onPosition: (ReadingAnchor) -> Void
    let onError: (String) -> Void
    @Environment(\.dynamicTypeSize) private var dynamicType

    func makeCoordinator() -> Coordinator { Coordinator(self) }
    func makeUIView(context: Context) -> UITableView {
        let table = BookTableView(frame: .zero, style: .plain)
        table.register(BookCell.self, forCellReuseIdentifier: "block")
        table.dataSource = context.coordinator; table.delegate = context.coordinator
        table.separatorStyle = .none; table.rowHeight = UITableView.automaticDimension
        table.showsVerticalScrollIndicator = false // The footer reports whole-book progress.
        table.estimatedRowHeight = 0 // All <=12 row heights are measured exactly.
        table.contentInset = UIEdgeInsets(top: 0, left: 0, bottom: 40, right: 0)
        table.accessibilityIdentifier = "reader.table"
        table.backgroundColor = preferences.theme.background
        context.coordinator.table = table
        context.coordinator.typeSize = dynamicType
        table.widthDidChange = { [weak coordinator = context.coordinator] in coordinator?.widthChanged() }
        return table
    }
    func updateUIView(_ table: UITableView, context: Context) {
        let coordinator = context.coordinator
        let changed = coordinator.parent.preferences != preferences || coordinator.typeSize != dynamicType
        coordinator.parent = self
        table.backgroundColor = preferences.theme.background
        var restore: ReadingAnchor?
        if changed {
            let current = coordinator.anchor()
            coordinator.typeSize = dynamicType
            coordinator.reloadRows()
            restore = current
        }
        if coordinator.lastJump != jump.revision {
            coordinator.lastJump = jump.revision
            restore = ReadingAnchor(block: jump.block, fraction: jump.fraction, utf16Offset: jump.utf16Offset)
        }
        if let restore {
            coordinator.requestRestore(restore)
        }
    }
    static func dismantleUIView(_ uiView: UITableView, coordinator: Coordinator) { coordinator.report(force: true) }

    @MainActor final class Coordinator: NSObject, UITableViewDataSource, UITableViewDelegate {
        var parent: ReaderTable
        weak var table: UITableView?
        var lastJump: UUID?
        var restoreToken = UUID()
        var typeSize: DynamicTypeSize?
        private var window: ReadingWindow
        private var windowShiftPending = false
        private var lastReport = Date.distantPast
        private var restoring = false
        private var hasRestored = false
        private var pendingAnchor: ReadingAnchor?
        private var lastKnownAnchor: ReadingAnchor?
        private var heightCache: [Int: CGFloat] = [:]
        private var heightWidth: CGFloat = 0
        private var lineMaps: [Int: ReaderLineMap] = [:]
        init(_ parent: ReaderTable) {
            self.parent = parent
            window = ReadingWindow(total: parent.document.blocks.count)
        }
        func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int { window.count }
        private func attributedText(for block: BookBlock) throws -> NSAttributedString {
            let text = try parent.storage.text(for: block, book: parent.bookID)
            let style = NSMutableParagraphStyle()
            style.lineSpacing = parent.preferences.lineSpacing
            style.paragraphSpacing = 5
            let font = UIFontMetrics(forTextStyle: .body).scaledFont(for: UIFont.systemFont(ofSize: parent.preferences.fontSize))
            return NSAttributedString(string: text, attributes: [
                .font: font, .foregroundColor: parent.preferences.theme.foreground, .paragraphStyle: style
            ])
        }
        func tableView(_ tableView: UITableView, heightForRowAt indexPath: IndexPath) -> CGFloat {
            guard tableView.bounds.width > 48 else { return 520 }
            if abs(heightWidth - tableView.bounds.width) > 0.5 { heightCache.removeAll(); heightWidth = tableView.bounds.width }
            let block = parent.document.blocks[window.lowerBound + indexPath.row]
            if let height = heightCache[block.id] { return height }
            let height: CGFloat
            if block.imagePath != nil { height = 276 }
            else {
                let probe = UILabel(); probe.numberOfLines = 0
                probe.attributedText = try? attributedText(for: block)
                height = max(44, ceil(probe.sizeThatFits(CGSize(width: tableView.bounds.width - 48, height: .greatestFiniteMagnitude)).height) + 16)
            }
            heightCache[block.id] = height
            return height
        }
        func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
            let cell = tableView.dequeueReusableCell(withIdentifier: "block", for: indexPath) as! BookCell
            let block = parent.document.blocks[window.lowerBound + indexPath.row]
            cell.backgroundColor = parent.preferences.theme.background
            cell.label.textColor = parent.preferences.theme.foreground
            cell.label.accessibilityIdentifier = "reader.block.\(block.id)"
            cell.picture.isHidden = block.imagePath == nil
            cell.label.isHidden = block.imagePath != nil
            do {
                if let image = block.imagePath {
                    let url = parent.storage.directory(for: parent.bookID).appendingPathComponent(image)
                    guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
                          let properties = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [CFString: Any],
                          let width = (properties[kCGImagePropertyPixelWidth] as? NSNumber)?.int64Value,
                          let height = (properties[kCGImagePropertyPixelHeight] as? NSNumber)?.int64Value,
                          width > 0, height > 0, width <= 16_384, height <= 16_384, width * height <= 40_000_000 else {
                        throw ReaderError.invalid("书中插图损坏或超过 40 MP / 16384 像素上限。")
                    }
                    guard let thumbnail = CGImageSourceCreateThumbnailAtIndex(source, 0, [
                            kCGImageSourceCreateThumbnailFromImageAlways: true,
                            kCGImageSourceThumbnailMaxPixelSize: 1600,
                            kCGImageSourceCreateThumbnailWithTransform: true
                          ] as CFDictionary) else { throw ReaderError.invalid("书中插图损坏或不受支持。") }
                    cell.picture.image = UIImage(cgImage: thumbnail)
                    cell.picture.accessibilityLabel = block.imageDescription ?? "书中插图"
                } else {
                    cell.label.attributedText = try attributedText(for: block)
                }
            } catch {
                cell.label.isHidden = false; cell.picture.isHidden = true
                cell.label.text = "此段内容无法读取。"
                DispatchQueue.main.async { self.parent.onError(error.localizedDescription) }
            }
            return cell
        }
        func anchor() -> ReadingAnchor {
            guard let table, let first = table.indexPathsForVisibleRows?.first else { return ReadingAnchor() }
            let top = table.contentOffset.y + table.adjustedContentInset.top
            let visible = table.indexPathForRow(at: CGPoint(x: 30, y: top + 1)) ?? first
            let rect = table.rectForRow(at: visible)
            let index = window.lowerBound + visible.row
            let block = parent.document.blocks[index]
            var offset: Int? = block.imagePath == nil ? nil : 0
            if block.imagePath == nil, let text = try? attributedText(for: block) {
                if lineMaps[index] == nil { lineMaps[index] = ReaderLineMap(text: text, width: table.bounds.width - 48) }
                offset = lineMaps[index]?.offset(atY: max(0, top - rect.minY - 8))
            }
            return ReadingAnchor(block: index, fraction: min(0.999, max(0, (top - rect.minY) / max(1, rect.height))), utf16Offset: offset)
        }
        func reloadRows() {
            restoring = true
            heightCache.removeAll()
            lineMaps.removeAll()
            table?.reloadData(); table?.layoutIfNeeded()
            // Keep scroll reports suspended until the queued anchor restoration.
        }
        func requestRestore(_ anchor: ReadingAnchor) {
            pendingAnchor = anchor
            let token = UUID(); restoreToken = token
            DispatchQueue.main.async { [weak self] in
                guard let self, self.restoreToken == token, let pending = self.pendingAnchor else { return }
                self.restore(pending)
            }
        }
        func widthChanged() {
            let anchor = pendingAnchor ?? lastKnownAnchor ?? ReadingAnchor(block: parent.jump.block, fraction: parent.jump.fraction)
            heightCache.removeAll()
            lineMaps.removeAll()
            DispatchQueue.main.async { [weak self] in
                guard let self else { return }
                self.reloadRows(); self.requestRestore(anchor)
            }
        }
        func restore(_ anchor: ReadingAnchor) {
            guard let table, table.bounds.width > 48, !parent.document.blocks.isEmpty else { return }
            restoring = true
            let block = min(max(0, anchor.block), parent.document.blocks.count - 1)
            let nextWindow = ReadingWindow(total: parent.document.blocks.count, anchor: block)
            if nextWindow != window { window = nextWindow; heightCache.removeAll(); lineMaps.removeAll(); table.reloadData() }
            let path = IndexPath(row: block - window.lowerBound, section: 0)
            table.scrollToRow(at: path, at: .top, animated: false)
            table.layoutIfNeeded()
            let rect = table.rectForRow(at: path)
            var within = min(0.999, max(0, anchor.fraction)) * rect.height
            if let offset = anchor.utf16Offset, parent.document.blocks[block].imagePath == nil,
               let text = try? attributedText(for: parent.document.blocks[block]) {
                let map = ReaderLineMap(text: text, width: table.bounds.width - 48)
                lineMaps[block] = map; within = 8 + map.y(for: offset)
            }
            let desired = rect.minY + within - table.adjustedContentInset.top
            let maximum = max(-table.adjustedContentInset.top, table.contentSize.height - table.bounds.height + table.adjustedContentInset.bottom)
            table.setContentOffset(CGPoint(x: 0, y: min(maximum, max(-table.adjustedContentInset.top, desired))), animated: false)
            hasRestored = true
            pendingAnchor = nil
            restoring = false
            report(force: true)
        }
        func report(force: Bool = false) {
            guard hasRestored, !restoring, pendingAnchor == nil, let table, table.indexPathsForVisibleRows?.isEmpty == false,
                  force || Date().timeIntervalSince(lastReport) > 0.5 else { return }
            lastReport = Date()
            let position = anchor()
            lastKnownAnchor = position
            #if DEBUG
            RenderDiagnostics.record(table: table, document: parent.document, anchor: position, window: window)
            #endif
            parent.onPosition(position)
            if window.shouldMove(at: position.block), !windowShiftPending {
                windowShiftPending = true
                DispatchQueue.main.async { [weak self] in
                    guard let self else { return }
                    self.windowShiftPending = false
                    let current = self.anchor()
                    if self.pendingAnchor == nil, self.window.shouldMove(at: current.block) { self.restore(current) }
                }
            }
        }
        func scrollViewDidScroll(_ scrollView: UIScrollView) { report() }
        func scrollViewDidEndDecelerating(_ scrollView: UIScrollView) { report(force: true) }
        func scrollViewDidEndDragging(_ scrollView: UIScrollView, willDecelerate decelerate: Bool) { if !decelerate { report(force: true) } }
    }
}

#if DEBUG
/// Metadata-only simulator instrumentation, absent from Release builds.
private enum RenderDiagnostics {
    private struct Sample: Codable {
        var session: String
        var time: Double
        var block: Int
        var blocks: Int
        var visibleCells: Int
        var maximumTextUTF16: Int
        var processPeakRSSBytes: Int64
        var windowStart: Int
        var windowBlocks: Int
    }
    private static let session = UUID().uuidString
    private static var history: [String: [Sample]] = [:]
    static func record(table: UITableView, document: BookDocument, anchor: ReadingAnchor, window: ReadingWindow) {
        guard ProcessInfo.processInfo.arguments.contains("--uitesting") else { return }
        let name = document.totalUTF16 > 1_000_000 ? "long" : "small"
        let url = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent(".s00-render-metrics-\(name).json")
        if history[name] == nil {
            history[name] = (try? JSONDecoder().decode([Sample].self, from: Data(contentsOf: url))) ?? []
        }
        var usage = rusage(); getrusage(RUSAGE_SELF, &usage)
        let textMaximum = table.visibleCells.compactMap { ($0 as? BookCell)?.label.attributedText?.length }.max() ?? 0
        let sample = Sample(session: session, time: Date().timeIntervalSince1970, block: anchor.block,
                            blocks: document.blocks.count, visibleCells: table.visibleCells.count,
                            maximumTextUTF16: textMaximum, processPeakRSSBytes: Int64(usage.ru_maxrss),
                            windowStart: window.lowerBound, windowBlocks: window.count)
        history[name, default: []].append(sample)
        history[name] = Array(history[name, default: []].suffix(256))
        try? JSONEncoder().encode(history[name, default: []]).write(to: url, options: .atomic)
        table.accessibilityValue = "visible=\(sample.visibleCells);maxText=\(sample.maximumTextUTF16);windowStart=\(window.lowerBound);peakRSS=\(sample.processPeakRSSBytes)"
    }
}
#endif
