import json
import os
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from ..retrieval.hybrid_search import hybrid_retrieve
from ..generation.generator import generate_answer
from ..database.db import save_evaluation, get_latest_evaluation, get_all_evaluations

DEFAULT_EVAL_FILE = "./evaluation/test_questions.json"

def load_test_dataset(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    path = file_path or DEFAULT_EVAL_FILE
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_evaluation_suite(
    dataset_path: Optional[str] = None,
    top_k: int = 5,
    relevance_threshold: float = 0.35
) -> Dict[str, Any]:
    dataset = load_test_dataset(dataset_path)
    if not dataset:
        raise ValueError("Evaluation dataset is empty or not found.")

    results = []
    reciprocal_ranks = []
    precisions = []
    recalls = []
    citation_accuracies = []
    answerability_correct_count = 0
    abstention_correct_count = 0
    total_unanswerable = 0
    groundedness_scores = []

    for item in dataset:
        q = item["question"]
        expected_sources = [s.lower() for s in item.get("expected_sources", [])]
        expected_answerable = item.get("answerable", True)
        q_type = item.get("question_type", "direct_answer")

        # 1. Retrieve
        retrieved_chunks = hybrid_retrieve(q, top_k=top_k, relevance_threshold=relevance_threshold)

        # 2. Evaluate Retrieval Metrics
        retrieved_docs = [c.get("document_name", "").lower() for c in retrieved_chunks]
        
        # Recall@K & Precision@K
        if expected_answerable and expected_sources:
            hits = [d for d in retrieved_docs if any(exp in d for exp in expected_sources)]
            p_at_k = len(hits) / len(retrieved_docs) if retrieved_docs else 0.0
            r_at_k = 1.0 if hits else 0.0

            # Rank of first relevant document
            first_rank = 0
            for r_idx, d in enumerate(retrieved_docs):
                if any(exp in d for exp in expected_sources):
                    first_rank = r_idx + 1
                    break
            rr = 1.0 / first_rank if first_rank > 0 else 0.0
        else:
            # Unanswerable question: ideally 0 relevant documents retrieved or low scores
            p_at_k = 1.0 if len(retrieved_chunks) == 0 else 0.5
            r_at_k = 1.0
            rr = 1.0

        precisions.append(p_at_k)
        recalls.append(r_at_k)
        reciprocal_ranks.append(rr)

        # 3. Generate Answer
        gen_result = generate_answer(q, retrieved_chunks, relevance_threshold=relevance_threshold)
        actual_answer = gen_result.get("answer", "")
        confidence = gen_result.get("confidence", "LOW")
        citations = gen_result.get("citations", [])

        # 4. Evaluate Answerability & Abstention
        is_unanswerable = not expected_answerable
        if is_unanswerable:
            total_unanswerable += 1
            if confidence == "LOW" or "couldn't find" in actual_answer.lower() or "insufficient" in actual_answer.lower():
                abstention_correct_count += 1
                answerability_correct = True
            else:
                answerability_correct = False
        else:
            if confidence in ["HIGH", "MEDIUM"]:
                answerability_correct = True
            else:
                answerability_correct = False

        if answerability_correct:
            answerability_correct_count += 1

        # 5. Evaluate Citation Correctness
        if expected_answerable and citations:
            valid_cits = 0
            for cit in citations:
                c_doc = cit.get("document_name", "").lower()
                if any(exp in c_doc for exp in expected_sources):
                    valid_cits += 1
            cit_acc = valid_cits / len(citations)
        elif not expected_answerable and not citations:
            cit_acc = 1.0
        else:
            cit_acc = 0.0
        citation_accuracies.append(cit_acc)

        # 6. Evaluate Groundedness
        grounded = 1.0 if (confidence != "LOW" and (citations or retrieved_chunks)) else (1.0 if not expected_answerable else 0.0)
        groundedness_scores.append(grounded)

        results.append({
            "question": q,
            "question_type": q_type,
            "answerable": expected_answerable,
            "expected_sources": item.get("expected_sources", []),
            "retrieved_sources": [c.get("document_name") for c in retrieved_chunks],
            "confidence": confidence,
            "actual_answer": actual_answer,
            "citations": citations,
            "p_at_k": round(p_at_k, 3),
            "r_at_k": round(r_at_k, 3),
            "reciprocal_rank": round(rr, 3),
            "citation_accuracy": round(cit_acc, 3),
            "answerability_correct": answerability_correct
        })

    total_q = len(dataset)
    mean_p = round(sum(precisions) / total_q, 4) if total_q else 0.0
    mean_r = round(sum(recalls) / total_q, 4) if total_q else 0.0
    mrr = round(sum(reciprocal_ranks) / total_q, 4) if total_q else 0.0
    mean_cit_acc = round(sum(citation_accuracies) / total_q, 4) if total_q else 0.0
    mean_grounded = round(sum(groundedness_scores) / total_q, 4) if total_q else 0.0
    answerability_acc = round(answerability_correct_count / total_q, 4) if total_q else 0.0
    abstention_rate = round(abstention_correct_count / (total_unanswerable or 1), 4)

    eval_id = str(uuid.uuid4())
    summary = {
        "id": eval_id,
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset_name": os.path.basename(dataset_path or DEFAULT_EVAL_FILE),
        "num_questions": total_q,
        "precision_at_k": mean_p,
        "recall_at_k": mean_r,
        "mrr": mrr,
        "groundedness_score": mean_grounded,
        "citation_accuracy": mean_cit_acc,
        "answerability_accuracy": answerability_acc,
        "abstention_accuracy": abstention_rate,
        "unanswerable_questions_tested": total_unanswerable,
        "unanswerable_rejected_correctly": abstention_correct_count,
        "results": results
    }

    # Save to SQLite
    save_evaluation(
        eval_id=eval_id,
        dataset_name=summary["dataset_name"],
        num_questions=total_q,
        p_at_k=mean_p,
        r_at_k=mean_r,
        mrr=mrr,
        groundedness=mean_grounded,
        citation_acc=mean_cit_acc,
        abstention_acc=abstention_rate,
        details=summary
    )

    return summary
