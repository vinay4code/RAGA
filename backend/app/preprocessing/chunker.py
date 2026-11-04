import re
from typing import List, Dict, Any

# Target chunk size: 500-800 tokens (approx 350-550 words)
# Target overlap: 100-150 tokens (approx 70-100 words)
TARGET_CHUNK_WORDS = 400
CHUNK_OVERLAP_WORDS = 80
MIN_CHUNK_WORDS = 30

INJECTION_PATTERNS = [
    re.compile(r'(?i)ignore\s+(all\s+)?previous\s+instructions'),
    re.compile(r'(?i)system\s*:\s*you\s+are\s+now'),
    re.compile(r'(?i)you\s+must\s+disregard\s+prior'),
    re.compile(r'(?i)new\s+system\s+directive'),
    re.compile(r'(?i)override\s+system\s+prompt'),
]

def neutralize_prompt_injections(text: str) -> str:
    """Neutralize potential prompt injections in untrusted document text."""
    sanitized = text
    for pattern in INJECTION_PATTERNS:
        sanitized = pattern.sub(r'[FLAGGED_UNTRUSTED_INSTRUCTION]', sanitized)
    return sanitized

def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences cleanly respecting punctuation."""
    sentence_endings = re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9])')
    raw_sentences = sentence_endings.split(text)
    clean_sentences = []
    for s in raw_sentences:
        s_strip = s.strip()
        if s_strip:
            clean_sentences.append(s_strip)
    return clean_sentences

def chunk_section(section_data: Dict[str, Any], doc_id: str, doc_name: str, start_chunk_idx: int) -> List[Dict[str, Any]]:
    """
    Split a document section into chunks respecting sentence boundaries,
    preserving headings, page numbers, and metadata.
    """
    raw_content = section_data.get("content", "").strip()
    if not raw_content:
        return []

    safe_content = neutralize_prompt_injections(raw_content)
    section_name = section_data.get("section", "General")
    page_number = section_data.get("page_number", 1)
    version = section_data.get("version", "1.0")
    last_updated = section_data.get("last_updated", "2024-01-01")

    sentences = split_into_sentences(safe_content)
    if not sentences:
        return []

    chunks = []
    current_sentences = []
    current_word_count = 0
    chunk_index = start_chunk_idx

    for sent in sentences:
        words = sent.split()
        sent_word_count = len(words)

        if current_word_count + sent_word_count > TARGET_CHUNK_WORDS and current_sentences:
            # Emit chunk
            chunk_text = " ".join(current_sentences)
            token_count = int(len(chunk_text.split()) * 1.3)  # heuristic tokens
            
            chunk_id = f"{doc_id}_chunk_{chunk_index}"
            chunks.append({
                "chunk_id": chunk_id,
                "document_id": doc_id,
                "document_name": doc_name,
                "chunk_index": chunk_index,
                "section": section_name,
                "section_heading": section_name,
                "page_number": page_number,
                "token_count": token_count,
                "content": chunk_text,
                "version": version,
                "last_updated": last_updated
            })
            chunk_index += 1

            # Keep overlap sentences from the end
            overlap_sentences = []
            overlap_words = 0
            for prev_sent in reversed(current_sentences):
                prev_len = len(prev_sent.split())
                if overlap_words + prev_len <= CHUNK_OVERLAP_WORDS:
                    overlap_sentences.insert(0, prev_sent)
                    overlap_words += prev_len
                else:
                    break

            current_sentences = overlap_sentences
            current_word_count = overlap_words

        current_sentences.append(sent)
        current_word_count += sent_word_count

    # Remaining sentences
    if current_sentences:
        chunk_text = " ".join(current_sentences)
        # If very small and we have a previous chunk in this section, append to previous chunk
        if len(chunk_text.split()) < MIN_CHUNK_WORDS and chunks:
            chunks[-1]["content"] += " " + chunk_text
            chunks[-1]["token_count"] = int(len(chunks[-1]["content"].split()) * 1.3)
        else:
            token_count = int(len(chunk_text.split()) * 1.3)
            chunk_id = f"{doc_id}_chunk_{chunk_index}"
            chunks.append({
                "chunk_id": chunk_id,
                "document_id": doc_id,
                "document_name": doc_name,
                "chunk_index": chunk_index,
                "section": section_name,
                "section_heading": section_name,
                "page_number": page_number,
                "token_count": token_count,
                "content": chunk_text,
                "version": version,
                "last_updated": last_updated
            })

    return chunks

def chunk_document(sections: List[Dict[str, Any]], doc_id: str, doc_name: str) -> List[Dict[str, Any]]:
    """
    Chunk all sections of a document while preserving continuous index and document metadata.
    """
    all_chunks = []
    chunk_idx = 0
    for section in sections:
        section_chunks = chunk_section(section, doc_id, doc_name, start_chunk_idx=chunk_idx)
        all_chunks.extend(section_chunks)
        chunk_idx = len(all_chunks)
    return all_chunks
