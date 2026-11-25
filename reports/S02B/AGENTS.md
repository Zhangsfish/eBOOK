# S02B integration evidence

Purpose: first-release local Suxin integration on branch codex/s02b-suxin-ios-integration.
Authority: tasks/S02B_SUXIN_IOS_INTEGRATION.md and docs/TTS_WORKSTREAMS.md.
Report: ../S02B_SUXIN_IOS_INTEGRATION.md. evidence/ contains only sanitized small
JSON/log metadata. Raw audio, models and private inputs never enter this folder.
Record exact tested implementation SHA, CI URL and Windows/simulator/iPhone states
separately. First-audible targets are NOT_RUN until actually measured, and a mixer
callback is not a physical acoustic measurement. Independent review precedes the
new internal TestFlight upload; never self-merge or start the training workstream.
