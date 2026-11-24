# Owner iPhone checks

Install only the exact build recorded in DELIVERY.md. This is the S00 reader
with Apple local speech; S01 vendor voices are not in the app.

Record only iPhone model, iOS version, app version/build and PASS/FAIL/NOT_RUN.
Never include UDID, Apple credentials or private book contents in public evidence.
Use the original synthetic files; generate the long fixture with
`python3 scripts/generate_long_gb18030_fixture.py` and transfer through Files.
Do not expect a test book bundled inside the app.

| Check | What to observe | Result |
|---|---|---|
| Install/open | Correct version/build; library opens without crashing | NOT_RUN |
| TXT/EPUB import | Import original small TXT and EPUB through Files; Chinese and TOC readable | NOT_RUN |
| Encodings | Import original UTF-8, UTF-16, GBK/GB18030 samples without garbled text | NOT_RUN |
| Long TXT | Import the generated 2,301,482-character book; scroll and navigate to chapter 624 | NOT_RUN |
| Reading controls | Change font, line spacing and warm/dark theme; text remains usable | NOT_RUN |
| Reading restore | Note chapter/block, close and reopen; position and settings restored | NOT_RUN |
| Local speech | Play/pause/resume, rate and chapter skipping work with a Mandarin system voice | NOT_RUN |
| Background/lock | Listen locked for 10 minutes, cross text-block boundaries, use lock-screen pause/resume | NOT_RUN |
| Listening restore | Pause, close and reopen; resume near saved listening position, separate from reading | NOT_RUN |
| Interruption | Receive/end a call; record actual pause/resume behavior | NOT_RUN |
| Headphones/Bluetooth | Disconnect headphones; test available play/pause controls | NOT_RUN |
| Accessibility | Large Dynamic Type and basic VoiceOver navigation remain usable | NOT_RUN |

The owner may do the first three checks first, then long-book/locked listening.
A successful simulator run cannot mark any row above PASS. Subjective smoothness
does not establish a measured device memory peak; memory profiling remains NOT_RUN
until real Instruments/device diagnostics are available.
