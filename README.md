# RunKumbh - Monsoon & Summer Running Revolution 🌧️☀️

A complete running/marathon event website with a stunning unified monsoon-summer theme design.

## 🎨 Design Theme

**Unified Monsoon-Summer Aesthetic:**
- **Monsoon Elements**: Cool teals (#0D9488), blues, water droplet icons, refreshing vibes
- **Summer Elements**: Warm oranges (#F97316), yellows, sun icons, energetic vibes
- **Unified Approach**: Smooth gradients blending cool and warm tones throughout the site
- **Visual Effects**: Animated water droplets, sun rays, hover transitions, glassmorphism

## ✨ Features

### Frontend
- **Hero Section**: Full-screen hero with dynamic background and gradient overlay
- **About Section**: Four feature cards showcasing Monsoon Magic, Summer Energy, Champion Spirit, and Community First
- **Events Section**: 6 upcoming events with registration functionality
  - Full event details (date, location, distance, category, price)
  - Participant tracking
  - One-click registration with modal forms
- **Gallery Section**: 8 event photos with hover effects
- **Contact Section**: Contact information cards + message form
- **Navigation**: Smooth scroll navigation with mobile-responsive hamburger menu
- **Animations**: Fade-in effects, droplet animations, sun ray rotations
- **Fully Responsive**: Mobile, tablet, and desktop optimized

### Backend API
Complete RESTful API with the following endpoints:

**Auth:**
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login with JWT

**Events:**
- `GET /api/events` - List all events
- `GET /api/events/{id}` - Get event details
- `POST /api/events` - Create event (admin)

**Registrations:**
- `POST /api/registrations` - Register for event
- `GET /api/registrations/email/{email}` - Get user's registrations

**Gallery:**
- `GET /api/gallery` - Get all gallery images
- `POST /api/gallery` - Upload gallery image

**Contact:**
- `POST /api/contact` - Submit contact form
- `GET /api/contacts` - Get all contact submissions

## 🗄️ Database Schema

**Collections:**
1. **users** - Runner profiles with authentication
2. **events** - Marathon/running event details
3. **registrations** - Event registrations with BIB numbers
4. **gallery** - Photo gallery items
5. **contacts** - Contact form submissions

## 🚀 Tech Stack

**Frontend:**
- React 19
- Tailwind CSS
- Radix UI Components (shadcn/ui)
- React Router
- Axios
- Lucide Icons

**Backend:**
- FastAPI
- Motor (Async MongoDB)
- PyJWT (Authentication)
- Bcrypt (Password hashing)
- Pydantic (Validation)

**Database:**
- MongoDB

## 📦 Setup & Running

### Backend
```bash
cd /app/backend
python seed_data.py  # Seed initial data
sudo supervisorctl restart backend
```

### Frontend
```bash
cd /app/frontend
sudo supervisorctl restart frontend
```

### Both Services
```bash
sudo supervisorctl restart all
```

## 🎯 Pre-seeded Data

**6 Events:**
1. Monsoon Marathon 2025 (42 km) - Mumbai
2. Summer Sprint 5K (5 km) - Bangalore
3. Half Marathon - Coastal Run (21 km) - Goa
4. Trail Run Adventure (15 km) - Coorg
5. Urban 10K Challenge (10 km) - Delhi NCR
6. Charity Fun Run (3 km) - Pune

**8 Gallery Images:**
- Marathon start lines
- Running events
- Finish line celebrations
- Community moments
- Medal ceremonies

## 🎨 Color Palette

- **Primary Teal**: #0D9488 (Monsoon freshness)
- **Primary Orange**: #F97316 (Summer energy)
- **Sky Blue**: #0EA5E9 (Rain and clear skies)
- **Golden Yellow**: #FCD34D (Sunshine)
- **Fresh Green**: #10B981 (Nature vibes)

## 📱 Responsive Breakpoints

- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

## ✅ Testing

All features have been tested:
- ✅ Event registration with form validation
- ✅ Contact form submission
- ✅ Mobile navigation menu
- ✅ Responsive design (mobile, tablet, desktop)
- ✅ API endpoints
- ✅ Database operations
- ✅ Success notifications (toast messages)

## 🌐 Live URL

The website is live at: https://kumbh-marathon.preview.emergentagent.com

## 🎉 Key Highlights

1. **Beautiful Design**: Unified monsoon-summer theme with professional aesthetics
2. **Fully Functional**: Complete backend with authentication, registration, and data management
3. **User Experience**: Smooth animations, responsive design, intuitive navigation
4. **Production Ready**: Form validations, error handling, success notifications
5. **Scalable**: Clean code architecture, RESTful API, MongoDB for flexibility

## 📝 Notes

- All passwords are hashed using bcrypt
- JWT tokens expire after 7 days
- UUIDs used instead of MongoDB ObjectIds for better JSON serialization
- CORS enabled for cross-origin requests
- Hot reload enabled for both frontend and backend during development

---

**Built with ❤️ combining the freshness of monsoon with the energy of summer!**
