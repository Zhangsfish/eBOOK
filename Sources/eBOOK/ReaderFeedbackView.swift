import SwiftUI
import UIKit

struct ReaderFeedbackView: View {
    @Environment(\.dismiss) private var dismiss
    @Environment(\.openURL) private var openURL
    @State private var copied = false

    var body: some View {
        NavigationStack {
            Form {
                Section("联系我") {
                    Button {
                        openURL(URL(string: "mailto:zhangs.taq@gmail.com?subject=eBOOK%20%E6%84%8F%E8%A7%81%E5%8F%8D%E9%A6%88")!)
                    } label: { Label("zhangs.taq@gmail.com", systemImage: "envelope") }
                        .accessibilityIdentifier("feedback.email")
                    Button(copied ? "已复制邮箱" : "复制邮箱", systemImage: "doc.on.doc") {
                        UIPasteboard.general.string = "zhangs.taq@gmail.com"; copied = true
                    }.accessibilityIdentifier("feedback.copy")
                    Link(destination: URL(string: "https://zhang-shuo-portfolio.vercel.app/")!) {
                        Label("个人主页", systemImage: "arrow.up.right.square")
                    }.accessibilityIdentifier("feedback.homepage")
                }
            }
            .navigationTitle("意见反馈").navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("完成") { dismiss() }.accessibilityIdentifier("feedback.dismiss")
                }
            }
        }
    }
}
