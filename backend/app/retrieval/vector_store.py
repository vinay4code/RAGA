import os
import shutil
from typing import List, Dict, Any, Tuple
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Set offline flags to ensure no network calls
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

CHROMA_PATH = os.getenv("CHROMA_DIR", "./data/vector_store/chroma")
COLLECTION_NAME = "enterprise_docs"

_model = None
_chroma_client = None

def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        # Load cached local model
        try:
            _model = SentenceTransformer(model_name, local_files_only=True)
        except Exception:
            _model = SentenceTransformer(model_name)
    return _model

def get_chroma_collection():
    global _chroma_client
    if _chroma_client is None:
        os.makedirs(CHROMA_PATH, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=CHROMA_PATH,
            settings=Settings(anonymized_telemetry=False, allow_reset=True)
        )
    return _chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

def embed_texts(texts: List[str]) -> List[List[float]]:
    model = get_embedding_model()
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return embeddings.tolist()

def index_chunks_in_vector_store(chunks: List[Dict[str, Any]]):
    if not chunks:
        return
    col = get_chroma_collection()

    ids = [c["chunk_id"] for c in chunks]
    texts = [f"Title: {c.get('document_name', '')} | Section: {c.get('section', '')}\n\n{c['content']}" for c in chunks]
    metadatas = [{
        "chunk_id": c["chunk_id"],
        "document_id": c["document_id"],
        "document_name": c.get("document_name", ""),
        "section": c.get("section", "General"),
        "page_number": c.get("page_number", 1) or 1,
        "version": c.get("version", "1.0") or "1.0",
        "last_updated": c.get("last_updated", "2024-01-01") or "2024-01-01"
    } for c in chunks]

    embeddings = embed_texts(texts)

    # Batch add
    col.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=[c["content"] for c in chunks],
        metadatas=metadatas
    )

def delete_chunks_by_document(document_id: str):
    col = get_chroma_collection()
    try:
        col.delete(where={"document_id": document_id})
    except Exception as e:
        print(f"Error deleting chunks for document {document_id} from vector store: {e}")

def semantic_search(query: str, top_k: int = 10) -> List[Tuple[Dict[str, Any], float]]:
    col = get_chroma_collection()
    if col.count() == 0:
        return []

    q_emb = embed_texts([query])
    results = col.query(
        query_embeddings=q_emb,
        n_results=min(top_k, col.count()),
        include=["documents", "metadatas", "distances"]
    )

    items = []
    if results and "ids" in results and results["ids"] and len(results["ids"][0]) > 0:
        for i in range(len(results["ids"][0])):
            meta = results["metadatas"][0][i]
            content = results["documents"][0][i]
            distance = results["distances"][0][i]
            # In cosine space, similarity = 1 - distance/2 or 1 - distance
            similarity = max(0.0, min(1.0, 1.0 - distance))

            chunk_info = {
                "chunk_id": meta["chunk_id"],
                "document_id": meta["document_id"],
                "document_name": meta.get("document_name", ""),
                "section": meta.get("section", "General"),
                "page_number": meta.get("page_number", 1),
                "version": meta.get("version", "1.0"),
                "last_updated": meta.get("last_updated", "2024-01-01"),
                "content": content
            }
            items.append((chunk_info, float(similarity)))
    return items

def clear_vector_store():
    global _chroma_client
    if _chroma_client:
        try:
            _chroma_client.reset()
        except Exception:
            pass
    if os.path.exists(CHROMA_PATH):
        try:
            shutil.rmtree(CHROMA_PATH)
        except Exception:
            pass
    _chroma_client = None
