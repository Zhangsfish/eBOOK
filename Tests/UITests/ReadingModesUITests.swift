import XCTest

final class ReadingModesUITests: XCTestCase {
    override func setUpWithError() throws { continueAfterFailure = false }
    private func launch(_ fixture: String, reset: Bool = true) -> XCUIApplication {
        let app = XCUIApplication()
        app.launchArguments = ["--uitesting", "--test-import", fixture, "-AppleLanguages", "(zh-Hans)", "-AppleLocale", "zh_CN"]
        if reset { app.launchArguments.append("--reset-library") }
        app.launch(); XCTAssertTrue(app.buttons["library.preferences"].waitForExistence(timeout: 180))
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
        XCTAssertEqual(XCTWaiter.wait(for: [ready], timeout: 15), .completed)
    }
    private func swipe(_ app: XCUIApplication, left: Bool) {
        let before = pagePosition(app)
        if left { app.textViews["reader.page.text"].swipeLeft() }
        else { app.textViews["reader.page.text"].swipeRight() }
        let changed = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
            !self.pagePosition(app).isEmpty && self.pagePosition(app) != before
        }, object: app)
        XCTAssertEqual(XCTWaiter.wait(for: [changed], timeout: 15), .completed)
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
        controls(app); app.sliders["reader.seek"].adjust(toNormalizedSliderPosition: 1)
        app.buttons["reader.controls.dismiss"].tap()
        waitForPosition("block=1874;offset=0", app: app)
        // Seeking to100% selects the final source block, which still spans
        // several viewport pages. Reach the actual source end before testing EOF.
        for _ in 0..<10 {
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
