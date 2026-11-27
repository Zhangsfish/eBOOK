# Reading modes follow-up

Owner request2026-11-26: after audit fixes, add horizontal viewport pagination
alongside existing vertical scrolling. Authority: tasks/S02B_READING_MODES.md.
Mode selection belongs on bookshelf, replacing TXT encoding toolbar menu.
Latest correction: shelf appearance is independent of existing reader theme.
Shelf gets system(default)/normal/warm/night. Reader theme stays adjustable inside
the book exactly as before and must not be overwritten by shelf changes.
Keep typography/speech, quiet ellipsis, synchronized TOC and persistent anchors.
No whole-book layout or giant Text. Preserve old preferences with vertical default.
Implementation: ReaderPages.swift uses native TextKit viewport layout and a native
horizontal UIPageViewController. Read at most4 source blocks, cache8 source strings
and64 predecessor positions; never pre-layout a whole book. Images have separate
pages and the existing1600px thumbnail safety limit. Native line maps add optional
UTF16 anchors to old compatible ReadingAnchor data for mode/reflow restoration.
ShelfAppearance defaults system and ReadingMode defaults vertical on legacy data.
LibraryView root NavigationStack path selects shelf/reader color scheme separately;
in-book ReaderSettings.theme remains intact. Encoding defaults automatic in import.
Five ReaderPaginationTests +two ReadingModesUITests pass on both18.5 and26.5 at
6469489062e6b91d743295cc2c08320334dbbf17; each full suite55/55,0skips.
Earlier6b3 mode assertion ignored localized commas; corrected numeric and exact
source offset assertions pass, with actual metadata and original screenshots.
READY_FOR_AUDIT, no further edits/reruns/upload before independent review.
Inspect bounded original-fixture CI screenshots for shelf-night/reader-warm/light
independence and horizontal text fit; don't count source compilation as visual QA.
Report actual CI/test SHA and phone/build availability honestly; no new TestFlight.
