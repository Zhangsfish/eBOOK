import XCTest

final class ReaderUITests: XCTestCase {
    override func setUpWithError() throws { continueAfterFailure = false }
    private func launch(_ fixture: String, reset: Bool = true) -> XCUIApplication {
        let app = XCUIApplication()
        app.launchArguments = ["--uitesting", "--test-import", fixture, "-AppleLanguages", "(zh-Hans)", "-AppleLocale", "zh_CN"]
        if reset { app.launchArguments.append("--reset-library") }
        app.launch()
        return app
    }
    private func open(_ app: XCUIApplication, title: String) {
        let book = app.buttons["library.book.\(title)"]
        XCTAssertTrue(book.waitForExistence(timeout: 180))
        book.tap()
        XCTAssertTrue(app.tables["reader.table"].waitForExistence(timeout: 20))
    }
    private func snapshot(_ name: String, _ app: XCUIApplication) {
        let attachment = XCTAttachment(screenshot: app.screenshot()); attachment.name = name; attachment.lifetime = .keepAlways; add(attachment)
    }

    private func assertSpeechPanelHidden(_ app: XCUIApplication) {
        // A tap can finish before the native sheet's dismissal animation ends.
        // Require actual disappearance, with a bounded wait on both OS versions.
        let hidden = XCTNSPredicateExpectation(predicate: NSPredicate(format: "exists == false"),
                                               object: app.buttons["speech.play"])
        XCTAssertEqual(XCTWaiter.wait(for: [hidden], timeout: 10), .completed,
                       "Speech controls must disappear after closing the panel")
    }

    private func assertImmersive(_ app: XCUIApplication) {
        let entry = app.buttons["reader.controls"]
        let ready = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
            entry.exists && entry.isHittable
        }, object: entry)
        XCTAssertEqual(XCTWaiter.wait(for: [ready], timeout: 10), .completed)
        for identifier in ["reader.back", "reader.speech", "reader.toc", "reader.settings", "reader.controls.dismiss", "speech.play"] {
            XCTAssertFalse(app.buttons[identifier].exists, "Hidden reading control: \(identifier)")
        }
        XCTAssertFalse(app.sliders["reader.seek"].exists)
        XCTAssertFalse(app.staticTexts["reader.progress"].exists)
        XCTAssertEqual(app.navigationBars.count, 0, "The reader has no permanent navigation bar")
        XCTAssertGreaterThanOrEqual(entry.frame.width, 44)
        XCTAssertGreaterThanOrEqual(entry.frame.height, 44)
    }

    private func showControls(_ app: XCUIApplication) {
        let entry = app.buttons["reader.controls"]
        XCTAssertTrue(entry.waitForExistence(timeout: 10)); entry.tap()
        XCTAssertTrue(app.buttons["reader.controls.dismiss"].waitForExistence(timeout: 10))
    }

    private func hideControls(_ app: XCUIApplication) {
        app.buttons["reader.controls.dismiss"].tap()
        assertImmersive(app)
    }

    private func longBookBlock(from anchor: String) -> Int {
        let digits = anchor.components(separatedBy: "/")[0].filter(\.isNumber)
        guard let block = Int(digits), block > 0 else {
            XCTFail("Missing live reading anchor: \(anchor)"); return 0
        }
        return block - 1
    }

    private func assertLongBookTOCTracksReading(_ app: XCUIApplication, snapshotName: String) {
        // The original 625-chapter fixture has three bounded blocks per chapter.
        // Read the live anchor, rather than assuming a previous navigation target.
        let anchor = app.staticTexts["reader.anchor"].label
        let block = longBookBlock(from: anchor)
        app.buttons["reader.toc"].tap()
        let search = app.searchFields.firstMatch
        XCTAssertTrue(search.waitForExistence(timeout: 10))
        XCTAssertNotEqual(search.value as? String, "624", "Opening the TOC clears the previous search")
        let current = app.buttons["toc.entry.\(block / 3)"]
        let visible = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
            current.exists && current.isHittable && current.isSelected
        }, object: current)
        XCTAssertEqual(XCTWaiter.wait(for: [visible], timeout: 15), .completed,
                       "Current chapter must be visible and selected without scrolling the TOC")
        XCTAssertEqual(current.value as? String, "当前阅读章节")
        snapshot(snapshotName, app)
        app.buttons["完成"].tap()
        assertImmersive(app)
        showControls(app)
        XCTAssertEqual(app.staticTexts["reader.anchor"].label, anchor, "Opening the TOC must not move the reader")
    }

    private func jumpLongBook(_ app: XCUIApplication, to chapter: Int) {
        app.buttons["reader.toc"].tap()
        let search = app.searchFields.firstMatch
        XCTAssertTrue(search.waitForExistence(timeout: 10))
        search.tap(); search.typeText(String(chapter))
        let entry = app.buttons["toc.entry.\(chapter - 1)"]
        XCTAssertTrue(entry.waitForExistence(timeout: 10)); entry.tap()
        assertImmersive(app)
        showControls(app)
    }

    func testTOCReopensAtLiveChapterAfterScrollingSearchAndRelaunch() throws {
        let app = launch("synthetic_long_gb18030.txt")
        open(app, title: "synthetic_long_gb18030")
        showControls(app)
        jumpLongBook(app, to: 500)
        let previousChapter = longBookBlock(from: app.staticTexts["reader.anchor"].label) / 3
        var currentChapter = previousChapter
        // Cross an actual chapter boundary by reading, independently of the
        // last TOC selection. Bound the gesture count on both simulator sizes.
        for _ in 0..<4 {
            hideControls(app)
            for _ in 0..<8 { app.tables["reader.table"].swipeUp() }
            showControls(app)
            currentChapter = longBookBlock(from: app.staticTexts["reader.anchor"].label) / 3
            if currentChapter > previousChapter { break }
        }
        XCTAssertGreaterThan(currentChapter, previousChapter)
        assertLongBookTOCTracksReading(app, snapshotName: "toc-follows-manual-reading")
        jumpLongBook(app, to: 624)
        XCTAssertEqual(longBookBlock(from: app.staticTexts["reader.anchor"].label), 1869)
        assertLongBookTOCTracksReading(app, snapshotName: "toc-current-chapter-624")
        let saved = app.staticTexts["reader.anchor"].label
        app.terminate()
        let reopened = launch("synthetic_long_gb18030.txt", reset: false)
        open(reopened, title: "synthetic_long_gb18030")
        showControls(reopened)
        XCTAssertEqual(reopened.staticTexts["reader.anchor"].label, saved)
        assertLongBookTOCTracksReading(reopened, snapshotName: "toc-follows-restored-reading")
    }

    func testLongBookIncrementalScrollingChapterNavigationTypographyAndRelaunch() throws {
        let app = launch("synthetic_long_gb18030.txt")
        open(app, title: "synthetic_long_gb18030")
        let table = app.tables["reader.table"]
        assertImmersive(app)
        showControls(app)
        XCTAssertTrue(app.staticTexts["reader.anchor"].waitForExistence(timeout: 10))
        let beginning = app.staticTexts["reader.anchor"].label
        hideControls(app)
        for _ in 0..<42 { table.swipeUp() }
        assertImmersive(app) // Scrolling must not reveal the panel.
        snapshot("long-book-warm", app)
        showControls(app)
        XCTAssertNotEqual(app.staticTexts["reader.anchor"].label, beginning)
        app.buttons["reader.toc"].tap()
        let search = app.searchFields.firstMatch
        XCTAssertTrue(search.waitForExistence(timeout: 10)); search.tap(); search.typeText("624")
        let chapter = app.buttons["toc.entry.623"]
        XCTAssertTrue(chapter.waitForExistence(timeout: 10)); chapter.tap()
        XCTAssertTrue(table.waitForExistence(timeout: 10))
        assertImmersive(app)
        showControls(app)
        let anchor = app.staticTexts["reader.anchor"].label
        XCTAssertNotEqual(anchor, beginning)
        XCTAssertEqual(anchor.components(separatedBy: "/")[0].filter(\.isNumber), "1870")
        app.buttons["reader.settings"].tap()
        let font = app.sliders["settings.font"]
        XCTAssertTrue(font.waitForExistence(timeout: 10)); font.adjust(toNormalizedSliderPosition: 0.65)
        app.buttons["夜间"].tap(); app.buttons["完成"].tap()
        assertImmersive(app)
        snapshot("long-book-dark", app)
        showControls(app)
        let saved = app.staticTexts["reader.anchor"].label
        XCTAssertEqual(saved, anchor, "Typography changes must retain the absolute reading block")
        app.terminate()
        let reopened = launch("synthetic_long_gb18030.txt", reset: false)
        open(reopened, title: "synthetic_long_gb18030")
        assertImmersive(reopened)
        showControls(reopened)
        XCTAssertEqual(reopened.staticTexts["reader.anchor"].label, saved)
        reopened.buttons["reader.settings"].tap()
        XCTAssertTrue(reopened.buttons["夜间"].isSelected)
        reopened.buttons["完成"].tap()
        assertImmersive(reopened)
        snapshot("long-book-restored", reopened)
    }

    func testEPUBTOCImageAndReaderControls() throws {
        let app = launch("synthetic.epub")
        open(app, title: "合成的清晨")
        assertImmersive(app)
        let table = app.tables["reader.table"]
        let viewport = table.frame
        table.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)).tap()
        assertImmersive(app) // Only the deliberate ellipsis entry opens controls.
        snapshot("epub-reader", app)
        showControls(app)
        XCTAssertEqual(table.frame, viewport, "Showing controls must not resize the text viewport")
        app.buttons["reader.toc"].tap()
        let chapter = app.buttons["toc.entry.2"]
        XCTAssertTrue(chapter.waitForExistence(timeout: 10)); chapter.tap()
        XCTAssertTrue(app.tables["reader.table"].waitForExistence(timeout: 10))
        assertImmersive(app)
        showControls(app)
        let anchor = app.staticTexts["reader.anchor"].label
        hideControls(app)
        showControls(app)
        XCTAssertEqual(app.staticTexts["reader.anchor"].label, anchor)
        snapshot("reading-controls-expanded", app)
        app.buttons["reader.speech"].tap()
        XCTAssertTrue(app.buttons["speech.play"].waitForExistence(timeout: 10))
        XCTAssertTrue(app.buttons["下一章"].exists)
        XCTAssertTrue(app.buttons["从当前阅读位置开始朗读"].exists)
        snapshot("speech-controls-expanded", app)
        app.buttons["speech.dismiss"].tap()
        assertSpeechPanelHidden(app)
        assertImmersive(app)
        showControls(app)
        XCTAssertEqual(app.staticTexts["reader.anchor"].label, anchor)
        app.buttons["reader.speech"].tap()
        XCTAssertTrue(app.buttons["speech.play"].waitForExistence(timeout: 10))
        app.buttons["speech.dismiss"].tap()
        assertSpeechPanelHidden(app)
        assertImmersive(app)
        snapshot("epub-reader-speech-hidden", app)
        for (theme, name) in [("明亮", "light"), ("护眼", "warm"), ("夜间", "dark")] {
            showControls(app)
            app.buttons["reader.settings"].tap()
            XCTAssertTrue(app.buttons[theme].waitForExistence(timeout: 10)); app.buttons[theme].tap()
            app.buttons["完成"].tap()
            assertImmersive(app)
            XCTAssertEqual(table.frame, viewport)
            snapshot("immersive-\(name)", app)
        }
        showControls(app)
        app.buttons["reader.back"].tap()
        XCTAssertTrue(app.buttons["library.book.合成的清晨"].waitForExistence(timeout: 10))
    }

    func testSystemDocumentPickerPresentsAndCanCancel() throws {
        let app = launch("sample_utf8.txt")
        let button = app.buttons["library.import"].firstMatch
        XCTAssertTrue(button.waitForExistence(timeout: 180)); button.tap()
        let cancel = app.buttons.matching(NSPredicate(format: "label == '取消' OR label == 'Cancel'")).firstMatch
        XCTAssertTrue(cancel.waitForExistence(timeout: 20)); cancel.tap()
        XCTAssertTrue(button.waitForExistence(timeout: 10))
    }

    func testSuxinVoiceAndSeparateRatePersistWhileQuietReaderRemains() throws {
        let app = launch("synthetic.epub")
        open(app, title: "合成的清晨")
        showControls(app); app.buttons["reader.settings"].tap()
        let voice = app.buttons["settings.voice"]
        XCTAssertTrue(voice.waitForExistence(timeout: 15)); voice.tap()
        let suxin = app.buttons["苏心 · 离线中文 · zh-CN"]
        XCTAssertTrue(suxin.waitForExistence(timeout: 10)); suxin.tap()
        let rate = app.sliders["settings.suxinRate"]
        XCTAssertTrue(rate.waitForExistence(timeout: 10)); rate.adjust(toNormalizedSliderPosition: 2.0 / 3.0)
        let saved = rate.value as? String
        app.buttons["完成"].tap(); assertImmersive(app)
        app.terminate()
        let reopened = launch("synthetic.epub", reset: false)
        open(reopened, title: "合成的清晨"); showControls(reopened)
        reopened.buttons["reader.settings"].tap()
        XCTAssertTrue(reopened.sliders["settings.suxinRate"].waitForExistence(timeout: 10))
        XCTAssertEqual(reopened.sliders["settings.suxinRate"].value as? String, saved)
        reopened.buttons["完成"].tap(); assertImmersive(reopened)
    }

    func testFilesPickerImportsSelectedTXTAndEPUB() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--uitesting", "--reset-library", "-AppleLanguages", "(zh-Hans)", "-AppleLocale", "zh_CN"]
        app.launch()
        func choose(_ filename: String, expectedTitle: String) {
            let button = app.buttons["library.import"].firstMatch
            XCTAssertTrue(button.waitForExistence(timeout: 30)); button.tap()
            let name = (filename as NSString).deletingPathExtension
            let file = app.staticTexts.matching(NSPredicate(format: "label == %@ OR label == %@", name, filename)).firstMatch
            let sourceFolder = "eBOOK Import Test"
            if !app.navigationBars[sourceFolder].waitForExistence(timeout: 2) {
                let browse = app.tabBars["DOC.browsingModeTabBar"].buttons.matching(
                    NSPredicate(format: "label == '浏览' OR label == 'Browse'")
                ).firstMatch
                XCTAssertTrue(browse.waitForExistence(timeout: 30)); browse.tap()
                let folder = app.staticTexts[sourceFolder].firstMatch
                if !folder.waitForExistence(timeout: 2) {
                    let backToPhone = app.buttons.matching(NSPredicate(format:
                        "label == 'On My iPhone' OR label == '我的iPhone' OR label == '我的 iPhone' OR label == '在我的 iPhone 上'"
                    )).firstMatch
                    if backToPhone.exists, backToPhone.isHittable { backToPhone.tap() }
                }
                if !folder.waitForExistence(timeout: 2) {
                    let phone = app.staticTexts.matching(NSPredicate(format:
                        "label == 'On My iPhone' OR label == '我的iPhone' OR label == '我的 iPhone' OR label == '在我的 iPhone 上'"
                    )).firstMatch
                    if !phone.waitForExistence(timeout: 20) { print("S00_LOCATIONS_TREE \(app.debugDescription)") }
                    XCTAssertTrue(phone.waitForExistence(timeout: 10)); phone.tap()
                }
                XCTAssertTrue(folder.waitForExistence(timeout: 20))
                let folderCell = app.collectionViews["File View"].cells.containing(.staticText, identifier: sourceFolder).firstMatch
                XCTAssertTrue(folderCell.waitForExistence(timeout: 10)); folderCell.tap()
            }
            XCTAssertTrue(app.navigationBars[sourceFolder].waitForExistence(timeout: 10),
                          "Select original files from the external system provider")
            do {
                // Both runtimes expose icon previews separately from filename
                // activation. Use the same native List mode on 18.5 and26.5.
                let more: XCUIElement
                if #available(iOS 26.0, *) { more = app.buttons["OverflowBarButtonItem"] }
                else { more = app.buttons.matching(NSPredicate(format: "label == '更多' OR label == 'More'")).firstMatch }
                XCTAssertTrue(more.waitForExistence(timeout: 10)); more.tap()
                let list = app.buttons.matching(NSPredicate(format: "label == '列表' OR label == 'List'")).firstMatch
                if !list.waitForExistence(timeout: 10) { print("S00_PICKER_VIEW_MENU \(app.debugDescription)") }
                XCTAssertTrue(list.waitForExistence(timeout: 2)); list.tap()
            }
            snapshot("system-picker-\(name)", app)
            if !file.waitForExistence(timeout: 10) { print("S00_PICKER_TREE \(app.debugDescription)") }
            XCTAssertTrue(file.waitForExistence(timeout: 10))
            print("S02B_PICKER_TARGET enabled=\(file.isEnabled) hittable=\(file.isHittable) frame=\(file.frame)")
            XCTAssertTrue(file.isEnabled, "The real Files entry must accept this ebook type")
            XCTAssertTrue(file.isHittable)
            let fileCell = app.collectionViews["File View"].cells.containing(.staticText, identifier: file.label).firstMatch
            XCTAssertTrue(fileCell.waitForExistence(timeout: 10)); XCTAssertTrue(fileCell.isEnabled)
            fileCell.tap()
            let confirm = app.buttons.matching(NSPredicate(format: "label == '打开' OR label == 'Open'")).firstMatch
            if confirm.waitForExistence(timeout: 2), confirm.isHittable { confirm.tap() }
            let libraryBook = app.buttons["library.book.\(expectedTitle)"]
            let imported = libraryBook.waitForExistence(timeout: 30)
            if !imported {
                snapshot("system-picker-import-result-\(name)", app)
                print("S00_NATIVE_IMPORT_RESULT \(app.debugDescription)")
            }
            XCTAssertTrue(imported)
        }
        choose("sample_utf8.txt", expectedTitle: "sample_utf8")
        choose("synthetic.epub", expectedTitle: "合成的清晨")
        XCTAssertEqual(app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH 'library.book.'")).count, 2)
        snapshot("files-imported-library", app)
    }
}
