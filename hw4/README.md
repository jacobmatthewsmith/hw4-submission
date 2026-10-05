# Campus Customs: AI Foundations HW 4

A storefront for **Campus Customs**, a fictional Yale-merch shop, with an AI shopping assistant called **BulldogBot**.

- **Frontend:** React + Vite + TypeScript.
- **Backend:** FastAPI.
- **Agent:** Pydantic AI, using OpenAI `gpt-5.6-sol` through Portkey.

Shoppers can browse products, create an account and log in, keep a saved bag, check out, and chat about merch. The chat answers honestly about price and stock from the database and puts matching products on the page.

Full technical documentation is in [`output/harness.md`](output/harness.md).

---

## 1. Place the local data pack

The database and product images are **not in this repo**: they're excluded by `.gitignore`. Copy your local data pack into `hw4/data/` so the layout looks like this:

```
hw4/
├── data/                       ← create this folder (not tracked by git)
│   ├── campus_customs.db       ← SQLite DB: catalogue, inventory, users, chat_messages
│   └── products/               ← product images referenced by catalogue.image_file_path
│       ├── basic-hoodie-big-yale.jpg
│       └── …
├── backend/
├── frontend/
└── …
```

If you have the provided `data.zip`, unzip it inside `hw4/`. It already contains the `data/` folder:

```bash
cd hw4
unzip /path/to/data.zip
```

The backend reads `data/campus_customs.db` and serves `data/products/` at `/media/products/…`. On first start it adds three small tables (`cart_items`, `orders`, `order_items`) if they're missing. It never changes the provided tables' structure.

## 2. Add your API key

```bash
cd hw4
cp .env.example .env
# then edit .env:
#   PORTKEY_API_KEY=<your Portkey key>
#   SESSION_SECRET=<any long random string>
```

`.env` is gitignored. The backend also looks for `.env` up to two folders above `hw4/`, so the key can live outside the repo.

## 3. Run the backend (FastAPI, port 8000)

Requires Python 3.11+ (developed on 3.14).

```bash
cd hw4/backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r ../requirements.txt
uvicorn main:app --reload
```

The API is now at http://127.0.0.1:8000. A quick check: http://127.0.0.1:8000/api/health returns `{"status":"ok"}`.

## 4. Run the frontend (Vite, port 5173)

Requires Node 20+. Run this in a **second terminal**:

```bash
cd hw4/frontend
npm install
npm run dev
```

Open **http://localhost:5173**. The Vite dev server forwards `/api` and `/media` to the backend on port 8000, so keep both running.

**Test login:** `test@campuscustoms.yale.edu` / `password`. You can also create a new account.

## 5. Things to try

- **Chat checks stock:** open a product page, click **Chat with BulldogBot**, and ask "How many are left in XL?"
- **Chat search fills the page:** ask "Show me your hoodies". The Products page fills with matching cards, and each card opens its product page.
- **Saved bag:** add items, reload or come back later, and the bag is still there. Logging in merges a guest bag into your account.
- **Duplicate-order check:** check out, then place the identical order again within 5 minutes. You'll be asked to confirm.

---

## Repo contents

| Path | What it is |
|---|---|
| `AI_prompts.md` | Every prompt used to build the project, by problem |
| `requirements.txt` | Backend Python dependencies |
| `.env.example` | Template for the `.env` file (placeholders only) |
| `frontend/` | Vite + React + TypeScript app |
| `backend/main.py` | FastAPI app (`uvicorn main:app --reload` from `backend/`) |
| `backend/agent.py`, `tools.py`, `models.py`, `prompts/prompt.md` | The Pydantic AI agent: wiring, tools, Pydantic types, system prompt |
| `backend/auth.py`, `chat_history.py`, `store.py`, `ratelimit.py`, `audit.py`, `db.py` | Accounts, saved chat history, cart and orders, rate limits, audit trail, DB access |
| `output/harness.md` | Specs, tools, model fields, safety rules, and how it all fits together |
| `output/design.md` | Y2K Alien design rationale and before/after |
| `output/usability.md` | Why each usability improvement was added |
| `output/app_check.html` + `output/app_check_images/` | Captioned screenshots of the working app. Open the HTML locally, or run `python3 -m http.server 8099 --directory output` and visit `http://localhost:8099/app_check.html` |
| `output/audit_trail.json` | Append-only log of agent activity (tool calls and stop reasons) |
| `docs/brand_notes.md` | Brand and style research notes |

**Not committed:** `data/` (the database and product images), `.env`, `node_modules/`, `.venv/`, `dist/`.
