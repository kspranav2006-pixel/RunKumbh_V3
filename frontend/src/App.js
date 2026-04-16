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
import { Calendar, MapPin, Droplets, Sun, ArrowRight, Phone, Menu, X, Clock, Trophy } from "lucide-react";

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
        <h1 className="text-5xl sm:text-6xl lg:text-8xl font-bold text-white mb-4 animate-fadeIn drop-shadow-2xl">
          RUN KUMBH
        </h1>
        
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
          <br />Department of Physical Education & Sports
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
                  <span className="mr-3 text-2xl">🏆</span>
                  <span>*CASH PRIZE ONLY FOR 5K CATEGORIES*</span>
                </li>
                <li className="flex items-start text-gray-700">
                  <span className="mr-3 text-2xl">💰</span>
                  <span>Total Cash Prize Of ₹30,000</span>
                </li>
                <li className="flex items-start text-gray-700">
                  <span className="mr-3 text-2xl">🚑</span>
                  <span>Medical support throughout</span>
                </li>
              </ul>
              <p className="text-sm text-coral-600 mt-6 font-semibold bg-yellow-50 p-3 rounded-lg border-l-4 border-coral-500">
                *Cash prize applicable for 5K categories with minimum 50 participants per gender
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

        <Card className="card-modern max-w-5xl mx-auto">
          <CardHeader>
            <CardTitle className="text-2xl text-center">Race Route - Coming Soon</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-gradient-light rounded-lg p-12 text-center min-h-[400px] flex items-center justify-center">
              <div>
                <MapPin className="w-24 h-24 text-teal-600 mx-auto mb-4 animate-float" />
                <p className="text-lg text-gray-700 font-semibold">
                  Route map will be updated soon
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
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
                <CardTitle className="text-xl">Lt. Raghu G M</CardTitle>
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
                <CardTitle className="text-xl">Pranav</CardTitle>
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
                <CardTitle className="text-xl">Prajeet</CardTitle>
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
            <p className="text-gray-600 mt-2">Department of Physical Education & Sports</p>
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
              Department of Physical Education & Sports
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

export default App;
