import sqlite3
import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

DB_PATH = os.getenv("DATABASE_URL", "./data/metadata.db").replace("sqlite:///", "")

def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        filename TEXT NOT NULL,
        format TEXT NOT NULL,
        size_bytes INTEGER NOT NULL,
        file_hash TEXT NOT NULL UNIQUE,
        title TEXT,
        status TEXT NOT NULL DEFAULT 'uploaded',
        error_message TEXT,
        num_chunks INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chunks (
        chunk_id TEXT PRIMARY KEY,
        document_id TEXT NOT NULL,
        chunk_index INTEGER NOT NULL,
        section_heading TEXT,
        page_number INTEGER,
        token_count INTEGER NOT NULL,
        content TEXT NOT NULL,
        version TEXT,
        last_updated TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        conversation_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        confidence TEXT,
        citations TEXT,
        retrieved_evidence TEXT,
        conflict_warning TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evaluations (
        id TEXT PRIMARY KEY,
        run_timestamp TEXT NOT NULL,
        dataset_name TEXT NOT NULL,
        num_questions INTEGER NOT NULL,
        precision_at_k REAL NOT NULL,
        recall_at_k REAL NOT NULL,
        mrr REAL NOT NULL,
        groundedness_score REAL NOT NULL,
        citation_accuracy REAL NOT NULL,
        abstention_accuracy REAL NOT NULL,
        details_json TEXT NOT NULL
    )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(document_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id)")
    conn.commit()
    conn.close()

# Document DAO functions
def insert_document(doc_id: str, filename: str, doc_format: str, size_bytes: int, file_hash: str, title: Optional[str] = None) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO documents (id, filename, format, size_bytes, file_hash, title, status, num_chunks, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, 'uploaded', 0, ?, ?)
    """, (doc_id, filename, doc_format.lower(), size_bytes, file_hash, title or filename, now, now))
    conn.commit()
    conn.close()
    return get_document(doc_id)

def get_document_by_hash(file_hash: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE file_hash = ?", (file_hash,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_document(doc_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def list_documents() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_document_status(doc_id: str, status: str, error_message: Optional[str] = None, num_chunks: Optional[int] = None):
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    if num_chunks is not None:
        cursor.execute("""
            UPDATE documents 
            SET status = ?, error_message = ?, num_chunks = ?, updated_at = ?
            WHERE id = ?
        """, (status, error_message, num_chunks, now, doc_id))
    else:
        cursor.execute("""
            UPDATE documents 
            SET status = ?, error_message = ?, updated_at = ?
            WHERE id = ?
        """, (status, error_message, now, doc_id))
    conn.commit()
    conn.close()

def delete_document(doc_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))
    cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# Chunks DAO functions
def insert_chunks(chunks_data: List[Dict[str, Any]]):
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    for c in chunks_data:
        cursor.execute("""
            INSERT OR REPLACE INTO chunks 
            (chunk_id, document_id, chunk_index, section_heading, page_number, token_count, content, version, last_updated, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            c["chunk_id"],
            c["document_id"],
            c["chunk_index"],
            c.get("section_heading", "General"),
            c.get("page_number"),
            c.get("token_count", len(c["content"].split())),
            c["content"],
            c.get("version"),
            c.get("last_updated"),
            now
        ))
    conn.commit()
    conn.close()

def get_chunk(chunk_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, d.filename, d.title as doc_title
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE c.chunk_id = ?
    """, (chunk_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_chunks() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, d.filename, d.title as doc_title
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE d.status = 'indexed'
        ORDER BY c.document_id, c.chunk_index
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Conversations DAO
def create_conversation(conv_id: str, title: str) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                   (conv_id, title, now, now))
    conn.commit()
    conn.close()
    return {"id": conv_id, "title": title, "created_at": now, "updated_at": now}

def list_conversations() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM conversations ORDER BY updated_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_conversation_messages(conv_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC", (conv_id,))
    rows = cursor.fetchall()
    conn.close()
    res = []
    for r in rows:
        d = dict(r)
        if d.get("citations"):
            try:
                d["citations"] = json.loads(d["citations"])
            except Exception:
                pass
        if d.get("retrieved_evidence"):
            try:
                d["retrieved_evidence"] = json.loads(d["retrieved_evidence"])
            except Exception:
                pass
        res.append(d)
    return res

def insert_message(msg_id: str, conv_id: str, role: str, content: str, 
                   confidence: Optional[str] = None, citations: Optional[List[Dict[str, Any]]] = None,
                   retrieved_evidence: Optional[List[Dict[str, Any]]] = None,
                   conflict_warning: Optional[str] = None) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cit_json = json.dumps(citations) if citations else None
    ev_json = json.dumps(retrieved_evidence) if retrieved_evidence else None
    
    cursor.execute("""
        INSERT INTO messages (id, conversation_id, role, content, confidence, citations, retrieved_evidence, conflict_warning, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (msg_id, conv_id, role, content, confidence, cit_json, ev_json, conflict_warning, now))
    
    cursor.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conv_id))
    conn.commit()
    conn.close()
    return {
        "id": msg_id,
        "conversation_id": conv_id,
        "role": role,
        "content": content,
        "confidence": confidence,
        "citations": citations or [],
        "retrieved_evidence": retrieved_evidence or [],
        "conflict_warning": conflict_warning,
        "created_at": now
    }

# Evaluations DAO
def save_evaluation(eval_id: str, dataset_name: str, num_questions: int,
                    p_at_k: float, r_at_k: float, mrr: float,
                    groundedness: float, citation_acc: float, abstention_acc: float,
                    details: Dict[str, Any]):
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO evaluations 
        (id, run_timestamp, dataset_name, num_questions, precision_at_k, recall_at_k, mrr, groundedness_score, citation_accuracy, abstention_accuracy, details_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (eval_id, now, dataset_name, num_questions, p_at_k, r_at_k, mrr, groundedness, citation_acc, abstention_acc, json.dumps(details)))
    conn.commit()
    conn.close()

def get_latest_evaluation() -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM evaluations ORDER BY run_timestamp DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    try:
        d["details"] = json.loads(d["details_json"])
    except Exception:
        d["details"] = {}
    return d

def get_all_evaluations() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, run_timestamp, dataset_name, num_questions, precision_at_k, recall_at_k, mrr, groundedness_score, citation_accuracy, abstention_accuracy FROM evaluations ORDER BY run_timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
