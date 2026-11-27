# Bottom controls, tutorial and feedback

Owner instruction 2026-11-27 reopens PR12 on its existing branch from
566a7fa94296633c4078f9b06b7d261a26cc32a7. Changes: a quiet bottom row of four
reader icons with the progress slider below and a smaller visible thumb; a local,
skippable/replayable animated tutorial adapted from Lecture Asset; bookshelf feedback.
The exact existing public email/homepage come from Lecture Asset's AboutSupportView.

The owner explicitly requests direct internal phone testing after real validation,
without another web review. This scoped authorization supersedes prior freeze/audit
gates for these changes and the existing pinned eBOOK-only signing bridge. No merge,
public release, paid service, new voice, model/queue change or other workstream edit.

DELIVERY.md and evidence.json will record actual tested source, commands, CI and
Apple build availability. Temporary downloads, screenshots and raw signing logs stay
in ignored .local-test-data/s02b/reader-help/. Never commit models/audio/private books,
keys, signing logs or simulator/device IDs. Phone UX acceptance waits for owner feedback.

Current candidate1619c200ed7552be5687c4446240daefe676fb4c is undergoing14-method
reading runs46014013164(26.5)/46014021341(18.5). Prior18.5 candidates each14/14;
prior26.5 attempts failed default swipe/slider events or an immediate tutorial-title
assertion. All remain in DELIVERY.md/evidence.json. The current candidate adds
explicit overlay zIndex, a DEBUG+uitesting+test-seek-probe-only UISlider subclass
that reports real native geometry/events, and bounded title waiting. It does not
fake progress or set values during tests. Actual signed upload has NOT_RUN;48.1
remains latest available. Preserve paused bridge edits and do not dispatch until
actual current results are checked. No source or report is independently approved
merely because it was pushed; owner authorized direct internal testing for this scope.
