import re
from typing import List, Dict, Any, Tuple
from ..retrieval.bm25 import tokenize

SPECIFIC_ENTITIES = {
    "api", "password", "sso", "mfa", "login", "auth", "authentication",
    "billing", "subscription", "starter", "professional", "enterprise",
    "invoice", "overage", "webhook", "proxy", "token", "lockout", "session",
    "err-401", "err-403", "err-429"
}

GENERIC_VERBS = {
    "how", "do", "can", "what", "where", "when", "why", "who", "which",
    "configure", "setup", "use", "get", "set", "make", "find", "check"
}

def assess_confidence_and_answerability(
    query: str,
    retrieved_chunks: List[Dict[str, Any]],
    relevance_threshold: float = 0.35
) -> Tuple[str, float, Dict[str, Any]]:
    """
    Evaluates evidence coverage, retrieval score distribution, and question specificity.
    Returns:
        confidence_level: 'HIGH', 'MEDIUM', 'LOW'
        confidence_score: float in [0.0, 1.0]
        meta: diagnostic details
    """
    if not retrieved_chunks:
        return "LOW", 0.0, {
            "reason": "zero_evidence",
            "top_score": 0.0,
            "avg_score": 0.0,
            "term_coverage": 0.0,
            "is_ambiguous": False
        }

    top_chunk = retrieved_chunks[0]
    top_score = top_chunk.get("relevance_score", 0.0)

    # Average score of top 3 chunks
    top_3_scores = [c.get("relevance_score", 0.0) for c in retrieved_chunks[:3]]
    avg_score = sum(top_3_scores) / len(top_3_scores)

    # Term coverage: does retrieved evidence actually contain query content keywords?
    q_tokens = tokenize(query)
    content_tokens = [t for t in q_tokens if t not in GENERIC_VERBS]
    all_content = " ".join([c.get("content", "").lower() for c in retrieved_chunks])
    
    if content_tokens:
        matched_tokens = sum(1 for t in content_tokens if t in all_content)
        term_coverage = matched_tokens / len(content_tokens)
    else:
        term_coverage = 0.0

    # Ambiguity check: query lacks specific subject or entity
    words = re.findall(r'\b[a-zA-Z0-9_-]+\b', query.lower())
    has_specific_entity = any(w in SPECIFIC_ENTITIES for w in words)
    has_broad_term = any(w in words for w in ["limit", "limits", "rate", "cost", "price", "policy", "timeout", "fee", "how"])

    is_ambiguous = False
    ambiguity_reason = None

    if len(words) <= 5 and has_broad_term and not has_specific_entity:
        is_ambiguous = True
        ambiguity_reason = "The query asks for a limit or policy without identifying the target product, service, or context (e.g., API limits, session timeout, or billing tiers)."

    # Composite confidence score
    composite_score = round(0.45 * top_score + 0.30 * avg_score + 0.25 * term_coverage, 4)

    # Categorization
    # If the key nouns/content tokens are largely missing (coverage < 35%), it is unanswerable (LOW)
    if top_score < relevance_threshold or composite_score < 0.40 or term_coverage < 0.35:
        level = "LOW"
    elif is_ambiguous or composite_score < 0.62 or term_coverage < 0.55:
        level = "MEDIUM"
    else:
        level = "HIGH"

    return level, composite_score, {
        "top_score": top_score,
        "avg_score": round(avg_score, 4),
        "term_coverage": round(term_coverage, 4),
        "is_ambiguous": is_ambiguous,
        "ambiguity_reason": ambiguity_reason
    }
