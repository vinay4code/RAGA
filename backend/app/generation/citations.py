import re
from typing import List, Dict, Any, Tuple

def extract_citations_from_text(answer_text: str) -> List[Dict[str, Any]]:
    """
    Parses bracketed citations like:
    [Doc: Employee_Account_Manual.pdf, Section: Account Security, Page: 12]
    or [Source: Employee_Account_Manual.pdf, Page: 12]
    or [1] ...
    """
    citations = []
    # Pattern 1: [Doc: ..., Section: ..., Page: ...]
    pattern1 = re.compile(
        r'\[(?:Doc|Document|Source):\s*([^,\]]+)(?:,\s*Section:\s*([^,\]]+))?(?:,\s*Page:\s*(\d+))?\]',
        re.IGNORECASE
    )
    for m in pattern1.finditer(answer_text):
        doc_name = m.group(1).strip()
        sec = m.group(2).strip() if m.group(2) else "General"
        page = int(m.group(3)) if m.group(3) else None
        citations.append({
            "document_name": doc_name,
            "section": sec,
            "page_number": page
        })
    return citations

def validate_and_enrich_citations(
    candidate_citations: List[Dict[str, Any]],
    retrieved_chunks: List[Dict[str, Any]],
    answer_text: str
) -> List[Dict[str, Any]]:
    """
    Validates citations against actual retrieved chunks:
    1. Checks if document_name exists among retrieved chunks.
    2. Links citation to the exact chunk_id.
    3. Extracts a representative excerpt from the chunk.
    4. Eliminates hallucinated documents.
    If LLM did not explicitly embed bracket citations or generated fewer,
    infers grounded citations from top contributing chunks.
    """
    validated = []
    seen_chunk_ids = set()

    # Create lookup map of retrieved chunks
    chunk_by_doc = {}
    for c in retrieved_chunks:
        doc = c.get("document_name", "").lower()
        if doc not in chunk_by_doc:
            chunk_by_doc[doc] = []
        chunk_by_doc[doc].append(c)

    # 1. Validate explicitly parsed citations
    for cand in candidate_citations:
        cand_doc = cand["document_name"].strip().lower()
        matched_chunk = None

        # Exact or partial filename match
        for doc_key, chunks in chunk_by_doc.items():
            if cand_doc in doc_key or doc_key in cand_doc:
                # Find best section or page match
                for chk in chunks:
                    if cand.get("page_number") and chk.get("page_number") == cand.get("page_number"):
                        matched_chunk = chk
                        break
                if not matched_chunk:
                    matched_chunk = chunks[0]
                break

        if matched_chunk and matched_chunk["chunk_id"] not in seen_chunk_ids:
            seen_chunk_ids.add(matched_chunk["chunk_id"])
            excerpt = matched_chunk["content"][:250].strip() + "..."
            validated.append({
                "chunk_id": matched_chunk["chunk_id"],
                "document_name": matched_chunk["document_name"],
                "section": matched_chunk.get("section", "General"),
                "page_number": matched_chunk.get("page_number"),
                "version": matched_chunk.get("version"),
                "last_updated": matched_chunk.get("last_updated"),
                "excerpt": excerpt,
                "relevance_score": matched_chunk.get("relevance_score", 1.0)
            })

    # 2. If no valid citations matched from text, ground directly against top relevant chunks
    if not validated and retrieved_chunks:
        for chk in retrieved_chunks[:3]:
            # Verify if chunk content has lexical overlap with the answer text
            chk_words = set(chk["content"].lower().split())
            ans_words = set(answer_text.lower().split())
            overlap = len(chk_words.intersection(ans_words))
            if overlap >= 5 and chk["chunk_id"] not in seen_chunk_ids:
                seen_chunk_ids.add(chk["chunk_id"])
                excerpt = chk["content"][:250].strip() + "..."
                validated.append({
                    "chunk_id": chk["chunk_id"],
                    "document_name": chk["document_name"],
                    "section": chk.get("section", "General"),
                    "page_number": chk.get("page_number"),
                    "version": chk.get("version"),
                    "last_updated": chk.get("last_updated"),
                    "excerpt": excerpt,
                    "relevance_score": chk.get("relevance_score", 1.0)
                })

    return validated
