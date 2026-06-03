# Prototype — ChatGPT Life OS Contextual Action Engine

See `docs/source_of_truth.md` for the full spec.

## Requirements

- Python 3.9+
- Node.js 18+

---

## Quick start with Claude Code

If you have [Claude Code](https://claude.ai/code) installed, this is the fastest way to get running. Open a terminal in the repo root and run:

```bash
claude
```

Then type:

```
Help me set up and run this project
```

Claude will read the repo, install dependencies, create the `.env` file (it will ask for your Groq key), seed the database, and give you the exact commands to start the servers.

---

## Manual setup

Follow these steps in order if you prefer to set things up yourself.

### 1. Install backend dependencies

> These are the Python libraries the server needs — the web framework, database driver, and AI client.

```bash
cd prototype/backend
pip install -r requirements.txt
```

### 2. Add your Groq API key

> The backend calls Groq to fetch real restaurant suggestions and handle chat. Without a key it falls back to a small set of hardcoded venues — the app still works, but results won't be live. Get a free key at [console.groq.com](https://console.groq.com).

Create a file called `.env` inside `prototype/backend/`:

```
prototype/backend/.env
```

Add this line to it (replace with your actual key):

```
GROQ_API_KEY=gsk_your-key-here
```

The backend loads this file automatically on startup. Do not commit it — it is already listed in `.gitignore`.

### 3. Seed the demo database

> Loads pre-built visit history for the demo user so the app shows personalised restaurant rankings and "Your pick" badges from the first search.
>
> The repo ships with a pre-seeded `data.db` so you can skip this step on first clone. **Run it if:** `data.db` is missing, you want to reset after a demo session, or personalisation features (badges, ranked results) have stopped appearing.

```bash
cd prototype/backend
python3 seed.py
```

Expected output:
```
Seeded 15 restaurant history records for demo_user_01
Database: .../prototype/backend/data.db
```

> **Note:** `seed.py` automatically shifts all history dates to be relative to today, so the 90-day personalisation window never expires no matter when you clone the repo.

### 4. Install frontend dependencies

> Downloads the JavaScript packages the chat UI needs to run in your browser.

```bash
cd prototype/frontend
npm install
```

### 5. Start the servers

Open two terminal windows and run one command in each.

**Terminal 1 — backend**

> Starts the API server on http://localhost:8000. Keep this terminal open while using the app.

```bash
cd prototype/backend
python3 -m uvicorn main:app --reload
```

**Terminal 2 — frontend**

> Starts the chat UI. Open http://localhost:5173 in your browser once this is running.

```bash
cd prototype/frontend
npm run dev
```

Then open **http://localhost:5173**.

---

## Demo flow

1. Type: **"Book me a table for 2 at an Italian place in River North tonight"**
2. Agent collects any missing details (date, etc.)
3. Agent surfaces Piccolo Sogno and RPM Italian (ranked from your behavioral history)
4. Select a restaurant by number or name
5. Agent shows a confirmation card — confirm to book
6. Agent collects name + phone, completes the booking
7. Booking confirmation appears in chat

### Privacy commands
- **"What do you know about me?"** — shows all behavioral patterns currently influencing results
- **"Forget everything"** — permanently deletes all history for the demo user

---

## Run eval (dining prompts only)

```bash
cd prototype/backend
python3 eval_runner.py
```

Scores D1 (tool selection), D2 (parameter accuracy), D3 (recommendation relevance), D4 (history grounding), D6 (adversarial refusal) across 157 dining prompts. Results are written back to `appendix/eval/dataset.json`. D5 (ranking coherence) requires human review.

> **Eval isolation:** the eval runner uses its own database (`eval_data.db`) and never touches `data.db`. Running the eval will not affect your demo data or require a re-seed. `eval_data.db` is excluded from git.

---

## Database architecture

The app uses three data files that serve distinct purposes:

```
appendix/eval/user_history.json   ← static source of truth (never changes)
         │
         └──▶  seed.py  ──▶  prototype/backend/data.db   ← what the app reads
                    │
                    └── dates shifted to today on every run

         └──▶  eval_runner.py  ──▶  prototype/backend/eval_data.db  ← eval only, gitignored
                    │
                    └── dates frozen to 2026-05-10 for deterministic scoring
```

| File | Who writes it | Who reads it | When to regenerate |
|---|---|---|---|
| `user_history.json` | Humans (static) | `seed.py`, `eval_runner.py` | Never — it's the source of truth |
| `data.db` | `seed.py`, app bookings | App at runtime | Run `seed.py` to reset or refresh |
| `eval_data.db` | `eval_runner.py` | `eval_runner.py` | Auto-regenerated on every eval run |

**Why dates are shifted in `seed.py`:** The app ranks history venues within a 90-day window. `user_history.json` was authored on 2026-05-10 — without shifting, those dates would eventually age out and personalisation would silently stop working. `seed.py` computes the delta between the authoring date and today, and shifts all `last_visited` dates forward so the window is always fresh.

**Why eval uses a separate database:** The eval runner re-seeds with frozen dates (2026-05-10) to keep scoring deterministic. If it used `data.db`, running the eval would overwrite your demo history with stale dates. The isolated `eval_data.db` means you can run eval and demo in any order without interference.

---

## Entrypoints

| File | Purpose |
|---|---|
| `backend/main.py` | FastAPI app — POST /chat, POST /reset, GET /health |
| `backend/agent.py` | Agent logic and conversation state machine |
| `backend/tools.py` | Tool implementations (search, book, history) |
| `backend/db.py` | SQLite read/write operations |
| `backend/claude_search.py` | Live restaurant search via Groq |
| `backend/mock_api.py` | Fallback hardcoded restaurant data |
| `backend/seed.py` | Seeds `data.db` with demo history, dates shifted to today |
| `backend/eval_runner.py` | Eval script (dining, 157 prompts) — uses isolated `eval_data.db` |
| `appendix/eval/user_history.json` | Static source of truth for demo history data |
| `frontend/src/App.jsx` | React chat UI |

---

## Glossary

| Term | What it means |
|---|---|
| **Backend** | The Python server that runs the agent logic, calls Groq, and reads/writes the database |
| **Frontend** | The chat UI you see in the browser — built with React |
| **SQLite / data.db** | A lightweight database file stored locally — no separate database server needed. The app reads this at runtime. |
| **eval_data.db** | Isolated database used only by `eval_runner.py` — never affects the demo. Auto-regenerated on each eval run, not committed to git. |
| **Seed data** | A pre-built set of fake booking history in `user_history.json` used to demo personalisation features. `seed.py` writes it into `data.db` with dates shifted to today. |
| **Behavioral history** | Past restaurant bookings used to rank results — the more you've visited a place, the higher it appears |
| **Mock data** | Hardcoded fallback restaurants used when no Groq key is set |
| **RAG** | Retrieval-Augmented Generation — the technique of pulling relevant past behaviour before generating a response |
| **`.env` file** | A local config file that stores secrets like API keys — never committed to git |
