import httpx
import json

BASE_URL = "http://127.0.0.1:8000"

def test_api_suite():
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)

    print("1. Testing Health Endpoint...")
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("   Health OK:", res.json())

    print("2. Testing Current User Profile (Ramesh Kumar)...")
    res = client.get("/api/auth/users/me")
    assert res.status_code == 200, f"User fetch failed: {res.text}"
    user = res.json()
    print(f"   Logged in as: {user['name']} ({user['role_name']}) - {user['employee_id']}")
    assert user['name'] == "Ramesh Kumar"
    assert user['employee_id'] == "MOSPI-SO-7429"

    print("3. Testing Competency Gaps Engine...")
    res = client.get("/api/competency/gaps")
    assert res.status_code == 200, f"Gaps fetch failed: {res.text}"
    gaps_data = res.json()
    print(f"   Overall Score: {gaps_data['overall_competency_score']}%")
    print(f"   Priority Gaps Count: {gaps_data['high_gaps_count']} High Gaps, {gaps_data['moderate_gaps_count']} Moderate Gaps")
    
    # Verify exact prompt-specified baseline gaps
    gap_map = {g['competency_name']: g for g in gaps_data['ranked_gaps']}
    assert gap_map['Sampling Methods']['baseline_score'] == 42.0, "Sampling Methods baseline mismatch"
    assert gap_map['Data Visualization']['baseline_score'] == 35.0, "Data Visualization baseline mismatch"
    assert gap_map['Statistical Analysis']['baseline_score'] == 61.0, "Statistical Analysis baseline mismatch"
    assert gap_map['Data Quality']['baseline_score'] == 82.0, "Data Quality baseline mismatch"
    print("   Verified Baseline Scores: Sampling=42%, DataViz=35%, StatAnalysis=61%, DataQuality=82%")

    print("4. Testing iGOT Course Recommendations & Explainability...")
    res = client.get("/api/recommendations")
    assert res.status_code == 200, f"Recommendations failed: {res.text}"
    recs = res.json()
    print(f"   Total iGOT courses recommended: {len(recs)}")
    print(f"   Top Recommendation: {recs[0]['course']['title']}")
    print(f"   Explainability: \"{recs[0]['reason']}\"")
    assert len(recs) > 0

    print("5. Testing Document Ingestion Pipeline...")
    res = client.get("/api/documents")
    assert res.status_code == 200, f"Documents fetch failed: {res.text}"
    docs = res.json()
    assert len(docs) > 0, "No documents found"
    sample_doc = docs[0]
    print(f"   Active Document: {sample_doc['filename']} (Status: {sample_doc['processing_status']}, Pages: {sample_doc['page_count']})")

    print("6. Testing Document Chunks...")
    res = client.get(f"/api/documents/{sample_doc['id']}/chunks")
    assert res.status_code == 200
    chunks = res.json()
    print(f"   Retrieved {len(chunks)} chunks with page and section metadata.")

    print("7. Testing AI Grounded MCQ Generator...")
    res = client.post(f"/api/documents/{sample_doc['id']}/generate-quiz", json={
        "document_id": sample_doc['id'],
        "num_questions": 5,
        "difficulty": "Mixed"
    })
    assert res.status_code == 200, f"MCQ generation failed: {res.text}"
    mcqs = res.json()
    assert len(mcqs) > 0
    print(f"   Generated {len(mcqs)} grounded MCQs. Sample Question 1:")
    print(f"   Q: {mcqs[0]['question_text']}")
    print(f"   Citation: Page {mcqs[0]['source_page']} ({mcqs[0]['source_document']})")

    print("8. Testing Interactive Quiz Submission & Closed-Loop Score Update...")
    quiz_answers = [
        {"question_id": q["id"], "selected_option": q["correct_option"], "time_spent": 15}
        for q in mcqs
    ]
    res = client.post("/api/quiz/submit", json={
        "document_id": sample_doc['id'],
        "answers": quiz_answers
    })
    assert res.status_code == 200, f"Quiz submission failed: {res.text}"
    quiz_eval = res.json()
    print(f"   Quiz Score: {quiz_eval['overall_score']}%")
    print(f"   Adaptive Next Step: {quiz_eval['adaptive_recommendation']}")
    print("   Updated Competency Scores (The Closed Loop):", quiz_eval['updated_competency_scores'])

    print("9. Testing Learner Dashboard API...")
    res = client.get("/api/dashboard/learner")
    assert res.status_code == 200
    dash = res.json()
    print(f"   Learner Dashboard Loaded for {dash['user']['name']}, Net Improvement: +{dash['recent_improvement']}%")

    print("10. Testing Admin Dashboard API...")
    res = client.get("/api/dashboard/admin")
    assert res.status_code == 200
    admin_dash = res.json()
    print(f"   Admin Dashboard: Total Learners: {admin_dash['total_learners']}, Org Avg: {admin_dash['average_competency']}%")
    print(f"   Top Org Gaps: {[g['competency'] for g in admin_dash['top_competency_gaps'][:3]]}")

    print("\nALL 10 API & CLOSED-LOOP SUITE TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    test_api_suite()
