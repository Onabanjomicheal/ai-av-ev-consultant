"""
Quick CLI to test retrieval quality before connecting to the LLM.
Run: python scripts/test_retrieval.py "What is SAE Level 4 autonomy?"
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv
load_dotenv()

from api.services.rag import retrieve, RAGSettings


def main():
    question = " ".join(sys.argv[1:]) or "What is SAE Level 4 autonomy?"
    print(f"\nQuery: {question}\n{'─'*60}")
    chunks = retrieve(question, RAGSettings())
    if not chunks:
        print("No results. Make sure the vector store is built (run ingest_docs.py).")
        return
    for i, c in enumerate(chunks, 1):
        print(f"\n[{i}] Source: {c['source']}")
        print(c["content"][:400])


if __name__ == "__main__":
    main()
