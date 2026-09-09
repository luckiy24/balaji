import sys
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_routes_mounted():
    print("1. Testing Health...")
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("   Health OK:", res.json())

def test_chat_suggestions():
    print("2. Testing Chat Suggestions...")
    res = client.get("/api/chat/suggestions")
    assert res.status_code == 200, f"Chat suggestions failed: {res.text}"
    data = res.json()
    assert "categories" in data
    assert len(data["categories"]) > 0
    print(f"   Retrieved {len(data['categories'])} prompt categories.")

def test_chat_ask():
    print("3. Testing Chat Ask with Stratified vs Cluster Doubt...")
    payload = {
        "message": "What is the difference between Stratified and Cluster Sampling?"
    }
    res = client.post("/api/chat/ask", json=payload)
    assert res.status_code == 200, f"Chat ask failed: {res.text}"
    data = res.json()
    assert "reply" in data
    assert "Stratified" in data["reply"]
    assert len(data["suggested_questions"]) > 0
    print("   Chat response generated successfully with reply snippet:")
    print("   " + data["reply"][:120].replace('\n', ' '))

def test_certifications():
    print("4. Testing User Certifications...")
    res = client.get("/api/certifications")
    assert res.status_code == 200, f"Certifications fetch failed: {res.text}"
    data = res.json()
    assert "officer" in data
    assert "completed_certificates" in data
    assert "digital_badges" in data
    assert "in_progress_certifications" in data
    print(f"   Officer: {data['officer']['name']} ({data['officer']['employee_id']})")
    print(f"   Completed Certificates: {len(data['completed_certificates'])}")
    print(f"   Digital Badges: {len(data['digital_badges'])}")
    print(f"   In-Progress: {len(data['in_progress_certifications'])}")
    assert len(data["completed_certificates"]) > 0

def test_certificate_verification():
    print("5. Testing Certificate Verification...")
    cert_id = "CERT-IGOT-MOSPI-CORE-001-MOSPI-SO-7429"
    res = client.get(f"/api/certifications/verify/{cert_id}")
    assert res.status_code == 200, f"Certificate verify failed: {res.text}"
    data = res.json()
    assert data["is_valid"] is True
    assert "cryptographic_hash" in data
    print("   Verification Result:", data["verification_status"], data["cryptographic_hash"])

if __name__ == "__main__":
    test_routes_mounted()
    test_chat_suggestions()
    test_chat_ask()
    test_certifications()
    test_certificate_verification()
    print("\nALL BACKEND CHAT & CERTIFICATION TESTS PASSED SUCCESSFULLY!")
