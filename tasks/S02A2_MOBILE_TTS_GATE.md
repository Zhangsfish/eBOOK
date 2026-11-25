# S02A.2 — Mobile TTS performance and lightweight Chinese model gate

GitHub Issue: https://github.com/Zhangsfish/eBOOK/issues/9
Continue existing PR #7 branch: `codex/s02a-kokoro-ios-spike`.

## Owner decision

The owner accepts the Kokoro demo sound but considers it somewhat ordinary. Do not spend indefinitely optimizing it. Test one bounded Kokoro/CoreML + actual-iPhone path, then screen two smaller open-source alternatives. If none is both fast and acceptable, stop and ship Apple AVSpeechSynthesizer only. **No cloud TTS, no Google, no paid fallback.**

## Current public research shortlist (not yet iPhone-verified)

| Candidate | Published profile | What remains unverified |
|---|---|---|
| Kokoro v1.1 INT8 | Already has real iOS simulator inference; 215 MiB full pack; best ARM simulator weighted RTF 1.4213 | Actual iPhone performance, CoreML EP availability and operator assignment |
| Matcha zh-baker | ~73 MB acoustic model, one female voice; sherpa docs list iOS Swift example; Raspberry Pi 4 four-thread RTF 0.391 | Full package size, iPhone speed, quality and licensing |
| Suxin-Light | 28.65M VITS student; author reports RTF 0.164 on 8-core Cortex-A55; MIT model card | Custom decoder/frontend integration, iOS support, actual iPhone speed and voice quality |
| M5-TTS | 50M LM plus separate codec; author reports Xeon CPU streaming RTF 0.653 and 225 ms warm first chunk | Mobile footprint/runtime; only research/demo reference, not an S02A.2 port |

References:
- Matcha model and sizes: https://k2-fsa.github.io/sherpa/onnx/tts/pretrained_models/vits.html
- sherpa RTF table (Raspberry Pi 4): https://k2-fsa.github.io/sherpa/onnx/tts/pretrained_models/rtf.html
- Matcha Swift example: https://k2-fsa.github.io/sherpa/onnx/tts/all/Chinese-English/matcha-icefall-zh-en.html
- Suxin-Light: https://huggingface.co/TEQUILA123/suxin-light
- M5-TTS: https://github.com/ASLP-lab/M5-TTS
- ONNX Runtime CoreML EP: https://onnxruntime.ai/docs/execution-providers/CoreML-ExecutionProvider.html

These upstream benchmark numbers are not directly comparable: different hardware, model revisions, sample text, runtimes, warmup and thread counts. Reproduce with one fixed original corpus before ranking.

## Execution order

1. Kokoro: one bounded CoreML availability/provider-node-assignment test and one real-iPhone benchmark if an authorized device/signing path exists. If no iPhone can be connected or signed, record DEVICE_NOT_RUN; do not infer from a simulator.
2. Matcha zh-baker: run with the existing sherpa-onnx Swift runtime, measure full pack and quality. One speaker is acceptable for this experiment.
3. Suxin-Light: assess and, if feasible within a strict time cap, run its custom ONNX decoder/frontend. If not native-portable, document the exact blocker and keep results at desktop/ARM evidence level.
4. M5-TTS: inspect official sample and metadata only; no full iOS port, no broad research.

## Pass criteria

For a model to be considered for S02B:
- actual iPhone inference, not only desktop or simulator;
- warmed first audible output <=5 s;
- sustained weighted RTF <1; <=0.8 preferred;
- p95 chunk RTF and memory/thermal behavior acceptable;
- no unbounded memory growth during 10–15 minute playback;
- owner finds voice quality acceptable.

If Kokoro cannot meet the performance bar after the one bounded attempt, stop optimizing it. If Matcha/Suxin are too robotic or fail the iOS gate, do not ship them merely because they are smaller. Apple system speech remains the no-cost fallback and a valid final product choice.

## Output and privacy

Use only original synthetic Mandarin samples. WAVs, downloaded model files, private listening pages and logs stay under ignored `.local-test-data/`. Never commit or upload model weights, binaries, generated audio, private novel text or credentials. No cloud TTS.

Update PR #7 with `reports/S02A2_MOBILE_TTS_EVALUATION.md`, reproducible scripts, exact tested SHA, device/model/OS details, asset sizes, actual metrics, audio listening location and a GO/NO-GO conclusion. No production App source changes. Stop READY_FOR_AUDIT; do not merge or start S02B.
