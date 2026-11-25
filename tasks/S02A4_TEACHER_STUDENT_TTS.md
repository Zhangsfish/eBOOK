# S02A.4 — Owner-approved teacher to fast offline novel speech

State: **READY — teacher audition and reproducible training preparation**.

Owner direction, 2026-11-25: the owner judges the sound; the implementer chooses
the architecture, training method and compute. The final result must sound better
than Suxin-Light to the owner and run promptly and continuously on an actual
iPhone in our novel reader. AutoDL rental is available for the research. Do not
turn architecture choices back into questions for the owner.

## Scope and working branch

- Use a new task branch, `codex/s02a4-teacher-student-tts`, and a separate worktree.
  Read root `AGENTS.md`, `STATUS.md`, `docs/PRODUCT_SPEC.md`,
  `docs/TECHNICAL_PLAN.md` and this task before implementation.
- Put training and audition tooling under `tools/tts-training/`, with a scoped
  `AGENTS.md`; put measured results in `reports/S02A4_TEACHER_STUDENT_TTS.md`.
- Preserve PR #7 and its active S02A.3 executor. Its inspected reference HEAD is
  `9713f7596c9f9a3b9565cfb61dd836b1b3602b5b`; do not claim that S02A.3 is fully
  delivered. Do not overwrite its task, generated audio or unfinished report.
- Preserve the reader work in PR #5, the S01 work in PR #4 and all unrelated
  changes. Do not merge, deploy a production service or publish to the App Store.
- This phase prepares audition, training, export and validation. Later prototype
  execution follows the owner's actual teacher approval and access to an
  authorized GPU environment; later app integration is a separate reviewable
  change against the current reader branch. Do not mix it into PR #7.

## Technical decision owned by the implementer

These are initial engineering choices, not owner-imposed architectures. Revise
them when measured quality, reproducibility or phone performance warrants it,
without asking the owner to choose technical components. The sound approval and
product acceptance targets remain binding.

1. **Teachers:** start with Qwen3-TTS 1.7B VoiceDesign/CustomVoice and
   Fun-CosyVoice3 0.5B. Use the actual published checkpoint, not an unreleased
   larger version's demo. Official samples are useful for initial screening;
   approval must ultimately identify a reproducible, fixed voice reading our
   original material. Qwen Base may preserve an approved designed voice through
   a fixed generated reference; record its provenance and exact recipe.
2. **Student:** use the maintained Piper medium VITS training/export workflow
   from `OHF-Voice/piper1-gpl`, with a Mandarin frontend that can be reproduced in
   native iOS code. Train from teacher-generated text/audio pairs. Do not assume
   Suxin's inference-only ONNX is a trainable checkpoint or that its custom
   SuxinVoc architecture is publicly reproducible.
3. **Initialization:** verify the available clean-license base checkpoints,
   including the documented rdh CC0 and hifi_tts 92 CC-BY options, before choosing
   the concrete initialization. Pin source, model card, license and checksum.
   Verify phoneme vocabulary, sampling rate, speaker conditioning and tensor
   compatibility. Record any intentional vocabulary adaptation. A partial load
   that silently drops most weights is not a successful fine-tune. Do not use
   Matcha zh-baker's training-data uncertainty as the basis of our new model.
4. **Phone runtime:** exported ONNX plus standard ONNX Runtime and our native
   Mandarin normalization/phoneme frontend. No full Piper/Python runtime is
   planned inside the phone app. Verify operator support and numerical/audio
   parity early; this design choice is not evidence that compatibility already
   passed. GPL training-code obligations, checkpoint/data terms and distributed
   runtime notices remain distinct; do not claim blanket license clearance from
   the runtime choice alone.
5. **Compute candidate:** one AutoDL RTX 4090 with 24 GB VRAM for a controlled
   pilot. This is a proposed configuration, not a provisioned instance or a
   measured capacity promise. Establish actual batch size, peak VRAM, storage,
   throughput and projected run cost with a short probe. Use an isolated pinned
   environment; preserve resumable checkpoints. The owner has accepted
   GPU rental as the compute route. No account connection, running instance or
   concrete billable job exists yet; resolve those operational facts when needed
   rather than asking the owner to choose the architecture again.

Primary implementation sources: https://github.com/QwenLM/Qwen3-TTS,
https://github.com/QwenAudio/CosyVoice,
https://github.com/OHF-Voice/piper1-gpl and the exact model cards selected during
preparation. Resolve current immutable revisions and concrete commands; do not
leave an untested generic installation recipe as a completed deliverable.

## Owner-selected first target voice: MOSS-TTS-Nano zh_6 (2026-11-25)

**Owner listening feedback:** The owner listened to the actual ~2m30s demo audio titled **「🇨🇳 深夜温柔晚安」** and said **「这个可以」**. This is a positive, explicit acceptance of that particular demo voice/tone as the **first target sound**. The preceding Qwen fixed voices and dramatic-stage demos are not the selection. Do not ask the owner to shortlist teachers again, or replace this voice with an arbitrary generic "gentle female" preset.

**Exact upstream provenance (source-resolved, not freshly synthesized in eBOOK):**
- Official model repository: `OpenMOSS/MOSS-TTS-Nano`, inspected revision `8b7bcc9341b3b4ef3a3a58ba1338a7d85ff133eb`.
- Official demo repository: `OpenMOSS/MOSS-TTS-Nano-Demo`, inspected revision `72c080d4dcf8847fa68b86c67c61ae42ec754fb3`.
- Official demo metadata: `assets/metadata.jsonl`, selected entry `🇨🇳 深夜温柔晚安`, whose `prompt_speech` is `audio/zh_6.wav`. Preserve the metadata's exact text and prompt mapping.
- Reference audio: `assets/audio/zh_6.wav`, Git blob SHA `1cb86e2050c71b0d07b14963d59e5676f55b5e36`, 837,198 bytes. The official model and demo repositories expose the **same blob**.
- Owner-approved demo output: `assets/🇨🇳 深夜温柔晚安.wav` in demo repo, Git blob SHA `f3279b7bc387ed7a09cc64ec0d457c976b9cc53c`, 28,830,798 bytes. This is an **upstream showcase**, not a result generated or tested by our code.
- Official model/ONNX weight cards and repository indicate Apache-2.0 for code/model weights, voice cloning with one reference audio, streaming ONNX CPU inference, and an actual `finetuning/README_zh.md` pipeline with `prepare_data.py` + `sft.py` + `verify.py`. This establishes a mature route for an experiment, **not** proof of iOS performance or reference-voice speaker-rights clearance.

**Immediate priority: faithfully reproduce the selected voice on fiction.** Use the pinned model, pinned `zh_6.wav` reference, and the six pre-existing original fiction scenes in `tools/tts-training/fixtures/teacher_audition.json`. Keep at least one coherent ~2–5-minute single-voice narration sample including normal narration, dialogue and restrained suspense. Generate actual WAV with the upstream reference-conditioned `voice_clone` path, first in original PyTorch implementation then, if feasible, compare to the official ONNX CPU export. Pin source revisions, model and tokenizer SHA, reference SHA, generation settings, duration, content fidelity, WER/CER as a *filter not a quality grade*, pauses, clipping and voice drift. Do not substitute the older official soothing prose for newly generated fiction or call a generic TTS voice a match.

**Choose minimal working route before distilling:** This selected teacher is already around 100M TTS parameters plus ~20M codec. Test direct-use/ONNX streaming and actual iPhone feasibility *before* spending AutoDL time distilling a new student. If it meets owner sound and iPhone performance requirements with the same voice, direct deployment or modest SFT is preferable. If direct inference is too slow/heavy, then choose and train a compatible smaller student with a real reproducible code/export path; architecture remains the implementer's responsibility, not the owner's.

**Approval gates:** The owner has accepted this *demo's sound*. Do not silently upgrade that to acceptance of arbitrary re-synthesis or a commercial distribution license. Reproduced fiction must retain its tone and timbre; owner feedback on the real generated fiction is the next subjective gate, before batch teacher-data generation. The reference recording's speaker/recording and permissible commercial voice-reproduction/redistribution rights must be explicitly established before shipping a model trained on, conditioned on, or packaged with it. Root Apache-2.0 model/code notices do not automatically decide voice/personality and recording rights.

**No repeated teacher hunt.** Investigate an alternative teacher only if this exact same-voice reproduction objectively fails or the owner rejects the actual fiction audio. Preserve prior Suxin comparison/PR #7; do not conflate preference for the demo with proof a novel-length student is already delivered.

## First delivery: the owner can actually choose a teacher voice

## New owner audition feedback: narration restraint versus dramatic demo

The owner listened to the public official fiction/dramatic demonstration and judged the **model's expressive technical ability positively**. However, its high-emotion delivery may sound like a stage speech, public announcement or dramatic monologue rather than a book narrator. The three short single-voice fixed presets were considered ordinary. **This is not teacher-voice approval.**

For teacher audition and student-data generation, favor **restrained long-form audiobook narration**:
- One stable, recognizable narrator timbre across entire paragraphs and chapters. Do not use the demo's multi-character voice switching or extreme character imitation as a default training target.
- Neutral-to-gentle baseline: intimate, conversational, clear, unhurried; natural syntactic phrasing, emphasis only on meaning-bearing words, no excessive rhetorical rises/falls, proclamatory projection or breathy affectation.
- Emotion follows the story **subtly**, especially suspense, sadness and dialogue. A single narrator may slightly vary speech rhythm and intonation for a character, but must not turn each sentence into a performance.
- Preserve pauses between sentences and paragraphs while avoiding slow/robotic monotonous delivery. Aim for continuous 10–15-minute fatigue resistance, not a ten-second spectacular showcase.
- Keep **timbre** and **delivery style** as distinct controllable variables. First test the same fixed teacher voice reading identical quiet narration/dialogue/suspense in (A) neutral-natural and (B) restrained expressive styles. The owner chooses both the underlying sound and actual narration style. All teacher audio must be newly generated from original text and clearly labelled, never infer approval from official pre-recorded samples.
- Prefer 2–5 minute coherent single-speaker clips before teacher approval; after shortlist, compare 10–15-minute coherent narration. Include anti-pattern examples (speech-like proclamation, commercial announcer, audiobook overacting) as rejected targets. Do not create student training data until an exact teacher + style is explicitly approved.

Use these criteria for the owner-listening rubric; do not treat a highly theatrical demo as a proven single-voice audiobook teacher.

Produce a small private listening package, with real playable audio, a plain
description of each fixed voice and precise provenance. Include quiet narration,
dialogue, tension, emotional restraint, numbers, names and polyphones. Use the
same original passages across candidates where generation is available. Preserve
the original audio; if loudness-matched copies are useful, label the processing
and retain the originals.

Official pre-recorded demos must be labelled as such. They do not prove our
chosen voice, text, consistency or phone performance. Do not present a demo link
as newly generated audio. The decisive audition consists of our fixed passages
and a longer coherent passage in the exact selected voice. Ask only for the
owner's sound judgment when the actual audio is accessible; do not ask the owner
to choose VITS, parameter counts or GPU settings.

Record approval against teacher model/revision, voice identity, reference audio
hash where used, prompt/settings and audition audio hashes. Until that actual
voice is approved, **do not bulk-generate its corpus or train a student**. Recipe
validation and environment preparation can proceed independently. If the owner
rejects a voice, revise the voice or teacher; do not overrule the judgment using
benchmarks.

## Verified initial listening access

The 2026-11-25 preparation checked official source HTML and HTTP/WAV metadata.
These are upstream demo clips, not new synthesis, a teacher approval, or mobile
performance evidence. Keep them as links, not student training recordings.

- Qwen official article: https://qwen.ai/blog?id=qwen3tts-0115
- Serena / A, 4.88 s: https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-TTS-0115/F05.wav
- Vivian / B, 5.36 s: https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-TTS-0115/F062.wav
- Uncle_Fu / C, 5.92 s: https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-TTS-0115/aopeng@m22.wav
- CosyVoice official 0.5B demo column: https://qwenaudio.github.io/cosyvoice3/

A new original-text request to the official Qwen public Space returned an SSE
error with null details and no audio. Its cause was not established. Do not
claim a new common-text audition was generated in this preparation. Use an
accessible authorized GPU for that milestone; do not fabricate a fallback WAV.

## Training data and prototype sequence

1. Prepare original synthetic Mandarin fiction and targeted pronunciation cases.
   Do not read, upload or train on the owner's private novels or extract reader
   services' audio. Keep speaker identity and normal narration style consistent.
   Avoid contradictory renditions of identical text without an explicit,
   reproducible style-conditioning scheme.
2. Split training, validation and final listening material before generation.
   Keep whole scenes and near-duplicate sentences in one split. Hold out final
   comparison passages from student training and hyperparameter selection.
   Track text hashes, teacher settings, audio hashes, duration and provenance in
   manifests; keep audio/checkpoints outside Git and CI artifacts.
3. After voice approval and GPU access, generate a small pilot before scaling.
   Verify transcription alignment, omitted/repeated words, silence, clipping,
   duration outliers and speaker drift. ASR is a filtering aid; it cannot award
   naturalness, expressivity or owner approval. Audit samples by listening.
4. Run a short real train/resume/export cycle first. Verify checkpoint recovery,
   finite losses, representative ONNX inputs, native operator support and
   teacher/student frontend consistency. Then train the controlled audio pilot.
   Use measured pilot throughput and quality to determine expansion, not an
   invented promise that a fixed number of hours guarantees success.
5. Compare the trained student, approved teacher and pinned Suxin baseline on
   unseen same-text passages. Give the owner a short A/B audition and a coherent
   10–15 minute listen. Preserve all actual feedback. Expand or revise the model
   if it does not improve on Suxin to the owner's ear.
6. Build early-audio playback, bounded synthesis prefetch/cache and cancellation.
   Generate and play incrementally while preserving punctuation and phrasing;
   do not wait for an entire chapter or mask insufficient throughput by
   pre-generating the whole evaluation session.

## Phone acceptance targets — design requirements, not measured results

The actual target iPhone is not yet identified. Record its model, iOS version,
build, audio route, power mode and thermal conditions when a device path becomes
available. Simulator/desktop observations cannot fill the device result fields.

| User-facing behavior | Target and evidence |
| --- | --- |
| Play with model already ready | First audible output p95 ≤1.0 s from the user's play action |
| Fresh app/process, uncached audio | First audible output ≤3.0 s, including model/frontend/audio-session initialization; exclude model installation/download |
| Jump to an uncached location | First audible output p95 ≤1.5 s; cancelling the old request must not play stale speech |
| Continuous listening | 30 minutes at 1.0× and 1.5×, no synthesis-buffer underflow, duplicated/dropped text or unintended gap |
| Synthesis headroom | Aim for per-chunk generation RTF p95 ≤0.5 at normal speech rate; report distribution and tails, not only an average |
| Practical phone use | UI remains responsive; lock-screen/background playback, pause/resume, interruptions and audio-route changes preserve position |
| Sound | Owner prefers the actual student over Suxin and accepts the longer listening sample |

RTF alone is not the playback pass criterion. Measure actual buffer occupancy,
output cadence and underflows, including at 1.5×. Distinguish natural punctuation
pauses from buffer starvation. Report memory, battery and thermal changes and
test under representative ordinary use, not only an idle simulator. Record
sample counts and the percentile method. Measure first audible output at the
real device playback boundary with documented output-latency validation or an
external recording; a model callback or WAV-generation timestamp is insufficient.

## Final delivery and honest state reporting

The eventual deliverable is a selectable voice in the owner's internal TestFlight
reader, with the trained checkpoint, exported ONNX, native frontend/player,
reproducible training/export recipe, artifact/license provenance, owner listening
results and physical-device measurements. A downloadable model or notebook alone
does not satisfy the product goal.

For this preparation milestone, deliver the real audition access, resolved
training/export recipe, pinned dependency/source plan, original text splits,
AutoDL pilot commands and a concise report of what actually ran. Separate
`PREPARED`, `EXECUTED`, `OWNER_APPROVED` and `DEVICE_VERIFIED`. If GPU, signing or
device access is absent, state the exact missing access without inventing a run
or asking the owner to solve the architecture. Complete all independent work
first. Open a reviewable PR with exact tested HEAD and evidence, then stop at
`READY_FOR_AUDIT`; do not merge or claim the final voice is already delivered.
