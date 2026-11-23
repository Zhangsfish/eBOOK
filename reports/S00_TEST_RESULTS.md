# S00 test results

State: IN_PROGRESS. Xcode tests have not run yet.

## Executed on Windows

- `git status --short --branch`: original lecture-asset checkout contained
  unrelated untracked files; all were left untouched. Created separate eBOOK
  checkout and fast-forward synchronized the requested existing branch.
- `python3 scripts/generate_long_gb18030_fixture.py`: Windows Store alias did
  not execute Python. Retried with existing `C:\conda_envs\myenv\python.exe`.
- That existing Python generated 2,301,482 characters, 73,176 lines,
  4,236,594 bytes, 624 chapters plus afterword under ignored `.local-test-data/`.
- Host: Windows 10.0.26200. `xcodebuild`, `xcrun`, and `swift` are absent.

The owner authorized making the repository public to use free standard macOS
Actions. The workflow will perform real Debug build-for-testing, simulator tests
and a Release simulator build. No physical-device results are claimed.
