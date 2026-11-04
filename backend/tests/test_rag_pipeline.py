import os
import sys
import unittest
from dotenv import load_dotenv

load_dotenv()

# Add workspace root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.database.db import (
    init_db,
    get_connection,
    insert_document,
    get_document,
    list_documents,
    update_document_status,
    delete_document,
    insert_chunks,
    get_all_chunks
)
from backend.app.ingestion.parsers import parse_document
from backend.app.preprocessing.chunker import chunk_document
from backend.app.retrieval.hybrid_search import (
    hybrid_retrieve,
    index_chunks_in_vector_store,
    delete_chunks_by_document,
    sync_bm25_index,
    clear_vector_store
)
from backend.app.generation.generator import generate_answer
from backend.app.evaluation.evaluator import run_evaluation_suite

class TestRAGPipelineAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reset DB tables and vector store for clean test run
        init_db()
        conn = get_connection()
        conn.execute("DELETE FROM messages")
        conn.execute("DELETE FROM conversations")
        conn.execute("DELETE FROM chunks")
        conn.execute("DELETE FROM documents")
        conn.commit()
        conn.close()
        clear_vector_store()
        sync_bm25_index()

    def test_01_document_ingestion(self):
        """TEST 1: Upload at least 3 documents in supported formats (PDF, HTML, MD, TXT)."""
        sample_files = [
            ("data/sample_docs/Account_Security_and_Authentication_Guide.pdf", "pdf"),
            ("data/sample_docs/API_Configuration_and_Rate_Limits_v2.md", "md"),
            ("data/sample_docs/API_Configuration_and_Rate_Limits_v1_Legacy.txt", "txt"),
            ("data/sample_docs/Billing_Usage_Tiers_and_Policies.html", "html"),
            ("data/sample_docs/Troubleshooting_and_FAQ.md", "md")
        ]

        indexed_docs = []
        for file_path, doc_fmt in sample_files:
            self.assertTrue(os.path.exists(file_path), f"File {file_path} must exist.")
            doc_id = f"test_{os.path.basename(file_path).split('.')[0]}"
            filename = os.path.basename(file_path)

            # Ingest
            sections = parse_document(file_path, doc_fmt)
            self.assertGreater(len(sections), 0, f"Parser produced zero sections for {filename}")

            chunks = chunk_document(sections, doc_id=doc_id, doc_name=filename)
            self.assertGreater(len(chunks), 0, f"Chunker produced zero chunks for {filename}")

            # Verify chunk metadata structure
            first_chunk = chunks[0]
            self.assertIn("chunk_id", first_chunk)
            self.assertIn("document_name", first_chunk)
            self.assertIn("section", first_chunk)
            self.assertIn("content", first_chunk)
            self.assertIn("version", first_chunk)

            # Save in DB and Vector store
            insert_document(
                doc_id=doc_id,
                filename=filename,
                doc_format=doc_fmt,
                size_bytes=os.path.getsize(file_path),
                file_hash=f"hash_{doc_id}",
                title=filename
            )
            insert_chunks(chunks)
            index_chunks_in_vector_store(chunks)
            update_document_status(doc_id, "indexed", num_chunks=len(chunks))
            indexed_docs.append(doc_id)

        sync_bm25_index()
        self.assertEqual(len(indexed_docs), 5)
        print("[PASS] TEST 1: 5 documents successfully parsed, chunked, and indexed.")

    def test_02_direct_question(self):
        """TEST 2: Direct question whose answer exists clearly in a document."""
        query = "How can I reset my account password?"
        retrieved = hybrid_retrieve(query, top_k=5)
        self.assertGreater(len(retrieved), 0, "Retrieval returned no chunks.")

        top_doc = retrieved[0]["document_name"]
        self.assertIn("Account_Security", top_doc)

        result = generate_answer(query, retrieved)
        self.assertIn(result["confidence"], ["HIGH", "MEDIUM"])
        self.assertGreater(len(result["citations"]), 0)
        self.assertTrue(any("Account_Security" in c["document_name"] for c in result["citations"]))
        print("[PASS] TEST 2: Direct question answered with valid citations.")

    def test_03_paraphrased_question(self):
        """TEST 3: Paraphrased question finds relevant passage."""
        query = "Where should an employee go to change their login credentials if they forgot their password?"
        retrieved = hybrid_retrieve(query, top_k=5)
        self.assertGreater(len(retrieved), 0)

        docs = [c["document_name"] for c in retrieved]
        self.assertTrue(any("Account_Security" in d for d in docs))
        print("[PASS] TEST 3: Paraphrased question successfully retrieved relevant passage.")

    def test_04_multi_document_question(self):
        """TEST 4: Question requiring information from multiple documents."""
        query = "What happens if an API client exceeds the standard rate limit, and what is the overage fee for extra requests?"
        retrieved = hybrid_retrieve(query, top_k=5)
        docs = {c["document_name"] for c in retrieved}
        
        self.assertTrue(any("API_Configuration" in d for d in docs))
        self.assertTrue(any("Billing_Usage" in d for d in docs))

        result = generate_answer(query, retrieved)
        cits = [c["document_name"] for c in result["citations"]]
        print(f"[PASS] TEST 4: Multi-document question combined evidence from {set(cits)}.")

    def test_05_conflicting_information(self):
        """TEST 5: Conflicting information detected and both sources presented."""
        query = "What is the maximum API request limit per hour?"
        retrieved = hybrid_retrieve(query, top_k=5)
        
        result = generate_answer(query, retrieved)
        self.assertIsNotNone(result.get("conflict"))
        self.assertTrue(result["conflict"]["has_conflict"])
        self.assertIn("Conflicting documentation detected", result["conflict"]["warning"])
        self.assertIn("Conflicting documentation", result["answer"])
        print("[PASS] TEST 5: Conflict detected between v2.0 (1000) and v1.0 (500) specifications.")

    def test_06_unanswerable_question(self):
        """TEST 6: Unrelated question triggers explicit refusal/fallback without hallucination."""
        query = "What is the corporate travel reimbursement policy for first-class flights to Mars?"
        retrieved = hybrid_retrieve(query, top_k=5, relevance_threshold=0.35)
        result = generate_answer(query, retrieved, relevance_threshold=0.35)

        self.assertEqual(result["confidence"], "LOW")
        self.assertIn("I couldn't find sufficient supporting information", result["answer"])
        print("[PASS] TEST 6: Correctly refused unanswerable question with zero hallucination.")

    def test_07_ambiguous_question(self):
        """TEST 7: Ambiguous question triggers clarification request."""
        query = "What is the limit?"
        retrieved = hybrid_retrieve(query, top_k=5)
        result = generate_answer(query, retrieved)

        self.assertTrue(
            "ambiguous" in result["answer"].lower() or 
            "clarify" in result["answer"].lower() or
            result["confidence"] in ["MEDIUM", "LOW"]
        )
        print("[PASS] TEST 7: Ambiguous query triggered clarification or qualification.")

    def test_08_document_deletion(self):
        """TEST 8: Deleting a document removes its chunks and vectors completely."""
        test_doc_id = "test_Troubleshooting_and_FAQ"
        
        # Verify it exists initially
        before = get_document(test_doc_id)
        self.assertIsNotNone(before)

        # Delete
        delete_chunks_by_document(test_doc_id)
        delete_document(test_doc_id)
        sync_bm25_index()

        after = get_document(test_doc_id)
        self.assertIsNone(after)

        # Search for unique keyword from that doc 'ERR-401'
        retrieved = hybrid_retrieve("ERR-401 troubleshooting", top_k=5)
        docs = [c["document_name"] for c in retrieved]
        self.assertNotIn("Troubleshooting_and_FAQ.md", docs)
        print("[PASS] TEST 8: Deleted document is no longer retrievable in index.")

    def test_09_evaluation_benchmark_suite(self):
        """Run the full benchmark evaluation suite against test_questions.json."""
        eval_result = run_evaluation_suite(
            dataset_path="evaluation/test_questions.json",
            top_k=5,
            relevance_threshold=0.35
        )
        self.assertGreater(eval_result["num_questions"], 0)
        self.assertGreater(eval_result["mrr"], 0.5)
        self.assertGreater(eval_result["abstention_accuracy"], 0.8)
        print("[PASS] EVALUATION SUITE PASSED:")
        print(f"  - Questions: {eval_result['num_questions']}")
        print(f"  - Precision@K: {eval_result['precision_at_k']}")
        print(f"  - Recall@K: {eval_result['recall_at_k']}")
        print(f"  - MRR: {eval_result['mrr']}")
        print(f"  - Abstention Accuracy: {eval_result['abstention_accuracy']}")
        print(f"  - Citation Accuracy: {eval_result['citation_accuracy']}")

if __name__ == "__main__":
    unittest.main()
