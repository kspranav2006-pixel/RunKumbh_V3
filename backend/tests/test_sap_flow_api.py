"""
Backend API tests for the new SAP payment flow.

Covers:
- POST /api/register/pending (17-field payload, SAP URL, duplicate rejection)
- PUT /api/admin/registrations/{id} (pending_payment -> confirmed => BIB+QR+bib_card+email;
  already-confirmed no-op; cancelled/pending without BIB regeneration)
- Regressions: GET /api/admin/registrations, POST /api/admin/registrations (manual add),
  POST /api/admin/registrations/{id}/send-email, POST /api/admin/login,
  POST /api/admin/registrations/{id}/checkin
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
EXPECTED_SAP_URL = "https://wds-prd.rvei.edu.in:4430/sap/bc/ui5_ui5/sap/zeventregister/#/scode/RUN_KUMBHA-2026"
ADMIN_PASSWORD = "RunKumbh2026Admin"


# -------- Helpers / fixtures --------
@pytest.fixture(scope="module")
def event_id():
    r = requests.get(f"{BASE_URL}/api/events", timeout=30)
    assert r.status_code == 200, r.text
    events = r.json()
    assert isinstance(events, list) and len(events) > 0
    return events[0]["id"]


@pytest.fixture(scope="module")
def event_obj():
    r = requests.get(f"{BASE_URL}/api/events", timeout=30)
    return r.json()[0]


def _pending_payload(event_id, email=None, name="SAP Test Runner"):
    return {
        "event_id": event_id,
        "user_name": name,
        "user_email": email or f"sap_test_{uuid.uuid4().hex[:8]}@example.com",
        "user_phone": "+919876543210",
        "gender": "male",
        "dob": "1990-05-15",
        "tshirt_size": "L",
        "marathon_experience": "5K, 10K finisher",
        "emergency_contact_name": "Emergency Person",
        "emergency_contact": "+919876543299",
        "has_medical_condition": "no",
        "medical_condition_details": "",
        "consent_physically_fit": True,
        "consent_own_risk": True,
        "consent_event_rules": True,
        "consent_photography": True,
        "consent_results_published": True,
        "origin_url": BASE_URL,
    }


# Track ids to clean up at end
_CREATED_REG_IDS = []


@pytest.fixture(scope="module", autouse=True)
def cleanup():
    yield
    for rid in _CREATED_REG_IDS:
        try:
            requests.delete(f"{BASE_URL}/api/admin/registrations/{rid}", timeout=30)
        except Exception:
            pass


# -------- /register/pending --------
class TestRegisterPending:
    def test_accepts_full_17_field_payload(self, event_id, event_obj):
        payload = _pending_payload(event_id)
        r = requests.post(f"{BASE_URL}/api/register/pending", json=payload, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "registration_id" in data and data["registration_id"]
        assert data["payment_url"] == EXPECTED_SAP_URL
        assert data["event_title"] == event_obj["title"]
        assert data["amount"] == event_obj["registration_fee"]
        _CREATED_REG_IDS.append(data["registration_id"])

        # Verify DB record has status='pending_payment' & empty bib
        admin = requests.get(f"{BASE_URL}/api/admin/registrations", timeout=30).json()
        match = next((x for x in admin["registrations"] if x["id"] == data["registration_id"]), None)
        assert match is not None, "Pending registration not in admin list"
        assert match["status"] == "pending_payment"
        assert match.get("bib_number", "") == ""
        assert not match.get("bib_card")
        # Verify all 17 user-facing fields round-tripped
        for k in ("user_email", "user_name", "user_phone", "gender", "dob", "tshirt_size",
                  "emergency_contact_name", "emergency_contact", "has_medical_condition",
                  "consent_physically_fit", "consent_own_risk", "consent_event_rules",
                  "consent_photography", "consent_results_published"):
            assert k in match, f"Missing {k}"

    def test_rejects_duplicate_same_event_and_email(self, event_id):
        payload = _pending_payload(event_id)
        r1 = requests.post(f"{BASE_URL}/api/register/pending", json=payload, timeout=30)
        assert r1.status_code == 200
        _CREATED_REG_IDS.append(r1.json()["registration_id"])

        r2 = requests.post(f"{BASE_URL}/api/register/pending", json=payload, timeout=30)
        assert r2.status_code == 400, f"Expected 400, got {r2.status_code}: {r2.text}"
        err = r2.json()
        assert "detail" in err
        assert "already registered" in err["detail"].lower()

    def test_rejects_unknown_event(self):
        payload = _pending_payload("nonexistent-event-id-xxxx")
        r = requests.post(f"{BASE_URL}/api/register/pending", json=payload, timeout=30)
        assert r.status_code == 404, r.text


# -------- PUT /admin/registrations/{id} confirm transition --------
class TestAdminConfirmTransition:
    def _create_pending(self, event_id):
        payload = _pending_payload(event_id)
        r = requests.post(f"{BASE_URL}/api/register/pending", json=payload, timeout=30)
        assert r.status_code == 200, r.text
        rid = r.json()["registration_id"]
        _CREATED_REG_IDS.append(rid)
        return rid, payload["user_email"]

    def test_pending_to_confirmed_generates_bib_and_emails(self, event_id):
        rid, email = self._create_pending(event_id)
        r = requests.put(
            f"{BASE_URL}/api/admin/registrations/{rid}",
            json={"status": "confirmed"},
            timeout=60,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["bib_generated"] is True
        assert body["bib_number"] and isinstance(body["bib_number"], str) and len(body["bib_number"]) > 0

        # Persistence: GET to verify
        admin = requests.get(f"{BASE_URL}/api/admin/registrations", timeout=30).json()
        reg = next((x for x in admin["registrations"] if x["id"] == rid), None)
        assert reg is not None
        assert reg["status"] == "confirmed"
        assert reg["bib_number"] == body["bib_number"]
        assert reg.get("qr_code")
        assert reg.get("bib_card", "").startswith("data:image/png;base64,")

    def test_already_confirmed_is_noop(self, event_id):
        # Create pending, confirm it, then re-PUT status=confirmed — must NOT regenerate.
        rid, _ = self._create_pending(event_id)
        r1 = requests.put(f"{BASE_URL}/api/admin/registrations/{rid}",
                          json={"status": "confirmed"}, timeout=60)
        assert r1.status_code == 200
        bib1 = r1.json()["bib_number"]
        assert r1.json()["bib_generated"] is True

        r2 = requests.put(f"{BASE_URL}/api/admin/registrations/{rid}",
                          json={"status": "confirmed"}, timeout=30)
        assert r2.status_code == 200, r2.text
        body = r2.json()
        assert body["bib_generated"] is False
        assert body["bib_number"] == bib1

    def test_status_cancelled_no_bib_generation(self, event_id):
        rid, _ = self._create_pending(event_id)
        r = requests.put(f"{BASE_URL}/api/admin/registrations/{rid}",
                         json={"status": "cancelled"}, timeout=30)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["bib_generated"] is False
        # bib_number should still be empty
        assert body.get("bib_number", "") == ""

        # Verify DB
        admin = requests.get(f"{BASE_URL}/api/admin/registrations", timeout=30).json()
        reg = next((x for x in admin["registrations"] if x["id"] == rid), None)
        assert reg["status"] == "cancelled"
        assert reg.get("bib_number", "") == ""

    def test_status_pending_no_bib_generation(self, event_id):
        rid, _ = self._create_pending(event_id)
        r = requests.put(f"{BASE_URL}/api/admin/registrations/{rid}",
                         json={"status": "pending"}, timeout=30)
        assert r.status_code == 200, r.text
        assert r.json()["bib_generated"] is False


# -------- Regressions --------
class TestRegressions:
    def test_admin_login_ok(self):
        r = requests.post(f"{BASE_URL}/api/admin/login",
                          json={"password": ADMIN_PASSWORD}, timeout=30)
        assert r.status_code == 200
        assert "token" in r.json()

    def test_admin_login_wrong_password(self):
        r = requests.post(f"{BASE_URL}/api/admin/login",
                          json={"password": "wrong"}, timeout=30)
        assert r.status_code == 401

    def test_admin_get_registrations_shape(self):
        r = requests.get(f"{BASE_URL}/api/admin/registrations", timeout=30)
        assert r.status_code == 200
        d = r.json()
        for k in ("registrations", "transactions", "events", "total_registrations"):
            assert k in d, f"Missing key {k}"
        assert isinstance(d["registrations"], list)
        assert isinstance(d["events"], list)

    def test_admin_manual_create_generates_bib(self, event_id):
        email = f"sap_manual_{uuid.uuid4().hex[:8]}@example.com"
        payload = {
            "event_id": event_id,
            "user_name": "Manual Admin Runner",
            "user_email": email,
            "user_phone": "+919876543400",
            "gender": "female",
            "dob": "1992-02-02",
            "tshirt_size": "M",
            "marathon_experience": "Done a few 5Ks",
            "emergency_contact_name": "EC Name",
            "emergency_contact": "+919876543401",
            "has_medical_condition": "no",
            "medical_condition_details": "",
            "consent_physically_fit": True,
            "consent_own_risk": True,
            "consent_event_rules": True,
            "consent_photography": True,
            "consent_results_published": True,
        }
        r = requests.post(f"{BASE_URL}/api/admin/registrations", json=payload, timeout=60)
        assert r.status_code == 200, r.text
        reg = r.json()["registration"]
        assert reg.get("bib_number")
        assert reg.get("bib_card", "").startswith("data:image/png;base64,")
        _CREATED_REG_IDS.append(reg["id"])

    def test_resend_email_endpoint(self, event_id):
        # Need a confirmed registration with bib_number. Create pending + confirm.
        payload = _pending_payload(event_id)
        r = requests.post(f"{BASE_URL}/api/register/pending", json=payload, timeout=30)
        assert r.status_code == 200
        rid = r.json()["registration_id"]
        _CREATED_REG_IDS.append(rid)
        c = requests.put(f"{BASE_URL}/api/admin/registrations/{rid}",
                         json={"status": "confirmed"}, timeout=60)
        assert c.status_code == 200
        # resend
        r2 = requests.post(f"{BASE_URL}/api/admin/registrations/{rid}/send-email", timeout=60)
        assert r2.status_code == 200, r2.text
        body = r2.json()
        assert "sent" in body and "email" in body and "bib_number" in body

    def test_resend_email_404(self):
        r = requests.post(f"{BASE_URL}/api/admin/registrations/nonexistent-id/send-email",
                          timeout=30)
        assert r.status_code == 404

    def test_checkin_endpoint(self, event_id):
        # Create pending, confirm so bib_number exists, then checkin
        payload = _pending_payload(event_id)
        r = requests.post(f"{BASE_URL}/api/register/pending", json=payload, timeout=30)
        assert r.status_code == 200
        rid = r.json()["registration_id"]
        _CREATED_REG_IDS.append(rid)
        c = requests.put(f"{BASE_URL}/api/admin/registrations/{rid}",
                         json={"status": "confirmed"}, timeout=60)
        assert c.status_code == 200
        # checkin
        r2 = requests.post(f"{BASE_URL}/api/admin/registrations/{rid}/checkin", timeout=30)
        assert r2.status_code == 200, r2.text
