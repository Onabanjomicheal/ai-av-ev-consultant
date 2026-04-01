"""
Seeds Supabase with initial tables and sample query log.
Run: python scripts/seed_db.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv
load_dotenv()
from api.services.database import get_db

SQL = """
create table if not exists query_logs (
    id          uuid primary key default gen_random_uuid(),
    session_id  text not null,
    question    text not null,
    answer      text,
    sources     text[],
    created_at  timestamptz default now()
);
"""


def main():
    db = get_db()
    if db is None:
        print("Supabase not configured. Set SUPABASE_URL and SUPABASE_KEY in .env")
        return
    db.rpc("query", {"query": SQL}).execute()
    print("Database seeded.")


if __name__ == "__main__":
    main()
