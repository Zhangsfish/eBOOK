# Codex handoff — S02A.4

Read `AGENTS.md`, `STATUS.md`, `docs/PRODUCT_SPEC.md`,
`docs/TECHNICAL_PLAN.md`, and `tasks/S02A4_TEACHER_STUDENT_TTS.md` first.

## Owner's instruction

The owner delegates the architecture and training method. Deliver a voice that
the owner likes more than Suxin-Light, suitable for long Mandarin fiction and
fast offline playback in the iPhone reader. The teacher's exact voice must be
approved by the owner before bulk corpus generation or student training.
AutoDL can supply the research GPU; do not ask the owner to choose architecture.

## Work independently from the current experiment

Use a separate worktree and `codex/s02a4-teacher-student-tts`. Implement under
`tools/tts-training/` and report under
`reports/S02A4_TEACHER_STUDENT_TTS.md`. Preserve PR #7 and its ongoing S02A.3 work,
PR #4, PR #5 and production source. Do not merge or publish a release.

S02A.3 reference HEAD: `9713f7596c9f9a3b9565cfb61dd836b1b3602b5b`.
It now has real Suxin iOS simulator graph inference using author-precomputed
phoneme IDs, and a recorded short-audition preference for Suxin. It has no full
native Mandarin frontend or physical-phone acceptance. Do not repeat the stale
claim that Suxin has only loaded and never generated speech. Its final report was
not yet present at the inspected HEAD; do not declare that task finished.

## Execute this preparation milestone

The architecture is delegated, not frozen: revise the initial route from actual
evidence if needed, while preserving the owner sound gate and phone targets.
GPU rental is accepted in principle; there is no connected instance or executed
job yet. Resolve access and concrete cost when operationally necessary.

1. Resolve/pin official Qwen3-TTS 1.7B VoiceDesign/CustomVoice and
   Fun-CosyVoice3 0.5B sources. Prepare real accessible teacher auditions, clearly
   distinguishing official demos from our generated audio. Prioritize a small
   number of stable voices and the same original fiction passages. Fix voice
   identity/reference/settings. The owner judges the resulting sound.
2. Resolve the current `OHF-Voice/piper1-gpl` medium VITS training, resume and
   ONNX-export instructions. Select a compatible clean-license initialization
   from verified base checkpoints, including the documented rdh CC0 /
   hifi_tts 92 CC-BY candidates. Record exact checkpoint/card/license/hash and
   any phoneme-map adaptation; do not pretend incompatible state-dict loading is
   a working recipe. Do not fine-tune an inference-only Suxin ONNX file.
3. Prepare a new isolated environment and AutoDL pilot runbook for a single
   RTX 4090 24 GB. Pin dependencies after checking the actual official recipe.
   Include environment/VRAM/storage preflight, short throughput probe,
   resumable checkpoints, export and inference comparison. No GPU has been
   provisioned by this handoff. Do not create accounts, rent an instance or
   report a training run without actual access and execution.
4. Build original Mandarin fiction and pronunciation fixtures. Split at scene
   level before generation; keep final listening passages out of student
   training and model selection. Add a manifest schema for text/audio hashes,
   fixed voice, teacher revision/settings, split, duration and provenance.
   Keep private novels and external reader audio out of the training path.
5. Prepare synthesis-quality filtering and private A/B packaging. Check
   omissions/repetition, silence, clipping, duration and speaker consistency;
   ASR does not assess naturalness. Retain original audio. Provide final
   student/teacher/Suxin comparison on unseen identical text and a 10–15 minute
   coherent owner listen when actual student audio exists.
6. Prepare the deployment proof: standard ONNX Runtime plus native Mandarin
   normalization/phonemes, incremental first audio, bounded prefetch/cache,
   cancellation and stable reading-position mapping. Verify training/frontend
   parity and ONNX operators early. Do not bundle the full Piper/Python runtime
   into iOS by default. Record exact training/model/data/runtime licenses;
   runtime separation alone does not establish distribution clearance.

Do all independent preparation now. The owner approving a teacher voice is a
real requirement; do not invent approval or generate hours of training audio
before it. Once that approval and an authorized accessible GPU exist, proceed
with a small real train/resume/export pilot before scaling the dataset. Use its
measured cost/throughput and listening result to decide the next implementation
step. Missing GPU/device access should produce a precise factual blocker after
the useful preparation is finished, not another architecture questionnaire.

## Preserve these acceptance criteria

These are targets, not results:

- Ready-model play: actual first audible output p95 ≤1 s.
- Fresh app/process: actual first audible output ≤3 s including initialization;
  model installation/download is measured separately.
- Uncached jump: actual first audible output p95 ≤1.5 s, no stale queued speech.
- 30 minutes of real playback at both 1.0× and 1.5×: no synthesis-buffer
  underflow, dropped/repeated content or unintended gaps.
- Aim for per-chunk generation RTF p95 ≤0.5 at normal rate, but judge continuity
  by actual output cadence and buffer traces rather than average RTF alone.
- Measure on an identified physical iPhone; capture memory/thermal/battery
  behavior, UI responsiveness, lock-screen/background operation, interruption,
  audio-route changes and position restoration. No model callback or simulator
  timing may substitute for the phone's first audible output.
- Owner prefers the student to Suxin on held-out same-text short and long audio.

The final product is a selectable voice in the owner's internal TestFlight
reader plus checkpoint, ONNX, native frontend/player, reproducible training and
provenance/measurement evidence. App integration and TestFlight packaging belong
in a subsequent reviewable change after the prototype earns its listening and
device evidence; this preparation PR must not claim that outcome already exists.

## Handoff back

Give the owner a direct, working audition entry and only the sound decision they
need to make. Report source pins, what actually executed, exact tested HEAD,
tests that resolve real risks, and precise remaining access/approval facts.
Keep generated audio, weights and datasets out of Git and CI artifacts. Open a
reviewable PR, mark `READY_FOR_AUDIT`, and leave merge to the owner. Do not claim
that a written runbook, official demo, prepared job or uploaded task started
training automatically.
