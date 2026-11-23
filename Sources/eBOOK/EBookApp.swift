import SwiftUI

@main struct EBookApp: App {
    @StateObject private var library = LibraryModel()
    @StateObject private var speech = SpeechController()
    @Environment(\.scenePhase) private var scenePhase
    var body: some Scene {
        WindowGroup {
            LibraryView().environmentObject(library).environmentObject(speech)
                .task {
                    speech.attach(library)
                    #if DEBUG
                    await library.importUITestFixtureIfRequested()
                    #endif
                }
                .onChange(of: scenePhase) { _, phase in
                    if phase != .active { library.persist(); speech.persist() }
                }
        }
    }
}
