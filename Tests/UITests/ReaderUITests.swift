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

    private func assertLongBookTOCTracksReading(_ app: XCUIApplication, snapshotName: String) {
        // The original 625-chapter fixture has three bounded blocks per chapter.
        // Read the live anchor, rather than assuming a previous navigation target.
        let anchor = app.staticTexts["reader.anchor"].label
        let digits = anchor.components(separatedBy: "/")[0].filter(\.isNumber)
        guard let block = Int(digits), block > 0 else {
            XCTFail("Missing live reading anchor: \(anchor)"); return
        }
        app.buttons["reader.toc"].tap()
        let search = app.searchFields.firstMatch
        XCTAssertTrue(search.waitForExistence(timeout: 10))
        XCTAssertNotEqual(search.value as? String, "624", "Opening the TOC clears the previous search")
        let current = app.buttons["toc.entry.\((block - 1) / 3)"]
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
        assertLongBookTOCTracksReading(app, snapshotName: "toc-follows-manual-reading")
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
        assertLongBookTOCTracksReading(app, snapshotName: "toc-current-chapter-624")
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
        assertLongBookTOCTracksReading(reopened, snapshotName: "toc-follows-restored-reading")
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

    func testFilesPickerImportsSelectedTXTAndEPUB() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--uitesting", "--reset-library", "-AppleLanguages", "(zh-Hans)", "-AppleLocale", "zh_CN"]
        app.launch()
        func choose(_ filename: String, expectedTitle: String) {
            let button = app.buttons["library.import"].firstMatch
            XCTAssertTrue(button.waitForExistence(timeout: 30)); button.tap()
            let name = (filename as NSString).deletingPathExtension
            let file = app.staticTexts.matching(NSPredicate(format: "label == %@ OR label == %@", name, filename)).firstMatch
            if !file.waitForExistence(timeout: 5) {
                // A fresh simulator opens in empty Recents. DocumentManager's
                // remote view can expose its tabs after the sheet animation;
                // an immediate exists check silently skipped Browse before.
                let browse = app.tabBars["DOC.browsingModeTabBar"].buttons.matching(
                    NSPredicate(format: "label == '浏览' OR label == 'Browse'")
                ).firstMatch
                XCTAssertTrue(browse.waitForExistence(timeout: 30)); browse.tap()
                if !file.waitForExistence(timeout: 5) {
                    let phone = app.staticTexts.matching(NSPredicate(format:
                        "label == 'On My iPhone' OR label == '我的iPhone' OR label == '我的 iPhone' OR label == '在我的 iPhone 上'"
                    )).firstMatch
                    if !phone.waitForExistence(timeout: 20) { print("S00_LOCATIONS_TREE \(app.debugDescription)") }
                    XCTAssertTrue(phone.waitForExistence(timeout: 10)); phone.tap()
                    let folder = app.staticTexts["eBOOK"].firstMatch
                    XCTAssertTrue(folder.waitForExistence(timeout: 20))
                    let folderCell = app.collectionViews["File View"].cells.containing(.staticText, identifier: "eBOOK").firstMatch
                    if folderCell.exists { folderCell.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.25)).tap() }
                    else { folder.tap() }
                }
            }
            if #available(iOS 26.0, *) {
                // Current Files icon previews can consume an automation tap.
                // Use the native List view and activate the actual file row.
                let more = app.buttons["OverflowBarButtonItem"]
                XCTAssertTrue(more.waitForExistence(timeout: 10)); more.tap()
                let list = app.buttons.matching(NSPredicate(format: "label == '列表' OR label == 'List'")).firstMatch
                if !list.waitForExistence(timeout: 10) { print("S00_PICKER_VIEW_MENU \(app.debugDescription)") }
                XCTAssertTrue(list.waitForExistence(timeout: 2)); list.tap()
            }
            snapshot("system-picker-\(name)", app)
            if !file.waitForExistence(timeout: 10) { print("S00_PICKER_TREE \(app.debugDescription)") }
            XCTAssertTrue(file.waitForExistence(timeout: 10))
            let suffix = (filename as NSString).pathExtension
            if #available(iOS 26.0, *) {
                let row = app.collectionViews["File View"].cells.containing(.staticText, identifier: file.label).firstMatch
                XCTAssertTrue(row.waitForExistence(timeout: 10)); row.tap()
            } else {
                let cell = app.collectionViews["File View"].cells.matching(NSPredicate(
                    format: "identifier == %@ OR identifier == %@", "\(name), \(suffix)", "\(filename), \(suffix)"
                )).firstMatch
                XCTAssertTrue(cell.waitForExistence(timeout: 10))
                let thumbnail = cell.images.firstMatch
                if thumbnail.exists && thumbnail.isHittable { thumbnail.tap() }
                else { cell.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.25)).tap() }
            }
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
