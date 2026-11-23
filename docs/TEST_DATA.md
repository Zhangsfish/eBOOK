# Test Data and Local QA

## Repository data rule
Do not commit, upload, bundle, or redistribute a complete copyrighted novel or a user-imported commercial ebook in this repository, even though the repository is private. Do not place book text in CI artifacts, issue comments, PR descriptions, screenshots, crash reports, or logs.

Automated tests must use original synthetic text or public-domain text with a verified status. S00 uses the synthetic generator below.

## Real-world compatibility profile observed during planning

A ZIP attachment supplied in the planning conversation was inspected in place. Only its non-substantive format characteristics are recorded here; the archive and text are not part of this repository.

| Property | Observed value |
|---|---|
| Container | ZIP |
| ZIP entries | One TXT file |
| Inner filename | `绝境黑夜.txt` |
| Compressed archive size | 2,237,474 bytes |
| Uncompressed TXT size | 4,439,158 bytes |
| Strict decoding | Both GBK and GB18030 succeed |
| Decoded Unicode characters | 2,301,482 (including line endings) |
| Lines | 73,176 |
| Header metadata | Title `绝境黑夜`, author `滚开` |
| Header's stated progress | Chapter 624 and an afterword |
| Heading structure | Mixed styles; not every heading follows one uniform `第N章` pattern |

This profile establishes practical compatibility requirements: Chinese legacy-encoding detection, multi-megabyte input, tens of thousands of lines, long-form navigation, and non-uniform TXT chapter headings. It does not establish the archive's provenance or rights. ZIP is a container, not a required ebook format; S00 supports EPUB/TXT and does not need ZIP import.

## Generate a large synthetic fixture

From the repository root:

```bash
python3 scripts/generate_long_gb18030_fixture.py
```

The script creates:

```text
.local-test-data/synthetic_long_gb18030.txt
```

Default profile:
- GB18030 encoding (also decodable as GBK for the generated character set).
- 624 synthetic chapters plus an afterword.
- 2,301,482 Unicode characters including CRLF line endings.
- 73,176 lines.
- Mixed chapter-heading conventions to exercise heuristic navigation.
- Original synthetic prose only; no network access.

The entire `.local-test-data/` directory is ignored by Git. The generator itself is tracked, so every developer can reproduce the same fixture locally.

To change the size:

```bash
python3 scripts/generate_long_gb18030_fixture.py \
  --output .local-test-data/custom_long_book.txt \
  --chapters 300 \
  --target-chars 1000000 \
  --target-lines 30000
```

## S00 test expectations
- Test strict UTF-8, UTF-16 LE/BE, GBK, and GB18030 decoding with small synthetic fixtures.
- Use the generated large GB18030 file for import, scrolling/rendering, memory, progress persistence, and chapter-navigation performance checks.
- TXT chapter detection is heuristic. Recognize common patterns without treating every numbered line as a chapter. If confidence is low, retain readable continuous text and provide safe navigation rather than inventing a broken TOC.
- Never send imported book text to a cloud TTS service in S00. Use local AVSpeechSynthesizer only.
- The app's general-purpose Files import must remain local and must not upload book contents automatically.
