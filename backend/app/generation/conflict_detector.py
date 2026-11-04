import re
from typing import List, Dict, Any, Optional

def normalize_version(v: str) -> str:
    """Normalize version strings like 'v2', 'v2.0', '2.0.0' to comparable semantic string."""
    if not v or v.lower() == "unknown":
        return "1.0"
    v_clean = re.sub(r'^[vV]', '', v.strip())
    parts = v_clean.split('.')
    if len(parts) == 1:
        return f"{parts[0]}.0"
    return ".".join(parts[:2])

def extract_metric_statements(text: str) -> List[Dict[str, Any]]:
    """
    Extracts numerical limits and policy thresholds:
    e.g. '1000 requests per hour', '500 requests per hour', '30 minutes', '5 failed attempts'
    """
    pattern = re.compile(
        r'(\b(?:limit|maximum|minimum|rate|timeout|lockout|quota|fee|charge)\b[^\.\n;]{0,50}?(\d+(?:,\d+)*(?:\.\d+)?)\s*(requests?|req|hours?|hrs?|minutes?|mins?|seconds?|secs?|days?|users?|gb|mb|tb|percent|%|\$|dollars?)\b)',
        re.IGNORECASE
    )
    matches = []
    for m in pattern.finditer(text):
        full_match = m.group(1).strip()
        val_str = m.group(2).replace(',', '')
        unit = m.group(3).lower()
        # Normalize unit
        if unit in ["req", "request", "requests"]:
            unit = "requests"
        elif unit in ["hr", "hrs", "hour", "hours"]:
            unit = "hours"
        elif unit in ["min", "mins", "minute", "minutes"]:
            unit = "minutes"
        
        matches.append({
            "statement": full_match,
            "value": float(val_str) if val_str.replace('.', '', 1).isdigit() else val_str,
            "unit": unit
        })
    return matches

def detect_conflicts(retrieved_chunks: List[Dict[str, Any]], query: str) -> Optional[Dict[str, Any]]:
    """
    Detects substantive numerical limits and contradictory policies across documents.
    """
    if len(retrieved_chunks) < 2:
        return None

    # Group chunks by document
    docs_involved = {}
    for c in retrieved_chunks:
        doc_name = c.get("document_name", "Unknown")
        if doc_name not in docs_involved:
            docs_involved[doc_name] = {
                "document_name": doc_name,
                "version": normalize_version(c.get("version", "1.0")),
                "normalized_version": normalize_version(c.get("version", "1.0")),
                "raw_version": c.get("version", "1.0"),
                "last_updated": c.get("last_updated", "unknown"),
                "chunks": []
            }
        docs_involved[doc_name]["chunks"].append(c)

    if len(docs_involved) < 2:
        return None

    # Extract all metrics from each document's text
    all_metrics = []
    for doc_name, doc_data in docs_involved.items():
        doc_text = " ".join([c.get("content", "") for c in doc_data["chunks"]])
        extracted = extract_metric_statements(doc_text)
        for item in extracted:
            all_metrics.append({
                "doc_name": doc_name,
                "version": doc_data["raw_version"],
                "normalized_version": doc_data["version"],
                "last_updated": doc_data["last_updated"],
                "statement": item["statement"],
                "value": item["value"],
                "unit": item["unit"]
            })

    # Compare numeric limits for the same unit across different documents
    for i in range(len(all_metrics)):
        for j in range(i + 1, len(all_metrics)):
            m1 = all_metrics[i]
            m2 = all_metrics[j]
            if m1["doc_name"] != m2["doc_name"] and m1["unit"] == m2["unit"]:
                if m1["value"] != m2["value"]:
                    warning = "Conflicting documentation detected. Please verify the applicable policy or product version."
                    details = (
                        f"Document '{m1['doc_name']}' (version {m1['version']}, updated {m1['last_updated']}) specifies: '{m1['statement']}', "
                        f"whereas document '{m2['doc_name']}' (version {m2['version']}, updated {m2['last_updated']}) specifies: '{m2['statement']}'."
                    )
                    return {
                        "has_conflict": True,
                        "conflict_type": "numerical_mismatch",
                        "warning": warning,
                        "details": details,
                        "sources": [
                            {"document": m1["doc_name"], "version": m1["version"], "claim": m1["statement"], "date": m1["last_updated"]},
                            {"document": m2["doc_name"], "version": m2["version"], "claim": m2["statement"], "date": m2["last_updated"]}
                        ]
                    }

    # Explicit version comparison query (e.g., user asks 'v2 vs v1' or 'legacy vs current')
    query_lower = query.lower()
    if ("v1" in query_lower or "legacy" in query_lower) and ("v2" in query_lower or "current" in query_lower):
        norm_versions = {d.get("normalized_version", d.get("version", "1.0")) for d in docs_involved.values()}
        if len(norm_versions) > 1:
            warning = "Multiple document versions indexed with differing architectural specifications."
            return {
                "has_conflict": True,
                "conflict_type": "version_evolution",
                "warning": warning,
                "details": "The query specifically contrasts active and legacy documentation versions.",
                "sources": [
                    {"document": d["document_name"], "version": d["raw_version"], "date": d["last_updated"]}
                    for d in docs_involved.values()
                ]
            }

    return None
