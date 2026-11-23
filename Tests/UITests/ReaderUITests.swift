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

    func testLongBookIncrementalScrollingChapterNavigationTypographyAndRelaunch() throws {
        let app = launch("synthetic_long_gb18030.txt")
        open(app, title: "synthetic_long_gb18030")
        let table = app.tables["reader.table"]
        XCTAssertTrue(app.staticTexts["reader.anchor"].waitForExistence(timeout: 10))
        let beginning = app.staticTexts["reader.anchor"].label
        for _ in 0..<42 { table.swipeUp() }
        XCTAssertNotEqual(app.staticTexts["reader.anchor"].label, beginning)
        snapshot("long-book-warm", app)
        app.buttons["reader.toc"].tap()
        let search = app.searchFields.firstMatch
        XCTAssertTrue(search.waitForExistence(timeout: 10)); search.tap(); search.typeText("624")
        let chapter = app.buttons["toc.entry.623"]
        XCTAssertTrue(chapter.waitForExistence(timeout: 10)); chapter.tap()
        XCTAssertTrue(table.waitForExistence(timeout: 10))
        let anchor = app.staticTexts["reader.anchor"].label
        XCTAssertNotEqual(anchor, beginning)
        app.buttons["reader.settings"].tap()
        let font = app.sliders["settings.font"]
        XCTAssertTrue(font.waitForExistence(timeout: 10)); font.adjust(toNormalizedSliderPosition: 0.65)
        app.buttons["夜间"].tap(); app.buttons["完成"].tap()
        snapshot("long-book-dark", app)
        let saved = app.staticTexts["reader.anchor"].label
        app.terminate()
        let reopened = launch("synthetic_long_gb18030.txt", reset: false)
        open(reopened, title: "synthetic_long_gb18030")
        XCTAssertEqual(reopened.staticTexts["reader.anchor"].label, saved)
        reopened.buttons["reader.settings"].tap()
        XCTAssertTrue(reopened.buttons["夜间"].isSelected)
        reopened.buttons["完成"].tap()
        snapshot("long-book-restored", reopened)
    }

    func testEPUBTOCImageAndReaderControls() throws {
        let app = launch("synthetic.epub")
        open(app, title: "合成的清晨")
        snapshot("epub-reader", app)
        app.buttons["reader.toc"].tap()
        let chapter = app.buttons["toc.entry.2"]
        XCTAssertTrue(chapter.waitForExistence(timeout: 10)); chapter.tap()
        XCTAssertTrue(app.tables["reader.table"].waitForExistence(timeout: 10))
        XCTAssertTrue(app.buttons["speech.play"].exists)
        XCTAssertTrue(app.buttons["下一章"].exists)
        XCTAssertTrue(app.buttons["从当前阅读位置开始朗读"].exists)
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
                let browse = app.buttons.matching(NSPredicate(format: "label == '浏览' OR label == 'Browse'")).firstMatch
                if browse.exists { browse.tap() }
                let phone = app.staticTexts.matching(NSPredicate(format: "label == 'On My iPhone' OR label == '我的 iPhone' OR label == '在我的 iPhone 上'")).firstMatch
                if phone.waitForExistence(timeout: 8) { phone.tap() }
                let folder = app.staticTexts["eBOOK"].firstMatch
                if folder.waitForExistence(timeout: 8) { folder.tap() }
            }
            snapshot("system-picker-\(name)", app)
            if !file.waitForExistence(timeout: 10) { print("S00_PICKER_TREE \(app.debugDescription)") }
            XCTAssertTrue(file.waitForExistence(timeout: 10)); file.tap()
            let confirm = app.buttons.matching(NSPredicate(format: "label == '打开' OR label == 'Open'")).firstMatch
            if confirm.waitForExistence(timeout: 2), confirm.isHittable { confirm.tap() }
            let imported = app.buttons["library.book.\(expectedTitle)"].waitForExistence(timeout: 30)
            if !imported {
                snapshot("system-picker-import-result-\(name)", app)
                print("S00_NATIVE_IMPORT_RESULT \(app.debugDescription)")
            }
            XCTAssertTrue(imported)
        }
        choose("sample_utf8.txt", expectedTitle: "sample_utf8")
        choose("synthetic.epub", expectedTitle: "合成的清晨")
        snapshot("files-imported-library", app)
    }
}
