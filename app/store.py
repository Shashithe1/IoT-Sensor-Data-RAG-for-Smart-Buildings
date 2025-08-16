import os
import duckdb
import chromadb
from chromadb.config import Settings


# ---------- DuckDB (for IoT sensor readings) ----------
def get_duck():
    """
    Connect to DuckDB database (creates if not exists).
    Uses read_write mode to prevent locking issues.
    """
    os.makedirs("data", exist_ok=True)
    con = duckdb.connect("data/iot.duckdb", read_only=False)
    return con


def init_duck(con):
    """Initialize table for IoT sensor readings if not exists."""
    con.execute("""
    CREATE TABLE IF NOT EXISTS readings(
        ts TIMESTAMP,
        building TEXT,
        sensor_id TEXT,
        metric TEXT,
        value DOUBLE
    );
    """)
    return con


# ---------- Chroma (for RAG document storage) ----------
def get_vector_client():
    """Return Chroma client (persisted locally)."""
    os.makedirs("chroma_db", exist_ok=True)
    client = chromadb.Client(Settings(
        persist_directory="chroma_db"
    ))
    return client


def get_collection(client, name="manuals_specs"):
    """Return (or create) a collection for manuals/specs embeddings."""
    return client.get_or_create_collection(name=name)
