import SwiftUI
import UniformTypeIdentifiers
import UIKit

/// Files grants access to the selected document; LibraryModel coordinates the
/// read and creates the app-owned copy. Avoid a second picker-managed copy.
@MainActor struct BookDocumentPicker: UIViewControllerRepresentable {
    let onSelection: (URL?) -> Void
    func makeCoordinator() -> Coordinator { Coordinator(onSelection: onSelection) }
    func makeUIViewController(context: Context) -> UIDocumentPickerViewController {
        let picker = UIDocumentPickerViewController(forOpeningContentTypes: [.plainText, UTType(filenameExtension: "epub") ?? .data], asCopy: false)
        picker.allowsMultipleSelection = false
        picker.shouldShowFileExtensions = true
        picker.delegate = context.coordinator
        NSLog("EBOOK_IMPORT picker created")
        return picker
    }
    func updateUIViewController(_ controller: UIDocumentPickerViewController, context: Context) {
        context.coordinator.onSelection = onSelection
    }
    @MainActor final class Coordinator: NSObject, UIDocumentPickerDelegate {
        var onSelection: (URL?) -> Void
        init(onSelection: @escaping (URL?) -> Void) { self.onSelection = onSelection }
        func documentPicker(_ controller: UIDocumentPickerViewController, didPickDocumentsAt urls: [URL]) {
            NSLog("EBOOK_IMPORT picker selected count=%ld", urls.count)
            onSelection(urls.first)
        }
        func documentPickerWasCancelled(_ controller: UIDocumentPickerViewController) {
            NSLog("EBOOK_IMPORT picker cancelled")
            onSelection(nil)
        }
    }
}
