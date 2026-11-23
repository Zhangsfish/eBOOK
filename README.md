# eBOOK — iOS Reader

A focused iOS ebook reader for user-imported EPUB/TXT books, with a calm, high-quality Mandarin text-to-speech experience.

## Project status

The repository is being bootstrapped. See `STATUS.md`, `AGENTS.md`, `docs/PRODUCT_SPEC.md`, `docs/TECHNICAL_PLAN.md`, and `tasks/S00_READER_FOUNDATION.md` before making changes.

## Product boundary

- iOS only; native SwiftUI application.
- User-imported books only. No built-in catalog, scraping, redistribution, or bundled copyrighted books.
- Initial formats: EPUB and TXT, including common Chinese encodings.
- Reading and listening are the only primary workflows.

## Codex handoff

The currently authorized task is [S00 — Reader Foundation](tasks/S00_READER_FOUNDATION.md). The copy-ready local Codex prompt is [tasks/CODEX_HANDOFF_S00.md](tasks/CODEX_HANDOFF_S00.md). Track progress in [GitHub Issue #1](https://github.com/Zhangsfish/eBOOK/issues/1).

## Test data

Read [docs/TEST_DATA.md](docs/TEST_DATA.md). Generate the large original GB18030 test book locally with:

```bash
python3 scripts/generate_long_gb18030_fixture.py
```

The generated file is written under `.local-test-data/`, which is ignored by Git. Do not commit full copyrighted novels or user-imported commercial books.