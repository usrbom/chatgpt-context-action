# Prototype — ChatGPT Life OS Contextual Action Engine

See `docs/source_of_truth.md` for the full spec.

## Requirements

- Python 3.11+
- Node.js 18+

## Install

```bash
# Backend
cd prototype/backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

## Seed

Populate the SQLite store with the demo user's behavioral history:

```bash
cd prototype/backend
python seed.py
```

Expected output:
```
Seeded 15 restaurant history records for demo_user_01
Database: .../prototype/backend/data.db
```

## Run

```bash
# Terminal 1 — backend
cd prototype/backend
uvicorn main:app --reload

# Terminal 2 — frontend
cd prototype/frontend
npm run dev
```

Open http://localhost:5173

## Demo flow

1. Type: **"Book me a table for 2 at an Italian place in River North tonight"**
2. Agent collects any missing details (date, etc.)
3. Agent surfaces Piccolo Sogno and RPM Italian (ranked from behavioral history)
4. Select a restaurant
5. Agent shows a confirmation card — confirm to book
6. Agent collects name + phone, completes the booking
7. Booking confirmation appears in chat

### Privacy commands
- **"What do you know about me?"** — shows all behavioral patterns
- **"Forget everything"** — deletes all history for the demo user

## Run eval (dining prompts only)

```bash
cd prototype/backend
python eval_runner.py
```

Scores D1 (tool selection), D2 (parameter accuracy), D4 (history grounding), D6 (adversarial refusal) across 60 dining prompts. Results are written back to `appendix/eval/dataset.json`. D5 (ranking coherence) requires human review.

## Entrypoints

| File | Purpose |
|---|---|
| `backend/main.py` | FastAPI app — POST /chat, POST /reset, GET /health |
| `backend/agent.py` | Claude tool-use agent loop |
| `backend/tools.py` | Tool implementations |
| `backend/db.py` | SQLite operations |
| `backend/mock_api.py` | Mocked restaurant search and booking |
| `backend/seed.py` | One-command database seeding |
| `backend/eval_runner.py` | Eval script (dining, 60 prompts) |
| `frontend/src/App.jsx` | React chat UI |
