# Original synthetic fixtures

All text, metadata and navigation in this directory are original test data made
for S00. No commercial ebook or external prose was used. Recreate with
`python3 scripts/generate_small_fixtures.py` (stdlib only).

- `sample_*.txt`: six encoding variants; GB18030 also contains supplementary
  Unicode characters that cannot be encoded as GBK.
- `synthetic.epub`: EPUB 3 nav, fragment links, inline text and a single test pixel.
- `synthetic_ncx.epub`: EPUB 2 NCX.
- `unsafe_path.epub`, `unsafe_entity.epub`, `bad_spine.epub`: deliberate errors.

The large generated TXT belongs in ignored `.local-test-data/`, not here.
