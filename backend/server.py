from fastapi import FastAPI, APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import re
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator
from typing import List, Optional, Dict, Tuple
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
# ── Shared name validation ──────────────────────────────────────────────────
_NAME_RE = re.compile(r"^[A-Za-z\u00C0-\u024F\u1E00-\u1EFF' .-]{2,100}$")

def _validate_name(value: str, label: str = "Name") -> str:
    v = value.strip()
    if not v:
        raise ValueError(f"{label} is required.")
    if not _NAME_RE.match(v):
        raise ValueError(f"{label} must contain only letters — no numbers or special characters.")
    return v
# ────────────────────────────────────────────────────────────────────────────

class TeamMember(BaseModel):
    """Additional participant for Couple Run / Family Run team registrations."""
    user_name: str
    user_email: str = ""
    user_phone: str = ""
    gender: str
    dob: str
    tshirt_size: str
    blood_group: str = "A+"
    emergency_contact_name: str = ""
    emergency_contact: str = ""
    bib_card: Optional[str] = None

    @field_validator("user_name")
    @classmethod
    def validate_user_name(cls, v):
        return _validate_name(v, "Team member name")


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
    blood_group: Optional[str] = "A+"
    team_members: Optional[List[TeamMember]] = []
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
    team_members: List[TeamMember] = []
    registration_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "confirmed"
    bib_number: str = ""
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
    blood_group: Optional[str] = "A+"
    team_members: Optional[List[TeamMember]] = []
    consent_physically_fit: bool
    consent_own_risk: bool
    consent_event_rules: bool
    consent_photography: bool
    consent_results_published: bool
    origin_url: str

    @field_validator("user_name")
    @classmethod
    def validate_user_name(cls, v):
        return _validate_name(v, "Full name")

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
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"


def _bib_sort_key(bib: str):
    """Sort BIBs naturally: same prefix grouped, numeric suffix ascending. Empty BIBs last."""
    if not bib:
        return ("zzz", 999999)
    import re
    m = re.match(r"^([A-Z]+)(\d+)$", bib)
    if m:
        return (m.group(1), int(m.group(2)))
    return (bib, 0)


def generate_certificate(user_name: str, bib_number: str, event_category: str = "Monsoon Run 2.0") -> str:
    """Generate an A4 landscape PNG certificate for a runner. Returns data URL."""
    # A4 landscape @ 200 DPI = 2339 x 1654
    width, height = 2339, 1654
    img = Image.new('RGB', (width, height), '#FFFFFF')
    draw = ImageDraw.Draw(img)

    # Soft gradient background (teal-to-cream)
    for y in range(height):
        t = y / height
        r = int(245 + (250 - 245) * t)
        g = int(252 + (245 - 252) * t)
        b = int(245 + (240 - 245) * t)
        draw.rectangle([(0, y), (width, y + 1)], fill=(r, g, b))

    # Decorative outer border + inner border
    draw.rectangle([(60, 60), (width - 60, height - 60)], outline='#0D7377', width=8)
    draw.rectangle([(90, 90), (width - 90, height - 90)], outline='#FF6B35', width=2)

    # Top accent ribbon
    draw.rectangle([(60, 60), (width - 60, 220)], fill='#0D7377')

    font_candidates = [
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    italic_candidates = [
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
    ]
    font_path = next((p for p in font_candidates if os.path.exists(p)), None)
    italic_path = next((p for p in italic_candidates if os.path.exists(p)), font_path)

    def F(size, italic=False):
        path = italic_path if italic else font_path
        return ImageFont.truetype(path, size) if path else ImageFont.load_default()

    # Title band
    draw.text((width // 2, 140), "RUNKUMBH 2026 · MONSOON RUN 2.0",
              fill='#FFFFFF', font=F(60), anchor="mm")

    # Big Certificate title
    draw.text((width // 2, 360), "Certificate of Participation",
              fill='#0D7377', font=F(110), anchor="mm")

    # Subtitle
    draw.text((width // 2, 470), "This is to certify that",
              fill='#374151', font=F(48, italic=True), anchor="mm")

    # Participant name — auto-fit
    name = (user_name or "Participant").strip()
    name_size = 130
    while name_size > 50:
        bb = draw.textbbox((0, 0), name, font=F(name_size), anchor="mm")
        if (bb[2] - bb[0]) <= (width - 400) and (bb[3] - bb[1]) <= 180:
            break
        name_size -= 6
    draw.text((width // 2, 640), name, fill='#0D7377', font=F(name_size), anchor="mm")

    # Underline under name
    draw.line([(width // 2 - 600, 750), (width // 2 + 600, 750)], fill='#FF6B35', width=4)

    # Body text
    body = f"has successfully participated in the {event_category} event"
    draw.text((width // 2, 850), body, fill='#374151', font=F(52), anchor="mm")
    draw.text((width // 2, 920), "organised by RV Institute of Technology and Management, Bengaluru",
              fill='#374151', font=F(40, italic=True), anchor="mm")
    draw.text((width // 2, 980), "in association with the National Cadet Corps.",
              fill='#374151', font=F(40, italic=True), anchor="mm")

    # BIB number box (centered, prominent)
    bib_box_w, bib_box_h = 600, 180
    bib_box_x = (width - bib_box_w) // 2
    bib_box_y = 1100
    draw.rounded_rectangle(
        [(bib_box_x, bib_box_y), (bib_box_x + bib_box_w, bib_box_y + bib_box_h)],
        radius=20, fill='#F5F5DC', outline='#0D7377', width=4,
    )
    draw.text((width // 2, bib_box_y + 40), "BIB NUMBER", fill='#6B7280', font=F(36), anchor="mm")
    bib_text = bib_number or "—"
    draw.text((width // 2, bib_box_y + 115), bib_text, fill='#0D7377', font=F(80), anchor="mm")

    # Signature lines
    sig_y = 1430
    draw.line([(280, sig_y), (760, sig_y)], fill='#374151', width=3)
    draw.text((520, sig_y + 35), "Event Coordinator", fill='#374151', font=F(36), anchor="mm")

    draw.line([(width - 760, sig_y), (width - 280, sig_y)], fill='#374151', width=3)
    draw.text((width - 520, sig_y + 35), "Director, RV Institute", fill='#374151', font=F(36), anchor="mm")

    # Date footer
    draw.text((width // 2, sig_y + 80), "Event Date · 30th May 2026 · Bengaluru",
              fill='#6B7280', font=F(32, italic=True), anchor="mm")

    buffer = io.BytesIO()
    img.save(buffer, format='PNG', optimize=True)
    buffer.seek(0)
    return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"

# BIB card templates — one per race distance. 3K = blue banner, 5K = green banner.
BIB_TEMPLATE_3K = ROOT_DIR / "assets" / "bib_template_3k.png"
BIB_TEMPLATE_5K = ROOT_DIR / "assets" / "bib_template_5k.png"

# Pill geometry (detected from rendered slides, 1654x1166 px)
_TEMPLATE_LAYOUTS = {
    "3k": {
        "path": BIB_TEMPLATE_3K,
        "bib_pill":     (367, 428, 1284, 736),
        "blood_pill":   (283, 1021, 636, 1144),
        "barcode_pill": (891, 1013, 1432, 1137),
        "event_banner": (760, 30, 1510, 180),  # usable area inside top-right colored banner
    },
    "5k": {
        "path": BIB_TEMPLATE_5K,
        "bib_pill":     (367, 428, 1284, 736),
        "blood_pill":   (318, 1021, 643, 1146),
        "barcode_pill": (911, 1021, 1452, 1146),
        "event_banner": (760, 30, 1510, 180),
    },
}


def _pick_template(category: str) -> dict:
    """Blue template for 3K events, green template for 5K events.
    Falls back to 5K if distance can't be inferred."""
    cat = (category or "").lower()
    if "3k" in cat:
        return _TEMPLATE_LAYOUTS["3k"]
    return _TEMPLATE_LAYOUTS["5k"]


def generate_bib_card(bib_number: str, category: str = "", blood_group: str = "A+") -> str:
    """Render BIB card by overlaying BIB number, event title, blood group and barcode
    onto the appropriate branded template (blue for 3K, green for 5K). All other
    design elements in the template are preserved pixel-for-pixel."""
    layout = _pick_template(category)
    img = Image.open(layout["path"]).convert("RGB")
    draw = ImageDraw.Draw(img)

    font_candidates = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    font_path = next((p for p in font_candidates if os.path.exists(p)), None)

    def _font(size):
        return ImageFont.truetype(font_path, size) if font_path else ImageFont.load_default()

    def _fit_text(text, max_w, max_h, start_size, min_size=20, step=4):
        size = start_size
        while size > min_size:
            bb = draw.textbbox((0, 0), text, font=_font(size), anchor="mm")
            if (bb[2] - bb[0]) <= max_w and (bb[3] - bb[1]) <= max_h:
                return _font(size)
            size -= step
        return _font(min_size)

    # Event title in the top-right colored banner
    event_label = (category or "").strip() or "Event"
    ex1, ey1, ex2, ey2 = layout["event_banner"]
    f = _fit_text(event_label, (ex2 - ex1) - 30, (ey2 - ey1) - 20, start_size=110)
    draw.text(((ex1 + ex2) // 2, (ey1 + ey2) // 2), event_label,
              fill="#FFFFFF", font=f, anchor="mm")

    # BIB number in the big cream pill
    bx1, by1, bx2, by2 = layout["bib_pill"]
    f = _fit_text(bib_number, (bx2 - bx1) - 80, (by2 - by1) - 60, start_size=300, step=6)
    draw.text(((bx1 + bx2) // 2, (by1 + by2) // 2), bib_number,
              fill="#000000", font=f, anchor="mm")

    # Blood group in the red pill
    rx1, ry1, rx2, ry2 = layout["blood_pill"]
    f = _fit_text(blood_group, (rx2 - rx1) - 30, (ry2 - ry1) - 20, start_size=110)
    draw.text(((rx1 + rx2) // 2, (ry1 + ry2) // 2), blood_group,
              fill="#FFFFFF", font=f, anchor="mm")

    # Barcode fills the bottom-right cream pill
    try:
        cx1, cy1, cx2, cy2 = layout["barcode_pill"]
        pad = 16
        target_w = (cx2 - cx1) - pad * 2
        target_h = (cy2 - cy1) - pad * 2
        EAN = barcode.get_barcode_class('code128')
        ean = EAN(bib_number, writer=ImageWriter())
        bc_buf = io.BytesIO()
        ean.write(bc_buf, options={'write_text': False, 'module_height': 10, 'module_width': 0.4, 'quiet_zone': 1})
        bc_buf.seek(0)
        bc_img = Image.open(bc_buf).convert("RGB").resize((target_w, target_h))
        img.paste(bc_img, (cx1 + pad, cy1 + pad))
    except Exception as e:
        logger.warning(f"Barcode render failed for {bib_number}: {e}")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
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

# Pending Registration (SAP payment flow — no Stripe)
@api_router.post("/register/pending")
async def create_pending_registration(payload: PaymentCheckoutRequest):
    """Capture the full registration locally with status='pending_payment' and return
    the external SAP payment portal URL. The admin later flips the status to
    'confirmed' in the admin panel, which triggers BIB generation + email."""
    event = await db.events.find_one({"id": payload.event_id}, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Block only if a CONFIRMED registration already exists for this event + email.
    # pending_payment and cancelled rows are overwritten (useful when admin deletes
    # a stuck row, or when a user abandons mid-payment and retries).
    existing = await db.registrations.find_one({
        "event_id": payload.event_id,
        "user_email": payload.user_email,
    })
    if existing and existing.get("status") == "confirmed":
        raise HTTPException(
            status_code=400,
            detail=f"This email is already registered and confirmed for {event.get('title', 'this event')}."
        )

    reg_data = {
        "user_id": existing.get("user_id") if existing else str(uuid.uuid4()),
        "event_id": payload.event_id,
        "user_email": payload.user_email,
        "user_name": payload.user_name,
        "user_phone": payload.user_phone,
        "gender": payload.gender,
        "dob": payload.dob,
        "tshirt_size": payload.tshirt_size,
        "marathon_experience": payload.marathon_experience,
        "emergency_contact_name": payload.emergency_contact_name,
        "emergency_contact": payload.emergency_contact,
        "has_medical_condition": payload.has_medical_condition,
        "medical_condition_details": payload.medical_condition_details,
        "blood_group": payload.blood_group or "A+",
        "team_members": [m.model_dump() for m in (payload.team_members or [])],
        "consent_physically_fit": payload.consent_physically_fit,
        "consent_own_risk": payload.consent_own_risk,
        "consent_event_rules": payload.consent_event_rules,
        "consent_photography": payload.consent_photography,
        "consent_results_published": payload.consent_results_published,
        "bib_number": "",
        "qr_code": None,
        "bib_card": None,
        "status": "pending_payment",
    }

    if existing:
        # Overwrite the previous pending_payment / cancelled row
        await db.registrations.update_one(
            {"id": existing["id"]},
            {"$set": reg_data}
        )
        reg_id = existing["id"]
    else:
        reg_obj = Registration(**reg_data)
        doc = reg_obj.model_dump()
        doc['registration_date'] = doc['registration_date'].isoformat()
        await db.registrations.insert_one(doc)
        reg_id = reg_obj.id

    sap_url = os.environ.get(
        "SAP_PAYMENT_URL",
        "https://wds-prd.rvei.edu.in:4430/sap/bc/ui5_ui5/sap/zeventregister/#/scode/RUN_KUMBHA-2026"
    )
    return {
        "message": "Registration saved. Redirecting to payment portal.",
        "registration_id": reg_id,
        "payment_url": sap_url,
        "event_title": event.get('title', ''),
        "amount": event.get('registration_fee', 0),
    }

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
    checked_in: Optional[bool] = None,
    status: Optional[str] = None,
):
    # Get events first (needed for category filter mapping)
    events = await db.events.find({}, {"_id": 0}).to_list(1000)
    event_dict = {e['id']: e for e in events}

    # Build MongoDB query (server-side filtering — way faster than Python loop)
    query: dict = {}
    if gender:
        query["gender"] = gender
    if checked_in is not None:
        query["checked_in"] = checked_in
    if status:
        # status = "confirmed" | "pending_payment" | "cancelled" | "pending"
        query["status"] = status
    if search:
        # case-insensitive substring match on the indexed fields
        rx = {"$regex": search, "$options": "i"}
        query["$or"] = [
            {"user_name": rx},
            {"user_email": rx},
            {"bib_number": rx},
            {"user_phone": rx},
        ]
    if category:
        # Map category name -> event ids
        matching_event_ids = [eid for eid, e in event_dict.items() if e.get('category') == category]
        query["event_id"] = {"$in": matching_event_ids or ["__none__"]}

    # ── Performance: strip heavy bib_card base64 image (~500KB-1MB each) from list ──
    projection = {
        "_id": 0,
        "bib_card": 0,
    }

    registrations = await db.registrations.find(query, projection).to_list(10000)

    for reg in registrations:
        if isinstance(reg.get('registration_date'), str):
            reg['registration_date'] = datetime.fromisoformat(reg['registration_date'])
        # Strip bib_card from team_members for the list payload
        if reg.get('team_members'):
            reg['team_members'] = [
                {k: v for k, v in m.items() if k != 'bib_card'}
                for m in reg['team_members']
            ]

    # Sort by category (5K first, then 3K, alphabetical) and then BIB sequence ascending.
    # Pending/no-BIB rows sink to the bottom of each category.
    def cat_order(c):
        if c is None: return (3, "")
        if "5K" in c: return (0, c)
        if "3K" in c: return (1, c)
        return (2, c)

    def sort_key(r):
        cat = event_dict.get(r.get('event_id'), {}).get('category')
        return (cat_order(cat), _bib_sort_key(r.get('bib_number', '')))

    registrations.sort(key=sort_key)

    return {
        "registrations": registrations,
        "events": events,
        "total_registrations": len(registrations),
    }


@api_router.get("/admin/registrations/{registration_id}/full")
async def get_registration_full(registration_id: str):
    """Fetch the full registration including bib_card (heavy base64 image).
    Called on-demand only when admin opens the Detail modal or hits Download/Email."""
    reg = await db.registrations.find_one({"id": registration_id}, {"_id": 0})
    if not reg:
        raise HTTPException(status_code=404, detail="Registration not found")
    if isinstance(reg.get('registration_date'), str):
        reg['registration_date'] = datetime.fromisoformat(reg['registration_date'])
    return reg


@api_router.get("/admin/registrations/{registration_id}/certificate")
async def get_registration_certificate(registration_id: str):
    """Generate (on the fly) an A4 certificate PNG for a confirmed registration."""
    reg = await db.registrations.find_one({"id": registration_id}, {"_id": 0, "bib_card": 0})
    if not reg:
        raise HTTPException(status_code=404, detail="Registration not found")
    if reg.get('status') != 'confirmed' or not reg.get('bib_number'):
        raise HTTPException(status_code=400, detail="Certificates are only available for confirmed registrations with a BIB number.")
    event = await db.events.find_one({"id": reg['event_id']}, {"_id": 0}) or {}
    cert = generate_certificate(reg['user_name'], reg['bib_number'], event.get('category', 'Monsoon Run 2.0'))
    return {
        "certificate": cert,
        "bib_number": reg['bib_number'],
        "user_name": reg['user_name'],
        "category": event.get('category', ''),
    }


@api_router.get("/admin/certificates/download-all")
async def download_all_certificates():
    """Bundle all confirmed-runner certificates (A4 PNG) as a ZIP, including team members."""
    import zipfile
    import io as _io
    from fastapi.responses import StreamingResponse

    regs = await db.registrations.find(
        {"status": "confirmed", "bib_number": {"$ne": ""}},
        {"_id": 0, "bib_card": 0},
    ).to_list(10000)
    if not regs:
        raise HTTPException(status_code=404, detail="No confirmed registrations to generate certificates for.")

    events = await db.events.find({}, {"_id": 0}).to_list(1000)
    event_dict = {e['id']: e for e in events}

    buf = _io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for r in regs:
            cat = event_dict.get(r['event_id'], {}).get('category', 'Event')
            # Lead certificate
            cert = generate_certificate(r['user_name'], r['bib_number'], cat)
            png_bytes = base64.b64decode(cert.split(',', 1)[1])
            safe_name = (r['user_name'] or 'participant').replace(' ', '_').replace('/', '_')
            zf.writestr(f"{cat.replace(' ', '_')}/{r['bib_number']}_{safe_name}.png", png_bytes)
            # Team members share the same BIB, each gets their own certificate
            for m in (r.get('team_members') or []):
                m_cert = generate_certificate(m.get('user_name', 'Member'), r['bib_number'], cat)
                m_png = base64.b64decode(m_cert.split(',', 1)[1])
                m_safe = (m.get('user_name') or 'member').replace(' ', '_').replace('/', '_')
                zf.writestr(f"{cat.replace(' ', '_')}/{r['bib_number']}_{m_safe}.png", m_png)

    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="runkumbh_certificates.zip"'},
    )

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
    
    # Generate BIB card (with supplied blood group)
    blood_group = (registration.blood_group or "A+").strip()
    bib_card = generate_bib_card(bib_number, event_category, blood_group)

    # Per-member BIB cards for team events (Couple/Family)
    team_members_data = []
    extra_cards: List[Tuple[str, str]] = []
    for m in (registration.team_members or []):
        m_dict = m.model_dump() if hasattr(m, 'model_dump') else dict(m)
        m_card = generate_bib_card(bib_number, event_category, m_dict.get('blood_group', 'A+'))
        m_dict['bib_card'] = m_card
        team_members_data.append(m_dict)
        extra_cards.append((m_card, m_dict.get('user_name', 'member')))

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
        "team_members": team_members_data,
        "bib_number": bib_number,
        "qr_code": qr_code,
        "bib_card": bib_card,
        "blood_group": blood_group,
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
            extra_bib_cards=extra_cards,
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
    current = await db.registrations.find_one({"id": registration_id}, {"_id": 0})
    if not current:
        raise HTTPException(status_code=404, detail="Registration not found")

    # If admin is flipping to 'confirmed' and BIB isn't generated yet, do the full flow now
    transition_to_confirmed = (
        update_data.get("status") == "confirmed"
        and current.get("status") != "confirmed"
        and not current.get("bib_number")
    )

    if transition_to_confirmed:
        event = await db.events.find_one({"id": current['event_id']}, {"_id": 0})
        event_category = event.get('category', 'Event') if event else 'Event'
        event_title = event.get('title', 'Monsoon Run 2.0') if event else 'Monsoon Run 2.0'
        event_date = event.get('date', '30th May 2026') if event else '30th May 2026'

        bib_number = await generate_bib_number(current['event_id'], current.get('gender', 'male'))
        qr_code = generate_qr_code(bib_number)

        # Lead BIB card (with lead's blood group)
        bib_card = generate_bib_card(bib_number, event_category, current.get('blood_group', 'A+'))

        # Generate per-member BIB cards (same BIB number, each member's own blood group)
        team_members = current.get('team_members') or []
        updated_team = []
        for m in team_members:
            m_card = generate_bib_card(bib_number, event_category, m.get('blood_group', 'A+'))
            updated_team.append({**m, "bib_card": m_card})

        update_data = {
            **update_data,
            "bib_number": bib_number,
            "qr_code": qr_code,
            "bib_card": bib_card,
        }
        if updated_team:
            update_data["team_members"] = updated_team

        # Fire-and-forget email — only to the lead, with all BIB cards attached
        try:
            extra_cards = [
                (m["bib_card"], m["user_name"]) for m in updated_team if m.get("bib_card")
            ]
            send_bib_email(
                to_email=current['user_email'],
                user_name=current['user_name'],
                bib_number=bib_number,
                bib_card_data_url=bib_card,
                event_title=event_title,
                event_date=event_date,
                extra_bib_cards=extra_cards,
            )
        except Exception as e:
            logger.error(f"BIB email dispatch on confirm failed: {e}")

    result = await db.registrations.update_one(
        {"id": registration_id},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Registration not found")

    return {
        "message": "Registration updated successfully",
        "bib_generated": transition_to_confirmed,
        "bib_number": update_data.get("bib_number", current.get("bib_number", "")),
    }

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
):
    """Export confirmed registrations as a CSV grouped by category, with team members expanded as rows."""
    import csv
    import io
    import re
    from fastapi.responses import StreamingResponse

    # Only confirmed registrations
    filter_query: dict = {"status": "confirmed"}
    if gender:
        filter_query["gender"] = gender

    registrations = await db.registrations.find(filter_query, {"_id": 0, "bib_card": 0}).to_list(10000)
    events = await db.events.find({}, {"_id": 0}).to_list(1000)
    event_dict = {e['id']: e for e in events}

    if category:
        registrations = [r for r in registrations
                         if event_dict.get(r['event_id'], {}).get('category') == category]

    # Group registrations by category, then sort by BIB number within each category
    by_cat: dict = {}
    for reg in registrations:
        cat = event_dict.get(reg['event_id'], {}).get('category', 'Other')
        by_cat.setdefault(cat, []).append(reg)

    def bib_key(reg):
        bib = reg.get('bib_number', '') or ''
        m = re.match(r"^([A-Z]+)(\d+)$", bib)
        return (m.group(1), int(m.group(2))) if m else (bib, 0)

    output = io.StringIO()
    writer = csv.writer(output)
    headers = [
        'BIB Number', 'Name', 'Email', 'Phone', 'Gender', 'DOB',
        'T-Shirt Size', 'Blood Group',
        'Event Category', 'Event Title', 'Registration Fee',
        'Emergency Contact Name', 'Emergency Contact', 'Medical Condition',
        'Role', 'Signature'
    ]

    # Stable category order: 5K → 3K, then alphabetical within
    def cat_order(c):
        if "5K" in c: return (0, c)
        if "3K" in c: return (1, c)
        return (2, c)

    for cat in sorted(by_cat.keys(), key=cat_order):
        # Category section header
        writer.writerow([])
        writer.writerow([f"=== {cat} ==="])
        writer.writerow(headers)

        for reg in sorted(by_cat[cat], key=bib_key):
            event = event_dict.get(reg['event_id'], {})
            # Lead row
            writer.writerow([
                reg.get('bib_number', ''),
                reg.get('user_name', ''),
                reg.get('user_email', ''),
                reg.get('user_phone', ''),
                reg.get('gender', ''),
                reg.get('dob', ''),
                reg.get('tshirt_size', ''),
                reg.get('blood_group', ''),
                event.get('category', ''),
                event.get('title', ''),
                event.get('registration_fee', 0),
                reg.get('emergency_contact_name', ''),
                reg.get('emergency_contact', ''),
                reg.get('has_medical_condition', '') or 'No',
                'Lead' if reg.get('team_members') else 'Participant',
                ''  # signature column
            ])
            # Team member rows (Couple / Family)
            for m in (reg.get('team_members') or []):
                writer.writerow([
                    reg.get('bib_number', ''),
                    m.get('user_name', ''),
                    m.get('user_email', ''),
                    m.get('user_phone', ''),
                    m.get('gender', ''),
                    m.get('dob', ''),
                    m.get('tshirt_size', ''),
                    m.get('blood_group', ''),
                    event.get('category', ''),
                    event.get('title', ''),
                    '',  # fee already on lead row
                    m.get('emergency_contact_name', ''),
                    m.get('emergency_contact', ''),
                    '',
                    'Team Member',
                    ''
                ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=registrations.csv"}
    )

@api_router.get("/admin/registrations/bibs/download-zip")
async def download_confirmed_bibs_zip():
    """Stream a ZIP file containing BIB card PNGs for all confirmed registrations,
    including individual BIB cards for team members (Couple / Family runs)."""
    import zipfile
    from fastapi.responses import StreamingResponse

    confirmed = await db.registrations.find(
        {"status": "confirmed"},
        {"_id": 0, "bib_number": 1, "user_name": 1, "bib_card": 1, "team_members": 1}
    ).to_list(length=None)

    # Filter in Python — catches None, "", and missing keys
    confirmed = [r for r in confirmed if r.get("bib_card")]

    if not confirmed:
        raise HTTPException(status_code=404, detail="No confirmed registrations with BIB cards found. BIB cards are generated when a registration is confirmed.")

    zip_buffer = io.BytesIO()
    files_added = 0
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for reg in confirmed:
            bib_no = reg.get("bib_number", "UNKNOWN")
            name   = (reg.get("user_name") or "participant").replace(" ", "_")

            # Lead participant BIB card
            bib_b64 = reg.get("bib_card", "")
            if bib_b64:
                if "," in bib_b64:
                    bib_b64 = bib_b64.split(",", 1)[1]
                try:
                    img_bytes = base64.b64decode(bib_b64)
                    zf.writestr(f"BIB_{bib_no}_{name}.png", img_bytes)
                    files_added += 1
                except Exception as e:
                    logger.warning(f"Could not decode BIB card for {bib_no}: {e}")

            # Team member BIB cards
            for i, member in enumerate(reg.get("team_members") or [], start=2):
                m_card = member.get("bib_card", "")
                if not m_card:
                    continue
                m_name = (member.get("user_name") or f"member_{i}").replace(" ", "_")
                if "," in m_card:
                    m_card = m_card.split(",", 1)[1]
                try:
                    img_bytes = base64.b64decode(m_card)
                    zf.writestr(f"BIB_{bib_no}_{m_name}_member{i}.png", img_bytes)
                    files_added += 1
                except Exception as e:
                    logger.warning(f"Could not decode team member BIB for {bib_no} member {i}: {e}")

    if files_added == 0:
        raise HTTPException(status_code=404, detail="Confirmed registrations found but BIB card image data could not be read. Please regenerate BIB cards.")

    zip_buffer.seek(0)
    return StreamingResponse(
        iter([zip_buffer.getvalue()]),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=confirmed_bib_cards.zip"}
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

    extra_cards = [
        (m.get('bib_card'), m.get('user_name', 'member'))
        for m in (registration.get('team_members') or [])
        if m.get('bib_card')
    ]

    sent = send_bib_email(
        to_email=registration['user_email'],
        user_name=registration['user_name'],
        bib_number=registration['bib_number'],
        bib_card_data_url=bib_card,
        event_title=event_title,
        event_date=event_date,
        extra_bib_cards=extra_cards,
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