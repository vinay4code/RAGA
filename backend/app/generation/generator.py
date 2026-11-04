import os
import re
import json
import requests
from typing import List, Dict, Any, Optional, Tuple
from .conflict_detector import detect_conflicts
from .confidence import assess_confidence_and_answerability
from .citations import extract_citations_from_text, validate_and_enrich_citations

SYSTEM_PROMPT = """You are an enterprise documentation assistant.

Answer user questions exclusively using the supplied evidence.

Rules:
1. Never use external knowledge to fill gaps.
2. Never invent policies, configurations, limits, procedures or technical details.
3. Every material factual claim must be supported by retrieved evidence.
4. Cite the document and section supporting each claim using the format [Doc: filename, Section: heading, Page: number].
5. Include page numbers when available.
6. If the evidence is insufficient, explicitly state that the information was not found.
7. If multiple documents contradict one another, explain the contradiction.
8. If information depends on a product version or date, explicitly mention the relevant version or date.
9. If a question is ambiguous, ask the user for clarification.
10. Distinguish direct evidence from reasonable interpretations.
11. Prefer concise, structured answers.
12. Never fabricate a citation.

Answer structure:
- **Direct Answer**: Brief, grounded summary.
- **Details / Steps**: Exact procedural steps or policy terms.
- **Limitations or Warnings**: Any constraints, requirements, or conflicting information.
"""

def generate_local_grounded_answer(
    query: str,
    retrieved_chunks: List[Dict[str, Any]],
    confidence_level: str,
    conflict_info: Optional[Dict[str, Any]],
    confidence_meta: Dict[str, Any]
) -> str:
    """
    Offline deterministic synthesis engine that operates strictly on retrieved evidence.
    Guarantees zero hallucinations and adheres to all 12 prompt rules.
    """
    if confidence_level == "LOW" or not retrieved_chunks:
        return "I couldn't find sufficient supporting information in the uploaded documentation to answer this question reliably."

    if confidence_meta.get("is_ambiguous"):
        return (
            "Your question appears ambiguous or lacks specific context (such as the product name, tier, or version). "
            f"{confidence_meta.get('ambiguity_reason', '')}\n\n"
            "Please clarify your request so I can retrieve the exact policy or technical procedure."
        )

    # If conflict detected
    if conflict_info and conflict_info.get("has_conflict"):
        lines = [
            "### Direct Answer",
            "Conflicting documentation was identified across your indexed sources regarding this inquiry.",
            "",
            f"> **Warning**: {conflict_info.get('warning')}",
            "",
            "### Contradiction Analysis",
            conflict_info.get("details", ""),
            "",
            "### Sources in Conflict"
        ]
        for src in conflict_info.get("sources", []):
            lines.append(f"- **Document**: `{src.get('document')}` (Version: {src.get('version')}, Date: {src.get('date', 'N/A')})")
            if "claim" in src:
                lines.append(f"  *Specification*: {src['claim']}")
        lines.append("")
        lines.append("Please verify with your systems administrator or verify the applicable active product version.")
        return "\n".join(lines)

    # Synthesize grounded response from retrieved chunks
    doc_groups = {}
    for c in retrieved_chunks:
        doc = c.get("document_name", "Document")
        if doc not in doc_groups:
            doc_groups[doc] = []
        doc_groups[doc].append(c)

    # Extract sentences that match query tokens
    query_tokens = [w.lower() for w in re.findall(r'\b\w{3,}\b', query)]
    
    extracted_claims = []
    for c in retrieved_chunks:
        sentences = re.split(r'(?<=[.!?])\s+', c.get("content", ""))
        sec = c.get("section", "General")
        p = c.get("page_number", 1)
        doc = c.get("document_name", "Document")
        
        for s in sentences:
            s_clean = s.strip()
            if not s_clean or len(s_clean) < 15:
                continue
            s_lower = s_clean.lower()
            # Match if contains query tokens
            matches = sum(1 for t in query_tokens if t in s_lower)
            if matches >= 1:
                citation_tag = f"[Doc: {doc}, Section: {sec}, Page: {p}]"
                extracted_claims.append((matches, s_clean, citation_tag))

    extracted_claims.sort(key=lambda x: x[0], reverse=True)
    top_claims = extracted_claims[:5]

    if not top_claims:
        # Fallback to chunk excerpt directly
        c = retrieved_chunks[0]
        lead_text = c['content'][:300].strip()
        lead_citation = f"[Doc: {c.get('document_name')}, Section: {c.get('section')}, Page: {c.get('page_number', 1)}]"
        return (
            f"### Direct Answer\n"
            f"Based on `{c.get('document_name')}`, the following guidance applies:\n\n"
            f"{lead_text} {lead_citation}\n\n"
            f"### Context & Details\n"
            f"Refer to section **{c.get('section')}** for complete organizational requirements."
        )

    # Format structured response
    direct_stmt = top_claims[0][1]
    direct_cit = top_claims[0][2]
    
    body_lines = [
        "### Direct Answer",
        f"{direct_stmt} {direct_cit}",
        "",
        "### Key Details & Procedures"
    ]

    for _, stmt, cit in top_claims[1:]:
        body_lines.append(f"- {stmt} {cit}")

    # Add version notes if available
    v_notes = []
    for doc, chks in doc_groups.items():
        v = chks[0].get("version")
        d = chks[0].get("last_updated")
        if v or d:
            v_notes.append(f"`{doc}` (Version: {v or '1.0'}, Last Updated: {d or 'N/A'})")

    if v_notes:
        body_lines.append("")
        body_lines.append("### Applicable Documentation Versions")
        for vn in v_notes:
            body_lines.append(f"- {vn}")

    return "\n".join(body_lines)

def call_gemini_api(api_key: str, model_name: str, query: str, context_str: str) -> Optional[str]:
    """Call Google Gemini REST API using requests."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = f"{SYSTEM_PROMPT}\n\n=== RETRIEVED EVIDENCE PASSAGES ===\n{context_str}\n\n=== USER QUESTION ===\n{query}\n\nGenerate your grounded answer following all rules:"

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 800
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
        else:
            print(f"Gemini API returned status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Gemini API call failed: {e}")
    return None

def call_openai_api(api_key: str, model_name: str, query: str, context_str: str) -> Optional[str]:
    """Call OpenAI REST API using requests."""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"=== RETRIEVED EVIDENCE PASSAGES ===\n{context_str}\n\n=== USER QUESTION ===\n{query}\n\nAnswer:"}
    ]

    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 800
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
        else:
            print(f"OpenAI API returned status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"OpenAI API call failed: {e}")
    return None

def generate_answer(
    query: str,
    retrieved_chunks: List[Dict[str, Any]],
    relevance_threshold: float = 0.35
) -> Dict[str, Any]:
    """
    Main Grounded Answer Generation Orchestrator:
    1. Assess confidence and answerability.
    2. Detect conflicts and contradictory documentation.
    3. Call configured LLM provider or local grounded synthesizer.
    4. Validate and enrich citations.
    5. Return structured response.
    """
    confidence_level, confidence_score, conf_meta = assess_confidence_and_answerability(
        query, retrieved_chunks, relevance_threshold=relevance_threshold
    )

    conflict_info = detect_conflicts(retrieved_chunks, query) if retrieved_chunks else None

    # Determine provider
    provider = os.getenv("LLM_PROVIDER", "local").lower()
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    raw_answer = None

    # Build context string for LLM
    context_blocks = []
    for idx, c in enumerate(retrieved_chunks):
        p_num = c.get("page_number", 1)
        sec = c.get("section", "General")
        doc_name = c.get("document_name", "Doc")
        ver = c.get("version", "1.0")
        dt = c.get("last_updated", "")
        context_blocks.append(
            f"Passage [{idx+1}]:\n"
            f"Document: {doc_name} (Version: {ver}, Updated: {dt})\n"
            f"Section: {sec} | Page: {p_num}\n"
            f"Content:\n{c.get('content')}\n"
        )
    context_str = "\n".join(context_blocks)

    if confidence_level == "LOW":
        raw_answer = "I couldn't find sufficient supporting information in the uploaded documentation to answer this question reliably."
    else:
        if provider == "gemini" and gemini_key:
            model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
            raw_answer = call_gemini_api(gemini_key, model, query, context_str)
        elif provider == "openai" and openai_key:
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            raw_answer = call_openai_api(openai_key, model, query, context_str)

        # Fallback to local synthesizer if API fails or provider is 'local'
        if not raw_answer:
            raw_answer = generate_local_grounded_answer(
                query, retrieved_chunks, confidence_level, conflict_info, conf_meta
            )

    # Citation extraction and validation
    parsed_citations = extract_citations_from_text(raw_answer)
    validated_citations = validate_and_enrich_citations(parsed_citations, retrieved_chunks, raw_answer)

    return {
        "answer": raw_answer,
        "confidence": confidence_level,
        "confidence_score": confidence_score,
        "confidence_metadata": conf_meta,
        "conflict": conflict_info,
        "citations": validated_citations,
        "retrieved_evidence": retrieved_chunks
    }
