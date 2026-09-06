# Knowledge Ladder

> A local-first algorithm problem-dissection tool: asks one question at a time and converges to four directions using information gain. Includes a PySide6 desktop app and a Capacitor/PWA mobile app.

[中文](README.md) | **English**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Introduction

Knowledge Ladder is a "problem dissection" exercise for algorithm learning. It does not give answers directly. Instead, it selects the next question with the highest information gain based on your answers, gradually narrowing uncertainty toward one of four directions.

- **Desktop (Python / PySide6)**: 8-tier knowledge ladder, reflection log, growth statistics, and wallpapers.
- **Mobile (PWA / APK)**: dynamic entropy-reduction dissection with a minimal question flow, fully offline.
- **Local-first**: no remote API, no LLM, no analytics at runtime; only a JSON state machine and `log2` calculations.

## Features

### Mobile

- Single question flow: yes / no / uncertain / "this feels wrong".
- Automatically asks the highest-information-gain unanswered question each step.
- Shows a dynamic hint after each answer, mapping the current question and your response to a deeper structural understanding—not repeated boilerplate.
- Lists directions by computed probability on the final page; each detail shows a one-sentence hint and a deeper hint.
- Candidate pool comes from 120 local algorithms; initial weights come from public statistics.
- Supports Editorial and Glass themes.
- Fully offline; no external fonts or third-party resources.

### Desktop

- 8-tier knowledge ladder as the default main view, with Review, Reflection, and Statistics entries.
- 127 algorithm cards: one-sentence essence, problem-sensing signals, complexity, C++ templates; classified as Core / Common / Familiarize, with placeholder cards explicitly marked as "framework".
- Wallpapers: images, GIFs, videos with a glassmorphism overlay.
- Reflection notebook: record insights, algorithm cards viewed that day, and mark items for expert review.
- Growth statistics: knowledge coverage, weekly quantitative summary, 14-day trend, algorithm card intake.
- Windows portable build via `build_windows.bat`.

## Algorithm and Data

The dissection process is based on information theory:

- Maintains a candidate pool of 120 local algorithms.
- Orders questions by information gain, similar to Wordle guessing.
- Treats "uncertain" as weak evidence, not strong evidence.
- Converges when pool entropy falls below a threshold, information gain falls below a threshold, or the question limit is reached.

Data sources (public APIs cleaned into local static JSON):

- Codeforces: tags, ratings, combined statistics.
- DMOJ: 21 algorithm categories and problem ratings.
- AtCoder Problems: difficulty-curve cross-validation.

## Quick Start

### Mobile Web Preview

```bash
cd mobile
./serve.sh
```

Open `http://localhost:8000`.

### Android APK

Pushing to `main` triggers a GitHub Actions APK build. To build locally:

```bash
cd mobile
npm install
npx cap add android
npx cap sync android
cd android && ./gradlew assembleDebug
```

### Desktop

```bash
python -m pip install -r requirements.txt
python main.py
```

If a virtual environment already exists in the repo:

```bash
./.venv/bin/python main.py
```

Windows portable build:

```bat
build_windows.bat
```

## Documentation

- [System design](docs/system-design.md)
- [Editorial theme](docs/style-parallax-editorial.md)
- [Validation and release](VALIDATION.md)
- [Release notes](RELEASE_NOTES.md)

## Project Layout

```text
entropy_engine.py            # desktop entropy engine
info_framework.py            # information-theory labels
knowledge_data.py            # 120-algorithm registry
tiers_data.py                # 8-tier difficulty data
export_mobile_data.py        # mobile data generator
app/                         # PySide6 desktop modules
mobile/                      # PWA + Capacitor mobile app
expert_content/              # versioned expert direction content
scripts/                     # data validation, engine parity, release tooling
tests/                       # Python + JS tests
docs/                        # long-form documentation
```

See [AGENTS.md](AGENTS.md) for the complete module map.

## Development and Verification

```bash
python -m unittest discover -s tests -v
ruff check .
mypy --ignore-missing-imports entropy_engine.py info_framework.py knowledge_data.py \
  tiers_data.py export_mobile_data.py app/teacher_consensus.py
python scripts/check_data_schema.py
python export_mobile_data.py
python scripts/engine_parity.py
```

## Privacy and Offline Promise

- No remote API, LLM, or analytics at runtime.
- The mobile app does not load external fonts or third-party resources.
- Local progress is stored in the system data directory, not in the repository.
- Internal files such as `docs/`, `reports/`, `preview/`, and `系统提示词.txt` are ignored by `.gitignore` and must not be committed.
- Do not include personal paths, secrets, or real account information in public issues or pull requests.

## Contributing

Issues and pull requests are welcome. When changing machine behavior, update both the Python engine and the mobile JS engine together, and add or update tests.

- Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
- Security and privacy reporting: [SECURITY.md](SECURITY.md)
- Community guidelines: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

## License

[MIT](LICENSE)
