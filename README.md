# DocMind

DocMind is a local-first, AI-powered PDF workspace for asking questions, generating summaries, and tracing every answer back to its source page. It is designed for an 8 GB Linux laptop: document embeddings run locally while language generation uses an explicitly selected Gemini or Groq provider.

> **Status:** Phase 1 is complete: the FastAPI/SQLite foundation, configuration API, and responsive Next.js application shell are in place. PDF ingestion, retrieval, chat, and the viewer are implemented in later phases.

## Architecture

- **Frontend:** Next.js App Router, TypeScript, Tailwind CSS, shadcn-style components, and Lucide icons.
- **Backend:** FastAPI, Pydantic Settings, Uvicorn, and SQLite.
- **Planned RAG pipeline:** PyMuPDF, `sentence-transformers/all-MiniLM-L6-v2`, and persistent ChromaDB.
- **Inference:** Google Gemini by default, with Groq as an explicit alternative. API keys stay in the backend environment.

## Requirements

- Python 3.11 or newer
- Node.js 20.9 or newer
- npm
- A Gemini API key and/or Groq API key for later inference features

No Docker, Ollama, local chat model, or paid infrastructure is required.

## Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload
```

The backend is available at <http://localhost:8000>, with Swagger documentation at <http://localhost:8000/docs>.

Run the tests with:

```bash
cd backend
source .venv/bin/activate
pytest
```

If the repository is stored in a directory whose name contains a colon (as with this mounted `Local Disk (D:)` workspace), shell activation cannot safely add the virtual environment to `PATH`. The included `.venv` still works; invoke its tools directly instead:

```bash
cd backend
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m uvicorn app.main:app --reload
.venv/bin/python -m pytest
```

## Frontend setup

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open <http://localhost:3000>. Keep the backend running so the connection indicator can verify `/api/health`.

Useful checks:

```bash
npm run lint
npm run typecheck
npm run build
```

## Configuration

Copy `backend/.env.example` to `backend/.env` and add keys only for providers you intend to use. Never commit `.env`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `DEFAULT_LLM_PROVIDER` | `gemini` | Explicit active inference provider |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | Gemini model identifier |
| `GROQ_MODEL` | `openai/gpt-oss-20b` | Groq model identifier |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Lightweight local embedding model |
| `MAX_UPLOAD_SIZE_MB` | `20` | Upload limit used by the ingestion phase |
| `RAG_TOP_K` | `5` | Default number of retrieved chunks |

The model identifiers are configuration, not constants in provider code. The defaults were selected on November 24, 2026: Google recommends the cost-efficient `gemini-3.5-flash-lite` for new workloads, while Groq lists `openai/gpt-oss-20b` as a current production model. Provider availability and free-tier quotas can change, so check the [Gemini model/pricing documentation](https://ai.google.dev/gemini-api/docs/pricing) and [Groq supported models](https://console.groq.com/docs/models) before deployment.

## Local data and resource usage

- SQLite data is stored locally and ignored by Git.
- Uploaded PDFs and Chroma data live under `storage/` and are ignored except for directory placeholders.
- In a later phase, MiniLM downloads automatically on first use (roughly 90 MB of model files, plus cache overhead). It will be loaded once per backend process.
- Embedding work will be concurrency-limited to protect low-memory machines.

## Current API

- `GET /api/health` — application readiness and version
- `GET /api/settings` — safe runtime settings (never API keys)
- `PUT /api/settings` — provider, model, retrieval, and theme preferences

Additional document, conversation, chat, summary, and streaming routes are introduced with their corresponding working features.

## Repository layout

```text
backend/       FastAPI application, SQLite layer, and tests
frontend/      Next.js application
storage/       Local uploads and vector database data
AGENTS.md      Repository contribution guidance
```

## License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE).
