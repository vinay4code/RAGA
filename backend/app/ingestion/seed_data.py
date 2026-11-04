import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from backend.app.database.db import (
    init_db,
    insert_document,
    get_document_by_hash,
    update_document_status,
    insert_chunks
)
from backend.app.ingestion.parsers import parse_document
from backend.app.preprocessing.chunker import chunk_document
from backend.app.retrieval.hybrid_search import (
    index_chunks_in_vector_store,
    sync_bm25_index
)

def seed_sample_documents():
    init_db()
    sample_files = [
        ("data/sample_docs/Account_Security_and_Authentication_Guide.pdf", "pdf", "Account Security & Authentication Policy Guide"),
        ("data/sample_docs/API_Configuration_and_Rate_Limits_v2.md", "md", "API Configuration & Rate Limits Specification (v2.0)"),
        ("data/sample_docs/API_Configuration_and_Rate_Limits_v1_Legacy.txt", "txt", "Legacy API Limits & Architecture (v1.0 Deprecated)"),
        ("data/sample_docs/Billing_Usage_Tiers_and_Policies.html", "html", "Enterprise Billing, Usage Tiers & Quota Policies"),
        ("data/sample_docs/Troubleshooting_and_FAQ.md", "md", "Enterprise Systems Troubleshooting & FAQs")
    ]

    for file_path, doc_fmt, title in sample_files:
        if not os.path.exists(file_path):
            continue
        filename = os.path.basename(file_path)
        doc_id = f"doc_{filename.split('.')[0]}"
        file_hash = f"seed_hash_{filename}"

        if get_document_by_hash(file_hash):
            print(f"Sample doc '{filename}' already seeded.")
            continue

        size_bytes = os.path.getsize(file_path)
        insert_document(
            doc_id=doc_id,
            filename=filename,
            doc_format=doc_fmt,
            size_bytes=size_bytes,
            file_hash=file_hash,
            title=title
        )
        update_document_status(doc_id, "processing")

        sections = parse_document(file_path, doc_fmt)
        chunks = chunk_document(sections, doc_id=doc_id, doc_name=filename)
        insert_chunks(chunks)
        index_chunks_in_vector_store(chunks)
        update_document_status(doc_id, "indexed", num_chunks=len(chunks))
        print(f"Seeded '{filename}' with {len(chunks)} chunks.")

    sync_bm25_index()
    print("Seed complete! Vector store and BM25 index synchronized.")

if __name__ == "__main__":
    seed_sample_documents()
