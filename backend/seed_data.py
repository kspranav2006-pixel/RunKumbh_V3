import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
import uuid
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def seed_database():
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("Seeding database...")
    
    # Clear existing data
    await db.events.delete_many({})
    await db.gallery.delete_many({})
    
    # Seed RUN KUMBHA - MONSOON RUN 2.0 Events
    events = [
        {
            "id": str(uuid.uuid4()),
            "title": "Open Men & Women - 5K Run",
            "description": "Run Kumbha – Monsoon Run 2.0 🌧️ Open category for all participants. Minimum 50 participants required. Includes Medal, Certificate, Refreshments & T-Shirt. Compete for ₹30,000 total cash prize!",
            "date": "2026-06-21",
            "location": "RV Institute of Technology and Management, Bengaluru",
            "distance": "5 km",
            "category": "Open 5K",
            "max_participants": 500,
            "image_url": "https://images.unsplash.com/photo-1452626038306-9aae5e071dd3",
            "registration_fee": 499.00,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Students / NCC / NSS - 5K Run",
            "description": "Special category for Students, NCC & NSS members. Minimum 50 participants required per gender. Run for glory with your peers! Medal, Certificate, Refreshments & T-Shirt included.",
            "date": "2026-06-21",
            "location": "RV Institute of Technology and Management, Bengaluru",
            "distance": "5 km",
            "category": "Students 5K",
            "max_participants": 400,
            "image_url": "https://images.pexels.com/photos/2402777/pexels-photo-2402777.jpeg",
            "registration_fee": 349.00,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Students / Staff - 3K Run",
            "description": "For Students, NCC, NSS, NCMC & RVITM Staff members. A refreshing 3K monsoon run with full event perks including Medal, Certificate, T-Shirt & Refreshments.",
            "date": "2026-06-21",
            "location": "RV Institute of Technology and Management, Bengaluru",
            "distance": "3 km",
            "category": "Campus 3K",
            "max_participants": 300,
            "image_url": "https://images.unsplash.com/photo-1530143311094-34d807799e8f",
            "registration_fee": 349.00,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Family Run - 3K",
            "description": "Run together as a family! Perfect for 1 Male, 1 Female & 1 Child (Min 8 years). Make memories while staying fit. Complete family package with medals, certificates & refreshments for all!",
            "date": "2026-06-21",
            "location": "RV Institute of Technology and Management, Bengaluru",
            "distance": "3 km",
            "category": "Family 3K",
            "max_participants": 200,
            "image_url": "https://images.unsplash.com/photo-1695655300485-d3da8bc72076",
            "registration_fee": 999.00,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Couple Run - 3K (Open)",
            "description": "Run with your partner in this exciting couple's category! Open to all couples. Enjoy the monsoon together while running for fitness. Includes medals, certificates & refreshments for both.",
            "date": "2026-06-21",
            "location": "RV Institute of Technology and Management, Bengaluru",
            "distance": "3 km",
            "category": "Couple 3K",
            "max_participants": 150,
            "image_url": "https://images.unsplash.com/photo-1746046489457-9628dc3b8a1f",
            "registration_fee": 799.00,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.events.insert_many(events)
    print(f"Seeded {len(events)} events")
    
    # Seed Gallery
    gallery_items = [
        {
            "id": str(uuid.uuid4()),
            "title": "Marathon Start Line",
            "image_url": "https://images.unsplash.com/photo-1695655300485-d3da8bc72076?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1NTJ8MHwxfHNlYXJjaHwzfHxydW5uaW5nJTIwZXZlbnR8ZW58MHx8fHwxNzc1ODE0MDYzfDA&ixlib=rb-4.1.0&q=85",
            "category": "event",
            "uploaded_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Runners in Action",
            "image_url": "https://images.unsplash.com/photo-1746046489457-9628dc3b8a1f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1NTJ8MHwxfHNlYXJjaHw0fHxydW5uaW5nJTIwZXZlbnR8ZW58MHx8fHwxNzc1ODE0MDYzfDA&ixlib=rb-4.1.0&q=85",
            "category": "event",
            "uploaded_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Community Spirit",
            "image_url": "https://images.unsplash.com/photo-1452626038306-9aae5e071dd3?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1NTJ8MHwxfHNlYXJjaHwxfHxydW5uaW5nJTIwZXZlbnR8ZW58MHx8fHwxNzc1ODE0MDYzfDA&ixlib=rb-4.1.0&q=85",
            "category": "community",
            "uploaded_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Finish Line Celebration",
            "image_url": "https://images.unsplash.com/photo-1700667877838-e9c93ca95f05?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1NTJ8MHwxfHNlYXJjaHwyfHxydW5uaW5nJTIwZXZlbnR8ZW58MHx8fHwxNzc1ODE0MDYzfDA&ixlib=rb-4.1.0&q=85",
            "category": "celebration",
            "uploaded_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Victory Moment",
            "image_url": "https://images.unsplash.com/photo-1598011872583-100f9b06de80?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMzl8MHwxfHNlYXJjaHwyfHxtYXJhdGhvbiUyMGNlbGVicmF0aW9ufGVufDB8fHx8MTc3NTgxNDA2N3ww&ixlib=rb-4.1.0&q=85",
            "category": "celebration",
            "uploaded_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Team Achievement",
            "image_url": "https://images.unsplash.com/photo-1598012268972-217e6036c419?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMzl8MHwxfHNlYXJjaHwxfHxtYXJhdGhvbiUyMGNlbGVicmF0aW9ufGVufDB8fHx8MTc3NTgxNDA2N3ww&ixlib=rb-4.1.0&q=85",
            "category": "community",
            "uploaded_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Medals and Glory",
            "image_url": "https://images.unsplash.com/photo-1771402899719-1dd20061772c?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMzl8MHwxfHNlYXJjaHwzfHxtYXJhdGhvbiUyMGNlbGVicmF0aW9ufGVufDB8fHx8MTc3NTgxNDA2N3ww&ixlib=rb-4.1.0&q=85",
            "category": "celebration",
            "uploaded_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Happy Finishers",
            "image_url": "https://images.unsplash.com/photo-1598012113883-3a075ef160b4?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMzl8MHwxfHNlYXJjaHw0fHxtYXJhdGhvbiUyMGNlbGVicmF0aW9ufGVufDB8fHx8MTc3NTgxNDA2N3ww&ixlib=rb-4.1.0&q=85",
            "category": "event",
            "uploaded_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.gallery.insert_many(gallery_items)
    print(f"Seeded {len(gallery_items)} gallery items")
    
    print("Database seeding completed!")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())
