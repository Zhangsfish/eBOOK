import SwiftUI

/// The Lecture Asset tutorial's local, skippable storyboard adapted to reading.
/// Artwork never imports a file, changes a preference or starts real speech.
struct ReaderTutorialView: View {
    @Environment(\.dismiss) private var dismiss
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var page = 0
    private let titles = ["把好书放进书架", "按自己的习惯翻页", "需要时，打开阅读控制", "读累了，就听一会儿"]
    private let captions = [
        "点书架右上角的加号，从“文件”导入 EPUB 或 TXT。",
        "在书架设置里选择上下滚动或左右翻页。左右模式也可以点页面两侧翻页。",
        "点右下角三个点，打开返回、朗读、目录和字号。下方进度条可以跳转，点三个点收起。",
        "点喇叭开始朗读，在阅读设置里调整语音和语速。收起面板后也可以继续听。"
    ]

    private var staticArtwork: Bool {
        #if DEBUG
        if ProcessInfo.processInfo.arguments.contains("--test-reduce-motion") { return true }
        #endif
        return reduceMotion
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    Text(titles[page]).font(.title2.bold()).multilineTextAlignment(.center)
                        .accessibilityIdentifier("tutorial.title")
                    GeometryReader { geometry in
                        Group {
                            if staticArtwork { ReaderTutorialArtwork(page: page, time: 3) }
                            else { ReaderTutorialPlayback(page: page).id(page) }
                        }
                        .scaleEffect(min(1, geometry.size.width / 320), anchor: .top)
                        .frame(width: geometry.size.width, height: 350, alignment: .top)
                    }.frame(height: 350)
                        .accessibilityElement(children: .ignore)
                        .accessibilityLabel(captions[page])
                        .accessibilityIdentifier(staticArtwork ? "tutorial.static" : "tutorial.animation")
                        .contentShape(Rectangle())
                        .gesture(DragGesture().onEnded { value in
                            if value.translation.width < -40 { page = min(titles.count - 1, page + 1) }
                            if value.translation.width > 40 { page = max(0, page - 1) }
                        })
                    Text(captions[page]).font(.body).foregroundStyle(.secondary)
                        .multilineTextAlignment(.center).fixedSize(horizontal: false, vertical: true)
                    HStack(spacing: 8) {
                        ForEach(titles.indices, id: \.self) { index in
                            Capsule().fill(index == page ? Color.brown : Color.secondary.opacity(0.2))
                                .frame(width: index == page ? 20 : 6, height: 6)
                        }
                    }.accessibilityElement(children: .ignore).accessibilityLabel("\(page + 1) / \(titles.count)")
                        .accessibilityIdentifier("tutorial.page")
                }.padding(24)
            }
            .safeAreaInset(edge: .bottom) {
                HStack(spacing: 16) {
                    if page > 0 {
                        Button("上一步") { page -= 1 }.buttonStyle(.bordered)
                            .accessibilityIdentifier("tutorial.previous")
                    }
                    Button(page == titles.count - 1 ? "开始阅读" : "下一步") {
                        if page == titles.count - 1 { dismiss() } else { page += 1 }
                    }.buttonStyle(.borderedProminent).accessibilityIdentifier("tutorial.next")
                }.frame(maxWidth: .infinity).padding(16).background(.regularMaterial)
            }
            .navigationTitle("新手教程").navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("跳过") { dismiss() }.accessibilityIdentifier("tutorial.skip")
                }
            }
        }.tint(.brown)
    }
}

private struct ReaderTutorialPlayback: View {
    let page: Int
    @State private var start = Date()
    @State private var settled = false

    var body: some View {
        TimelineView(.animation(minimumInterval: 1.0 / 30, paused: settled)) { context in
            ReaderTutorialArtwork(page: page, time: settled ? 3 : min(3, max(0, context.date.timeIntervalSince(start))))
        }
        .task {
            start = Date(); settled = false
            do { try await Task.sleep(for: .seconds(3)) } catch { return }
            settled = true
        }
    }
}

private struct ReaderTutorialArtwork: View {
    let page: Int
    let time: Double
    private let ink = Color.brown
    private let paper = Color(red: 0.96, green: 0.93, blue: 0.83)

    private func phase(_ start: Double, _ end: Double) -> CGFloat {
        let x = CGFloat(min(1, max(0, (time - start) / (end - start))))
        return x * x * (3 - 2 * x)
    }

    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 28).fill(paper)
                .overlay(RoundedRectangle(cornerRadius: 28).stroke(ink.opacity(0.15)))
                .frame(width: 218, height: 320).shadow(color: .black.opacity(0.05), radius: 12, y: 6)
            Group {
                switch page {
                case 0: importing
                case 1: turning
                case 2: controls
                default: listening
                }
            }.frame(width: 190, height: 288)
        }.frame(width: 320, height: 350).foregroundStyle(ink).allowsHitTesting(false)
    }

    private var importing: some View {
        VStack(spacing: 22) {
            HStack {
                Text("书架").font(.title3.bold()); Spacer()
                Image(systemName: "plus").foregroundStyle(ink)
                    .scaleEffect(1 + 0.18 * sin(Double(phase(0.2, 0.8)) * .pi))
            }
            HStack(spacing: 14) {
                Image(systemName: "book.closed.fill").font(.system(size: 34)).foregroundStyle(ink)
                VStack(alignment: .leading, spacing: 8) {
                    Text("清晨随笔").font(.headline)
                    Text("开始阅读").font(.caption).foregroundStyle(.secondary)
                }
                Spacer(minLength: 0)
            }.padding(14).background(.white.opacity(0.75), in: RoundedRectangle(cornerRadius: 12))
                .offset(y: 36 * (1 - phase(1.0, 2.0))).opacity(Double(phase(1.0, 1.7)))
            HStack(spacing: 16) {
                Label("EPUB", systemImage: "doc"); Label("TXT", systemImage: "doc.text")
            }.font(.caption).foregroundStyle(ink)
                .offset(y: -10 * phase(0.6, 1.2)).opacity(Double(1 - phase(1.3, 2.1)))
            Spacer(minLength: 0)
        }.padding(.top, 16)
    }

    private var textLines: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("清晨").font(.headline).padding(.bottom, 6)
            Text("晨光落在书页上，窗外的风轻轻吹过。把这一刻留给自己，慢慢读下去。")
                .font(.system(size: 13)).lineSpacing(5)
            ForEach(0..<5) { index in
                Capsule().fill(ink.opacity(0.16)).frame(width: index == 4 ? 98 : 172, height: 3)
            }
        }.foregroundStyle(ink.opacity(0.85))
    }

    private var turning: some View {
        VStack(spacing: 18) {
            Text("左右翻页").font(.caption).foregroundStyle(ink)
                .padding(.horizontal, 14).padding(.vertical, 7)
                .background(.white.opacity(0.65), in: Capsule())
            textLines
                .offset(x: -18 * sin(Double(phase(0.9, 2.1)) * .pi))
                .opacity(1 - 0.35 * sin(Double(phase(0.9, 2.1)) * .pi))
            HStack {
                Image(systemName: "chevron.left"); Spacer()
                Image(systemName: "hand.tap.fill")
                    .scaleEffect(1 - 0.12 * sin(Double(phase(0.7, 1.5)) * .pi))
                Image(systemName: "chevron.right")
            }.font(.system(size: 20)).foregroundStyle(ink.opacity(0.5))
            Spacer(minLength: 0)
        }.padding(.top, 8)
    }

    private var toolRow: some View {
        HStack {
            ForEach(["chevron.left", "speaker.wave.2", "list.bullet", "textformat.size"], id: \.self) { icon in
                Image(systemName: icon).frame(maxWidth: .infinity)
            }
        }.font(.system(size: 14)).foregroundStyle(ink.opacity(0.65))
    }

    private var controls: some View {
        VStack(spacing: 12) {
            textLines.padding(.top, 10)
            Spacer(minLength: 0)
            VStack(spacing: 16) {
                toolRow.opacity(Double(phase(0.7, 1.5)))
                HStack(spacing: 10) {
                    Text("28%").font(.system(size: 9))
                    ZStack(alignment: .leading) {
                        Capsule().fill(ink.opacity(0.18)).frame(height: 2)
                        Circle().fill(ink.opacity(0.65)).frame(width: 7, height: 7).offset(x: 32)
                    }.opacity(Double(phase(0.7, 1.5)))
                    Image(systemName: "ellipsis").font(.system(size: 14))
                }.foregroundStyle(ink.opacity(0.65))
            }.padding(.bottom, 5).offset(y: 10 * (1 - phase(0.7, 1.5)))
        }
    }

    private var listening: some View {
        VStack(spacing: 24) {
            textLines.padding(.top, 10)
            HStack(alignment: .center, spacing: 4) {
                ForEach(0..<20) { index in
                    let wave = time >= 3 ? 0.5 : abs(sin(time * 4 + Double(index) * 0.7))
                    Capsule().fill(ink.opacity(0.55)).frame(width: 4, height: 8 + 26 * wave)
                }
            }.frame(height: 36)
            HStack(spacing: 26) {
                Text("0.8×").font(.caption)
                Image(systemName: "pause.fill").font(.title2)
                Image(systemName: "speaker.wave.2").font(.body)
            }.foregroundStyle(ink)
            Spacer(minLength: 0)
        }
    }
}
