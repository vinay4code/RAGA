import math
import re
from typing import List, Dict, Tuple, Any

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", 
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", 
    "by", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from", 
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him", 
    "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", 
    "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once", 
    "only", "or", "other", "our", "ours", "ourselves", "out", "over", "own", "same", "she", 
    "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves", 
    "then", "there", "these", "they", "this", "those", "through", "to", "too", "under", "until", 
    "up", "very", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom", 
    "why", "with", "would", "you", "your", "yours", "yourself", "yourselves"
}

def tokenize(text: str) -> List[str]:
    """Tokenize and normalize text into lowercase alphanumeric tokens, filtering stopwords."""
    words = re.findall(r'\b[a-zA-Z0-9_-]{2,}\b', text.lower())
    return [w for w in words if w not in STOP_WORDS]

class BM25Index:
    """Production BM25Okapi implementation for in-memory keyword search."""
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_chunks: List[Dict[str, Any]] = []
        self.tokenized_corpus: List[List[str]] = []
        self.doc_len: List[int] = []
        self.avgdl: float = 0.0
        self.df: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}

    def fit(self, chunks: List[Dict[str, Any]]):
        self.corpus_chunks = chunks
        self.tokenized_corpus = []
        self.doc_len = []
        self.df = {}
        self.idf = {}

        n_docs = len(chunks)
        if n_docs == 0:
            self.avgdl = 0.0
            return

        for chunk in chunks:
            # Combine content, section and doc title for better searchability
            enriched_text = f"{chunk.get('document_name', '')} {chunk.get('section', '')} {chunk.get('content', '')}"
            tokens = tokenize(enriched_text)
            self.tokenized_corpus.append(tokens)
            self.doc_len.append(len(tokens))

            unique_tokens = set(tokens)
            for t in unique_tokens:
                self.df[t] = self.df.get(t, 0) + 1

        self.avgdl = sum(self.doc_len) / n_docs

        for t, freq in self.df.items():
            # Standard Lucene/BM25 IDF formula
            self.idf[t] = math.log(1.0 + (n_docs - freq + 0.5) / (freq + 0.5))

    def search(self, query: str, top_k: int = 10) -> List[Tuple[Dict[str, Any], float]]:
        if not self.corpus_chunks:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores = [0.0] * len(self.corpus_chunks)
        for t in query_tokens:
            if t not in self.idf:
                continue
            idf_val = self.idf[t]
            for i, doc_tokens in enumerate(self.tokenized_corpus):
                f = doc_tokens.count(t)
                if f > 0:
                    num = f * (self.k1 + 1.0)
                    denom = f + self.k1 * (1.0 - self.b + self.b * (self.doc_len[i] / (self.avgdl or 1.0)))
                    scores[i] += idf_val * (num / denom)

        ranked = [(self.corpus_chunks[i], scores[i]) for i in range(len(scores)) if scores[i] > 0]
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked[:top_k]
