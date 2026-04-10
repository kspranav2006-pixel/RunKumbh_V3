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
    
    # Seed Events
    events = [
        {
            "id": str(uuid.uuid4()),
            "title": "Monsoon Marathon 2025",
            "description": "Experience the thrill of running through refreshing monsoon showers. A 42km full marathon through scenic routes with rain-kissed landscapes.",
            "date": "2025-07-15",
            "location": "Mumbai, Maharashtra",
            "distance": "42 km",
            "category": "Full Marathon",
            "max_participants": 500,
            "current_participants": 234,
            "image_url": "https://images.unsplash.com/photo-1452626038306-9aae5e071dd3",
            "registration_fee": 1500.0,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Summer Sprint 5K",
            "description": "Start your summer fitness journey with our energizing 5K sprint. Perfect for beginners and seasoned runners alike!",
            "date": "2025-05-20",
            "location": "Bangalore, Karnataka",
            "distance": "5 km",
            "category": "Sprint",
            "max_participants": 1000,
            "current_participants": 567,
            "image_url": "https://images.pexels.com/photos/2402777/pexels-photo-2402777.jpeg",
            "registration_fee": 500.0,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Half Marathon - Coastal Run",
            "description": "Run along the beautiful coastline with ocean breeze and stunning views. A perfect blend of challenge and scenery.",
            "date": "2025-06-10",
            "location": "Goa",
            "distance": "21 km",
            "category": "Half Marathon",
            "max_participants": 750,
            "current_participants": 412,
            "image_url": "https://images.unsplash.com/photo-1530143311094-34d807799e8f",
            "registration_fee": 1000.0,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Trail Run Adventure",
            "description": "Explore nature's beauty on winding trails through forests and hills. An adventure for trail running enthusiasts.",
            "date": "2025-08-05",
            "location": "Coorg, Karnataka",
            "distance": "15 km",
            "category": "Trail Run",
            "max_participants": 300,
            "current_participants": 145,
            "image_url": "https://images.unsplash.com/photo-1695655300485-d3da8bc72076",
            "registration_fee": 800.0,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Urban 10K Challenge",
            "description": "Navigate through the vibrant cityscape in this exciting urban running challenge. Great for city runners!",
            "date": "2025-09-12",
            "location": "Delhi NCR",
            "distance": "10 km",
            "category": "Urban Run",
            "max_participants": 800,
            "current_participants": 523,
            "image_url": "https://images.unsplash.com/photo-1746046489457-9628dc3b8a1f",
            "registration_fee": 700.0,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Charity Fun Run",
            "description": "Run for a cause! All proceeds go to children's education. Family-friendly event with multiple distance options.",
            "date": "2025-10-01",
            "location": "Pune, Maharashtra",
            "distance": "3 km",
            "category": "Fun Run",
            "max_participants": 2000,
            "current_participants": 1456,
            "image_url": "https://images.unsplash.com/photo-1700667877838-e9c93ca95f05",
            "registration_fee": 300.0,
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
