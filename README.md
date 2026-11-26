# DocMind

DocMind is a local-first, AI-powered PDF workspace for asking questions, generating summaries, and tracing every answer back to its source page. It is designed for an 8 GB Linux laptop: document embeddings run locally while language generation uses an explicitly selected Gemini or Groq provider.

> **Status:** Core application and Phase 5 verification are complete. The backend test suite covers upload, extraction, retrieval, chat, citations, conversations, streaming, summaries, and document deletion.

## Architecture

- **Frontend:** Next.js App Router, TypeScript, Tailwind CSS, shadcn-style components, and Lucide icons.
- **Backend:** FastAPI, Pydantic Settings, Uvicorn, and SQLite.
- **Document pipeline:** PyMuPDF, `sentence-transformers/all-MiniLM-L6-v2`, and persistent ChromaDB.
- **Inference:** Google Gemini by default, with Groq as an explicit alternative. API keys stay in the backend environment; switching providers in the chat composer takes effect without a restart.

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
pip install torch --index-url https://download.pytorch.org/whl/cpu
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

For a fresh environment at this mounted path, first run `.venv/bin/python -m pip install torch --index-url https://download.pytorch.org/whl/cpu` before the requirements command. This keeps PyTorch CPU-only and avoids large CUDA downloads.

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

The repository also includes an API flow test that uploads a generated PDF, indexes it in ChromaDB, streams an answer with a page citation, restores the saved conversation, and deletes the PDF and its vectors. From `backend/`, run `.venv/bin/python -m pytest tests/test_flow.py`, or use the backend test command above for the full suite. A live Gemini account check was performed during development; live Groq access requires your own `GROQ_API_KEY`.

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
- MiniLM downloads automatically on first upload (roughly 90 MB of model files, plus cache overhead). It is loaded once per backend process.
- Embedding work runs one document at a time to protect low-memory machines.

## Current API

- `GET /api/health` — application readiness and version
- `GET /api/settings` — safe runtime settings (never API keys)
- `PUT /api/settings` — provider, model, retrieval, and theme preferences
- `POST /api/documents/upload` — upload one to ten PDFs as multipart `files`
- `GET /api/documents` and `GET /api/documents/{id}` — list and inspect processing status
- `GET /api/documents/{id}/file` — view the saved PDF
- `DELETE /api/documents/{id}` — remove the PDF, metadata, and vectors
- `POST /api/chat` — answer a question from selected, ready documents with validated source metadata
- `POST /api/chat/stream` — stream answer text and a final citation-verified response as server-sent events
- `GET /api/conversations`, `GET /api/conversations/{id}` — list and restore saved conversations
- `POST /api/conversations`, `PATCH /api/conversations/{id}`, `DELETE /api/conversations/{id}` — create, rename, and delete conversations
- `POST /api/documents/{id}/summarize` — concise, detailed, or key takeaway summary

Files need selectable text. Encrypted, empty, corrupted, and image-only PDFs receive clear errors. The first upload downloads the MiniLM weights into the local Hugging Face cache; allow time and disk space for that one-time step. Embedding jobs run one at a time to protect an 8 GB laptop.

To chat, upload a text PDF, wait until its status is **ready**, select its checkbox in the library, and enter a question. Answers stream into the chat and are saved in SQLite with the selected documents. Source chips navigate the in-app PDF viewer to the cited page. The assistant receives only retrieved chunks from selected documents; PDF text is treated as untrusted context. If the model still cannot provide valid source markers after one correction, DocMind returns an explicit “not found” answer. Assistant Markdown is rendered safely, so any `*` formatting markers are displayed as formatting rather than raw syntax. The prompt also asks for clean prose with minimal markup.

The document library shows processing state, offers a larger click target for each ready PDF, supports selecting all ready PDFs, and has an **OK** button to return to chat. Retrieval ranks the selected documents' best matches without a fixed similarity cutoff, so broad questions can still use relevant pages. If the model omits source markers, DocMind asks it once to add citations grounded in those retrieved pages before returning the answer.

Use the sidebar to restore, rename (double-click), or delete conversations. The welcome screen offers concise, detailed, and key takeaway summaries for the first selected PDF. Long PDFs are summarized in batches and combined hierarchically to avoid sending the whole document in one request.

Provider settings are saved locally through `PUT /api/settings`; switching providers never sends content to the other service automatically. The official [Google Gen AI Python SDK](https://googleapis.github.io/python-genai/) and [Groq chat API](https://console.groq.com/docs/text-chat) are used with 30-second timeouts. Missing credentials, quotas, invalid credentials, and unavailable model IDs return clear API errors. Model access depends on the API key's account and can change.

## Repository layout

```text
backend/       FastAPI application, SQLite layer, and tests
frontend/      Next.js application
storage/       Local uploads and vector database data
AGENTS.md      Repository contribution guidance
```

## License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE).
