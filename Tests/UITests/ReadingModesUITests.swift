import XCTest

final class ReadingModesUITests: XCTestCase {
    override func setUpWithError() throws { continueAfterFailure = false }
    private func launch(_ fixture: String, reset: Bool = true, extra: [String] = []) -> XCUIApplication {
        let app = XCUIApplication()
        app.launchArguments = ["--uitesting", "--test-import", fixture, "-AppleLanguages", "(zh-Hans)", "-AppleLocale", "zh_CN"]
        if reset { app.launchArguments.append("--reset-library") }
        app.launchArguments += extra
        app.launch()
        let ready = extra.contains("--show-tutorial") ? "tutorial.skip" : "library.preferences"
        XCTAssertTrue(app.buttons[ready].waitForExistence(timeout: 180))
        return app
    }
    private func choose(_ app: XCUIApplication, id: String, title: String) {
        app.buttons["library.preferences"].tap()
        let identified = app.buttons[id]
        let item = identified.waitForExistence(timeout: 3) ? identified : app.buttons[title]
        XCTAssertTrue(item.waitForExistence(timeout: 10)); item.tap()
        let saved = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
            (app.buttons["library.preferences"].value as? String)?.contains(title) == true
        }, object: app)
        XCTAssertEqual(XCTWaiter.wait(for: [saved], timeout: 10), .completed)
    }
    private func open(_ app: XCUIApplication, title: String, horizontal: Bool) {
        let book = app.buttons["library.book.\(title)"]
        XCTAssertTrue(book.waitForExistence(timeout: 180)); book.tap()
        let content = horizontal ? app.textViews["reader.page.text"] : app.tables["reader.table"]
        XCTAssertTrue(content.waitForExistence(timeout: 20))
        XCTAssertFalse(app.buttons["library.preferences"].exists)
    }
    private func controls(_ app: XCUIApplication) {
        let entry = app.buttons["reader.controls"]
        XCTAssertTrue(entry.waitForExistence(timeout: 10)); entry.tap()
        XCTAssertTrue(app.buttons["reader.back"].waitForExistence(timeout: 10))
    }
    private func snapshot(_ app: XCUIApplication, _ name: String) {
        let attachment = XCTAttachment(screenshot: app.screenshot())
        attachment.name = "reading-modes-" + name; attachment.lifetime = .keepAlways; add(attachment)
    }
    private func pagePosition(_ app: XCUIApplication) -> String {
        let value = app.textViews["reader.page.text"].value as? String ?? ""
        return value.components(separatedBy: ";visibleUTF16=")[0]
    }
    private func waitForPosition(_ expected: String, app: XCUIApplication) {
        let ready = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in self.pagePosition(app) == expected }, object: app)
        XCTAssertEqual(XCTWaiter.wait(for: [ready], timeout: 15), .completed, "expected=\(expected); actual=\(pagePosition(app))")
    }
    private func waitForTutorialTitle(_ title: String, app: XCUIApplication) {
        let ready = XCTNSPredicateExpectation(predicate: NSPredicate(format: "label == %@", title),
                                               object: app.staticTexts["tutorial.title"])
        XCTAssertEqual(XCTWaiter.wait(for: [ready], timeout: 10), .completed)
    }
    private func swipe(_ app: XCUIApplication, left: Bool) {
        let before = pagePosition(app)
        // A defined80%-width drag crosses the paging threshold on both iOS
        // versions; XCTest's default text-element flick can be too short.
        let page = app.textViews["reader.page.text"]
        let start = page.coordinate(withNormalizedOffset: CGVector(dx: left ? 0.9 : 0.1, dy: 0.45))
        let end = page.coordinate(withNormalizedOffset: CGVector(dx: left ? 0.1 : 0.9, dy: 0.45))
        start.press(forDuration: 0.05, thenDragTo: end)
        let changed = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
            !self.pagePosition(app).isEmpty && self.pagePosition(app) != before
        }, object: app)
        XCTAssertEqual(XCTWaiter.wait(for: [changed], timeout: 15), .completed,
                       "Swipe did not move: before=\(before), actual=\(pagePosition(app))")
    }
    private func tapPage(_ app: XCUIApplication, x: CGFloat) {
        let before = pagePosition(app)
        app.textViews["reader.page.text"].coordinate(withNormalizedOffset: CGVector(dx: x, dy: 0.45)).tap()
        let changed = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
            !self.pagePosition(app).isEmpty && self.pagePosition(app) != before
        }, object: app)
        XCTAssertEqual(XCTWaiter.wait(for: [changed], timeout: 10), .completed)
    }
    private func assertPositionStays(_ expected: String, app: XCUIApplication) {
        let changed = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
            let value = self.pagePosition(app)
            return !value.isEmpty && value != expected
        }, object: app)
        changed.isInverted = true
        XCTAssertEqual(XCTWaiter.wait(for: [changed], timeout: 1), .completed)
        XCTAssertEqual(pagePosition(app), expected)
    }
    func testBottomIconRowAndSmallSliderKeepNavigationAndThemes() {
        let app = launch("synthetic.epub")
        choose(app, id: "library.mode.horizontal", title: "左右翻页")
        open(app, title: "合成的清晨", horizontal: true)
        let beginning = pagePosition(app)
        for theme in ["护眼", "夜间", "明亮"] {
            controls(app)
            let buttons = ["reader.back", "reader.speech", "reader.toc", "reader.settings"].map { app.buttons[$0] }
            for button in buttons {
                XCTAssertTrue(button.isHittable)
                XCTAssertGreaterThanOrEqual(button.frame.height, 44)
                XCTAssertGreaterThanOrEqual(button.frame.width, 44)
                XCTAssertEqual(button.frame.midY, buttons[0].frame.midY, accuracy: 1)
                XCTAssertGreaterThan(button.frame.minY, app.frame.maxY - 200)
            }
            for index in 1..<buttons.count { XCTAssertGreaterThan(buttons[index].frame.minX, buttons[index - 1].frame.maxX) }
            let slider = app.sliders["reader.seek"]
            XCTAssertTrue(slider.isHittable)
            XCTAssertGreaterThanOrEqual(slider.frame.minY, buttons[0].frame.maxY - 1)
            assertPositionStays(beginning, app: app)
            app.buttons["reader.settings"].tap()
            XCTAssertTrue(app.buttons[theme].waitForExistence(timeout: 10)); app.buttons[theme].tap()
            app.buttons["完成"].tap()
            controls(app); snapshot(app, "bottom-controls-" + theme)
            app.buttons["reader.controls.dismiss"].tap()
            XCTAssertTrue(app.buttons["reader.controls"].waitForExistence(timeout: 10))
            waitForPosition(beginning, app: app)
        }
        controls(app)
        let slider = app.sliders["reader.seek"]
        let beforeValue = slider.value as? String ?? ""
        // Drag the real thumb centre, rather than relying on XCTest's
        // normalized adjustment geometry for a custom UISlider thumb image.
        let fields = Dictionary(uniqueKeysWithValues: beforeValue.components(separatedBy: ";").compactMap { field -> (String, String)? in
            let pair = field.components(separatedBy: "=")
            return pair.count == 2 ? (pair[0], pair[1]) : nil
        })
        guard let x = Double(fields["screenX"] ?? ""), let y = Double(fields["screenY"] ?? "") else {
            XCTFail("Missing actual native thumb geometry: \(beforeValue)"); return
        }
        print("READER_SEEK_BEFORE frame=\(slider.frame) \(beforeValue)")
        let start = app.coordinate(withNormalizedOffset: .zero).withOffset(CGVector(dx: x, dy: y))
        let end = slider.coordinate(withNormalizedOffset: CGVector(dx: 0.9, dy: 0.5))
        start.press(forDuration: 0.05, thenDragTo: end)
        let sought = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in self.pagePosition(app) != beginning }, object: app)
        let result = XCTWaiter.wait(for: [sought], timeout: 10)
        print("READER_SEEK_AFTER \(slider.value ?? "nil") position=\(pagePosition(app))")
        XCTAssertEqual(result, .completed,
                       "Seek did not move: slider \(beforeValue)→\(slider.value ?? "nil"), before=\(beginning), actual=\(pagePosition(app))")
        let saved = pagePosition(app)
        app.buttons["reader.toc"].tap()
        XCTAssertTrue(app.buttons["完成"].waitForExistence(timeout: 10)); app.buttons["完成"].tap()
        waitForPosition(saved, app: app)
    }
    func testTutorialCanSkipReplayAndFinishWithoutChangingBookPreferences() {
        let app = launch("synthetic.epub", extra: ["--show-tutorial"])
        XCTAssertTrue(app.buttons["tutorial.skip"].waitForExistence(timeout: 10))
        XCTAssertTrue(app.otherElements["tutorial.animation"].exists)
        snapshot(app, "tutorial-import")
        app.buttons["tutorial.skip"].tap()
        choose(app, id: "library.mode.horizontal", title: "左右翻页")
        app.buttons["library.preferences"].tap()
        app.buttons["library.tutorial"].tap()
        XCTAssertTrue(app.staticTexts["tutorial.title"].waitForExistence(timeout: 10))
        XCTAssertEqual(app.staticTexts["tutorial.title"].label, "把好书放进书架")
        let titles = ["按自己的习惯翻页", "需要时，打开阅读控制", "读累了，就听一会儿"]
        for title in titles {
            app.buttons["tutorial.next"].tap()
            waitForTutorialTitle(title, app: app)
        }
        app.buttons["tutorial.previous"].tap()
        waitForTutorialTitle(titles[1], app: app)
        snapshot(app, "tutorial-reading-controls")
        app.buttons["tutorial.next"].tap(); waitForTutorialTitle(titles[2], app: app)
        app.buttons["tutorial.next"].tap()
        XCTAssertTrue(app.buttons["library.preferences"].waitForExistence(timeout: 10))
        XCTAssertTrue((app.buttons["library.preferences"].value as? String)?.contains("左右翻页") == true)
        open(app, title: "合成的清晨", horizontal: true)
        XCTAssertFalse(app.buttons["reader.back"].exists)
    }
    func testTutorialReduceMotionShowsStaticStoryboard() {
        let app = launch("synthetic.epub", extra: ["--show-tutorial", "--test-reduce-motion"])
        XCTAssertTrue(app.buttons["tutorial.skip"].waitForExistence(timeout: 10))
        XCTAssertTrue(app.otherElements["tutorial.static"].exists)
        XCTAssertFalse(app.otherElements["tutorial.animation"].exists)
        for _ in 0..<3 { app.buttons["tutorial.next"].tap(); XCTAssertTrue(app.otherElements["tutorial.static"].exists) }
        app.buttons["tutorial.next"].tap()
        XCTAssertTrue(app.buttons["library.preferences"].waitForExistence(timeout: 10))
    }
    func testFeedbackCanCopyContactAndReturnToShelf() {
        let app = launch("synthetic.epub")
        app.buttons["library.preferences"].tap(); app.buttons["library.feedback"].tap()
        let email = app.buttons["feedback.email"]
        XCTAssertTrue(email.waitForExistence(timeout: 10)); XCTAssertTrue(email.label.contains("zhangs.taq@gmail.com"))
        XCTAssertTrue(app.buttons["feedback.homepage"].isHittable)
        app.buttons["feedback.copy"].tap()
        XCTAssertTrue(app.buttons["feedback.copy"].label.contains("已复制邮箱"))
        snapshot(app, "feedback-contact")
        // Do not launch Mail/browser or send a message during automated tests.
        app.buttons["feedback.dismiss"].tap()
        XCTAssertTrue(app.buttons["library.preferences"].waitForExistence(timeout: 10))
        open(app, title: "合成的清晨", horizontal: false)
    }
    func testSideTapsMatchSwipesAndLeaveCentreAndControlsAlone() {
        let app = launch("synthetic_long_gb18030.txt")
        choose(app, id: "library.mode.horizontal", title: "左右翻页")
        open(app, title: "synthetic_long_gb18030", horizontal: true)
        let beginning = pagePosition(app)
        app.textViews["reader.page.text"].coordinate(withNormalizedOffset: CGVector(dx: 0.14, dy: 0.45)).tap()
        assertPositionStays(beginning, app: app)
        tapPage(app, x: 0.86)
        let second = pagePosition(app)
        tapPage(app, x: 0.14); waitForPosition(beginning, app: app)
        swipe(app, left: true); waitForPosition(second, app: app)
        tapPage(app, x: 0.86)
        let third = pagePosition(app)
        tapPage(app, x: 0.14); waitForPosition(second, app: app)
        swipe(app, left: true); waitForPosition(third, app: app)
        app.textViews["reader.page.text"].coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.45)).tap()
        assertPositionStays(third, app: app)
        XCTAssertFalse(app.buttons["reader.back"].exists)
        controls(app); assertPositionStays(third, app: app)
        app.buttons["reader.settings"].tap()
        XCTAssertTrue(app.sliders["settings.font"].waitForExistence(timeout: 10))
        app.buttons["完成"].tap(); waitForPosition(third, app: app)
        XCTAssertFalse(app.buttons["reader.back"].exists)
        let text = app.textViews["reader.page.text"]
        text.coordinate(withNormalizedOffset: CGVector(dx: 0.86, dy: 0.45)).doubleTap()
        assertPositionStays(third, app: app)
        snapshot(app, "side-taps-and-text-selection")
        app.terminate()
        let reopened = launch("synthetic_long_gb18030.txt", reset: false)
        open(reopened, title: "synthetic_long_gb18030", horizontal: true)
        waitForPosition(third, app: reopened)
    }
    func testSideTapsStopAtLastPageAndKeepTOCAtLiveChapter() {
        let app = launch("synthetic_long_gb18030.txt")
        choose(app, id: "library.mode.horizontal", title: "左右翻页")
        open(app, title: "synthetic_long_gb18030", horizontal: true)
        controls(app); app.buttons["reader.toc"].tap()
        let search = app.searchFields.firstMatch
        XCTAssertTrue(search.waitForExistence(timeout: 10)); search.tap(); search.typeText("625")
        let afterword = app.buttons["toc.entry.624"]
        XCTAssertTrue(afterword.waitForExistence(timeout: 10)); afterword.tap()
        waitForPosition("block=1872;offset=0", app: app)
        // The last chapter spans several blocks/pages. Follow actual source
        // endpoints, not a100% slider approximation or a guessed page count.
        for _ in 0..<32 {
            if (app.textViews["reader.page.text"].value as? String)?.contains(";endBlock=1875;endOffset=0") == true { break }
            swipe(app, left: true)
        }
        XCTAssertTrue((app.textViews["reader.page.text"].value as? String)?.contains(";endBlock=1875;endOffset=0") == true)
        let last = pagePosition(app)
        app.textViews["reader.page.text"].coordinate(withNormalizedOffset: CGVector(dx: 0.86, dy: 0.45)).tap()
        assertPositionStays(last, app: app)
        tapPage(app, x: 0.14); tapPage(app, x: 0.86)
        waitForPosition(last, app: app)
        controls(app); app.buttons["reader.toc"].tap()
        let selected = app.buttons["toc.entry.624"]
        XCTAssertTrue(selected.waitForExistence(timeout: 10)); XCTAssertTrue(selected.isSelected); XCTAssertTrue(selected.isHittable)
        app.buttons["完成"].tap(); waitForPosition(last, app: app)
    }
    func testShelfAppearanceAndReaderThemePersistIndependently() {
        let app = launch("synthetic.epub")
        choose(app, id: "library.appearance.dark", title: "夜间")
        snapshot(app, "shelf-night")
        open(app, title: "合成的清晨", horizontal: false)
        snapshot(app, "reader-warm-shelf-night")
        controls(app); app.buttons["reader.settings"].tap()
        XCTAssertTrue(app.buttons["护眼"].waitForExistence(timeout: 10))
        XCTAssertTrue(app.buttons["护眼"].isSelected)
        XCTAssertFalse(app.buttons["library.mode.horizontal"].exists)
        app.buttons["明亮"].tap(); app.buttons["完成"].tap()
        snapshot(app, "reader-light-shelf-night")
        controls(app); app.buttons["reader.back"].tap()
        XCTAssertTrue(app.buttons["library.preferences"].waitForExistence(timeout: 10))
        XCTAssertTrue((app.buttons["library.preferences"].value as? String)?.contains("书架夜间") == true)
        snapshot(app, "shelf-still-night")
        app.terminate()
        let reopened = launch("synthetic.epub", reset: false)
        XCTAssertTrue((reopened.buttons["library.preferences"].value as? String)?.contains("书架夜间") == true)
        open(reopened, title: "合成的清晨", horizontal: false)
        controls(reopened); reopened.buttons["reader.settings"].tap()
        XCTAssertTrue(reopened.buttons["明亮"].waitForExistence(timeout: 10))
        XCTAssertTrue(reopened.buttons["明亮"].isSelected)
    }
    func testHorizontalPagesReturnRestoreTOCAndSwitchToVertical() {
        let app = launch("synthetic_long_gb18030.txt")
        choose(app, id: "library.mode.horizontal", title: "左右翻页")
        open(app, title: "synthetic_long_gb18030", horizontal: true)
        let beginning = pagePosition(app)
        XCTAssertTrue(beginning.contains("block=0;offset=0"))
        swipe(app, left: true); swipe(app, left: false); waitForPosition(beginning, app: app)
        for _ in 0..<3 { swipe(app, left: true) }
        let saved = pagePosition(app)
        XCTAssertNotEqual(saved, beginning)
        snapshot(app, "horizontal-page")
        app.terminate()
        let reopened = launch("synthetic_long_gb18030.txt", reset: false)
        open(reopened, title: "synthetic_long_gb18030", horizontal: true)
        waitForPosition(saved, app: reopened)
        controls(reopened); reopened.buttons["reader.toc"].tap()
        let search = reopened.searchFields.firstMatch
        XCTAssertTrue(search.waitForExistence(timeout: 10)); search.tap(); search.typeText("624")
        let target = reopened.buttons["toc.entry.623"]
        XCTAssertTrue(target.waitForExistence(timeout: 10)); target.tap()
        waitForPosition("block=1869;offset=0", app: reopened)
        controls(reopened); reopened.buttons["reader.toc"].tap()
        let selected = reopened.buttons["toc.entry.623"]
        XCTAssertTrue(selected.waitForExistence(timeout: 15)); XCTAssertTrue(selected.isSelected); XCTAssertTrue(selected.isHittable)
        snapshot(reopened, "toc-current-horizontal")
        reopened.buttons["完成"].tap()
        controls(reopened); reopened.buttons["reader.settings"].tap()
        let font = reopened.sliders["settings.font"]
        XCTAssertTrue(font.waitForExistence(timeout: 10)); font.adjust(toNormalizedSliderPosition: 0.75)
        reopened.buttons["完成"].tap()
        waitForPosition("block=1869;offset=0", app: reopened)
        snapshot(reopened, "horizontal-large-font")
        controls(reopened); reopened.buttons["reader.back"].tap()
        XCTAssertTrue(reopened.buttons["library.preferences"].waitForExistence(timeout: 10))
        choose(reopened, id: "library.mode.vertical", title: "上下滚动")
        open(reopened, title: "synthetic_long_gb18030", horizontal: false)
        controls(reopened)
        snapshot(reopened, "vertical-restored-chapter")
        let anchor = reopened.staticTexts["reader.anchor"].label
        let table = reopened.tables["reader.table"].value as? String ?? ""
        print("S02B_MODE_RESTORE anchor=\(anchor) table=\(table)")
        // SwiftUI localizes interpolated integers (for example1,870). Compare
        // the actual numbers, then independently verify the precise source anchor.
        let numbers = anchor.components(separatedBy: "/").map { $0.filter(\.isNumber) }
        XCTAssertEqual(numbers, ["1870", "1875"], "\(anchor); \(table)")
        let fields = Dictionary(uniqueKeysWithValues: table.components(separatedBy: ";").compactMap { value -> (String, String)? in
            let pair = value.components(separatedBy: "=")
            return pair.count == 2 ? (pair[0], pair[1]) : nil
        })
        XCTAssertEqual(fields["block"], "1869", table)
        XCTAssertEqual(fields["offset"], "0", table)
        XCTAssertFalse(reopened.textViews["reader.page.text"].exists)
    }
}
