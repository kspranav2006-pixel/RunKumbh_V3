import { useState, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";
import { Toaster } from "@/components/ui/toaster";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Calendar, MapPin, Droplets, Sun, ArrowRight, Phone, Menu, X, Clock, Wallet, Trophy, Trash2, Plus, Edit2 } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const EVENT_DATE = new Date('2026-05-30T00:00:00');

function App() {
  const [events, setEvents] = useState([]);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    fetchEvents();
    checkPaymentStatus();
  }, []);

  const checkPaymentStatus = async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');
    
    if (sessionId) {
      let attempts = 0;
      const maxAttempts = 5;
      
      const pollStatus = async () => {
        try {
          const response = await axios.get(`${API}/payments/checkout/status/${sessionId}`);
          
          if (response.data.payment_status === 'paid') {
            toast({
              title: 'Payment Successful! 🎉',
              description: `Registration confirmed! Your BIB number is: ${response.data.bib_number}`,
              duration: 10000,
            });
            window.history.replaceState({}, document.title, window.location.pathname);
            return;
          }
          
          attempts++;
          if (attempts < maxAttempts) {
            setTimeout(pollStatus, 2000);
          }
        } catch (error) {
          console.error('Error checking payment status:', error);
        }
      };
      
      pollStatus();
    }
  };

  const fetchEvents = async () => {
    try {
      const response = await axios.get(`${API}/events`);
      setEvents(response.data);
    } catch (error) {
      console.error('Error fetching events:', error);
    }
  };

  const scrollToSection = (sectionId) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
      setIsMenuOpen(false);
    }
  };

  return (
    <BrowserRouter>
      <div className="App min-h-screen">
        <Toaster />
        <Routes>
          <Route path="/" element={
            <HomePage 
              events={events}
              scrollToSection={scrollToSection}
              isMenuOpen={isMenuOpen}
              setIsMenuOpen={setIsMenuOpen}
              toast={toast}
            />
          } />
          <Route path="/admin" element={<AdminPage toast={toast} />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

function HomePage({ events, scrollToSection, isMenuOpen, setIsMenuOpen, toast }) {
  return (
    <>
      <Navigation scrollToSection={scrollToSection} isMenuOpen={isMenuOpen} setIsMenuOpen={setIsMenuOpen} />
      <HeroSection scrollToSection={scrollToSection} />
      <CountdownSection />
      <AboutSection />
      <EventsSection events={events} toast={toast} />
      <RouteMapSection />
      <RulesSection />
      <ContactSection />
      <Footer scrollToSection={scrollToSection} />
    </>
  );
}

function Navigation({ scrollToSection, isMenuOpen, setIsMenuOpen }) {
  const navItems = [
    { label: 'Home', id: 'home' },
    { label: 'About', id: 'about' },
    { label: 'Register', id: 'events' },
    { label: 'Route Map', id: 'routemap' },
    { label: 'Rules', id: 'rules' },
    { label: 'Contact', id: 'contact' }
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-2">
            <Droplets className="w-8 h-8 text-teal-600" />
            <Sun className="w-8 h-8 text-orange-600" />
            <span className="text-2xl font-bold text-gradient">RunKumbh</span>
          </div>

          <div className="hidden md:flex items-center space-x-8">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => scrollToSection(item.id)}
                className="text-gray-700 hover:text-teal-600 font-semibold transition-colors"
              >
                {item.label}
              </button>
            ))}
          </div>

          <button
            className="md:hidden p-2"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            {isMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {isMenuOpen && (
          <div className="md:hidden py-4 bg-white rounded-lg shadow-lg">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => scrollToSection(item.id)}
                className="block w-full text-left px-4 py-3 text-gray-700 hover:bg-teal-50 hover:text-teal-600 font-semibold"
              >
                {item.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </nav>
  );
}

function HeroSection({ scrollToSection }) {
  return (
    <section id="home" className="relative min-h-screen flex items-center justify-center overflow-hidden bg-gradient-primary pt-16">
      <div className="absolute inset-0 bg-gradient-to-br from-teal-600 via-teal-500 to-orange-500 opacity-90"></div>

      <div className="relative z-10 text-center px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto">
        
        {/* RUN KUMBH title with photos on left and right */}
        <div className="flex items-center justify-center gap-4 mb-4 animate-fadeIn">
          
          {/* LEFT PHOTO - RVITM Logo */}
          <img
            src="https://lh3.googleusercontent.com/d/1fMPtMJ-gRTr_31b4zn02PK4dneRuknZ5"
            alt="RVITM Logo"
            className="hidden sm:block object-contain rounded-2xl"
            style={{ width: '120px', height: '100px' }}
          />

          <h1 className="text-5xl sm:text-6xl lg:text-8xl font-bold text-white drop-shadow-2xl">
            RUN KUMBH
          </h1>

          {/* RIGHT PHOTO - NCC Logo */}
          <img
            src="https://lh3.googleusercontent.com/d/1Rn8TjlvghEiEzfMvtW8eZkVybc8d2vpi"
            alt="NCC Logo"
            className="hidden sm:block object-contain rounded-2xl"
            style={{ width: '120px', height: '120px' }}
          />

        </div>
        
        <div className="bg-white/20 backdrop-blur-md rounded-3xl px-8 py-4 mb-6 inline-block animate-fadeIn delay-100">
          <h2 className="text-4xl sm:text-5xl lg:text-7xl font-extrabold text-white tracking-wide">
            MONSOON RUN 2.0
          </h2>
        </div>
        
        <p className="text-2xl sm:text-3xl text-yellow-200 font-bold mb-4 animate-fadeIn delay-200">
          🌧️ 2026-27 Edition ☀️
        </p>
        
        <p className="text-xl text-white mb-8 animate-fadeIn delay-300">
          <span className="font-bold text-2xl">RV Institute of Technology and Management</span>
          <br />National Cadet Corps 
        </p>
        
        <div className="bg-white/15 backdrop-blur-md rounded-2xl p-6 mb-8 inline-block animate-fadeIn delay-400">
          <p className="text-white text-lg font-semibold mb-2">📅 Registration Period</p>
          <p className="text-yellow-200 text-2xl font-bold">20th April - 15th May 2026</p>
          <p className="text-white mt-3">🎁 Medal | Certificate | T-Shirt | Refreshments</p>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center animate-fadeIn delay-400">
          <Button
            size="lg"
            onClick={() => scrollToSection('events')}
            className="bg-white text-teal-600 hover:bg-teal-50 text-xl px-10 py-7 shadow-2xl font-bold"
          >
            Register Now <ArrowRight className="ml-2" />
          </Button>
          <Button
            size="lg"
            variant="outline"
            onClick={() => scrollToSection('contact')}
            className="bg-white/20 backdrop-blur-md text-white border-2 border-white hover:bg-white/30 text-xl px-10 py-7 shadow-2xl"
          >
            Contact Us
          </Button>
        </div>
      </div>
    </section>
  );
}

function CountdownSection() {
  const [timeLeft, setTimeLeft] = useState({
    days: 0,
    hours: 0,
    minutes: 0,
    seconds: 0
  });

  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date().getTime();
      const distance = EVENT_DATE.getTime() - now;

      if (distance > 0) {
        setTimeLeft({
          days: Math.floor(distance / (1000 * 60 * 60 * 24)),
          hours: Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)),
          minutes: Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60)),
          seconds: Math.floor((distance % (1000 * 60)) / 1000)
        });
      }
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  return (
    <section className="py-16 bg-gradient-secondary">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-8">
          <h2 className="text-4xl font-bold text-white mb-2 flex items-center justify-center gap-3">
            <Clock className="w-10 h-10" />
            Event Countdown
          </h2>
          <p className="text-white text-lg">May 30, 2026 - Get Ready!</p>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
          {Object.entries(timeLeft).map(([unit, value]) => (
            <div key={unit} className="bg-white/20 backdrop-blur-md rounded-xl p-6 text-center animate-float">
              <div className="text-6xl font-bold text-white mb-2">{value}</div>
              <div className="text-white text-lg capitalize">{unit}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function AboutSection() {
  const features = [
    {
      icon: <Droplets className="w-12 h-12 text-teal-600" />,
      title: 'Monsoon Magic',
      description: 'Run through refreshing rain showers and experience nature\'s cooling embrace!'
    },
    {
      icon: <Sun className="w-12 h-12 text-orange-600" />,
      title: 'Summer Energy',
      description: 'Feel the warmth of summer sunshine energizing your every step.'
    },
    {
      icon: <Wallet className="w-12 h-12 text-orange-600" />,
      title: 'Prize Money',
      description: 'The Total Prize pool for this event is ₹45000. Cash prizes for: Open 5K (₹24,000), Students 3K (₹10,000), and Staff 3K (₹10,000). Minimum participant requirements apply.'
    }
  ];

  return (
    <section id="about" className="py-20 px-4 sm:px-6 lg:px-8 section-cream">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-5xl font-bold text-gray-900 mb-4 animate-fadeIn">
            About <span className="text-gradient">RunKumbh 2.0</span>
          </h2>
          <p className="text-2xl text-gray-700 font-semibold">
            RV Institute of Technology and Management
          </p>
          <p className="text-2xl text-gray-700 font-semibold">
            National Cadet Corps
          </p>
          <p className="text-lg text-gray-600 mt-2">
            monsoon running event
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {features.map((feature, index) => (
            <Card key={index} className="card-modern animate-slideInLeft" style={{animationDelay: `${index * 0.1}s`, opacity: 0}}>
              <CardHeader>
                <div className="mb-4 animate-float">{feature.icon}</div>
                <CardTitle className="text-2xl">{feature.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 text-lg">{feature.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}

function EventsSection({ events, toast }) {
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [registrationData, setRegistrationData] = useState({
    user_name: '',
    user_email: '',
    user_phone: ''
  });
  const [isRegistering, setIsRegistering] = useState(false);

  const handleRegister = async (e) => {
    e.preventDefault();
    setIsRegistering(true);

    try {
      const originUrl = window.location.origin;
      
      const response = await axios.post(`${API}/payments/checkout/session`, {
        event_id: selectedEvent.id,
        origin_url: originUrl,
        ...registrationData
      });

      if (response.data.url) {
        window.location.href = response.data.url;
      }
    } catch (error) {
      toast({
        title: 'Registration Failed',
        description: error.response?.data?.detail || 'Please try again later',
        variant: 'destructive'
      });
      setIsRegistering(false);
    }
  };

  return (
    <section id="events" className="py-20 px-4 sm:px-6 lg:px-8 section-coral">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-5xl font-bold text-gray-900 mb-4">
            Registration <span className="text-gradient">Categories</span>
          </h2>
          <p className="text-2xl text-gray-700 font-semibold mb-4">
            Choose Your Challenge & Run for Glory!
          </p>
          <div className="inline-block bg-gradient-primary text-white px-8 py-3 rounded-full text-lg font-bold shadow-xl animate-pulse">
            Registration: 20 April - 15 May 2026
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {/* Event Details & Perks Card */}
          <Card className="card-modern animate-fadeIn" style={{border: '4px solid #0D7377'}}>
            <CardHeader className="bg-gradient-ocean text-white">
              <CardTitle className="text-2xl flex items-center gap-2">
                <Trophy className="w-8 h-8 animate-bounce" />
                Event Details & Perks
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <ul className="space-y-3">
                <li className="flex items-start text-gray-700">
                  <span className="mr-3 text-2xl">🏅</span>
                  <span>Finisher Medal for all participants</span>
                </li>
                <li className="flex items-start text-gray-700">
                  <span className="mr-3 text-2xl">📜</span>
                  <span>Certificate of participation</span>
                </li>
                <li className="flex items-start text-gray-700">
                  <span className="mr-3 text-2xl">👕</span>
                  <span>Event T-Shirt</span>
                </li>
                <li className="flex items-start text-gray-700">
                  <span className="mr-3 text-2xl">🥤</span>
                  <span>Refreshments & Water stations</span>
                </li>
                <li className="flex items-start text-gray-700">
                  <span className="mr-3 text-2xl">💰</span>
                  <span>Total Cash Prize Of ₹45,000</span>
                </li>
                <li className="flex items-start text-gray-700">
                  <span className="mr-3 text-2xl">🚑</span>
                  <span>Medical support throughout</span>
                </li>
              </ul>
              <p className="text-sm text-coral-600 mt-6 font-semibold bg-yellow-50 p-3 rounded-lg border-l-4 border-coral-500">
                *Cash prize applicable for categories(Open Men & Women- 5K Run, Students/NCC/NSS- 5K Run, Students/Staff- 3K Run)
              </p>
            </CardContent>
          </Card>

          {/* Event Cards */}
          {events.map((event, index) => (
            <Card key={event.id} className="card-modern animate-fadeIn" style={{animationDelay: `${index * 0.1}s`, opacity: 0}}>
              <div className="relative h-48 overflow-hidden rounded-t-lg">
                <img
                  src={event.image_url}
                  alt={event.title}
                  className="w-full h-full object-cover"
                />
                <div className="absolute top-4 right-4 bg-gradient-primary text-white px-4 py-2 rounded-full font-bold shadow-lg">
                  {event.category}
                </div>
              </div>
              <CardHeader>
                <CardTitle className="text-2xl">{event.title}</CardTitle>
                <CardDescription className="text-gray-600 text-base">{event.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center text-gray-700">
                  <Calendar className="w-5 h-5 mr-2 text-teal-600" />
                  <span>{new Date(event.date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</span>
                </div>
                <div className="flex items-center text-gray-700">
                  <MapPin className="w-5 h-5 mr-2 text-orange-600" />
                  <span>{event.location}</span>
                </div>
                <div className="flex justify-between items-center pt-4 border-t">
                  <span className="text-3xl font-bold text-gradient">₹{event.registration_fee}</span>
                  <span className="text-xl font-semibold text-gray-700">{event.distance}</span>
                </div>
              </CardContent>
              <CardFooter>
                <Dialog open={selectedEvent?.id === event.id} onOpenChange={(open) => !open && setSelectedEvent(null)}>
                  <DialogTrigger asChild>
                    <Button
                      className="w-full bg-gradient-primary hover:opacity-90 text-white font-bold text-lg py-6"
                      onClick={() => setSelectedEvent(event)}
                    >
                      Register & Pay Now
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="sm:max-w-md">
                    <DialogHeader>
                      <DialogTitle>Register for {event.title}</DialogTitle>
                      <DialogDescription>
                        Complete your details to proceed to payment
                      </DialogDescription>
                    </DialogHeader>
                    <form onSubmit={handleRegister} className="space-y-4">
                      <div>
                        <Label htmlFor="user_name">Full Name</Label>
                        <Input
                          id="user_name"
                          required
                          value={registrationData.user_name}
                          onChange={(e) => setRegistrationData({ ...registrationData, user_name: e.target.value })}
                        />
                      </div>
                      <div>
                        <Label htmlFor="user_email">Email</Label>
                        <Input
                          id="user_email"
                          type="email"
                          required
                          value={registrationData.user_email}
                          onChange={(e) => setRegistrationData({ ...registrationData, user_email: e.target.value })}
                        />
                      </div>
                      <div>
                        <Label htmlFor="user_phone">Phone Number</Label>
                        <Input
                          id="user_phone"
                          type="tel"
                          required
                          value={registrationData.user_phone}
                          onChange={(e) => setRegistrationData({ ...registrationData, user_phone: e.target.value })}
                        />
                      </div>
                      <Button
                        type="submit"
                        className="w-full bg-gradient-primary hover:opacity-90 text-lg py-6"
                        disabled={isRegistering}
                      >
                        {isRegistering ? 'Processing...' : `Pay ₹${event.registration_fee} & Register`}
                      </Button>
                      <p className="text-xs text-center text-gray-500">
                        ✅ Secure payment powered by Stripe
                      </p>
                    </form>
                  </DialogContent>
                </Dialog>
              </CardFooter>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}

function RouteMapSection() {
  return (
    <section id="routemap" className="py-20 px-4 sm:px-6 lg:px-8 section-cream">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-5xl font-bold text-gray-900 mb-4">
            Event <span className="text-gradient">Route Map</span>
          </h2>
          <p className="text-xl text-gray-600">
            Scenic route through RVITM campus
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* 3K Route */}
          <Card className="card-modern">
            <CardHeader>
              <CardTitle className="text-2xl text-center text-gradient">3kms Route</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="rounded-lg overflow-hidden">
                <img 
                  src="https://lh3.googleusercontent.com/d/1457pNBVAoWXHY61-RSq2MeqM0iFOzH4j"
                  alt="3km Route Map"
                  className="w-full h-auto object-cover"
                />
              </div>
            </CardContent>
          </Card>

          {/* 5K Route */}
          <Card className="card-modern">
            <CardHeader>
              <CardTitle className="text-2xl text-center text-gradient">5kms Route</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="rounded-lg overflow-hidden">
                <img 
                  src="https://customer-assets.emergentagent.com/job_kumbh-marathon/artifacts/6bk49mbp_Route-5k.png"
                  alt="5km Route Map"
                  className="w-full h-auto object-cover"
                />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
}

function RulesSection() {
  const rules = [
    {
      title: "Eligibility",
      points: [
        "Participants must be 8 years or older",
        "Students must carry valid ID cards",
        "NCC/NSS members need membership proof",
        "Family run: 1 Male, 1 Female, 1 Child (min 8 years)"
      ]
    },
    {
      title: "Registration",
      points: [
        "Online registration mandatory",
        "Registration closes on 15th May 2026",
        "BIB numbers issued after payment confirmation",
        "No refunds after registration"
      ]
    },
    {
      title: "Event Day Rules",
      points: [
        "Report 30 minutes before start time",
        "BIB number must be worn visibly",
        "Follow marshal instructions",
        "Stay hydrated at water stations"
      ]
    },
    {
      title: "Schedule",
      points: [
        "5:30 AM - Registration",
        "6:00 AM - Warm-up",
        "6:30 AM - Marathon Start",
        "8:30 AM - Prize Distribution"
      ]
    }
  ];

  return (
    <section id="rules" className="py-20 px-4 sm:px-6 lg:px-8 section-coral">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-5xl font-bold text-gray-900 mb-4">
            Event <span className="text-gradient">Rules & Schedule</span>
          </h2>
          <p className="text-xl text-gray-600">
            Please read carefully before registration
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {rules.map((section, index) => (
            <Card key={index} className="card-modern animate-slideInLeft" style={{animationDelay: `${index * 0.1}s`, opacity: 0}}>
              <CardHeader>
                <CardTitle className="text-2xl flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-primary flex items-center justify-center text-white font-bold">
                    {index + 1}
                  </div>
                  {section.title}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {section.points.map((point, idx) => (
                    <li key={idx} className="flex items-start text-gray-700">
                      <span className="text-teal-600 mr-2 font-bold text-xl">•</span>
                      <span className="text-base">{point}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}

function ContactSection() {
  return (
    <section id="contact" className="py-20 px-4 sm:px-6 lg:px-8 section-cream">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-5xl font-bold text-gray-900 mb-4">
            Get in <span className="text-gradient">Touch</span>
          </h2>
          <p className="text-xl text-gray-600">
            Have questions? Contact us!
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          <Card className="card-modern">
            <CardHeader>
              <div className="flex items-center space-x-3">
                <Phone className="w-7 h-7 text-teal-600" />
                <CardTitle className="text-xl">Lt. Raghu G M(Event Manager)</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-teal-600 font-semibold text-xl">+91 9743743618</p>
            </CardContent>
          </Card>

          <Card className="card-modern">
            <CardHeader>
              <div className="flex items-center space-x-3">
                <Phone className="w-7 h-7 text-orange-600" />
                <CardTitle className="text-xl">Pranav(Event co-ordinator)</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-orange-600 font-semibold text-xl">+91 8073290482</p>
            </CardContent>
          </Card>

          <Card className="card-modern">
            <CardHeader>
              <div className="flex items-center space-x-3">
                <Phone className="w-7 h-7 text-teal-600" />
                <CardTitle className="text-xl">Prajeet(Event co-ordinator)</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-teal-600 font-semibold text-xl">+91 9845610718</p>
            </CardContent>
          </Card>
        </div>

        <Card className="card-modern mt-8 max-w-3xl mx-auto">
          <CardHeader>
            <CardTitle className="text-2xl text-center">Location</CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <p className="text-gray-700 font-semibold text-lg">RV Institute of Technology and Management</p>
            <p className="text-gray-600 mt-2">National Cadet Corps</p>
            <p className="text-gray-600">Bengaluru, Karnataka</p>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}

function Footer({ scrollToSection }) {
  return (
    <footer className="bg-gradient-primary text-white py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <Droplets className="w-8 h-8" />
              <Sun className="w-8 h-8" />
              <span className="text-2xl font-bold">RunKumbh 2.0</span>
            </div>
            <p className="text-white/90 font-semibold">
              RV Institute of Technology and Management
            </p>
            <p className="text-white/70 text-sm mt-2">
              National Cadet Corps
            </p>
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-4">Quick Links</h3>
            <ul className="space-y-2">
              {['about', 'events', 'rules', 'contact'].map((link) => (
                <li key={link}>
                  <button onClick={() => scrollToSection(link)} className="text-white/80 hover:text-white capitalize">
                    {link === 'events' ? 'Register' : link}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-4">Contact</h3>
            <p className="text-white/80 mb-2">Lt. Raghu G M: +91 9743743618</p>
            <p className="text-white/80 mb-2">Pranav: +91 8073290482</p>
            <p className="text-white/80 mb-4">Prajeet: +91 9845610718</p>
            <p className="text-sm text-white/70">Registration: 20 April - 15 May 2026</p>
          </div>
        </div>

        <div className="border-t border-white/20 mt-8 pt-8 text-center">
          <p className="font-semibold">© 2026-27 RunKumbh - Monsoon Run 2.0</p>
          <p className="text-sm mt-2">RV Institute of Technology and Management</p>
        </div>
      </div>
    </footer>
  );
}

function AdminPage({ toast }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState('');
  const [registrations, setRegistrations] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({ total_registrations: 0, total_transactions: 0 });
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [newRegistration, setNewRegistration] = useState({
    event_id: '',
    user_name: '',
    user_email: '',
    user_phone: ''
  });

  const [showEditEventDialog, setShowEditEventDialog] = useState(false);
  const [showAddEventDialog, setShowAddEventDialog] = useState(false);
  const [selectedEditEvent, setSelectedEditEvent] = useState(null);
  const [editEventData, setEditEventData] = useState({
    title: '',
    description: '',
    registration_fee: '',
    image_url: '',
    location: '',
    distance: '',
    category: '',
    max_participants: ''
  });
  const [newEventData, setNewEventData] = useState({
    title: '',
    description: '',
    date: '2026-05-30',
    location: 'RV Institute of Technology and Management, Bengaluru',
    distance: '',
    category: '',
    max_participants: '',
    image_url: '',
    registration_fee: ''
  });

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/admin/login`, { password });
      localStorage.setItem('admin_token', response.data.token);
      setIsAuthenticated(true);
      toast({
        title: 'Login Successful!',
        description: 'Welcome to admin dashboard',
      });
      fetchRegistrations();
    } catch (error) {
      toast({
        title: 'Login Failed',
        description: 'Invalid password',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchRegistrations = async () => {
    try {
      const response = await axios.get(`${API}/admin/registrations`);
      setRegistrations(response.data.registrations);
      setTransactions(response.data.transactions);
      setEvents(response.data.events);
      setStats({
        total_registrations: response.data.total_registrations,
        total_transactions: response.data.total_transactions
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to fetch registrations',
        variant: 'destructive'
      });
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('admin_token');
    if (token) {
      setIsAuthenticated(true);
      fetchRegistrations();
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    setIsAuthenticated(false);
    setPassword('');
  };

  const getEventName = (eventId) => {
    const event = events.find(e => e.id === eventId);
    return event ? event.title : eventId;
  };

  const handleDeleteRegistration = async (registrationId) => {
    if (!window.confirm('Are you sure you want to delete this registration?')) {
      return;
    }

    try {
      await axios.delete(`${API}/admin/registrations/${registrationId}`);
      toast({
        title: 'Registration Deleted',
        description: 'Registration has been removed successfully',
      });
      fetchRegistrations();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete registration',
        variant: 'destructive'
      });
    }
  };

  const handleDeleteTransaction = async (transactionId) => {
    if (!window.confirm('Are you sure you want to delete this transaction?')) {
      return;
    }

    try {
      await axios.delete(`${API}/admin/transactions/${transactionId}`);
      toast({
        title: 'Transaction Deleted',
        description: 'Transaction has been removed successfully',
      });
      fetchRegistrations();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete transaction',
        variant: 'destructive'
      });
    }
  };

  const handleAddRegistration = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.post(`${API}/admin/registrations`, newRegistration);
      toast({
        title: 'Registration Added!',
        description: 'New registration created successfully',
      });
      setShowAddDialog(false);
      setNewRegistration({ event_id: '', user_name: '', user_email: '', user_phone: '' });
      fetchRegistrations();
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to add registration',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (registrationId, newStatus) => {
    try {
      await axios.put(`${API}/admin/registrations/${registrationId}`, { status: newStatus });
      toast({
        title: 'Status Updated',
        description: 'Registration status has been updated',
      });
      fetchRegistrations();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to update status',
        variant: 'destructive'
      });
    }
  };

  const handleEditEvent = (event) => {
    setSelectedEditEvent(event);
    setEditEventData({
      title: event.title,
      description: event.description,
      registration_fee: event.registration_fee,
      image_url: event.image_url,
      location: event.location,
      distance: event.distance,
      category: event.category,
      max_participants: event.max_participants
    });
    setShowEditEventDialog(true);
  };

  const handleUpdateEvent = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.put(`${API}/admin/events/${selectedEditEvent.id}`, {
        ...editEventData,
        registration_fee: parseFloat(editEventData.registration_fee),
        max_participants: parseInt(editEventData.max_participants)
      });
      toast({
        title: 'Event Updated!',
        description: 'Event details have been updated successfully',
      });
      setShowEditEventDialog(false);
      fetchRegistrations();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to update event',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleAddEvent = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/admin/events`, {
        ...newEventData,
        registration_fee: parseFloat(newEventData.registration_fee),
        max_participants: parseInt(newEventData.max_participants)
      });
      toast({
        title: 'Event Added!',
        description: 'New event created successfully',
      });
      setShowAddEventDialog(false);
      setNewEventData({
        title: '',
        description: '',
        date: '2026-05-30',
        location: 'RV Institute of Technology and Management, Bengaluru',
        distance: '',
        category: '',
        max_participants: '',
        image_url: '',
        registration_fee: ''
      });
      fetchRegistrations();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to add event',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteEvent = async (eventId) => {
    if (!window.confirm('Are you sure you want to delete this event? This action cannot be undone.')) {
      return;
    }

    try {
      await axios.delete(`${API}/admin/events/${eventId}`);
      toast({
        title: 'Event Deleted',
        description: 'Event has been removed successfully',
      });
      fetchRegistrations();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete event',
        variant: 'destructive'
      });
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-primary flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="text-3xl text-center">Admin Login</CardTitle>
            <CardDescription className="text-center">Enter password to access registrations</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter admin password"
                  required
                />
              </div>
              <Button
                type="submit"
                className="w-full bg-gradient-primary"
                disabled={loading}
              >
                {loading ? 'Logging in...' : 'Login'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-light p-4">
      <div className="max-w-[1800px] mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-gradient">Admin Dashboard</h1>
            <p className="text-gray-600 mt-2">RunKumbh Registrations & BIB Numbers</p>
          </div>
          <Button onClick={handleLogout} variant="outline">
            Logout
          </Button>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card className="card-modern">
            <CardHeader>
              <CardTitle>Total Registrations</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-4xl font-bold text-gradient">{stats.total_registrations}</p>
            </CardContent>
          </Card>
          <Card className="card-modern">
            <CardHeader>
              <CardTitle>Total Transactions</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-4xl font-bold text-gradient">{stats.total_transactions}</p>
            </CardContent>
          </Card>
          <Card className="card-modern">
            <CardHeader>
              <CardTitle>Events</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-4xl font-bold text-gradient">{events.length}</p>
            </CardContent>
          </Card>
        </div>

        {/* Manage Events Card */}
        <div className="flex flex-row items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">Manage Events</h2>
          <Button 
            className="bg-gradient-primary whitespace-nowrap"
            onClick={() => setShowAddEventDialog(true)}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Event
          </Button>
        </div>
        <Card className="card-modern mb-8">
          <CardContent className="pt-6">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-3 font-semibold">Title</th>
                    <th className="text-left p-3 font-semibold">Category</th>
                    <th className="text-left p-3 font-semibold">Distance</th>
                    <th className="text-left p-3 font-semibold">Price</th>
                    <th className="text-left p-3 font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map((event, index) => (
                    <tr key={index} className="border-b hover:bg-teal-50">
                      <td className="p-3 font-semibold">{event.title}</td>
                      <td className="p-3">{event.category}</td>
                      <td className="p-3">{event.distance}</td>
                      <td className="p-3 font-bold text-teal-600">₹{event.registration_fee}</td>
                      <td className="p-3">
                        <div className="flex gap-2 min-w-[200px]">
                          <Button
                            size="sm"
                            className="bg-gradient-primary"
                            onClick={() => handleEditEvent(event)}
                          >
                            <Edit2 className="w-4 h-4 mr-1" />
                            Edit
                          </Button>
                          <Button
                            size="sm"
                            variant="destructive"
                            className="bg-red-500 hover:bg-red-600"
                            onClick={() => handleDeleteEvent(event.id)}
                          >
                            <Trash2 className="w-4 h-4 mr-1" />
                            Delete
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Add Event Dialog */}
        <Dialog open={showAddEventDialog} onOpenChange={setShowAddEventDialog}>
          <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Add New Event</DialogTitle>
              <DialogDescription>Create a new event category</DialogDescription>
            </DialogHeader>
            <form onSubmit={handleAddEvent} className="space-y-4">
              <div>
                <Label>Title</Label>
                <Input
                  value={newEventData.title}
                  onChange={(e) => setNewEventData({...newEventData, title: e.target.value})}
                  placeholder="E.g., Open Men & Women - 5K Run"
                  required
                />
              </div>
              <div>
                <Label>Description</Label>
                <textarea
                  className="w-full p-2 border rounded min-h-[100px] text-sm"
                  value={newEventData.description}
                  onChange={(e) => setNewEventData({...newEventData, description: e.target.value})}
                  placeholder="Include prize details and participant requirements"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Distance</Label>
                  <Input
                    value={newEventData.distance}
                    onChange={(e) => setNewEventData({...newEventData, distance: e.target.value})}
                    placeholder="E.g., 5 km"
                    required
                  />
                </div>
                <div>
                  <Label>Category</Label>
                  <Input
                    value={newEventData.category}
                    onChange={(e) => setNewEventData({...newEventData, category: e.target.value})}
                    placeholder="E.g., Open 5K"
                    required
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Price (₹)</Label>
                  <Input
                    type="number"
                    value={newEventData.registration_fee}
                    onChange={(e) => setNewEventData({...newEventData, registration_fee: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label>Max Participants</Label>
                  <Input
                    type="number"
                    value={newEventData.max_participants}
                    onChange={(e) => setNewEventData({...newEventData, max_participants: e.target.value})}
                    required
                  />
                </div>
              </div>
              <div>
                <Label>Location</Label>
                <Input
                  value={newEventData.location}
                  onChange={(e) => setNewEventData({...newEventData, location: e.target.value})}
                  required
                />
              </div>
              <div>
                <Label>Image URL</Label>
                <Input
                  value={newEventData.image_url}
                  onChange={(e) => setNewEventData({...newEventData, image_url: e.target.value})}
                  placeholder="https://..."
                  required
                />
                {newEventData.image_url && (
                  <img
                    src={newEventData.image_url}
                    alt="Preview"
                    className="mt-2 w-full h-32 object-cover rounded-lg"
                  />
                )}
              </div>
              <Button
                type="submit"
                className="w-full bg-gradient-primary text-lg py-6"
                disabled={loading}
              >
                {loading ? 'Creating...' : 'Create Event'}
              </Button>
            </form>
          </DialogContent>
        </Dialog>

        {/* Edit Event Dialog */}
        <Dialog open={showEditEventDialog} onOpenChange={setShowEditEventDialog}>
          <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Edit Event</DialogTitle>
              <DialogDescription>Update event details below</DialogDescription>
            </DialogHeader>
            <form onSubmit={handleUpdateEvent} className="space-y-4">
              <div>
                <Label>Title</Label>
                <Input
                  value={editEventData.title}
                  onChange={(e) => setEditEventData({...editEventData, title: e.target.value})}
                  required
                />
              </div>
              <div>
                <Label>Description</Label>
                <textarea
                  className="w-full p-2 border rounded min-h-[100px] text-sm"
                  value={editEventData.description}
                  onChange={(e) => setEditEventData({...editEventData, description: e.target.value})}
                  required
                />
              </div>
              <div>
                <Label>Price (₹)</Label>
                <Input
                  type="number"
                  value={editEventData.registration_fee}
                  onChange={(e) => setEditEventData({...editEventData, registration_fee: e.target.value})}
                  required
                />
              </div>
              <div>
                <Label>Image URL</Label>
                <Input
                  value={editEventData.image_url}
                  onChange={(e) => setEditEventData({...editEventData, image_url: e.target.value})}
                  required
                />
                {editEventData.image_url && (
                  <img
                    src={editEventData.image_url}
                    alt="Preview"
                    className="mt-2 w-full h-32 object-cover rounded-lg"
                  />
                )}
              </div>
              <div>
                <Label>Location</Label>
                <Input
                  value={editEventData.location}
                  onChange={(e) => setEditEventData({...editEventData, location: e.target.value})}
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Distance</Label>
                  <Input
                    value={editEventData.distance}
                    onChange={(e) => setEditEventData({...editEventData, distance: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label>Category</Label>
                  <Input
                    value={editEventData.category}
                    onChange={(e) => setEditEventData({...editEventData, category: e.target.value})}
                    required
                  />
                </div>
              </div>
              <div>
                <Label>Max Participants</Label>
                <Input
                  type="number"
                  value={editEventData.max_participants}
                  onChange={(e) => setEditEventData({...editEventData, max_participants: e.target.value})}
                  required
                />
              </div>
              <Button
                type="submit"
                className="w-full bg-gradient-primary text-lg py-6"
                disabled={loading}
              >
                {loading ? 'Saving...' : 'Save Changes'}
              </Button>
            </form>
          </DialogContent>
        </Dialog>

        {/* Registrations Table */}
        <div className="flex flex-row items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">Confirmed Registrations</h2>
          <Button 
            className="bg-gradient-primary whitespace-nowrap"
            onClick={() => setShowAddDialog(true)}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Registration
          </Button>
        </div>
        <Card className="card-modern mb-8">
          <CardContent className="pt-6">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-3 font-semibold">BIB Number</th>
                    <th className="text-left p-3 font-semibold">Name</th>
                    <th className="text-left p-3 font-semibold">Email</th>
                    <th className="text-left p-3 font-semibold">Phone</th>
                    <th className="text-left p-3 font-semibold">Event</th>
                    <th className="text-left p-3 font-semibold">Status</th>
                    <th className="text-left p-3 font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {registrations.map((reg, index) => (
                    <tr key={index} className="border-b hover:bg-teal-50">
                      <td className="p-3 font-bold text-teal-600">{reg.bib_number}</td>
                      <td className="p-3">{reg.user_name}</td>
                      <td className="p-3">{reg.user_email}</td>
                      <td className="p-3">{reg.user_phone}</td>
                      <td className="p-3">{getEventName(reg.event_id)}</td>
                      <td className="p-3">
                        <select
                          value={reg.status}
                          onChange={(e) => handleUpdateStatus(reg.id, e.target.value)}
                          className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm border-none"
                        >
                          <option value="confirmed">confirmed</option>
                          <option value="pending">pending</option>
                          <option value="cancelled">cancelled</option>
                        </select>
                      </td>
                      <td className="p-3">
                        <div className="min-w-[80px]">
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => handleDeleteRegistration(reg.id)}
                            className="bg-red-500 hover:bg-red-600"
                          >
                            <Trash2 className="w-4 h-4 mr-1" />
                            Delete
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {registrations.length === 0 && (
                <p className="text-center text-gray-500 py-8">No registrations yet</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Add Registration Dialog */}
        <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add New Registration</DialogTitle>
              <DialogDescription>Manually create a registration</DialogDescription>
            </DialogHeader>
            <form onSubmit={handleAddRegistration} className="space-y-4">
              <div>
                <Label htmlFor="event">Event</Label>
                <select
                  id="event"
                  className="w-full p-2 border rounded"
                  value={newRegistration.event_id}
                  onChange={(e) => setNewRegistration({...newRegistration, event_id: e.target.value})}
                  required
                >
                  <option value="">Select Event</option>
                  {events.map(event => (
                    <option key={event.id} value={event.id}>{event.title}</option>
                  ))}
                </select>
              </div>
              <div>
                <Label htmlFor="add_name">Name</Label>
                <Input
                  id="add_name"
                  value={newRegistration.user_name}
                  onChange={(e) => setNewRegistration({...newRegistration, user_name: e.target.value})}
                  required
                />
              </div>
              <div>
                <Label htmlFor="add_email">Email</Label>
                <Input
                  id="add_email"
                  type="email"
                  value={newRegistration.user_email}
                  onChange={(e) => setNewRegistration({...newRegistration, user_email: e.target.value})}
                  required
                />
              </div>
              <div>
                <Label htmlFor="add_phone">Phone</Label>
                <Input
                  id="add_phone"
                  value={newRegistration.user_phone}
                  onChange={(e) => setNewRegistration({...newRegistration, user_phone: e.target.value})}
                  required
                />
              </div>
              <Button type="submit" className="w-full bg-gradient-primary" disabled={loading}>
                {loading ? 'Adding...' : 'Add Registration'}
              </Button>
            </form>
          </DialogContent>
        </Dialog>

        {/* Transactions Table */}
        <Card className="card-modern">
          <CardHeader>
            <CardTitle className="text-2xl">Payment Transactions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-3 font-semibold">BIB Number</th>
                    <th className="text-left p-3 font-semibold">Name</th>
                    <th className="text-left p-3 font-semibold">Email</th>
                    <th className="text-left p-3 font-semibold">Amount</th>
                    <th className="text-left p-3 font-semibold">Event</th>
                    <th className="text-left p-3 font-semibold">Payment Status</th>
                    <th className="text-left p-3 font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((trans, index) => (
                    <tr key={index} className="border-b hover:bg-orange-50">
                      <td className="p-3 font-bold text-orange-600">{trans.bib_number}</td>
                      <td className="p-3">{trans.user_name}</td>
                      <td className="p-3">{trans.user_email}</td>
                      <td className="p-3">₹{trans.amount}</td>
                      <td className="p-3">{getEventName(trans.event_id)}</td>
                      <td className="p-3">
                        <span className={`px-3 py-1 rounded-full text-sm ${
                          trans.payment_status === 'paid' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {trans.payment_status}
                        </span>
                      </td>
                      <td className="p-3">
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleDeleteTransaction(trans.id)}
                          className="bg-red-500 hover:bg-red-600"
                        >
                          <Trash2 className="w-4 h-4 mr-1" />
                          Delete
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {transactions.length === 0 && (
                <p className="text-center text-gray-500 py-8">No transactions yet</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default App;