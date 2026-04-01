# AV/EV Consultant Assistant

AI-powered consultant for Autonomous Vehicle and Electric Vehicle practitioners and policy makers.

## Stack
| Layer | Tech |
|---|---|
| Frontend | Streamlit + Plotly |
| Backend | FastAPI + Uvicorn |
| LLM | Ollama (local) / Claude API |
| RAG | LangChain + ChromaDB + FAISS |
| Embeddings | HuggingFace all-MiniLM-L6-v2 |
| Memory | Upstash Redis |
| Database | Supabase (PostgreSQL) |
| Deploy | Streamlit Cloud + Render.com |

## Quick start

```bash
# 1. Install
make install

# 2. Configure
cp .env.example .env   # fill in your keys

# 3. Add AV/EV documents to data/raw_docs/av/ and data/raw_docs/ev/
# 4. Ingest
make ingest

# 5. Run API (terminal 1)
make api

# 6. Run frontend (terminal 2)
make frontend
```

## Tests
```bash
make test
```

## Deploy
- **Frontend**: Push to GitHub → connect to Streamlit Community Cloud
- **Backend**: Push to GitHub → connect to Render.com, use `deploy/render.yaml`
