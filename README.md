# AV/EV Consultant Assistant

AI-powered consultant for Autonomous Vehicle and Electric Vehicle practitioners and policy makers.

## Stack
| Layer | Tech |
|---|---|
| Frontend | Streamlit + Plotly |
| Backend | FastAPI + Uvicorn |
| LLM | Groq API / Ollama (local) / Claude API |
| RAG | LangChain + ChromaDB |
| Embeddings | HuggingFace all-MiniLM-L6-v2 |
| Memory | Upstash Redis |
| Database | Supabase (PostgreSQL) |
| Deploy | Streamlit Cloud + Render.com |

## Quick start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
cp .env.example .env   # fill in your keys

# If responses feel slow, prefer Groq:
# LLM_PROVIDER=groq
# LLM_MODEL=llama-3.1-8b-instant

# 3. Add AV/EV documents to data/raw_docs/av/ and data/raw_docs/ev/
# 4. Ingest
python scripts/ingest_docs.py

# 5. Run API (terminal 1)
uvicorn api.main:app --reload --port 8000

# 6. Run frontend (terminal 2)
streamlit run frontend/app.py
```

## Tests
```bash
make test
```

## Local Streamlit Testing
Run the API and Streamlit locally (two terminals):
```bash
uvicorn api.main:app --reload --port 8000
streamlit run frontend/app.py
```
The frontend reads `API_BASE_URL` (defaults to `http://localhost:8000`).

## Deploy
- **Frontend (Streamlit Cloud)**:
  - Main file: `frontend/app.py`
  - Secrets: `API_BASE_URL = "https://<your-render-service>.onrender.com"`
  - Python: set 3.11 in Streamlit settings or add `runtime.txt` with `python-3.11`
- **Backend (Render)**: Push to GitHub → connect to Render.com, use `deploy/render.yaml`
  - Free tier memory is limited (e.g., 512 MB). Keep `RERANK_ENABLED=false`
    and use smaller retrieval settings (`RETRIEVAL_K`, `RERANK_TOP_N`) if needed.
