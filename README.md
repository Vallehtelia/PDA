# Orja (terminal-first voice assistant foundation)

Minimal terminal MVP for the "orja" assistant with wake phrase `hei orja`. Audio, cloud LLM, and timers are placeholders; everything runs in text.

## Quick start (Raspberry Pi, Python 3.11+)
1) `cd /home/ylivoittamaton/PDA`
2) `source .venv/bin/activate`
3) `pip install -r requirements.txt`
4) `python -m orja`

## Usage
- Start commands with the wake phrase: `hei orja ...`
- Examples:
  - `hei orja aika`
  - `hei orja apua`
  - `hei orja ajastin 5 min`
  - `hei orja timer 10 min`
  - `hei orja kerro vitsi`

## Skills
- `aika`/`time`: current local time (Europe/Helsinki).
- `apua`/`help`: shows skill list and wake phrase reminder.
- `ajastin`/`timer`: sets a placeholder timer response.
- Anything else: handled by local placeholder LLM with short Finnish replies.

## Data and logs
- SQLite memory: `data/orja.sqlite` (auto-created).
- Logs: `logs/orja.log` (auto-created, also printed to terminal).
- Config: `config/config.yaml` (auto-created with defaults; env vars prefixed `ORJA_` override top-level keys).

## Checklist to verify
- Virtualenv active and deps installed.
- `python -m orja` starts and prints wake phrase hint.
- Typing `aika`, `apua`, `ajastin` commands prefixed by `hei orja` returns expected responses.
- Non-wake input is ignored or hints once.
- `data/orja.sqlite` and `logs/orja.log` appear after first run.

