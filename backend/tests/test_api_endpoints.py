import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.database.db import init_db
from backend.app.retrieval.hybrid_search import sync_bm25_index
from backend.app.api.routes import (
    health_check,
    get_dashboard_stats,
    list_all_documents,
    submit_question,
    get_evaluation_results,
    get_conversations,
    ChatRequest
)

def run_tests():
    init_db()
    sync_bm25_index()

    # 1. Health
    h = health_check()
    assert h["status"] == "healthy"
    print("[PASS] health_check() ->", h)

    # 2. Dashboard Stats
    stats = get_dashboard_stats()
    assert "total_documents" in stats
    assert "total_chunks" in stats
    assert "retrieval_success_rate" in stats
    print(f"[PASS] get_dashboard_stats() -> {stats['total_documents']} docs, {stats['total_chunks']} chunks")

    # 3. List Documents
    docs = list_all_documents()
    assert len(docs) > 0
    print(f"[PASS] list_all_documents() -> {len(docs)} documents listed")

    # 4. Chat: Direct Question
    req1 = ChatRequest(question="How can I reset my account password?")
    res1 = submit_question(req1)
    assert res1["confidence"] in ["HIGH", "MEDIUM"]
    assert len(res1["citations"]) > 0
    print(f"[PASS] submit_question(Direct) -> Confidence: {res1['confidence']}, Citations: {len(res1['citations'])}")

    # 5. Chat: Conflict Detection
    req2 = ChatRequest(question="What is the maximum API request limit per hour?")
    res2 = submit_question(req2)
    assert res2.get("conflict") is not None
    assert res2["conflict"]["has_conflict"] is True
    print(f"[PASS] submit_question(Conflict) -> Warning: {res2['conflict']['warning']}")

    # 6. Chat: Unanswerable Refusal
    req3 = ChatRequest(question="What is the company reimbursement policy for international business travel meals?")
    res3 = submit_question(req3)
    assert res3["confidence"] == "LOW"
    assert "insufficient" in res3["answer"].lower() or "couldn't find" in res3["answer"].lower()
    print(f"[PASS] submit_question(Unanswerable) -> Correctly abstained with confidence LOW")

    # 7. Conversations
    convs = get_conversations()
    assert len(convs) > 0
    print(f"[PASS] get_conversations() -> {len(convs)} conversation(s) recorded in SQLite")

    # 8. Evaluation Results
    eval_res = get_evaluation_results()
    assert "latest" in eval_res
    print(f"[PASS] get_evaluation_results() -> Latest run found: {eval_res['latest'] is not None}")

    print("\nALL 8 REST API HANDLERS TESTED AND VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
