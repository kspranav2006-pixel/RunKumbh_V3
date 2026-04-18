from fastapi import FastAPI, APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Stripe Configuration
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY', 'sk_test_emergent')

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# ==================== MODELS ====================

# User Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    phone: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserResponse(BaseModel):
    user: User
    token: str

# Event Models
class EventCreate(BaseModel):
    title: str
    description: str
    date: str
    location: str
    distance: str
    category: str
    max_participants: int
    image_url: str
    registration_fee: float

class Event(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    date: str
    location: str
    distance: str
    category: str
    max_participants: int
    image_url: str
    registration_fee: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Registration Models
class RegistrationCreate(BaseModel):
    event_id: str
    user_email: str
    user_name: str
    user_phone: str
    gender: str
    dob: str
    tshirt_size: str
    marathon_experience: Optional[str] = ""
    emergency_contact_name: str
    emergency_contact: str
    has_medical_condition: str
    medical_condition_details: Optional[str] = ""
    consent_physically_fit: bool
    consent_own_risk: bool
    consent_event_rules: bool
    consent_photography: bool
    consent_results_published: bool

class Registration(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    event_id: str
    user_email: str
    user_name: str
    user_phone: str
    gender: str
    dob: str
    tshirt_size: str
    marathon_experience: str = ""
    emergency_contact_name: str
    emergency_contact: str
    has_medical_condition: str
    medical_condition_details: str = ""
    consent_physically_fit: bool
    consent_own_risk: bool
    consent_event_rules: bool
    consent_photography: bool
    consent_results_published: bool
    registration_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "confirmed"
    bib_number: str

# Contact Models
class ContactCreate(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str

class Contact(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    subject: str
    message: str
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "new"

# Payment Models
class PaymentCheckoutRequest(BaseModel):
    event_id: str
    user_name: str
    user_email: EmailStr
    user_phone: str
    gender: str
    dob: str
    tshirt_size: str
    marathon_experience: Optional[str] = ""
    emergency_contact_name: str
    emergency_contact: str
    has_medical_condition: str
    medical_condition_details: Optional[str] = ""
    consent_physically_fit: bool
    consent_own_risk: bool
    consent_event_rules: bool
    consent_photography: bool
    consent_results_published: bool
    origin_url: str

class PaymentTransaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    event_id: str
    user_name: str
    user_email: EmailStr
    user_phone: str
    amount: float
    currency: str
    payment_status: str = "pending"
    status: str = "initiated"
    bib_number: str = ""
    metadata: Dict = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ==================== HELPER FUNCTIONS ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==================== ROUTES ====================

@api_router.get("/")
async def root():
    return {"message": "RunKumbh API - Monsoon Summer Edition"}

# Auth Routes
@api_router.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user_dict = user_data.model_dump()
    password = user_dict.pop('password')
    user_dict['password_hash'] = hash_password(password)
    user_obj = User(**{k: v for k, v in user_dict.items() if k != 'password_hash'})
    
    doc = user_obj.model_dump()
    doc['password_hash'] = user_dict['password_hash']
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.users.insert_one(doc)
    
    # Create token
    token = create_access_token({"sub": user_obj.email, "id": user_obj.id})
    
    return UserResponse(user=user_obj, token=token)

@api_router.post("/auth/login", response_model=UserResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Convert datetime
    if isinstance(user.get('created_at'), str):
        user['created_at'] = datetime.fromisoformat(user['created_at'])
    
    user_obj = User(**{k: v for k, v in user.items() if k != 'password_hash'})
    token = create_access_token({"sub": user_obj.email, "id": user_obj.id})
    
    return UserResponse(user=user_obj, token=token)

# Event Routes
@api_router.get("/events", response_model=List[Event])
async def get_events():
    events = await db.events.find({}, {"_id": 0}).to_list(1000)
    for event in events:
        if isinstance(event.get('created_at'), str):
            event['created_at'] = datetime.fromisoformat(event['created_at'])
    return events

@api_router.get("/events/{event_id}", response_model=Event)
async def get_event(event_id: str):
    event = await db.events.find_one({"id": event_id}, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    if isinstance(event.get('created_at'), str):
        event['created_at'] = datetime.fromisoformat(event['created_at'])
    
    return event

@api_router.post("/events", response_model=Event)
async def create_event(event_data: EventCreate):
    event_obj = Event(**event_data.model_dump())
    doc = event_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.events.insert_one(doc)
    return event_obj

# Contact Routes
@api_router.post("/contact", response_model=Contact)
async def create_contact(contact_data: ContactCreate):
    contact_obj = Contact(**contact_data.model_dump())
    doc = contact_obj.model_dump()
    doc['submitted_at'] = doc['submitted_at'].isoformat()
    
    await db.contacts.insert_one(doc)
    return contact_obj

@api_router.get("/contacts", response_model=List[Contact])
async def get_contacts():
    contacts = await db.contacts.find({}, {"_id": 0}).to_list(1000)
    for contact in contacts:
        if isinstance(contact.get('submitted_at'), str):
            contact['submitted_at'] = datetime.fromisoformat(contact['submitted_at'])
    return contacts

# Payment Routes
@api_router.post("/payments/checkout/session")
async def create_payment_checkout(request: Request, payment_request: PaymentCheckoutRequest):
    # Get event details
    event = await db.events.find_one({"id": payment_request.event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if already registered
    existing_reg = await db.payment_transactions.find_one({
        "event_id": payment_request.event_id,
        "user_email": payment_request.user_email,
        "payment_status": "paid"
    })
    if existing_reg:
        raise HTTPException(status_code=400, detail="Already registered for this event")
    
    # Get amount from event (server-side, not from frontend)
    amount = float(event['registration_fee'])
    currency = "inr"
    
    # Build success and cancel URLs from frontend origin
    origin_url = payment_request.origin_url
    success_url = f"{origin_url}?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = origin_url
    
    # Initialize Stripe Checkout
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    # Generate BIB number
    bib_number = f"BIB{str(uuid.uuid4())[:8].upper()}"
    
    # Create checkout session
    # Convert boolean values to strings for Stripe metadata (Stripe only accepts strings in metadata)
    metadata = {
        "event_id": payment_request.event_id,
        "event_title": event['title'],
        "user_name": payment_request.user_name,
        "user_email": payment_request.user_email,
        "user_phone": payment_request.user_phone,
        "gender": payment_request.gender,
        "dob": payment_request.dob,
        "tshirt_size": payment_request.tshirt_size,
        "marathon_experience": payment_request.marathon_experience,
        "emergency_contact_name": payment_request.emergency_contact_name,
        "emergency_contact": payment_request.emergency_contact,
        "has_medical_condition": payment_request.has_medical_condition,
        "medical_condition_details": payment_request.medical_condition_details,
        "consent_physically_fit": str(payment_request.consent_physically_fit),
        "consent_own_risk": str(payment_request.consent_own_risk),
        "consent_event_rules": str(payment_request.consent_event_rules),
        "consent_photography": str(payment_request.consent_photography),
        "consent_results_published": str(payment_request.consent_results_published),
        "bib_number": bib_number
    }
    
    checkout_request = CheckoutSessionRequest(
        amount=amount,
        currency=currency,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=metadata
    )
    
    session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Create payment transaction record
    payment_transaction = PaymentTransaction(
        session_id=session.session_id,
        event_id=payment_request.event_id,
        user_name=payment_request.user_name,
        user_email=payment_request.user_email,
        user_phone=payment_request.user_phone,
        amount=amount,
        currency=currency,
        payment_status="pending",
        status="initiated",
        bib_number=bib_number,
        metadata=metadata
    )
    
    doc = payment_transaction.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    await db.payment_transactions.insert_one(doc)
    
    return {"url": session.url, "session_id": session.session_id}

@api_router.get("/payments/checkout/status/{session_id}")
async def get_payment_status(request: Request, session_id: str):
    # Get payment transaction
    transaction = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    if not transaction:
        raise HTTPException(status_code=404, detail="Payment transaction not found")
    
    # If already processed as paid, return the status
    if transaction.get('payment_status') == 'paid':
        return {
            "status": transaction.get('status'),
            "payment_status": transaction.get('payment_status'),
            "amount_total": int(transaction.get('amount', 0) * 100),
            "currency": transaction.get('currency'),
            "metadata": transaction.get('metadata', {}),
            "bib_number": transaction.get('bib_number', '')
        }
    
    # Initialize Stripe Checkout
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    # Get checkout status from Stripe
    checkout_status: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)
    
    # Update transaction status
    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "status": checkout_status.status,
                "payment_status": checkout_status.payment_status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # If payment is successful and not already processed, create registration
    if checkout_status.payment_status == 'paid':
        # Check if registration already exists (prevent duplicate)
        existing_reg = await db.registrations.find_one({
            "event_id": transaction['event_id'],
            "user_email": transaction['user_email']
        })
        
        if not existing_reg:
            # Create registration with all participant data from metadata
            metadata = transaction.get('metadata', {})
            # Convert string boolean values back to actual booleans
            def str_to_bool(val):
                if isinstance(val, bool):
                    return val
                return str(val).lower() == 'true'
            
            reg_data = {
                "user_id": str(uuid.uuid4()),
                "event_id": transaction['event_id'],
                "user_email": transaction['user_email'],
                "user_name": transaction['user_name'],
                "user_phone": transaction['user_phone'],
                "gender": metadata.get('gender', ''),
                "dob": metadata.get('dob', ''),
                "tshirt_size": metadata.get('tshirt_size', 'M'),
                "marathon_experience": metadata.get('marathon_experience', ''),
                "emergency_contact_name": metadata.get('emergency_contact_name', ''),
                "emergency_contact": metadata.get('emergency_contact', ''),
                "has_medical_condition": metadata.get('has_medical_condition', 'no'),
                "medical_condition_details": metadata.get('medical_condition_details', ''),
                "consent_physically_fit": str_to_bool(metadata.get('consent_physically_fit', 'False')),
                "consent_own_risk": str_to_bool(metadata.get('consent_own_risk', 'False')),
                "consent_event_rules": str_to_bool(metadata.get('consent_event_rules', 'False')),
                "consent_photography": str_to_bool(metadata.get('consent_photography', 'False')),
                "consent_results_published": str_to_bool(metadata.get('consent_results_published', 'False')),
                "bib_number": transaction['bib_number'],
                "status": "confirmed"
            }
            
            reg_obj = Registration(**reg_data)
            doc = reg_obj.model_dump()
            doc['registration_date'] = doc['registration_date'].isoformat()
            
            await db.registrations.insert_one(doc)
            
            # TODO: Send confirmation email here
            # Email will be sent with BIB number and event details
    
    return {
        "status": checkout_status.status,
        "payment_status": checkout_status.payment_status,
        "amount_total": checkout_status.amount_total,
        "currency": checkout_status.currency,
        "metadata": checkout_status.metadata,
        "bib_number": transaction.get('bib_number', '')
    }

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    # Get raw body
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    
    # Initialize Stripe Checkout
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    try:
        # Handle webhook
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        # Update transaction based on webhook event
        await db.payment_transactions.update_one(
            {"session_id": webhook_response.session_id},
            {
                "$set": {
                    "payment_status": webhook_response.payment_status,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Admin Routes
class AdminLogin(BaseModel):
    password: str

@api_router.post("/admin/login")
async def admin_login(credentials: AdminLogin):
    admin_password = os.environ.get('ADMIN_PASSWORD', 'RunKumbh2026Admin')
    
    if credentials.password == admin_password:
        # Create a simple admin token
        token = create_access_token({"sub": "admin", "role": "admin"})
        return {"token": token, "message": "Login successful"}
    else:
        raise HTTPException(status_code=401, detail="Invalid password")

@api_router.get("/admin/registrations")
async def get_all_registrations():
    # Get all registrations
    registrations = await db.registrations.find({}, {"_id": 0}).to_list(10000)
    for reg in registrations:
        if isinstance(reg.get('registration_date'), str):
            reg['registration_date'] = datetime.fromisoformat(reg['registration_date'])
    
    # Get all payment transactions
    transactions = await db.payment_transactions.find({}, {"_id": 0}).to_list(10000)
    for trans in transactions:
        if isinstance(trans.get('created_at'), str):
            trans['created_at'] = datetime.fromisoformat(trans['created_at'])
        if isinstance(trans.get('updated_at'), str):
            trans['updated_at'] = datetime.fromisoformat(trans['updated_at'])
    
    # Get events for reference
    events = await db.events.find({}, {"_id": 0}).to_list(1000)
    
    return {
        "registrations": registrations,
        "transactions": transactions,
        "events": events,
        "total_registrations": len(registrations),
        "total_transactions": len(transactions)
    }

@api_router.post("/admin/registrations")
async def create_manual_registration(registration: RegistrationCreate):
    # Check if already registered
    existing_reg = await db.registrations.find_one({
        "event_id": registration.event_id,
        "user_email": registration.user_email
    })
    if existing_reg:
        raise HTTPException(status_code=400, detail="Already registered for this event")
    
    # Create registration
    reg_data = {
        "user_id": str(uuid.uuid4()),
        "event_id": registration.event_id,
        "user_email": registration.user_email,
        "user_name": registration.user_name,
        "user_phone": registration.user_phone,
        "gender": registration.gender,
        "dob": registration.dob,
        "tshirt_size": registration.tshirt_size,
        "marathon_experience": registration.marathon_experience,
        "emergency_contact_name": registration.emergency_contact_name,
        "emergency_contact": registration.emergency_contact,
        "has_medical_condition": registration.has_medical_condition,
        "medical_condition_details": registration.medical_condition_details,
        "consent_physically_fit": registration.consent_physically_fit,
        "consent_own_risk": registration.consent_own_risk,
        "consent_event_rules": registration.consent_event_rules,
        "consent_photography": registration.consent_photography,
        "consent_results_published": registration.consent_results_published,
        "bib_number": f"BIB{str(uuid.uuid4())[:8].upper()}",
        "status": "confirmed"
    }
    
    reg_obj = Registration(**reg_data)
    doc = reg_obj.model_dump()
    doc['registration_date'] = doc['registration_date'].isoformat()
    
    await db.registrations.insert_one(doc)
    
    return {"message": "Registration created successfully", "registration": reg_obj}

@api_router.delete("/admin/registrations/{registration_id}")
async def delete_registration(registration_id: str):
    result = await db.registrations.delete_one({"id": registration_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    return {"message": "Registration deleted successfully"}

@api_router.delete("/admin/transactions/{transaction_id}")
async def delete_transaction(transaction_id: str):
    result = await db.payment_transactions.delete_one({"id": transaction_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return {"message": "Transaction deleted successfully"}

@api_router.put("/admin/registrations/{registration_id}")
async def update_registration(registration_id: str, update_data: dict):
    result = await db.registrations.update_one(
        {"id": registration_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    return {"message": "Registration updated successfully"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
@api_router.put("/admin/events/{event_id}")
async def update_event(event_id: str, event_data: dict):
    # Convert numeric fields if present
    if 'registration_fee' in event_data:
        event_data['registration_fee'] = float(event_data['registration_fee'])
    if 'max_participants' in event_data:
        event_data['max_participants'] = int(event_data['max_participants'])
    
    result = await db.events.update_one(
        {"id": event_id},
        {"$set": event_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"message": "Event updated successfully"}

@api_router.post("/admin/events")
async def create_event(event_data: EventCreate):
    event_obj = Event(**event_data.model_dump())
    doc = event_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.events.insert_one(doc)
    return {"message": "Event created successfully", "event": event_obj}

@api_router.delete("/admin/events/{event_id}")
async def delete_event(event_id: str):
    result = await db.events.delete_one({"id": event_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return {"message": "Event deleted successfully"}