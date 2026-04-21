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
import qrcode
import io
import base64
from PIL import Image, ImageDraw, ImageFont
import barcode
from barcode.writer import ImageWriter
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
from email_service import send_bib_email

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
    qr_code: Optional[str] = None
    bib_card: Optional[str] = None
    blood_group: str = "A+"
    checked_in: bool = False
    checked_in_at: Optional[datetime] = None

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
    bib_number: str = ""  # Will be generated after payment confirmation
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

async def generate_bib_number(event_id: str, gender: str):
    """Generate category-specific BIB numbers with proper prefixes and incremental numbering"""
    # Get event to determine category
    event = await db.events.find_one({"id": event_id}, {"_id": 0})
    if not event:
        return f"BIB{str(uuid.uuid4())[:8].upper()}"
    
    category = event.get('category', '')
    
    # Define prefix based on category and gender
    if category == 'Open 5K' or category == 'Students 5K':
        # Both Open 5K and Students 5K share the same BIB sequence
        prefix = 'OSM' if gender.lower() == 'male' else 'OSW'
    elif category == 'Students 3K':
        prefix = 'SM' if gender.lower() == 'male' else 'SW'
    elif category == 'Family 3K':
        prefix = 'FR'
    elif category == 'Couple 3K':
        prefix = 'CR'
    elif category == 'Staff 3K':
        prefix = 'STAFF'
    else:
        prefix = 'BIB'
    
    # Find the last BIB number with this prefix
    regex_pattern = f"^{prefix}"
    existing_bibs = await db.registrations.find(
        {"bib_number": {"$regex": regex_pattern}},
        {"bib_number": 1, "_id": 0}
    ).to_list(10000)
    
    # Extract numbers and find max
    max_num = 0
    for bib in existing_bibs:
        bib_str = bib.get('bib_number', '')
        try:
            # Extract numeric part after prefix
            num_str = bib_str.replace(prefix, '')
            num = int(num_str)
            if num > max_num:
                max_num = num
        except:
            continue
    
    # Increment and format
    next_num = max_num + 1
    if prefix == 'STAFF':
        return f"{prefix}{next_num:03d}"  # STAFF001, STAFF002...
    else:
        return f"{prefix}{next_num:03d}"  # OM001, OW001, SM001, etc.

def generate_qr_code(bib_number: str) -> str:
    """Generate QR code for BIB number and return as base64 string"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(bib_number)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_base64}"

def generate_bib_card(bib_number: str, category: str, blood_group: str = "A+") -> str:
    """Generate professional BIB card image for t-shirt printing"""
    width, height = 1200, 1200
    img = Image.new('RGB', (width, height), '#FFFFFF')
    draw = ImageDraw.Draw(img)
    
    # Gradient background (teal to blue)
    for y in range(height):
        r = int(13 + (20 - 13) * (y / height))
        g = int(115 + (174 - 115) * (y / height))
        b = int(119 + (242 - 119) * (y / height))
        draw.rectangle([(0, y), (width, y + 1)], fill=(r, g, b))
    
    # Locate an available bold font (DejaVu isn't installed on this image)
    font_candidates = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    font_path = next((p for p in font_candidates if os.path.exists(p)), None)

    def _font(size):
        if font_path:
            return ImageFont.truetype(font_path, size)
        return ImageFont.load_default()

    title_font = _font(120)
    category_font = _font(70)
    bib_font = _font(260)          # fits 6-char BIB (e.g. OSM001) nicely within 1000px box
    blood_label_font = _font(42)
    blood_font = _font(140)        # much larger

    # Top banner
    points = [(0, 0), (width, 0), (width, 200), (width - 150, 200)]
    draw.polygon(points, fill='#FFFFFF')
    draw.text((100, 60), "RunKumbh", fill='#0D7377', font=title_font)
    
    # Category
    cat_bg_points = [(width - 500, 0), (width, 0), (width, 200), (width - 350, 200)]
    draw.polygon(cat_bg_points, fill='#FF6B35')
    draw.text((width - 480, 80), category, fill='#FFFFFF', font=category_font, anchor='lm')
    
    # BIB number (large, centered, upper half of card)
    bib_box_width, bib_box_height = 1000, 500
    bib_box_x = (width - bib_box_width) // 2
    bib_box_y = 260
    draw.rounded_rectangle(
        [(bib_box_x, bib_box_y), (bib_box_x + bib_box_width, bib_box_y + bib_box_height)],
        radius=50, fill='#F5F5DC'
    )
    bbox = draw.textbbox((0, 0), bib_number, font=bib_font)
    bib_w = bbox[2] - bbox[0]
    bib_h = bbox[3] - bbox[1]
    text_x = bib_box_x + (bib_box_width - bib_w) // 2 - bbox[0]
    text_y = bib_box_y + (bib_box_height - bib_h) // 2 - bbox[1]
    draw.text((text_x, text_y), bib_number, fill='#0D7377', font=bib_font)
    
    # Blood group — placed RIGHT BELOW the BIB number box
    blood_box_width, blood_box_height = 420, 220
    blood_box_x = (width - blood_box_width) // 2
    blood_box_y = bib_box_y + bib_box_height + 40
    draw.rounded_rectangle(
        [(blood_box_x, blood_box_y), (blood_box_x + blood_box_width, blood_box_y + blood_box_height)],
        radius=30, fill='#C41E3A'
    )
    # Small label "BLOOD GROUP"
    label_text = "BLOOD GROUP"
    lbbox = draw.textbbox((0, 0), label_text, font=blood_label_font)
    lw = lbbox[2] - lbbox[0]
    draw.text(
        (blood_box_x + (blood_box_width - lw) // 2 - lbbox[0], blood_box_y + 20 - lbbox[1]),
        label_text, fill='#FFFFFF', font=blood_label_font
    )
    # Actual blood group value
    bbox = draw.textbbox((0, 0), blood_group, font=blood_font)
    bw = bbox[2] - bbox[0]
    bh = bbox[3] - bbox[1]
    draw.text(
        (blood_box_x + (blood_box_width - bw) // 2 - bbox[0],
         blood_box_y + 75 + (blood_box_height - 75 - bh) // 2 - bbox[1]),
        blood_group, fill='#FFFFFF', font=blood_font
    )
    
    # Barcode
    try:
        EAN = barcode.get_barcode_class('code128')
        ean = EAN(bib_number, writer=ImageWriter())
        barcode_buffer = io.BytesIO()
        ean.write(barcode_buffer, options={'write_text': False, 'module_height': 8, 'module_width': 0.3})
        barcode_buffer.seek(0)
        barcode_img = Image.open(barcode_buffer)
        barcode_img = barcode_img.resize((500, 100))
        img.paste(barcode_img, ((width - 500) // 2, height - 130))
    except Exception:
        pass
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"

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
    
    # NOTE: BIB number will be generated AFTER payment is confirmed
    # Store participant data in metadata without BIB number yet
    
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
        "consent_results_published": str(payment_request.consent_results_published)
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
            # Generate BIB number based on category and gender
            metadata = transaction.get('metadata', {})
            gender = metadata.get('gender', 'male')
            bib_number = await generate_bib_number(transaction['event_id'], gender)
            
            # Generate QR code for the BIB number
            qr_code = generate_qr_code(bib_number)
            
            # Get event details for BIB card
            event = await db.events.find_one({"id": transaction['event_id']}, {"_id": 0})
            event_category = event.get('category', 'Event') if event else 'Event'
            
            # Generate BIB card for t-shirt printing
            bib_card = generate_bib_card(bib_number, event_category)
            
            # Create registration with all participant data from metadata
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
                "bib_number": bib_number,
                "qr_code": qr_code,
                "bib_card": bib_card,
                "blood_group": "A+",
                "status": "confirmed"
            }
            
            reg_obj = Registration(**reg_data)
            doc = reg_obj.model_dump()
            doc['registration_date'] = doc['registration_date'].isoformat()
            
            await db.registrations.insert_one(doc)
            
            # Update transaction with BIB number
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {"bib_number": bib_number}}
            )
            
            # Send BIB card email to participant (best-effort, non-blocking of response)
            try:
                event_title = event.get('title', 'Monsoon Run 2.0') if event else 'Monsoon Run 2.0'
                event_date = event.get('date', '30th May 2026') if event else '30th May 2026'
                send_bib_email(
                    to_email=transaction['user_email'],
                    user_name=transaction['user_name'],
                    bib_number=bib_number,
                    bib_card_data_url=bib_card,
                    event_title=event_title,
                    event_date=event_date,
                )
            except Exception as e:
                logger.error(f"BIB email dispatch failed: {e}")
    
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
async def get_all_registrations(
    search: Optional[str] = None,
    category: Optional[str] = None,
    gender: Optional[str] = None,
    checked_in: Optional[bool] = None
):
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
    event_dict = {e['id']: e for e in events}
    
    # Apply filters
    if search or category or gender is not None or checked_in is not None:
        filtered = []
        for reg in registrations:
            # Search filter (name, email, bib)
            if search:
                search_lower = search.lower()
                if not (
                    search_lower in reg.get('user_name', '').lower() or
                    search_lower in reg.get('user_email', '').lower() or
                    search_lower in reg.get('bib_number', '').lower()
                ):
                    continue
            
            # Category filter
            if category:
                event = event_dict.get(reg['event_id'])
                if not event or event.get('category') != category:
                    continue
            
            # Gender filter
            if gender and reg.get('gender') != gender:
                continue
            
            # Checked-in filter
            if checked_in is not None and reg.get('checked_in', False) != checked_in:
                continue
            
            filtered.append(reg)
        registrations = filtered
    
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
    # Generate BIB number based on category and gender
    bib_number = await generate_bib_number(registration.event_id, registration.gender)
    
    # Generate QR code
    qr_code = generate_qr_code(bib_number)
    
    # Get event details for BIB card
    event = await db.events.find_one({"id": registration.event_id}, {"_id": 0})
    event_category = event.get('category', 'Event') if event else 'Event'
    
    # Generate BIB card
    bib_card = generate_bib_card(bib_number, event_category)
    
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
        "bib_number": bib_number,
        "qr_code": qr_code,
        "bib_card": bib_card,
        "blood_group": "A+",
        "status": "confirmed"
    }
    
    reg_obj = Registration(**reg_data)
    doc = reg_obj.model_dump()
    doc['registration_date'] = doc['registration_date'].isoformat()
    
    await db.registrations.insert_one(doc)
    
    # Send BIB card email to participant (best-effort)
    try:
        event_title = event.get('title', 'Monsoon Run 2.0') if event else 'Monsoon Run 2.0'
        event_date = event.get('date', '30th May 2026') if event else '30th May 2026'
        send_bib_email(
            to_email=registration.user_email,
            user_name=registration.user_name,
            bib_number=bib_number,
            bib_card_data_url=bib_card,
            event_title=event_title,
            event_date=event_date,
        )
    except Exception as e:
        logger.error(f"BIB email dispatch (manual) failed: {e}")
    
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
async def create_event_admin(event_data: EventCreate):
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

# New Admin Features

@api_router.get("/admin/analytics")
async def get_analytics():
    """Get analytics data for dashboard"""
    # Get all registrations and events
    registrations = await db.registrations.find({}, {"_id": 0}).to_list(10000)
    events = await db.events.find({}, {"_id": 0}).to_list(1000)
    
    # Create event lookup dictionary
    event_dict = {e['id']: e for e in events}
    
    # Calculate total revenue by category
    revenue_by_category = {}
    gender_distribution = {"male": 0, "female": 0, "other": 0}
    tshirt_distribution = {}
    age_distribution = {"18-25": 0, "26-35": 0, "36-45": 0, "46+": 0}
    registration_trends = {}
    
    for reg in registrations:
        # Revenue by category
        event = event_dict.get(reg['event_id'])
        if event:
            category = event.get('category', 'Unknown')
            fee = float(event.get('registration_fee', 0))
            revenue_by_category[category] = revenue_by_category.get(category, 0) + fee
        
        # Gender distribution
        gender = reg.get('gender', 'other').lower()
        if gender in gender_distribution:
            gender_distribution[gender] += 1
        
        # T-shirt size distribution
        tshirt = reg.get('tshirt_size', 'M')
        tshirt_distribution[tshirt] = tshirt_distribution.get(tshirt, 0) + 1
        
        # Age distribution
        dob = reg.get('dob', '')
        if dob:
            try:
                birth_year = int(dob.split('-')[0])
                age = 2026 - birth_year
                if age < 26:
                    age_distribution["18-25"] += 1
                elif age < 36:
                    age_distribution["26-35"] += 1
                elif age < 46:
                    age_distribution["36-45"] += 1
                else:
                    age_distribution["46+"] += 1
            except:
                pass
        
        # Registration trends (by date)
        reg_date_str = reg.get('registration_date', '')
        if isinstance(reg_date_str, str):
            reg_date = reg_date_str.split('T')[0]  # Get just the date part
        else:
            reg_date = datetime.now(timezone.utc).date().isoformat()
        registration_trends[reg_date] = registration_trends.get(reg_date, 0) + 1
    
    # Calculate total revenue
    total_revenue = sum(revenue_by_category.values())
    
    # Sort registration trends by date
    sorted_trends = [
        {"date": date, "count": count}
        for date, count in sorted(registration_trends.items())
    ]
    
    return {
        "total_registrations": len(registrations),
        "total_revenue": total_revenue,
        "revenue_by_category": [
            {"category": cat, "revenue": rev}
            for cat, rev in revenue_by_category.items()
        ],
        "gender_distribution": [
            {"gender": gender, "count": count}
            for gender, count in gender_distribution.items()
        ],
        "tshirt_distribution": [
            {"size": size, "count": count}
            for size, count in sorted(tshirt_distribution.items())
        ],
        "age_distribution": [
            {"range": range_name, "count": count}
            for range_name, count in age_distribution.items()
        ],
        "registration_trends": sorted_trends,
        "checked_in_count": sum(1 for r in registrations if r.get('checked_in', False))
    }

@api_router.get("/admin/registrations/export")
async def export_registrations(
    category: Optional[str] = None,
    gender: Optional[str] = None,
    checked_in: Optional[bool] = None
):
    """Export registrations as CSV"""
    import csv
    import io
    from fastapi.responses import StreamingResponse
    
    # Get registrations with filters
    filter_query = {}
    registrations = await db.registrations.find(filter_query, {"_id": 0}).to_list(10000)
    events = await db.events.find({}, {"_id": 0}).to_list(1000)
    event_dict = {e['id']: e for e in events}
    
    # Apply filters
    if category or gender is not None or checked_in is not None:
        filtered = []
        for reg in registrations:
            event = event_dict.get(reg['event_id'])
            if category and event and event.get('category') != category:
                continue
            if gender and reg.get('gender') != gender:
                continue
            if checked_in is not None and reg.get('checked_in', False) != checked_in:
                continue
            filtered.append(reg)
        registrations = filtered
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        'BIB Number', 'Name', 'Email', 'Phone', 'Gender', 'DOB', 
        'T-Shirt Size', 'Event Category', 'Event Title', 'Registration Fee',
        'Emergency Contact Name', 'Emergency Contact', 'Medical Condition',
        'Registration Date', 'Checked In', 'Check-in Time'
    ])
    
    # Data rows
    for reg in registrations:
        event = event_dict.get(reg['event_id'], {})
        checked_in_at = reg.get('checked_in_at', '')
        if checked_in_at and not isinstance(checked_in_at, str):
            checked_in_at = checked_in_at.isoformat()
        
        writer.writerow([
            reg.get('bib_number', ''),
            reg.get('user_name', ''),
            reg.get('user_email', ''),
            reg.get('user_phone', ''),
            reg.get('gender', ''),
            reg.get('dob', ''),
            reg.get('tshirt_size', ''),
            event.get('category', ''),
            event.get('title', ''),
            event.get('registration_fee', 0),
            reg.get('emergency_contact_name', ''),
            reg.get('emergency_contact', ''),
            reg.get('has_medical_condition', ''),
            reg.get('registration_date', ''),
            'Yes' if reg.get('checked_in', False) else 'No',
            checked_in_at
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=registrations.csv"}
    )

@api_router.post("/admin/registrations/{registration_id}/checkin")
async def checkin_registration(registration_id: str):
    """Mark a registration as checked in"""
    result = await db.registrations.update_one(
        {"id": registration_id},
        {
            "$set": {
                "checked_in": True,
                "checked_in_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    return {"message": "Check-in successful"}

@api_router.get("/admin/registrations/bib/{bib_number}")
async def get_registration_by_bib(bib_number: str):
    """Get registration by BIB number for check-in"""
    registration = await db.registrations.find_one({"bib_number": bib_number}, {"_id": 0})
    
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    # Get event details
    event = await db.events.find_one({"id": registration['event_id']}, {"_id": 0})
    
    return {
        "registration": registration,
        "event": event
    }

@api_router.post("/admin/registrations/{registration_id}/send-email")
async def resend_bib_email(registration_id: str):
    """Resend BIB card email to a participant."""
    registration = await db.registrations.find_one({"id": registration_id}, {"_id": 0})
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    bib_card = registration.get('bib_card')
    if not bib_card:
        # Regenerate if missing
        event = await db.events.find_one({"id": registration['event_id']}, {"_id": 0})
        event_category = event.get('category', 'Event') if event else 'Event'
        bib_card = generate_bib_card(registration['bib_number'], event_category)
        await db.registrations.update_one(
            {"id": registration_id},
            {"$set": {"bib_card": bib_card}}
        )
    
    event = await db.events.find_one({"id": registration['event_id']}, {"_id": 0})
    event_title = event.get('title', 'Monsoon Run 2.0') if event else 'Monsoon Run 2.0'
    event_date = event.get('date', '30th May 2026') if event else '30th May 2026'
    
    sent = send_bib_email(
        to_email=registration['user_email'],
        user_name=registration['user_name'],
        bib_number=registration['bib_number'],
        bib_card_data_url=bib_card,
        event_title=event_title,
        event_date=event_date,
    )
    
    return {
        "sent": sent,
        "email": registration['user_email'],
        "bib_number": registration['bib_number'],
    }

class BulkEmailRequest(BaseModel):
    subject: str
    message: str
    recipients: str  # "all", "category", or specific category name

@api_router.post("/admin/email/send-bulk")
async def send_bulk_email(email_data: BulkEmailRequest):
    """Send bulk email to participants"""
    # Get recipients based on filter
    filter_query = {}
    
    if email_data.recipients != "all":
        # Get events with matching category
        events = await db.events.find({"category": email_data.recipients}, {"_id": 0}).to_list(1000)
        event_ids = [e['id'] for e in events]
        filter_query = {"event_id": {"$in": event_ids}}
    
    registrations = await db.registrations.find(filter_query, {"_id": 0}).to_list(10000)
    emails = [reg['user_email'] for reg in registrations]
    
    # Note: Actual email sending would require an email service integration
    # For now, we'll just return the count and emails
    return {
        "message": "Email sending initiated",
        "recipient_count": len(emails),
        "recipients": emails[:10],  # Sample of first 10
        "note": "Email service integration required for actual sending"
    }

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