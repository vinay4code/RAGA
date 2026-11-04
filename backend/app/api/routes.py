import os
import uuid
import hashlib
import shutil
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pydantic import BaseModel

from ..database.db import (
    insert_document,
    get_document,
    get_document_by_hash,
    list_documents,
    update_document_status,
    delete_document,
    insert_chunks,
    get_chunk,
    get_all_chunks,
    create_conversation,
    list_conversations,
    get_conversation_messages,
    insert_message,
    get_latest_evaluation,
    get_all_evaluations
)
from ..ingestion.parsers import parse_document
from ..preprocessing.chunker import chunk_document
from ..retrieval.hybrid_search import (
    hybrid_retrieve,
    index_chunks_in_vector_store,
    delete_chunks_by_document,
    sync_bm25_index
)
from ..generation.generator import generate_answer
from ..evaluation.evaluator import run_evaluation_suite

router = APIRouter(prefix="/api")

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./data/uploads")
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB
ALLOWED_EXTENSIONS = {".pdf", ".html", ".htm", ".md", ".markdown", ".txt"}

# Pydantic Request/Response Models
class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None
    top_k: Optional[int] = 5
    relevance_threshold: Optional[float] = 0.35

class EvaluationRequest(BaseModel):
    dataset_path: Optional[str] = None
    top_k: Optional[int] = 5
    relevance_threshold: Optional[float] = 0.35

# Endpoints

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "llm_provider": os.getenv("LLM_PROVIDER", "local"),
        "embedding_model": os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
        "has_gemini_key": bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
        "has_openai_key": bool(os.getenv("OPENAI_API_KEY"))
    }

@router.get("/dashboard/stats")
def get_dashboard_stats():
    docs = list_documents()
    total_docs = len(docs)
    indexed_docs = sum(1 for d in docs if d.get("status") == "indexed")
    total_chunks = sum(d.get("num_chunks", 0) for d in docs)
    
    convs = list_conversations()
    # Count total questions asked
    total_questions = 0
    high_med_confidence_count = 0
    for c in convs:
        msgs = get_conversation_messages(c["id"])
        user_msgs = [m for m in msgs if m.get("role") == "user"]
        total_questions += len(user_msgs)
        for m in msgs:
            if m.get("role") == "assistant" and m.get("confidence") in ["HIGH", "MEDIUM"]:
                high_med_confidence_count += 1

    retrieval_success_rate = (
        round((high_med_confidence_count / (total_questions or 1)) * 100, 1)
        if total_questions > 0 else 100.0
    )

    latest_eval = get_latest_evaluation()

    return {
        "total_documents": total_docs,
        "indexed_documents": indexed_docs,
        "total_chunks": total_chunks,
        "total_questions": total_questions,
        "retrieval_success_rate": retrieval_success_rate,
        "recent_documents": docs[:5],
        "system_status": {
            "llm_provider": os.getenv("LLM_PROVIDER", "local"),
            "embedding_model": os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            "vector_store": "ChromaDB (Local)",
            "keyword_index": "BM25Okapi"
        },
        "latest_evaluation": latest_eval
    }

@router.post("/documents/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """
    Accepts multiple documents, validates file types/sizes,
    computes SHA-256 hash for deduplication, extracts text,
    creates section-aware chunks, generates embeddings,
    and updates vector index and database.
    """
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    uploaded_results = []

    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            uploaded_results.append({
                "filename": file.filename,
                "status": "failed",
                "error": f"Unsupported format '{ext}'. Allowed: {', '.join(sorted(list(ALLOWED_EXTENSIONS)))}"
            })
            continue

        content_bytes = await file.read()
        if len(content_bytes) > MAX_FILE_SIZE:
            uploaded_results.append({
                "filename": file.filename,
                "status": "failed",
                "error": f"File size exceeds maximum limit of {MAX_FILE_SIZE // (1024*1024)}MB."
            })
            continue

        # Compute SHA-256 hash
        file_hash = hashlib.sha256(content_bytes).hexdigest()
        existing = get_document_by_hash(file_hash)
        if existing:
            uploaded_results.append({
                "document_id": existing["id"],
                "filename": existing["filename"],
                "status": existing["status"],
                "num_chunks": existing["num_chunks"],
                "message": "Duplicate document detected (identical hash). Existing record returned."
            })
            continue

        doc_id = str(uuid.uuid4())
        safe_filename = f"{doc_id}_{os.path.basename(file.filename)}"
        dest_path = os.path.join(UPLOAD_DIR, safe_filename)

        with open(dest_path, "wb") as f_out:
            f_out.write(content_bytes)

        # Record in DB as 'uploaded'
        doc_format = ext.lstrip('.')
        doc_record = insert_document(
            doc_id=doc_id,
            filename=file.filename,
            doc_format=doc_format,
            size_bytes=len(content_bytes),
            file_hash=file_hash,
            title=file.filename
        )

        try:
            update_document_status(doc_id, "processing")

            # Parse document
            sections = parse_document(dest_path, doc_format)
            if not sections:
                raise ValueError("Could not extract any text content from document.")

            # Chunk document
            chunks = chunk_document(sections, doc_id=doc_id, doc_name=file.filename)
            if not chunks:
                raise ValueError("Chunking produced zero chunks from extracted text.")

            # Save chunks to SQLite
            insert_chunks(chunks)

            # Store in ChromaDB vector store
            index_chunks_in_vector_store(chunks)

            # Re-sync BM25 in-memory index
            sync_bm25_index()

            # Mark document as indexed
            update_document_status(doc_id, "indexed", num_chunks=len(chunks))

            uploaded_results.append({
                "document_id": doc_id,
                "filename": file.filename,
                "format": doc_format,
                "size_bytes": len(content_bytes),
                "num_chunks": len(chunks),
                "status": "indexed"
            })
        except Exception as e:
            update_document_status(doc_id, "failed", error_message=str(e))
            uploaded_results.append({
                "document_id": doc_id,
                "filename": file.filename,
                "status": "failed",
                "error": str(e)
            })

    return {"uploaded_documents": uploaded_results}

@router.get("/documents")
def list_all_documents():
    return list_documents()

@router.get("/documents/{document_id}")
def get_document_details(document_id: str):
    doc = get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    all_chunks = get_all_chunks()
    doc_chunks = [c for c in all_chunks if c["document_id"] == document_id]
    return {
        "document": doc,
        "chunks": doc_chunks
    }

@router.delete("/documents/{document_id}")
def remove_document(document_id: str):
    doc = get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 1. Delete from vector store
    delete_chunks_by_document(document_id)

    # 2. Delete from SQLite
    delete_document(document_id)

    # 3. Synchronize BM25
    sync_bm25_index()

    return {"success": True, "message": f"Document '{doc['filename']}' and its associated index entries have been removed."}

@router.post("/chat")
def submit_question(req: ChatRequest):
    """
    Submit a question:
    1. Hybrid retrieval (semantic + BM25 + RRF + rerank)
    2. Grounded answer generation + citation validation + conflict detection
    3. Persist to conversation history
    """
    query = req.question.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    conv_id = req.conversation_id
    if not conv_id:
        conv_id = str(uuid.uuid4())
        # Derive conversation title from first 35 chars of question
        short_title = query[:35] + ("..." if len(query) > 35 else "")
        create_conversation(conv_id, short_title)

    # Record user message
    user_msg_id = str(uuid.uuid4())
    insert_message(user_msg_id, conv_id, "user", query)

    # Hybrid Retrieval
    retrieved_chunks = hybrid_retrieve(
        query,
        top_k=req.top_k or 5,
        relevance_threshold=req.relevance_threshold or 0.35
    )

    # Generate grounded answer
    gen_result = generate_answer(
        query,
        retrieved_chunks,
        relevance_threshold=req.relevance_threshold or 0.35
    )

    # Record assistant message
    asst_msg_id = str(uuid.uuid4())
    conflict_warn = gen_result.get("conflict", {}).get("warning") if gen_result.get("conflict") else None
    
    msg_record = insert_message(
        asst_msg_id,
        conv_id,
        "assistant",
        gen_result["answer"],
        confidence=gen_result["confidence"],
        citations=gen_result["citations"],
        retrieved_evidence=gen_result["retrieved_evidence"],
        conflict_warning=conflict_warn
    )

    return {
        "conversation_id": conv_id,
        "message": msg_record,
        "answer": gen_result["answer"],
        "confidence": gen_result["confidence"],
        "confidence_score": gen_result["confidence_score"],
        "confidence_metadata": gen_result["confidence_metadata"],
        "conflict": gen_result["conflict"],
        "citations": gen_result["citations"],
        "retrieved_evidence": gen_result["retrieved_evidence"]
    }

@router.get("/conversations")
def get_conversations():
    return list_conversations()

@router.get("/conversations/{conversation_id}")
def get_conversation_history(conversation_id: str):
    messages = get_conversation_messages(conversation_id)
    return {"conversation_id": conversation_id, "messages": messages}

@router.get("/sources/{chunk_id}")
def get_source_chunk(chunk_id: str):
    chunk = get_chunk(chunk_id)
    if not chunk:
        raise HTTPException(status_code=404, detail="Source chunk not found")
    return chunk

@router.post("/evaluation/run")
def execute_evaluation(req: EvaluationRequest = EvaluationRequest()):
    try:
        results = run_evaluation_suite(
            dataset_path=req.dataset_path,
            top_k=req.top_k or 5,
            relevance_threshold=req.relevance_threshold or 0.35
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/evaluation/results")
def get_evaluation_results():
    latest = get_latest_evaluation()
    history = get_all_evaluations()
    return {
        "latest": latest,
        "history": history
    }
