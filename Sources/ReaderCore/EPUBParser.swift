import Foundation
#if canImport(FoundationXML)
import FoundationXML
#endif

private enum XMLContent { case text(String), node(XMLNode) }
private final class XMLNode {
    let name: String
    let attributes: [String: String]
    var content: [XMLContent] = []
    init(name: String, attributes: [String: String]) { self.name = name; self.attributes = attributes }
    var children: [XMLNode] { content.compactMap { if case .node(let node) = $0 { return node }; return nil } }
    var text: String { content.map { switch $0 { case .text(let text): return text; case .node(let node): return node.text } }.joined() }
    func all(_ name: String) -> [XMLNode] { (self.name == name ? [self] : []) + children.flatMap { $0.all(name) } }
}

private final class XMLTree: NSObject, XMLParserDelegate {
    var root: XMLNode?
    private var stack: [XMLNode] = []
    private var count = 0, textCount = 0
    private var failure: Error?

    static func parse(_ data: Data) throws -> XMLNode {
        guard data.count <= 8 * 1024 * 1024 else { throw ReaderError.tooLarge("EPUB XML 文档过大。") }
        // XML keywords are ASCII. Ignore encoding padding so declarations in
        // UTF-16/32, with or without a BOM, cannot bypass the same policy.
        let entityKeyword = Array("<!ENTITY".utf8)
        var matched = 0
        for byte in data where byte != 0 {
            let upper = (97...122).contains(byte) ? byte - 32 : byte
            matched = upper == entityKeyword[matched] ? matched + 1 : (upper == 60 ? 1 : 0)
            if matched == entityKeyword.count { throw ReaderError.unsupported("EPUB 不允许自定义 XML 实体。") }
        }
        let delegate = XMLTree(), parser = XMLParser(data: data)
        parser.shouldResolveExternalEntities = false
        parser.externalEntityResolvingPolicy = .never
        parser.delegate = delegate
        guard parser.parse(), delegate.failure == nil, let root = delegate.root else {
            throw delegate.failure ?? ReaderError.invalid("EPUB XML/XHTML 格式损坏。")
        }
        return root
    }
    static func parseXHTML(_ data: Data) throws -> XMLNode {
        do { return try parse(data) }
        catch let error as ReaderError {
            switch error {
            case .invalid, .tooLarge:
                // Strict XML remains the authority, including on the repaired
                // document. Never retry forbidden entity declarations.
                guard let repaired = XHTMLVoidRepair.repair(data) else { throw error }
                return try parse(repaired)
            default: throw error
            }
        }
    }
    func parser(_ parser: XMLParser, didStartElement elementName: String, namespaceURI: String?, qualifiedName qName: String?, attributes: [String: String]) {
        count += 1
        guard count <= 100_000, stack.count < 128 else {
            failure = ReaderError.tooLarge("EPUB XML 结构过于复杂。"); parser.abortParsing(); return
        }
        let node = XMLNode(name: elementName.split(separator: ":").last.map(String.init) ?? elementName, attributes: attributes)
        if let parent = stack.last { parent.content.append(.node(node)) } else { root = node }
        stack.append(node)
    }
    func parser(_ parser: XMLParser, didEndElement elementName: String, namespaceURI: String?, qualifiedName qName: String?) { _ = stack.popLast() }
    func parser(_ parser: XMLParser, foundCharacters string: String) {
        textCount += string.utf16.count
        guard textCount <= 8 * 1024 * 1024 else { failure = ReaderError.tooLarge("EPUB XML 文字过多。"); parser.abortParsing(); return }
        stack.last?.content.append(.text(string))
    }
    func parser(_ parser: XMLParser, foundCDATA CDATABlock: Data) {
        if let text = String(data: CDATABlock, encoding: .utf8) { self.parser(parser, foundCharacters: text) }
    }
    func parser(_ parser: XMLParser, foundInternalEntityDeclarationWithName name: String, value: String?) {
        failure = ReaderError.unsupported("EPUB 不允许 XML 实体声明。"); parser.abortParsing()
    }
    func parser(_ parser: XMLParser, foundExternalEntityDeclarationWithName name: String, publicID: String?, systemID: String?) {
        failure = ReaderError.unsupported("EPUB 不允许外部 XML 实体。"); parser.abortParsing()
    }
    func parser(_ parser: XMLParser, resolveExternalEntityName name: String, systemID: String?) -> Data? { nil }
}

enum EPUBParser {
    private struct ManifestItem {
        let path: String
        let media: String
        let properties: [Substring]
    }
    private struct Navigation { let title: String; let path: String; let fragment: String?; let depth: Int }

    static func parse(_ data: Data, builder: BookBuilder, fallbackTitle: String) throws -> BookDocument {
        let archive = try ZIPArchive(data: data)
        guard try archive.read("mimetype", maximum: 100) == Data("application/epub+zip".utf8) else { throw ReaderError.invalid("文件不是有效 EPUB。") }
        guard archive.entries["META-INF/encryption.xml"] == nil else {
            throw ReaderError.unsupported("这本 EPUB 含有加密内容，无法导入。")
        }
        let container = try XMLTree.parse(archive.read("META-INF/container.xml"))
        guard let rootfile = container.all("rootfile").first?.attributes["full-path"] else { throw ReaderError.invalid("EPUB 缺少根文档。") }
        let packagePath = try resolve(rootfile, relativeTo: "")
        let package = try XMLTree.parse(archive.read(packagePath))
        guard package.name == "package", let manifestNode = package.all("manifest").first,
              let spine = package.all("spine").first else { throw ReaderError.invalid("EPUB 缺少 manifest 或 spine。") }
        let title = package.all("metadata").first?.all("title").first?.text.trimmingCharacters(in: .whitespacesAndNewlines)
        let author = package.all("metadata").first?.all("creator").first?.text.trimmingCharacters(in: .whitespacesAndNewlines)
        var manifest: [String: ManifestItem] = [:]
        for item in manifestNode.children where item.name == "item" {
            guard let id = item.attributes["id"], let href = item.attributes["href"], manifest[id] == nil else {
                throw ReaderError.invalid("EPUB manifest 标识无效或重复。")
            }
            manifest[id] = ManifestItem(path: try resolve(href, relativeTo: packagePath), media: item.attributes["media-type"] ?? "",
                                        properties: (item.attributes["properties"] ?? "").split(separator: " "))
        }
        var navigation: [Navigation] = []
        if let nav = manifest.values.first(where: { $0.properties.contains("nav") }) {
            let tree = try XMLTree.parseXHTML(archive.read(nav.path))
            if let toc = tree.all("nav").first(where: { ($0.attributes["epub:type"] ?? $0.attributes["type"] ?? "").split(separator: " ").contains("toc") }) {
                func visit(_ node: XMLNode, depth: Int) throws {
                    if node.name == "a", let href = node.attributes["href"] {
                        let label = clean(node.text)
                        if !label.isEmpty { navigation.append(try target(label, href: href, base: nav.path, depth: max(0, depth - 1))) }
                    }
                    for child in node.children { try visit(child, depth: depth + (node.name == "ol" ? 1 : 0)) }
                }
                try visit(toc, depth: 0)
            }
        } else if let ncxID = spine.attributes["toc"], let ncx = manifest[ncxID] {
            let tree = try XMLTree.parse(archive.read(ncx.path))
            func visit(_ node: XMLNode, depth: Int) throws {
                if node.name == "navPoint", let href = node.children.first(where: { $0.name == "content" })?.attributes["src"],
                   let label = node.children.first(where: { $0.name == "navLabel" })?.text {
                    navigation.append(try target(clean(label), href: href, base: ncx.path, depth: depth))
                }
                for child in node.children { try visit(child, depth: depth + (node.name == "navPoint" ? 1 : 0)) }
            }
            try visit(tree, depth: 0)
        }
        let references = spine.children.filter { $0.name == "itemref" && $0.attributes["linear"] != "no" }
        guard !references.isEmpty, references.count <= 2000 else { throw ReaderError.invalid("EPUB 阅读顺序为空或过长。") }
        var locations: [String: Int] = [:]
        for reference in references {
            guard let id = reference.attributes["idref"], let item = manifest[id], item.media == "application/xhtml+xml" else {
                throw ReaderError.unsupported("EPUB spine 含有缺失或非 XHTML 章节。")
            }
            let tree = try XMLTree.parseXHTML(archive.read(item.path))
            guard let body = tree.all("body").first else { throw ReaderError.invalid("EPUB XHTML 缺少 body。") }
            let label = navigation.first(where: { $0.path == item.path })?.title
                ?? tree.all("h1").first.map { clean($0.text) } ?? "第 \(builder.chapters.count + 1) 节"
            try builder.beginChapter(label)
            locations[item.path] = builder.blocks.count
            var pending = ""
            func flush() throws {
                let paragraph = clean(pending)
                if !paragraph.isEmpty { try builder.append(paragraph) }
                pending = ""
            }
            func walk(_ node: XMLNode) throws {
                if ["head", "script", "style", "iframe", "object", "svg", "audio", "video"].contains(node.name) { return }
                let blockTag = ["p", "div", "section", "article", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr", "blockquote", "pre"].contains(node.name)
                if blockTag { try flush() }
                if let anchor = node.attributes["id"] {
                    try flush(); try builder.flush()
                    locations[item.path + "#" + anchor] = builder.blocks.count
                }
                if node.name == "br" { pending += "\n" }
                if node.name == "img", let source = node.attributes["src"] {
                    try flush()
                    let imagePath = try resolve(source, relativeTo: item.path)
                    let suffix = URL(fileURLWithPath: imagePath).pathExtension.lowercased()
                    if ["png", "jpg", "jpeg", "gif"].contains(suffix) {
                        let bytes = try archive.read(imagePath, maximum: 8 * 1024 * 1024)
                        try builder.appendImage(bytes, extension: suffix, description: node.attributes["alt"] ?? "书中插图")
                    } else { try builder.append(node.attributes["alt"] ?? "[此插图格式暂不支持]") }
                    return
                }
                for content in node.content {
                    switch content { case .text(let text): pending += text; case .node(let child): try walk(child) }
                }
                if blockTag { try flush() }
            }
            try walk(body); try flush(); try builder.flush()
        }
        let toc = navigation.compactMap { entry -> TOCEntry? in
            let key = entry.path + (entry.fragment.map { "#" + $0 } ?? "")
            guard let block = locations[key] ?? locations[entry.path] else { return nil }
            return TOCEntry(id: 0, title: entry.title, block: block, depth: min(8, entry.depth))
        }.enumerated().map { TOCEntry(id: $0.offset, title: $0.element.title, block: $0.element.block, depth: $0.element.depth) }
        let fallbackTOC = builder.chapters.enumerated().map { TOCEntry(id: $0.offset, title: $0.element.title, block: $0.element.firstBlock) }
        return try builder.finish(title: title.flatMap { $0.isEmpty ? nil : $0 } ?? fallbackTitle,
                                  author: author, encoding: nil, toc: toc.isEmpty ? fallbackTOC : toc, heuristic: false)
    }

    private static func target(_ title: String, href: String, base: String, depth: Int) throws -> Navigation {
        let parts = href.split(separator: "#", maxSplits: 1, omittingEmptySubsequences: false)
        let fragment = parts.count == 2 ? String(parts[1]).removingPercentEncoding : nil
        return Navigation(title: title, path: try resolve(String(parts[0]), relativeTo: base), fragment: fragment, depth: depth)
    }

    private static func clean(_ text: String) -> String {
        text.replacingOccurrences(of: #"[\t\r\n ]+"#, with: " ", options: .regularExpression).trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private static func resolve(_ href: String, relativeTo base: String) throws -> String {
        let path = String(href.split(separator: "#", maxSplits: 1, omittingEmptySubsequences: false)[0])
        guard let decoded = path.removingPercentEncoding, !decoded.contains(":"), !decoded.contains("\\"),
              !decoded.contains("\0"), !decoded.contains("?"), !decoded.hasPrefix("/") else {
            throw ReaderError.unsupported("EPUB 中的资源地址无法读取。")
        }
        if decoded.isEmpty { return base }
        var components = base.split(separator: "/").dropLast().map(String.init)
        for part in decoded.split(separator: "/") {
            if part == "." { continue }
            if part == ".." {
                guard !components.isEmpty else { throw ReaderError.invalid("EPUB 资源路径越界。") }
                components.removeLast()
            } else { components.append(String(part)) }
        }
        guard !components.isEmpty else { throw ReaderError.invalid("EPUB 资源路径为空。") }
        return components.joined(separator: "/")
    }
}
