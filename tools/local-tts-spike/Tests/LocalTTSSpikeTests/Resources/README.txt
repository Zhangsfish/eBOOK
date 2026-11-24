Only original synthetic fixtures belong here.
scripts/run_ios.py stages a fresh package under ignored .local-test-data/s02a/,
copies the verified model to Resources/kokoro/ in that staging directory, and
adds corpus.json, model.json and run-context.json. No model is committed here.
Missing assets must FAIL the inference test, never silently skip it.
