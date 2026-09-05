# Contributing to Knowledge Ladder

Thanks for helping improve this project. It is a small, local-first tool, so
small focused changes are preferred over large rewrites.

## Ground rules

- Keep the app **offline and private**: no analytics, telemetry, hidden
  network calls, or remote AI/API at runtime.
- Prefer **deep modules**: a simple public interface with a rich
  implementation. If deleting a layer makes the code simpler, delete it.
- Update both **desktop** (`entropy_engine.py`) and **mobile**
  (`mobile/www/entropy_engine.js`) when changing the entropy engine behavior.
- Data lives in the JSON files at the repository root; generated mobile data
  (`mobile/www/entropy_data.js`) is produced by `export_mobile_data.py`.

## Development

```bash
# Desktop
python -m pip install -r requirements.txt
python main.py

# Tests
python -m unittest discover -s tests -v

# Quality gates (also run in CI)
ruff check .
mypy --ignore-missing-imports entropy_engine.py info_framework.py knowledge_data.py \
  tiers_data.py export_mobile_data.py app/teacher_consensus.py
python scripts/check_data_schema.py
python scripts/engine_parity.py

# Regenerate mobile data after data changes
python export_mobile_data.py
```

## Pull requests

1. Work on a branch, not directly on `main`.
2. Keep changes small and explain the motivation.
3. Add or update tests when changing public behavior.
4. Never commit `.env`, API keys, local user paths, `docs/`, `reports/`,
   `preview/`, or `系统提示词.txt` — these are already ignored for privacy.
5. Before pushing, run `python -m unittest discover -s tests -v`.

## Issue labels

- `bug` — broken behavior
- `enhancement` — new feature
- `privacy` — anything touching network, data collection, or secrets
- `performance` — speed or memory improvements
