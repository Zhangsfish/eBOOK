# Codex handoff: S02A.3 — owner determines AI voice

Repository: `Zhangsfish/eBOOK`
Issue: https://github.com/Zhangsfish/eBOOK/issues/10
Branch: `codex/s02a-kokoro-ios-spike`
PR to update: https://github.com/Zhangsfish/eBOOK/pull/7

The owner explicitly decided **Matcha remains the leading AI TTS candidate, and Suxin-Light MUST receive real synthesis and listening testing**. Prior assistant recommendation to stop local AI experiments is superseded. Do not decide whether the voice is good on the owner's behalf.

1. Inspect all current worktrees and `git status`; protect existing model/audio data and others' branches. Safely fetch/fast-forward the named branch only. Read the root `AGENTS.md`, `tools/local-tts-spike/AGENTS.md`, Issue #10, `tasks/S02A3_SUXIN_MATCHA_LISTENING.md`, and the existing S02A.2 report/asset pins.
2. Suxin was NOT previously found slow/bad. Only its ONNX graph was loaded. Use its official pinned `SuxinTTS` synthesizer and actual Mandarin frontend. The owner now authorizes a bounded Suxin test, including installing required **free** pinned frontend packages in a NEW isolated venv under ignored `.local-test-data/s02a2/` (never globally). Start with exact documented `pypinyin`, `piper-tts`, `pathvalidate` versions/hashes and their audited dependencies; reuse installed runtime where possible. Do not install accounts or paid services. If an unrelated policy still demands explicit installation confirmation, document the exact blocker rather than mischaracterizing the model as failed.
3. Generate **real Suxin Chinese WAV files** from the five existing original Chinese sample cases using the author's normal frontend. No mock, no fake phoneme mappings, no pretrained-audio substitutions. Test mixed English separately and label if unsupported or blocked.
4. Verify actual audio WAV integrity, text/model hashes, speaker identity, startup, RTF, peak memory, real synthesized durations and failures. Record audio evidence without uploading recordings publicly.
5. Reuse the existing Matcha genuine audio and make a private same-text A/B HTML and ZIP: Matcha vs Suxin; optionally Kokoro baseline. Include sample-by-sample playable WAVs, audio provenance, no fake subjective ratings. Provide the exact local output path for owner listening. If the Suxin frontend cannot be run, give reproducible exact errors and a narrow fix; do not simply stop at load-only again.
6. If Suxin desktop audio is viable, test real native ORT graph on iOS simulator with author-generated phoneme IDs, explicitly mark `PRECOMPUTED_FRONTEND_ONLY`. Do not call it full iPhone text-to-audio without a native frontend. Distinguish desktop, simulator and real device; record measured RTF/RSS. Time-box porting.
7. Matcha remains our current working AI candidate; do not reject it due to preferences or non-I/O evidence. Real-device performance, continuous-playback prebuffer design and correct redistribution permissions remain product/shipping gates, **separate from owner listening**.
8. Do not edit production iOS reader, Xcode project, original tests, main, PR #4 or PR #5. Update the existing PR #7 with evidence and `reports/S02A3_SUXIN_MATCHA_LISTENING.md`; stop at `READY_FOR_AUDIT / OWNER_LISTENING_PENDING`. Do not merge or start S02B; do not use cloud/paid TTS or upload private novels, weights or audio to GitHub.
