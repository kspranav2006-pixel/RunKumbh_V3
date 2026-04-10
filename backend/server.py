from fastapi import FastAPI, APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt

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
    current_participants: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Registration Models
class RegistrationCreate(BaseModel):
    event_id: str
    user_email: str
    user_name: str
    user_phone: str

class Registration(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    event_id: str
    user_email: str
    user_name: str
    user_phone: str
    registration_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "confirmed"
    bib_number: str

# Gallery Models
class GalleryCreate(BaseModel):
    title: str
    image_url: str
    category: str = "event"

class Gallery(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    image_url: str
    category: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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

# Registration Routes
@api_router.post("/registrations", response_model=Registration)
async def create_registration(reg_data: RegistrationCreate):
    # Check if event exists
    event = await db.events.find_one({"id": reg_data.event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if already registered
    existing_reg = await db.registrations.find_one({
        "event_id": reg_data.event_id,
        "user_email": reg_data.user_email
    })
    if existing_reg:
        raise HTTPException(status_code=400, detail="Already registered for this event")
    
    # Check capacity
    if event.get('current_participants', 0) >= event.get('max_participants', 0):
        raise HTTPException(status_code=400, detail="Event is full")
    
    # Create registration
    reg_dict = reg_data.model_dump()
    reg_dict['user_id'] = str(uuid.uuid4())
    reg_dict['bib_number'] = f"BIB{str(uuid.uuid4())[:8].upper()}"
    reg_obj = Registration(**reg_dict)
    
    doc = reg_obj.model_dump()
    doc['registration_date'] = doc['registration_date'].isoformat()
    
    await db.registrations.insert_one(doc)
    
    # Update event participant count
    await db.events.update_one(
        {"id": reg_data.event_id},
        {"$inc": {"current_participants": 1}}
    )
    
    return reg_obj

@api_router.get("/registrations/email/{email}", response_model=List[Registration])
async def get_user_registrations(email: str):
    registrations = await db.registrations.find({"user_email": email}, {"_id": 0}).to_list(1000)
    for reg in registrations:
        if isinstance(reg.get('registration_date'), str):
            reg['registration_date'] = datetime.fromisoformat(reg['registration_date'])
    return registrations

# Gallery Routes
@api_router.get("/gallery", response_model=List[Gallery])
async def get_gallery():
    images = await db.gallery.find({}, {"_id": 0}).to_list(1000)
    for img in images:
        if isinstance(img.get('uploaded_at'), str):
            img['uploaded_at'] = datetime.fromisoformat(img['uploaded_at'])
    return images

@api_router.post("/gallery", response_model=Gallery)
async def create_gallery_item(gallery_data: GalleryCreate):
    gallery_obj = Gallery(**gallery_data.model_dump())
    doc = gallery_obj.model_dump()
    doc['uploaded_at'] = doc['uploaded_at'].isoformat()
    
    await db.gallery.insert_one(doc)
    return gallery_obj

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
