# Product Specification — eBOOK

## Product definition
A minimal iPhone ebook reader whose two primary jobs are:
1. Let a user import and comfortably read their own ebook.
2. Let the user listen to that same book in a pleasant, natural Mandarin voice.

The product should feel quiet, legible, and dependable. Reading and listening are the product; everything else is secondary.

## Target platform
- iPhone / iOS first.
- Native SwiftUI interface.
- App Store distribution is the intended destination.
- iPad-specific layouts are not required for the first MVP, but avoid architecture that prevents them.

## MVP features

### Library
- Import via the system document picker / Files.
- EPUB and TXT are the initial required formats.
- For TXT, support common Chinese ebook encodings: UTF-8, UTF-16, and GBK/GB18030.
- Show title, author when available, and reading progress.
- Open, remove, and resume a book.
- Store imported content locally and persist reading/listening positions.
- Graceful handling of unsupported, encrypted, malformed, and oversized files.

### Reading
- EPUB chapter/section navigation and table of contents.
- Each TOC opening reveals and marks the chapter at the live reading position;
  stale chapter searches are cleared. Browsing or closing the TOC preserves the
  reading anchor; only choosing a chapter navigates the book.
- TXT reading with sensible paragraph and chapter heuristics; do not pretend TXT has a reliable semantic TOC if it does not.
- Font size controls, line spacing, page/background themes, including a warm low-glare / eye-comfort theme.
- Progress indicator and restore last reading position.
- Screen should remain readable with Dynamic Type and VoiceOver support.

### Listening
- Play, pause, resume, seek, skip chapter, and playback speed.
- Continue audio while the screen is locked / app is in background where iOS permits.
- Respect audio-session interruptions and headphone controls.
- Track listening position separately from reading position.
- Speech should be chunked at paragraph/sentence boundaries, not sent as one enormous request.
- First milestone may use Apple AVSpeechSynthesizer as a functional baseline. Design a provider abstraction so premium cloud voices can be added without rewriting the player.
- Clearly communicate when a voice requires network access. Keep a local fallback.

## Explicit non-goals
- No bookstore, content discovery, scraping, online library, social/community, comments, highlights/notes, recommendation feed, user accounts, ads, or subscription/paywall in the MVP.
- No DRM circumvention.
- No bundled full copyrighted books.
- No requirement to sync across devices in the MVP.

## Quality bar
- Importing a valid EPUB/TXT should be straightforward.
- The first reading screen should be usable without onboarding.
- Typography and background themes should be calm and comfortable for long sessions.
- The speech voice should sound natural over long-form Chinese fiction, not like a navigation system or news bulletin.
- Playback must not restart from the beginning after ordinary app suspension or navigation.
- Failures must be visible and recoverable; no silent loss of reading position.

## App Store and content rights
The app is a user-import reader. Users provide their own files. The app must not source or redistribute copyrighted books. Any external content source, if ever added, requires explicit authorization and terms review. Apple App Review Guidelines require rights to third-party material and restrict unauthorized downloading/conversion of third-party media. Review current rules before release:
- https://developer.apple.com/app-store/review/guidelines/
- https://developer.apple.com/support/reader-apps/

## Example validation title
`绝境黑夜` by 滚开 is a useful real-world long-form Chinese novel for compatibility/performance testing, but it is copyrighted content. Do not fetch, commit, package, or redistribute an unauthorized EPUB/TXT copy. Validate the parser with synthetic/public-domain Chinese test content first. If the owner supplies a lawfully obtained, DRM-free file that can be exported from the source platform, it can be imported locally for private compatibility testing.
