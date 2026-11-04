import os
import re
from typing import List, Dict, Any, Tuple
from .bm25 import BM25Index, tokenize
from .vector_store import (
    semantic_search,
    index_chunks_in_vector_store,
    delete_chunks_by_document,
    clear_vector_store
)
from ..database.db import get_all_chunks

_bm25_index = None

def get_bm25_index() -> BM25Index:
    global _bm25_index
    if _bm25_index is None:
        _bm25_index = BM25Index()
        sync_bm25_index()
    return _bm25_index

def sync_bm25_index():
    global _bm25_index
    if _bm25_index is None:
        _bm25_index = BM25Index()
    all_chunks = get_all_chunks()
    _bm25_index.fit(all_chunks)

def compute_rerank_features(query: str, chunk: Dict[str, Any]) -> float:
    """
    Computes lexical signals: term coverage, section match, exact phrase match.
    """
    q_tokens = tokenize(query)
    if not q_tokens:
        return 0.0

    content_lower = chunk.get("content", "").lower()
    section_lower = str(chunk.get("section", "")).lower()
    doc_lower = str(chunk.get("document_name", "")).lower()

    # 1. Term coverage
    matched_tokens = sum(1 for t in q_tokens if t in content_lower)
    term_coverage = matched_tokens / len(q_tokens)

    # 2. Section/title boost
    section_matches = sum(1 for t in q_tokens if t in section_lower or t in doc_lower)
    section_boost = 0.2 if section_matches > 0 else 0.0

    # 3. Exact 2-gram/3-gram phrase match
    phrase_boost = 0.0
    words = query.lower().split()
    if len(words) >= 2:
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            if len(bigram) > 6 and bigram in content_lower:
                phrase_boost = 0.15
                break

    return min(1.0, 0.65 * term_coverage + section_boost + phrase_boost)

def hybrid_retrieve(
    query: str,
    top_k: int = 5,
    relevance_threshold: float = 0.35
) -> List[Dict[str, Any]]:
    """
    Executes hybrid retrieval:
    1. Semantic retrieval (top 10)
    2. BM25 retrieval (top 10)
    3. Reciprocal Rank Fusion (RRF)
    4. Reranking & Cross-Scoring
    5. Threshold filtering
    """
    query_clean = query.strip()
    if not query_clean:
        return []

    # 1. Semantic search
    semantic_results = semantic_search(query_clean, top_k=10)
    semantic_ranks = {item[0]["chunk_id"]: (rank, item[1], item[0]) for rank, item in enumerate(semantic_results)}

    # 2. BM25 search
    bm25 = get_bm25_index()
    bm25_results = bm25.search(query_clean, top_k=10)
    max_bm25_score = max([item[1] for item in bm25_results], default=1.0) or 1.0
    bm25_ranks = {item[0]["chunk_id"]: (rank, item[1] / max_bm25_score, item[0]) for rank, item in enumerate(bm25_results)}

    # 3. Reciprocal Rank Fusion (RRF)
    all_chunk_ids = set(semantic_ranks.keys()).union(set(bm25_ranks.keys()))
    if not all_chunk_ids:
        return []

    k_rrf = 60.0
    fused_candidates = []

    for cid in all_chunk_ids:
        sem_rank, sem_sim, chunk_data_sem = semantic_ranks.get(cid, (100, 0.0, None))
        bm_rank, bm_norm_score, chunk_data_bm = bm25_ranks.get(cid, (100, 0.0, None))
        
        chunk = chunk_data_sem or chunk_data_bm

        # RRF score
        rrf_score = 0.0
        if cid in semantic_ranks:
            rrf_score += 1.0 / (k_rrf + sem_rank)
        if cid in bm25_ranks:
            rrf_score += 1.0 / (k_rrf + bm_rank)

        # Normalization of RRF score (max theoretical is 2/60 = 0.0333)
        normalized_rrf = min(1.0, rrf_score / (2.0 / k_rrf))

        # 4. Rerank lexical features
        lex_score = compute_rerank_features(query_clean, chunk)

        # Cross-score fusion
        # If semantic similarity is high and lexical is high, confidence is very high
        final_relevance = (
            0.50 * sem_sim +
            0.30 * bm_norm_score +
            0.20 * lex_score
        )

        retrieval_method = "hybrid"
        if cid in semantic_ranks and cid not in bm25_ranks:
            retrieval_method = "semantic"
        elif cid in bm25_ranks and cid not in semantic_ranks:
            retrieval_method = "bm25"

        chunk_result = {
            **chunk,
            "relevance_score": round(final_relevance, 4),
            "semantic_score": round(sem_sim, 4),
            "bm25_score": round(bm_norm_score, 4),
            "lexical_score": round(lex_score, 4),
            "retrieval_method": retrieval_method
        }
        fused_candidates.append(chunk_result)

    # Sort descending by final relevance
    fused_candidates.sort(key=lambda x: x["relevance_score"], reverse=True)

    # 5. Filter by threshold
    filtered = [c for c in fused_candidates if c["relevance_score"] >= relevance_threshold]

    # Return top_k
    return filtered[:top_k]
