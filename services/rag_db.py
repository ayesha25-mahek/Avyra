"""
services/rag_db.py
------------------
Database layer for Sovereign Avyara AI Workbench.
Supports dual backends:
1. Local Sovereign SQLite vector store (100% on-premise, zero network reliance, cosine similarity).
2. Supabase PostgreSQL + pgvector (hybrid cloud when configured and reachable).

Manages documents, chunks, vector storage, and similarity search queries.
"""

import json
import logging
import math
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor, execute_values
    from pgvector.psycopg2 import register_vector
except ImportError:
    psycopg2 = None  # type: ignore
    RealDictCursor = execute_values = register_vector = None  # type: ignore

logger = logging.getLogger(__name__)


def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculate cosine similarity between two float vectors."""
    dot = 0.0
    norm1 = 0.0
    norm2 = 0.0
    for a, b in zip(v1, v2):
        dot += a * b
        norm1 += a * a
        norm2 += b * b
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (math.sqrt(norm1) * math.sqrt(norm2))


class RagDatabase:
    """Manages local sovereign SQLite vector store or Supabase PostgreSQL pgvector."""

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.getenv(
            "SUPABASE_DB_URL",
            "postgresql://postgres:bizzoraai123@db.gsqlabyzhswqjrtwrkut.supabase.co:5432/postgres"
        )
        self.sqlite_path = Path(os.getenv("SOVEREIGN_RAG_DB_PATH", "output/sovereign_rag.sqlite3"))
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self._backend: Optional[str] = None
        self._init_sqlite_schema()

    def _init_sqlite_schema(self) -> None:
        """Ensure tables and indexes exist in local sovereign SQLite database."""
        with sqlite3.connect(str(self.sqlite_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    source_type TEXT DEFAULT 'text',
                    filename TEXT,
                    file_path TEXT,
                    file_size INTEGER DEFAULT 0,
                    total_chunks INTEGER DEFAULT 0,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    token_count INTEGER DEFAULT 0,
                    embedding TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON document_chunks(document_id);")
            conn.commit()

    def _get_backend(self) -> str:
        """Determine whether to use local sovereign SQLite or remote PostgreSQL."""
        if self._backend is not None:
            return self._backend

        sovereign_rag = os.getenv("SOVEREIGN_RAG", "true").strip().lower()
        if sovereign_rag in ("true", "1", "yes") or (self.db_url and self.db_url.startswith("sqlite")):
            self._backend = "sqlite"
            logger.info("Sovereign local RAG active: using local SQLite vector store at %s", self.sqlite_path)
            return self._backend

        # Try remote PostgreSQL only if sovereign mode is explicitly disabled
        if psycopg2 and self.db_url and self.db_url.startswith("postgresql"):
            try:
                conn = psycopg2.connect(self.db_url, sslmode="require", connect_timeout=3)
                conn.close()
                self._backend = "postgres"
                logger.info("Connected to remote PostgreSQL pgvector database.")
                return self._backend
            except Exception as exc:
                logger.warning(
                    "Remote PostgreSQL connection unavailable (%s). Falling back to local sovereign SQLite RAG storage.",
                    exc,
                )

        self._backend = "sqlite"
        logger.info("Defaulting to local sovereign SQLite vector store at %s", self.sqlite_path)
        return self._backend

    def get_connection(self):
        """Create and return a configured connection for the active backend."""
        backend = self._get_backend()
        if backend == "postgres":
            conn = psycopg2.connect(self.db_url, sslmode="require")
            register_vector(conn)
            return conn
        else:
            conn = sqlite3.connect(str(self.sqlite_path))
            conn.row_factory = sqlite3.Row
            return conn

    def init_db(self, schema_file: Optional[str] = "schema.sql") -> Dict[str, Any]:
        """Initialize schema for the active backend."""
        backend = self._get_backend()
        if backend == "postgres":
            schema_path = Path(schema_file) if schema_file else Path("schema.sql")
            if not schema_path.exists():
                raise FileNotFoundError(f"Schema file not found at '{schema_path}'")

            sql_content = schema_path.read_text(encoding="utf-8")

            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql_content)
                conn.commit()

            logger.info("Supabase pgvector schema initialized successfully.")
            return {
                "status": "success",
                "message": "Supabase pgvector schema, tables, and RPC functions created successfully."
            }
        else:
            self._init_sqlite_schema()
            logger.info("Local sovereign SQLite RAG database initialized at %s", self.sqlite_path)
            return {
                "status": "success",
                "message": f"Local sovereign SQLite RAG database initialized at '{self.sqlite_path}'."
            }

    def insert_document(
        self,
        title: str,
        source_type: str = "text",
        filename: Optional[str] = None,
        file_path: Optional[str] = None,
        file_size: int = 0,
        total_chunks: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Insert a document record and return its UUID."""
        backend = self._get_backend()
        meta_json = json.dumps(metadata or {})

        if backend == "postgres":
            sql = """
                INSERT INTO documents (title, source_type, filename, file_path, file_size, total_chunks, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                RETURNING id;
            """
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        sql,
                        (title, source_type, filename, file_path, file_size, total_chunks, meta_json),
                    )
                    doc_id = str(cur.fetchone()[0])
                conn.commit()
            return doc_id
        else:
            doc_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            with sqlite3.connect(str(self.sqlite_path)) as conn:
                conn.execute(
                    """
                    INSERT INTO documents (id, title, source_type, filename, file_path, file_size, total_chunks, metadata, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (doc_id, title, source_type, filename, file_path, file_size, total_chunks, meta_json, now, now),
                )
                conn.commit()
            return doc_id

    def update_document_chunks_count(self, document_id: str, count: int) -> None:
        """Update total_chunks count for a document."""
        backend = self._get_backend()
        if backend == "postgres":
            sql = "UPDATE documents SET total_chunks = %s WHERE id = %s;"
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (count, document_id))
                conn.commit()
        else:
            now = datetime.now(timezone.utc).isoformat()
            with sqlite3.connect(str(self.sqlite_path)) as conn:
                conn.execute(
                    "UPDATE documents SET total_chunks = ?, updated_at = ? WHERE id = ?",
                    (count, now, document_id),
                )
                conn.commit()

    def insert_chunks(self, document_id: str, chunks_data: List[Dict[str, Any]]) -> int:
        """
        Insert a list of chunk dicts into document_chunks.
        Each item: {'chunk_index': int, 'content': str, 'token_count': int, 'embedding': list[float], 'metadata': dict}
        """
        if not chunks_data:
            return 0

        backend = self._get_backend()

        if backend == "postgres":
            rows = [
                (
                    document_id,
                    chunk["chunk_index"],
                    chunk["content"],
                    chunk.get("token_count", len(chunk["content"].split())),
                    chunk["embedding"],
                    json.dumps(chunk.get("metadata", {})),
                )
                for chunk in chunks_data
            ]

            sql = """
                INSERT INTO document_chunks (document_id, chunk_index, content, token_count, embedding, metadata)
                VALUES %s;
            """
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    execute_values(
                        cur,
                        sql,
                        rows,
                        template="(%s, %s, %s, %s, %s, %s::jsonb)",
                    )
                conn.commit()
        else:
            rows = [
                (
                    str(uuid.uuid4()),
                    document_id,
                    chunk["chunk_index"],
                    chunk["content"],
                    chunk.get("token_count", len(chunk["content"].split())),
                    json.dumps(chunk["embedding"]),
                    json.dumps(chunk.get("metadata", {})),
                )
                for chunk in chunks_data
            ]
            with sqlite3.connect(str(self.sqlite_path)) as conn:
                conn.executemany(
                    """
                    INSERT INTO document_chunks (id, document_id, chunk_index, content, token_count, embedding, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    rows,
                )
                conn.commit()

        self.update_document_chunks_count(document_id, len(chunks_data))
        return len(chunks_data)

    def search_chunks(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        threshold: float = 0.2,
        filter_doc_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic similarity search.
        In PostgreSQL: uses pgvector cosine distance (<=> operator).
        In Sovereign SQLite: uses exact dot product / cosine similarity on local chunks.
        Returns list of matching chunks sorted by similarity desc.
        """
        backend = self._get_backend()

        if backend == "postgres":
            sql = """
                SELECT 
                    dc.id,
                    dc.document_id,
                    dc.chunk_index,
                    dc.content,
                    dc.metadata,
                    d.title as document_title,
                    d.source_type,
                    d.filename,
                    1 - (dc.embedding <=> %s::vector) AS similarity
                FROM document_chunks dc
                JOIN documents d ON d.id = dc.document_id
                WHERE 
                    (%s IS NULL OR dc.document_id = %s::uuid)
                    AND dc.embedding IS NOT NULL
                    AND (1 - (dc.embedding <=> %s::vector)) >= %s
                ORDER BY dc.embedding <=> %s::vector ASC
                LIMIT %s;
            """

            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        sql,
                        (
                            query_embedding,
                            filter_doc_id,
                            filter_doc_id,
                            query_embedding,
                            threshold,
                            query_embedding,
                            top_k,
                        ),
                    )
                    results = cur.fetchall()

            formatted = []
            for r in results:
                formatted.append({
                    "id": str(r["id"]),
                    "document_id": str(r["document_id"]),
                    "document_title": r.get("document_title"),
                    "source_type": r.get("source_type"),
                    "filename": r.get("filename"),
                    "chunk_index": r["chunk_index"],
                    "content": r["content"],
                    "metadata": r.get("metadata", {}),
                    "similarity": float(r["similarity"]) if r["similarity"] is not None else 0.0,
                })
            return formatted

        else:
            # Sovereign SQLite local retrieval
            with sqlite3.connect(str(self.sqlite_path)) as conn:
                conn.row_factory = sqlite3.Row
                if filter_doc_id:
                    cursor = conn.execute(
                        """
                        SELECT dc.id, dc.document_id, dc.chunk_index, dc.content, dc.metadata, dc.embedding,
                               d.title as document_title, d.source_type, d.filename
                        FROM document_chunks dc
                        JOIN documents d ON d.id = dc.document_id
                        WHERE dc.document_id = ?
                        """,
                        (filter_doc_id,)
                    )
                else:
                    cursor = conn.execute(
                        """
                        SELECT dc.id, dc.document_id, dc.chunk_index, dc.content, dc.metadata, dc.embedding,
                               d.title as document_title, d.source_type, d.filename
                        FROM document_chunks dc
                        JOIN documents d ON d.id = dc.document_id
                        """
                    )
                rows = cursor.fetchall()

            scored = []
            for r in rows:
                try:
                    emb = json.loads(r["embedding"])
                    sim = _cosine_similarity(query_embedding, emb)
                    if sim >= threshold:
                        meta = json.loads(r["metadata"]) if r["metadata"] else {}
                        scored.append({
                            "id": str(r["id"]),
                            "document_id": str(r["document_id"]),
                            "document_title": r["document_title"],
                            "source_type": r["source_type"],
                            "filename": r["filename"],
                            "chunk_index": r["chunk_index"],
                            "content": r["content"],
                            "metadata": meta,
                            "similarity": float(sim),
                        })
                except Exception:
                    continue

            scored.sort(key=lambda x: x["similarity"], reverse=True)
            return scored[:top_k]

    def list_documents(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List all indexed documents with chunk stats."""
        backend = self._get_backend()

        if backend == "postgres":
            sql = """
                SELECT 
                    id, title, source_type, filename, file_size, total_chunks, metadata, created_at, updated_at
                FROM documents
                ORDER BY created_at DESC
                LIMIT %s;
            """
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(sql, (limit,))
                    rows = cur.fetchall()

            return [
                {
                    "id": str(r["id"]),
                    "title": r["title"],
                    "source_type": r["source_type"],
                    "filename": r["filename"],
                    "file_size": r["file_size"],
                    "total_chunks": r["total_chunks"],
                    "metadata": r["metadata"],
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                    "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
                }
                for r in rows
            ]
        else:
            with sqlite3.connect(str(self.sqlite_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """
                    SELECT id, title, source_type, filename, file_size, total_chunks, metadata, created_at, updated_at
                    FROM documents
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (limit,)
                )
                rows = cursor.fetchall()

            return [
                {
                    "id": str(r["id"]),
                    "title": r["title"],
                    "source_type": r["source_type"],
                    "filename": r["filename"],
                    "file_size": r["file_size"],
                    "total_chunks": r["total_chunks"],
                    "metadata": json.loads(r["metadata"]) if r["metadata"] else {},
                    "created_at": r["created_at"],
                    "updated_at": r["updated_at"],
                }
                for r in rows
            ]

    def delete_document(self, document_id: str) -> bool:
        """Delete a document and its cascading chunks."""
        backend = self._get_backend()

        if backend == "postgres":
            sql = "DELETE FROM documents WHERE id = %s RETURNING id;"
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (document_id,))
                    deleted = cur.fetchone()
                conn.commit()
            return deleted is not None
        else:
            with sqlite3.connect(str(self.sqlite_path)) as conn:
                conn.execute("DELETE FROM document_chunks WHERE document_id = ?", (document_id,))
                cur = conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
                conn.commit()
                return cur.rowcount > 0
