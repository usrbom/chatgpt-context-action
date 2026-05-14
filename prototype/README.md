# Prototype — ChatGPT Life OS Contextual Action Engine

Working prototype. See `docs/source_of_truth.md` for the full spec.

## Install

```bash
pip install -r requirements.txt
```

No API key required — the prototype uses a rule-based mock agent.

## Seed the database

```bash
python seed.py
```

Loads 15 restaurant history records and preference signals for `demo_user_01` from `appendix/eval/user_history.json`.

## Run

```bash
python main.py
```

Then open http://localhost:8000.

## Run the eval

```bash
python eval_runner.py
```

Requires `ANTHROPIC_API_KEY`. Runs two test suites:
1. **Dataset eval** — 10 dining/normal prompts from the golden dataset. Checks D1 (tool selection), D2 (parameter accuracy), D4 (history grounding).
2. **Scripted booking eval** — 4-turn conversation asserting: (a) correct tool called, (b) history context used, (c) no booking before explicit confirmation, (d) booking logged to store.

## Entrypoints

| File | Purpose |
|---|---|
| `main.py` | FastAPI HTTP server + chat UI |
| `seed.py` | Seed SQLite from `appendix/eval/user_history.json` |
| `eval_runner.py` | Dataset + scripted booking eval |
| `agent.py` | Claude API agent loop |
| `tools.py` | Tool implementations |
| `database.py` | SQLite schema and queries |
| `mock_api.py` | Mock restaurant data (22 venues across 6 neighborhoods) |
| `static/index.html` | Chat UI |
