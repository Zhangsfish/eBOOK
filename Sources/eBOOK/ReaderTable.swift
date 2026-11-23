import SwiftUI
import UIKit
import ImageIO

struct ReaderJump: Equatable {
    var block: Int
    var fraction: Double = 0
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
        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 24),
            stack.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -24),
            stack.topAnchor.constraint(equalTo: contentView.topAnchor, constant: 8),
            stack.bottomAnchor.constraint(equalTo: contentView.bottomAnchor, constant: -8),
            picture.heightAnchor.constraint(equalToConstant: 260)
        ])
    }
    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
    override func prepareForReuse() { super.prepareForReuse(); picture.image = nil; label.attributedText = nil }
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
        let table = UITableView(frame: .zero, style: .plain)
        table.register(BookCell.self, forCellReuseIdentifier: "block")
        table.dataSource = context.coordinator; table.delegate = context.coordinator
        table.separatorStyle = .none; table.rowHeight = UITableView.automaticDimension
        table.estimatedRowHeight = 520; table.contentInset = UIEdgeInsets(top: 12, left: 0, bottom: 40, right: 0)
        table.accessibilityIdentifier = "reader.table"
        table.backgroundColor = preferences.theme.background
        context.coordinator.table = table
        context.coordinator.typeSize = dynamicType
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
            table.reloadData(); table.layoutIfNeeded()
            restore = current
        }
        if coordinator.lastJump != jump.revision {
            coordinator.lastJump = jump.revision
            restore = ReadingAnchor(block: jump.block, fraction: jump.fraction)
        }
        if let restore {
            let token = UUID()
            coordinator.restoreToken = token
            DispatchQueue.main.async {
                if coordinator.restoreToken == token { coordinator.restore(restore) }
            }
        }
    }
    static func dismantleUIView(_ uiView: UITableView, coordinator: Coordinator) { coordinator.report(force: true) }

    final class Coordinator: NSObject, UITableViewDataSource, UITableViewDelegate {
        var parent: ReaderTable
        weak var table: UITableView?
        var lastJump: UUID?
        var restoreToken = UUID()
        var typeSize: DynamicTypeSize?
        private var lastReport = Date.distantPast
        private var restoring = false
        init(_ parent: ReaderTable) { self.parent = parent }
        func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int { parent.document.blocks.count }
        func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
            let cell = tableView.dequeueReusableCell(withIdentifier: "block", for: indexPath) as! BookCell
            let block = parent.document.blocks[indexPath.row]
            cell.backgroundColor = parent.preferences.theme.background
            cell.label.textColor = parent.preferences.theme.foreground
            cell.label.accessibilityIdentifier = "reader.block.\(block.id)"
            cell.picture.isHidden = block.imagePath == nil
            cell.label.isHidden = block.imagePath != nil
            do {
                if let image = block.imagePath {
                    let url = parent.storage.directory(for: parent.bookID).appendingPathComponent(image)
                    guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
                          let thumbnail = CGImageSourceCreateThumbnailAtIndex(source, 0, [
                            kCGImageSourceCreateThumbnailFromImageAlways: true,
                            kCGImageSourceThumbnailMaxPixelSize: 1600,
                            kCGImageSourceCreateThumbnailWithTransform: true
                          ] as CFDictionary) else { throw ReaderError.invalid("书中插图损坏或不受支持。") }
                    cell.picture.image = UIImage(cgImage: thumbnail)
                    cell.picture.accessibilityLabel = block.imageDescription ?? "书中插图"
                } else {
                    let text = try parent.storage.text(for: block, book: parent.bookID)
                    let style = NSMutableParagraphStyle()
                    style.lineSpacing = parent.preferences.lineSpacing
                    style.paragraphSpacing = 5
                    let font = UIFontMetrics(forTextStyle: .body).scaledFont(for: UIFont.systemFont(ofSize: parent.preferences.fontSize))
                    cell.label.attributedText = NSAttributedString(string: text, attributes: [
                        .font: font, .foregroundColor: parent.preferences.theme.foreground, .paragraphStyle: style
                    ])
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
            return ReadingAnchor(block: visible.row, fraction: min(0.999, max(0, (top - rect.minY) / max(1, rect.height))))
        }
        func restore(_ anchor: ReadingAnchor) {
            guard let table, !parent.document.blocks.isEmpty else { return }
            restoring = true
            let block = min(max(0, anchor.block), parent.document.blocks.count - 1)
            let path = IndexPath(row: block, section: 0)
            table.scrollToRow(at: path, at: .top, animated: false)
            table.layoutIfNeeded()
            let rect = table.rectForRow(at: path)
            let desired = rect.minY + min(0.999, max(0, anchor.fraction)) * rect.height - table.adjustedContentInset.top
            let maximum = max(-table.adjustedContentInset.top, table.contentSize.height - table.bounds.height + table.adjustedContentInset.bottom)
            table.setContentOffset(CGPoint(x: 0, y: min(maximum, max(-table.adjustedContentInset.top, desired))), animated: false)
            restoring = false
            report(force: true)
        }
        func report(force: Bool = false) {
            guard !restoring, force || Date().timeIntervalSince(lastReport) > 0.5 else { return }
            lastReport = Date(); parent.onPosition(anchor())
        }
        func scrollViewDidScroll(_ scrollView: UIScrollView) { report() }
        func scrollViewDidEndDecelerating(_ scrollView: UIScrollView) { report(force: true) }
        func scrollViewDidEndDragging(_ scrollView: UIScrollView, willDecelerate decelerate: Bool) { if !decelerate { report(force: true) } }
    }
}
