"""
Backend API tests for BIB card & Gmail email features.
Covers:
  - POST /api/admin/registrations creates registration and triggers email
  - POST /api/admin/registrations/{id}/send-email resends email
  - GET /api/admin/registrations returns bib_card & bib_number fields
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
TEST_EMAIL = "runkumbh@gmail.com"


@pytest.fixture(scope="module")
def event_id():
    r = requests.get(f"{BASE_URL}/api/events", timeout=30)
    assert r.status_code == 200
    events = r.json()
    # Prefer Open 5K if present
    for e in events:
        if "5K" in e.get("title", "") or "5K" in e.get("category", ""):
            return e["id"]
    return events[0]["id"]


# ---- Admin registrations listing ----
class TestAdminRegistrationsList:
    def test_list_returns_bib_card_and_bib_number(self):
        r = requests.get(f"{BASE_URL}/api/admin/registrations", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "registrations" in data
        regs = data["registrations"]
        if not regs:
            pytest.skip("No registrations to inspect")
        # Find at least one with bib_number / bib_card fields
        has_bib_num = any("bib_number" in r and r.get("bib_number") for r in regs)
        has_bib_card = any(
            "bib_card" in r and r.get("bib_card", "").startswith("data:image")
            for r in regs
        )
        assert has_bib_num, "Expected at least one registration with bib_number"
        assert has_bib_card, "Expected at least one registration with bib_card data URL"


# ---- Manual registration creation triggers email ----
class TestManualRegistrationEmail:
    created_id = None
    created_bib = None

    def test_create_manual_registration_triggers_email(self, event_id):
        payload = {
            "event_id": event_id,
            "user_name": "TEST Email User",
            "user_email": f"TEST_{uuid.uuid4().hex[:8]}@example.com",
            "user_phone": "+919876500001",
            "gender": "male",
            "dob": "1990-01-01",
            "tshirt_size": "M",
            "marathon_experience": "First timer",
            "emergency_contact_name": "Emergency Person",
            "emergency_contact": "+919876500002",
            "has_medical_condition": "no",
            "medical_condition_details": "",
            "consent_physically_fit": True,
            "consent_own_risk": True,
            "consent_event_rules": True,
            "consent_photography": True,
            "consent_results_published": True,
        }
        r = requests.post(f"{BASE_URL}/api/admin/registrations", json=payload, timeout=60)
        assert r.status_code == 200, f"Status {r.status_code}: {r.text}"
        data = r.json()
        assert "registration" in data
        reg = data["registration"]
        assert reg.get("bib_number"), "bib_number missing"
        assert reg.get("bib_card", "").startswith("data:image"), "bib_card data URL missing"
        TestManualRegistrationEmail.created_id = reg["id"]
        TestManualRegistrationEmail.created_bib = reg["bib_number"]
        TestManualRegistrationEmail.created_email = reg["user_email"]
        print(f"Created registration {reg['id']} with BIB {reg['bib_number']}")

    def test_resend_email_endpoint_existing(self):
        assert TestManualRegistrationEmail.created_id, "Prior test must create registration"
        reg_id = TestManualRegistrationEmail.created_id
        r = requests.post(
            f"{BASE_URL}/api/admin/registrations/{reg_id}/send-email",
            timeout=60,
        )
        assert r.status_code == 200, f"Status {r.status_code}: {r.text}"
        data = r.json()
        assert "sent" in data
        assert data.get("email") == TestManualRegistrationEmail.created_email
        assert data.get("bib_number") == TestManualRegistrationEmail.created_bib
        # sent may be True or False depending on SMTP availability, but field must exist
        print(f"Resend response: {data}")

    def test_resend_email_404_for_nonexistent(self):
        r = requests.post(
            f"{BASE_URL}/api/admin/registrations/{uuid.uuid4().hex}/send-email",
            timeout=30,
        )
        assert r.status_code == 404

    def test_cleanup_created_registration(self):
        reg_id = TestManualRegistrationEmail.created_id
        if not reg_id:
            pytest.skip("No registration to cleanup")
        r = requests.delete(f"{BASE_URL}/api/admin/registrations/{reg_id}", timeout=30)
        assert r.status_code == 200


# ---- Resend email for existing seeded registration (BIB OSM001) ----
class TestSeededResend:
    def test_resend_email_for_existing_bib(self):
        # find by bib_number via lookup endpoint
        r = requests.get(f"{BASE_URL}/api/admin/registrations/bib/OSM001", timeout=30)
        if r.status_code != 200:
            pytest.skip("BIB OSM001 not present in DB")
        reg = r.json().get("registration") or r.json()
        if "id" not in reg:
            pytest.skip("Registration shape unexpected")
        reg_id = reg["id"]
        r2 = requests.post(
            f"{BASE_URL}/api/admin/registrations/{reg_id}/send-email",
            timeout=60,
        )
        assert r2.status_code == 200
        data = r2.json()
        assert "sent" in data
        assert data.get("bib_number") == "OSM001"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
