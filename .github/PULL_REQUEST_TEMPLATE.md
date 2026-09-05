## What changed

<!-- One or two sentences: what this PR does and why. -->

## Verification

- [ ] `python -m unittest discover -s tests -v` passes
- [ ] Desktop smoke test (offscreen or real launch) passes
- [ ] Mobile data regenerated if data files changed (`python export_mobile_data.py`)
- [ ] No secrets, local paths, or private data added
- [ ] No new network calls / telemetry

## Checklist

- I checked both Python engine and JS engine when behavior changed.
- I kept the change small and focused.
