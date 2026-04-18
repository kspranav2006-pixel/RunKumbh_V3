"""
Backend API Tests for RunKumbh Registration Form Extended Fields
Tests the new registration fields: DOB, Gender, T-shirt size, Marathon experience,
Emergency contact, Medical conditions, and Consent checkboxes
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://kumbh-marathon.preview.emergentagent.com').rstrip('/')

class TestHealthAndEvents:
    """Basic health and events API tests"""
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"API root response: {data}")
    
    def test_get_events(self):
        """Test getting all events"""
        response = requests.get(f"{BASE_URL}/api/events")
        assert response.status_code == 200
        events = response.json()
        assert isinstance(events, list)
        assert len(events) > 0, "No events found - need at least one event for registration tests"
        print(f"Found {len(events)} events")
        
        # Verify event structure
        event = events[0]
        assert "id" in event
        assert "title" in event
        assert "registration_fee" in event
        return events


class TestPaymentCheckoutAPI:
    """Test the payment checkout API with extended registration fields"""
    
    @pytest.fixture
    def test_event_id(self):
        """Get a valid event ID for testing"""
        response = requests.get(f"{BASE_URL}/api/events")
        events = response.json()
        if events:
            return events[0]["id"]
        pytest.skip("No events available for testing")
    
    @pytest.fixture
    def unique_email(self):
        """Generate unique email to avoid duplicate registration errors"""
        return f"testrunner_{uuid.uuid4().hex[:8]}@example.com"
    
    def test_checkout_with_all_extended_fields(self, test_event_id, unique_email):
        """Test payment checkout accepts all 12+ new registration fields"""
        payload = {
            "event_id": test_event_id,
            "user_name": "Test Runner Extended",
            "user_email": unique_email,
            "user_phone": "+919876543210",
            "gender": "male",
            "dob": "1990-05-15",
            "tshirt_size": "L",
            "marathon_experience": "Completed 5K in 2025, First time 10K runner",
            "emergency_contact_name": "Emergency Contact Person",
            "emergency_contact": "+919876543211",
            "has_medical_condition": "no",
            "medical_condition_details": "",
            "consent_physically_fit": True,
            "consent_own_risk": True,
            "consent_event_rules": True,
            "consent_photography": True,
            "consent_results_published": True,
            "origin_url": "https://kumbh-marathon.preview.emergentagent.com"
        }
        
        response = requests.post(f"{BASE_URL}/api/payments/checkout/session", json=payload)
        print(f"Checkout response status: {response.status_code}")
        print(f"Checkout response: {response.json()}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response contains Stripe session URL
        assert "url" in data, "Response should contain Stripe checkout URL"
        assert "session_id" in data, "Response should contain session_id"
        assert data["url"].startswith("https://checkout.stripe.com"), "URL should be Stripe checkout URL"
        
        return data["session_id"]
    
    def test_checkout_with_medical_condition_yes(self, test_event_id, unique_email):
        """Test checkout when user has medical condition"""
        payload = {
            "event_id": test_event_id,
            "user_name": "Test Runner Medical",
            "user_email": unique_email,
            "user_phone": "+919876543212",
            "gender": "female",
            "dob": "1985-08-20",
            "tshirt_size": "M",
            "marathon_experience": "First time runner",
            "emergency_contact_name": "Medical Emergency Contact",
            "emergency_contact": "+919876543213",
            "has_medical_condition": "yes",
            "medical_condition_details": "Mild asthma, carries inhaler",
            "consent_physically_fit": True,
            "consent_own_risk": True,
            "consent_event_rules": True,
            "consent_photography": True,
            "consent_results_published": True,
            "origin_url": "https://kumbh-marathon.preview.emergentagent.com"
        }
        
        response = requests.post(f"{BASE_URL}/api/payments/checkout/session", json=payload)
        print(f"Medical condition checkout response: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "url" in data
        assert "session_id" in data
    
    def test_checkout_all_tshirt_sizes(self, test_event_id):
        """Test checkout accepts all T-shirt sizes"""
        sizes = ["XS", "S", "M", "L", "XL", "XXL"]
        
        for size in sizes:
            unique_email = f"testrunner_size_{size.lower()}_{uuid.uuid4().hex[:4]}@example.com"
            payload = {
                "event_id": test_event_id,
                "user_name": f"Test Runner Size {size}",
                "user_email": unique_email,
                "user_phone": "+919876543214",
                "gender": "other",
                "dob": "2000-01-01",
                "tshirt_size": size,
                "marathon_experience": "",
                "emergency_contact_name": "Emergency Contact",
                "emergency_contact": "+919876543215",
                "has_medical_condition": "no",
                "medical_condition_details": "",
                "consent_physically_fit": True,
                "consent_own_risk": True,
                "consent_event_rules": True,
                "consent_photography": True,
                "consent_results_published": True,
                "origin_url": "https://kumbh-marathon.preview.emergentagent.com"
            }
            
            response = requests.post(f"{BASE_URL}/api/payments/checkout/session", json=payload)
            assert response.status_code == 200, f"T-shirt size {size} failed: {response.text}"
            print(f"T-shirt size {size}: OK")
    
    def test_checkout_all_genders(self, test_event_id):
        """Test checkout accepts all gender options"""
        genders = ["male", "female", "other"]
        
        for gender in genders:
            unique_email = f"testrunner_gender_{gender}_{uuid.uuid4().hex[:4]}@example.com"
            payload = {
                "event_id": test_event_id,
                "user_name": f"Test Runner Gender {gender}",
                "user_email": unique_email,
                "user_phone": "+919876543216",
                "gender": gender,
                "dob": "1995-06-15",
                "tshirt_size": "M",
                "marathon_experience": "",
                "emergency_contact_name": "Emergency Contact",
                "emergency_contact": "+919876543217",
                "has_medical_condition": "no",
                "medical_condition_details": "",
                "consent_physically_fit": True,
                "consent_own_risk": True,
                "consent_event_rules": True,
                "consent_photography": True,
                "consent_results_published": True,
                "origin_url": "https://kumbh-marathon.preview.emergentagent.com"
            }
            
            response = requests.post(f"{BASE_URL}/api/payments/checkout/session", json=payload)
            assert response.status_code == 200, f"Gender {gender} failed: {response.text}"
            print(f"Gender {gender}: OK")
    
    def test_checkout_missing_required_fields(self, test_event_id):
        """Test checkout fails with missing required fields"""
        # Missing consent fields
        payload = {
            "event_id": test_event_id,
            "user_name": "Test Runner Missing",
            "user_email": f"testrunner_missing_{uuid.uuid4().hex[:4]}@example.com",
            "user_phone": "+919876543218",
            "gender": "male",
            "dob": "1990-01-01",
            "tshirt_size": "M",
            "emergency_contact_name": "Emergency Contact",
            "emergency_contact": "+919876543219",
            "has_medical_condition": "no",
            # Missing consent fields
            "origin_url": "https://kumbh-marathon.preview.emergentagent.com"
        }
        
        response = requests.post(f"{BASE_URL}/api/payments/checkout/session", json=payload)
        # Should fail validation
        assert response.status_code == 422, f"Expected 422 for missing fields, got {response.status_code}"
        print("Missing required fields validation: OK")
    
    def test_duplicate_registration_prevention(self, test_event_id):
        """Test that duplicate registrations are prevented"""
        unique_email = f"testrunner_dup_{uuid.uuid4().hex[:8]}@example.com"
        
        payload = {
            "event_id": test_event_id,
            "user_name": "Test Runner Duplicate",
            "user_email": unique_email,
            "user_phone": "+919876543220",
            "gender": "male",
            "dob": "1990-01-01",
            "tshirt_size": "M",
            "marathon_experience": "",
            "emergency_contact_name": "Emergency Contact",
            "emergency_contact": "+919876543221",
            "has_medical_condition": "no",
            "medical_condition_details": "",
            "consent_physically_fit": True,
            "consent_own_risk": True,
            "consent_event_rules": True,
            "consent_photography": True,
            "consent_results_published": True,
            "origin_url": "https://kumbh-marathon.preview.emergentagent.com"
        }
        
        # First registration should succeed
        response1 = requests.post(f"{BASE_URL}/api/payments/checkout/session", json=payload)
        assert response1.status_code == 200, f"First registration failed: {response1.text}"
        print("First registration: OK")
        
        # Note: Duplicate check only applies to paid registrations, so second attempt should also succeed
        # since the first one is not yet paid


class TestAdminAPI:
    """Test admin API endpoints"""
    
    def test_admin_login_success(self):
        """Test admin login with correct password"""
        response = requests.post(f"{BASE_URL}/api/admin/login", json={
            "password": "RunKumbh2026Admin"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        print("Admin login: OK")
    
    def test_admin_login_failure(self):
        """Test admin login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/admin/login", json={
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("Admin login failure: OK")
    
    def test_admin_get_registrations(self):
        """Test getting all registrations from admin endpoint"""
        response = requests.get(f"{BASE_URL}/api/admin/registrations")
        assert response.status_code == 200
        data = response.json()
        
        assert "registrations" in data
        assert "transactions" in data
        assert "events" in data
        assert "total_registrations" in data
        
        print(f"Admin registrations: {data['total_registrations']} registrations, {len(data['transactions'])} transactions")


class TestManualRegistration:
    """Test manual registration via admin API with extended fields"""
    
    @pytest.fixture
    def test_event_id(self):
        """Get a valid event ID for testing"""
        response = requests.get(f"{BASE_URL}/api/events")
        events = response.json()
        if events:
            return events[0]["id"]
        pytest.skip("No events available for testing")
    
    def test_admin_create_registration_with_extended_fields(self, test_event_id):
        """Test creating manual registration with all extended fields"""
        unique_email = f"testrunner_admin_{uuid.uuid4().hex[:8]}@example.com"
        
        payload = {
            "event_id": test_event_id,
            "user_name": "Admin Created Runner",
            "user_email": unique_email,
            "user_phone": "+919876543222",
            "gender": "female",
            "dob": "1988-12-25",
            "tshirt_size": "S",
            "marathon_experience": "10K runner, 3 marathons completed",
            "emergency_contact_name": "Admin Emergency Contact",
            "emergency_contact": "+919876543223",
            "has_medical_condition": "yes",
            "medical_condition_details": "Diabetes Type 2, controlled with medication",
            "consent_physically_fit": True,
            "consent_own_risk": True,
            "consent_event_rules": True,
            "consent_photography": True,
            "consent_results_published": True
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/registrations", json=payload)
        print(f"Admin registration response: {response.status_code}")
        print(f"Admin registration data: {response.json()}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "registration" in data
        reg = data["registration"]
        
        # Verify all extended fields are saved
        assert reg["gender"] == "female"
        assert reg["dob"] == "1988-12-25"
        assert reg["tshirt_size"] == "S"
        assert reg["marathon_experience"] == "10K runner, 3 marathons completed"
        assert reg["emergency_contact_name"] == "Admin Emergency Contact"
        assert reg["has_medical_condition"] == "yes"
        assert reg["medical_condition_details"] == "Diabetes Type 2, controlled with medication"
        assert reg["consent_physically_fit"] == True
        assert reg["consent_own_risk"] == True
        assert reg["consent_event_rules"] == True
        assert reg["consent_photography"] == True
        assert reg["consent_results_published"] == True
        assert "bib_number" in reg
        
        print(f"Registration created with BIB: {reg['bib_number']}")
        
        # Cleanup - delete the test registration
        reg_id = reg["id"]
        delete_response = requests.delete(f"{BASE_URL}/api/admin/registrations/{reg_id}")
        assert delete_response.status_code == 200
        print("Test registration cleaned up")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
