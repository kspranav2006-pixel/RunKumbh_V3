import { useState, useEffect } from 'react';
import '@/App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import axios from 'axios';
import { Toaster } from '@/components/ui/toaster';
import { useToast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Calendar, MapPin, Users, Trophy, Droplets, Sun, ArrowRight, Mail, Phone, MessageSquare, Menu, X } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [events, setEvents] = useState([]);
  const [gallery, setGallery] = useState([]);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    fetchEvents();
    fetchGallery();
    checkPaymentStatus();
  }, []);

  const checkPaymentStatus = async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');
    
    if (sessionId) {
      // Poll for payment status
      let attempts = 0;
      const maxAttempts = 5;
      
      const pollStatus = async () => {
        try {
          const response = await axios.get(`${API}/payments/checkout/status/${sessionId}`);
          
          if (response.data.payment_status === 'paid') {
            toast({
              title: 'Payment Successful! 🎉',
              description: 'Your registration is confirmed. Check your email for details.',
            });
            // Clear URL params
            window.history.replaceState({}, document.title, window.location.pathname);
            return;
          } else if (response.data.status === 'expired') {
            toast({
              title: 'Payment Expired',
              description: 'Please try registering again.',
              variant: 'destructive'
            });
            window.history.replaceState({}, document.title, window.location.pathname);
            return;
          }
          
          // Continue polling if pending
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

  const fetchGallery = async () => {
    try {
      const response = await axios.get(`${API}/gallery`);
      setGallery(response.data);
    } catch (error) {
      console.error('Error fetching gallery:', error);
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
      <div className="App min-h-screen bg-gradient-to-br from-teal-50 via-orange-50 to-sky-50">
        <Toaster />
        <Routes>
          <Route path="/" element={
            <HomePage 
              events={events} 
              gallery={gallery} 
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

function HomePage({ events, gallery, scrollToSection, isMenuOpen, setIsMenuOpen, toast }) {
  return (
    <>
      <Navigation scrollToSection={scrollToSection} isMenuOpen={isMenuOpen} setIsMenuOpen={setIsMenuOpen} />
      <HeroSection scrollToSection={scrollToSection} />
      <AboutSection />
      <EventsSection events={events} toast={toast} />
      <GallerySection gallery={gallery} />
      <ContactSection toast={toast} />
      <Footer scrollToSection={scrollToSection} />
    </>
  );
}

function Navigation({ scrollToSection, isMenuOpen, setIsMenuOpen }) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navItems = [
    { label: 'Home', id: 'home' },
    { label: 'About', id: 'about' },
    { label: 'Events', id: 'events' },
    { label: 'Gallery', id: 'gallery' },
    { label: 'Contact', id: 'contact' }
  ];

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
      scrolled ? 'bg-white/90 backdrop-blur-md shadow-lg' : 'bg-transparent'
    }`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-2" data-testid="logo">
            <div className="flex items-center space-x-2">
              <Droplets className="w-8 h-8 text-teal-600" />
              <Sun className="w-8 h-8 text-orange-500" />
            </div>
            <span className="text-2xl font-bold bg-gradient-to-r from-teal-600 to-orange-500 bg-clip-text text-transparent">
              RunKumbh
            </span>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => scrollToSection(item.id)}
                className="text-gray-700 hover:text-teal-600 font-medium transition-colors duration-200"
                data-testid={`nav-${item.id}`}
              >
                {item.label}
              </button>
            ))}
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden p-2"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            data-testid="mobile-menu-button"
          >
            {isMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <div className="md:hidden py-4 bg-white/95 backdrop-blur-md rounded-lg mt-2 shadow-lg" data-testid="mobile-menu">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => scrollToSection(item.id)}
                className="block w-full text-left px-4 py-3 text-gray-700 hover:bg-teal-50 hover:text-teal-600 font-medium transition-colors"
                data-testid={`mobile-nav-${item.id}`}
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
    <section id="home" className="relative min-h-screen flex items-center justify-center overflow-hidden" data-testid="hero-section">
      {/* Background Image with Overlay */}
      <div className="absolute inset-0">
        <img
          src="https://images.unsplash.com/photo-1452626038306-9aae5e071dd3"
          alt="Marathon runners"
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-br from-teal-900/85 via-orange-900/75 to-sky-900/85"></div>
      </div>

      {/* Animated 3D Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="droplet droplet-1"></div>
        <div className="droplet droplet-2"></div>
        <div className="droplet droplet-3"></div>
        <div className="droplet droplet-4"></div>
        <div className="sunray sunray-1"></div>
        <div className="sunray sunray-2"></div>
      </div>

      {/* Content */}
      <div className="relative z-10 text-center px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto">
        {/* Prize Badge */}
        <div className="prize-badge inline-block px-8 py-3 rounded-full text-white font-bold text-xl mb-6 animate-fade-in-up">
          🏆 Total Cash Prize: ₹30,000 🏆
        </div>
        
        <h1 className="text-4xl sm:text-5xl lg:text-7xl font-bold text-white mb-4 animate-fade-in-up animation-delay-200 neon-text">
          RUN KUMBHA
          <br />
          <span className="gradient-text-3d text-5xl sm:text-6xl lg:text-8xl">
            MONSOON RUN 2.0
          </span>
        </h1>
        
        <p className="text-xl sm:text-2xl lg:text-3xl text-yellow-300 font-semibold mb-3 animate-fade-in-up animation-delay-400">
          🌧️ 2026-27 Edition 🌧️
        </p>
        
        <p className="text-lg sm:text-xl text-gray-100 mb-6 animate-fade-in-up animation-delay-400">
          <span className="font-bold">RV Institute of Technology and Management</span>
          <br />Department of Physical Education & Sports
        </p>
        
        <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 mb-8 inline-block animate-fade-in-up animation-delay-600">
          <p className="text-white text-lg font-semibold mb-3">📅 Registration Open</p>
          <p className="text-teal-300 text-2xl font-bold">20th April - 15th May 2026</p>
          <p className="text-gray-200 mt-3">🎁 Medal | Certificate | T-Shirt | Refreshments</p>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center animate-fade-in-up animation-delay-600">
          <Button
            size="lg"
            onClick={() => scrollToSection('events')}
            className="shine-effect bg-gradient-to-r from-teal-500 to-teal-600 hover:from-teal-600 hover:to-teal-700 text-white text-xl px-10 py-7 shadow-2xl hover:shadow-3xl transform hover:scale-105 transition-all duration-200"
            data-testid="view-events-button"
          >
            View Categories <ArrowRight className="ml-2" />
          </Button>
          <Button
            size="lg"
            variant="outline"
            onClick={() => scrollToSection('contact')}
            className="glass-effect-3d text-white border-2 border-white/40 hover:bg-white/20 text-xl px-10 py-7 shadow-2xl"
            data-testid="get-in-touch-button"
          >
            Contact Us
          </Button>
        </div>
      </div>
    </section>
  );
}

function AboutSection() {
  const features = [
    {
      icon: <Droplets className="w-12 h-12 text-teal-500" />,
      title: 'Monsoon Magic',
      description: 'Run through refreshing rain showers and experience nature\'s cooling embrace. Feel the monsoon energy!'
    },
    {
      icon: <Sun className="w-12 h-12 text-orange-500" />,
      title: 'Summer Energy',
      description: 'Experience the warmth and vibrance of summer sunshine energizing your every step.'
    },
    {
      icon: <Trophy className="w-12 h-12 text-yellow-500" />,
      title: '₹30,000 Prize',
      description: 'Compete for the total cash prize pool of ₹30,000! Break records and win big!'
    },
    {
      icon: <Users className="w-12 h-12 text-blue-500" />,
      title: '5 Categories',
      description: 'Open, Students, Family, Couple & Campus runs. Something for everyone at RVITM!'
    }
  ];

  return (
    <section id="about" className="py-20 px-4 sm:px-6 lg:px-8 relative overflow-hidden" data-testid="about-section">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0" style={{backgroundImage: 'radial-gradient(circle, #0d9488 1px, transparent 1px)', backgroundSize: '50px 50px'}}></div>
      </div>
      
      <div className="max-w-7xl mx-auto relative z-10">
        <div className="text-center mb-16">
          <h2 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 mb-4 animate-slide-in-left">
            About <span className="gradient-text-3d">Run Kumbha 2.0</span>
          </h2>
          <p className="text-xl sm:text-2xl text-gray-700 max-w-4xl mx-auto font-semibold">
            RV Institute of Technology and Management
          </p>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto mt-2">
            India's premier monsoon running event celebrating fitness, community, and the spirit of competition
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <Card
              key={index}
              className="card-3d border-2 border-transparent hover:border-teal-300 bg-white/90 backdrop-blur-sm animate-slide-in-right"
              style={{animationDelay: `${index * 0.1}s`}}
              data-testid={`feature-card-${index}`}
            >
              <CardHeader>
                <div className="mb-4 floating-badge">{feature.icon}</div>
                <CardTitle className="text-xl font-bold">{feature.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">{feature.description}</p>
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
      // Get current origin for payment redirect
      const originUrl = window.location.origin;
      
      // Create payment checkout session
      const response = await axios.post(`${API}/payments/checkout/session`, {
        event_id: selectedEvent.id,
        origin_url: originUrl,
        ...registrationData
      });

      // Redirect to Stripe checkout
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
    <section id="events" className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-teal-50 via-orange-50 to-sky-50" data-testid="events-section">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 mb-4 animate-fade-in-up">
            Registration <span className="gradient-text-3d">Categories</span>
          </h2>
          <p className="text-xl sm:text-2xl text-gray-700 max-w-4xl mx-auto mb-3 font-semibold">
            Choose Your Challenge & Run for Glory!
          </p>
          <div className="inline-block bg-gradient-to-r from-teal-500 to-orange-500 text-white px-6 py-2 rounded-full text-lg font-bold pulse-glow-3d">
            Registration: 20 April - 15 May 2026
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {events.map((event) => (
            <Card
              key={event.id}
              className="card-3d overflow-hidden bg-white shine-effect"
              data-testid={`event-card-${event.id}`}
            >
              <div className="relative h-48 overflow-hidden">
                <img
                  src={event.image_url}
                  alt={event.title}
                  className="w-full h-full object-cover transform hover:scale-110 transition-transform duration-500"
                />
                <div className="absolute top-4 right-4 bg-orange-500 text-white px-3 py-1 rounded-full text-sm font-semibold">
                  {event.category}
                </div>
              </div>
              <CardHeader>
                <CardTitle className="text-2xl text-gray-900">{event.title}</CardTitle>
                <CardDescription className="text-gray-600">{event.description}</CardDescription>
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
                <div className="flex items-center text-gray-700">
                  <Users className="w-5 h-5 mr-2 text-blue-600" />
                  <span>{event.current_participants}/{event.max_participants} Registered</span>
                </div>
                <div className="flex justify-between items-center pt-4 border-t">
                  <span className="text-2xl font-bold text-teal-600">₹{event.registration_fee}</span>
                  <span className="text-lg font-semibold text-gray-700">{event.distance}</span>
                </div>
              </CardContent>
              <CardFooter>
                <Dialog open={selectedEvent?.id === event.id} onOpenChange={(open) => !open && setSelectedEvent(null)}>
                  <DialogTrigger asChild>
                    <Button
                      className="w-full bg-gradient-to-r from-teal-500 to-orange-500 hover:from-teal-600 hover:to-orange-600 text-white font-semibold"
                      onClick={() => setSelectedEvent(event)}
                      data-testid={`register-button-${event.id}`}
                    >
                      Register Now
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="sm:max-w-md" data-testid="registration-dialog">
                    <DialogHeader>
                      <DialogTitle>Register for {event.title}</DialogTitle>
                      <DialogDescription>
                        Fill in your details to secure your spot
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
                          data-testid="registration-name-input"
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
                          data-testid="registration-email-input"
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
                          data-testid="registration-phone-input"
                        />
                      </div>
                      <Button
                        type="submit"
                        className="w-full bg-gradient-to-r from-teal-500 to-orange-500 hover:from-teal-600 hover:to-orange-600"
                        disabled={isRegistering}
                        data-testid="submit-registration-button"
                      >
                        {isRegistering ? 'Processing...' : `Pay ₹${event.registration_fee} & Register`}
                      </Button>
                      <p className="text-xs text-center text-gray-500 mt-2">
                        Secure payment powered by Stripe
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

function GallerySection({ gallery }) {
  return (
    <section id="gallery" className="py-20 px-4 sm:px-6 lg:px-8" data-testid="gallery-section">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4">
            Event <span className="bg-gradient-to-r from-teal-600 to-orange-500 bg-clip-text text-transparent">Gallery</span>
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Moments of triumph, community, and pure running joy
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {gallery.map((item, index) => (
            <div
              key={item.id}
              className="relative overflow-hidden rounded-lg shadow-lg hover:shadow-2xl transition-all duration-300 transform hover:scale-105 group"
              data-testid={`gallery-item-${index}`}
            >
              <img
                src={item.image_url}
                alt={item.title}
                className="w-full h-64 object-cover group-hover:scale-110 transition-transform duration-500"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end">
                <p className="text-white font-semibold p-4">{item.title}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function ContactSection({ toast }) {
  const [contactData, setContactData] = useState({
    name: '',
    email: '',
    subject: '',
    message: ''
  });
  const [isSending, setIsSending] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSending(true);

    try {
      await axios.post(`${API}/contact`, contactData);
      toast({
        title: 'Message Sent! ✉️',
        description: 'We\'ll get back to you soon.',
      });
      setContactData({ name: '', email: '', subject: '', message: '' });
    } catch (error) {
      toast({
        title: 'Failed to Send',
        description: 'Please try again later',
        variant: 'destructive'
      });
    } finally {
      setIsSending(false);
    }
  };

  return (
    <section id="contact" className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-orange-50 to-teal-50" data-testid="contact-section">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4">
            Get in <span className="bg-gradient-to-r from-teal-600 to-orange-500 bg-clip-text text-transparent">Touch</span>
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Have questions? We'd love to hear from you!
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          <div className="space-y-8">
            <Card className="card-3d bg-white/90 backdrop-blur-sm border-2 hover:border-teal-300">
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <Phone className="w-7 h-7 text-teal-600" />
                  <CardTitle className="text-xl">Contact Numbers</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                <p className="text-gray-700 font-medium">Lt. Raghu G M</p>
                <p className="text-teal-600 font-semibold text-lg">📞 +91 9743743618</p>
                <p className="text-gray-700 font-medium mt-3">Pranav</p>
                <p className="text-orange-600 font-semibold text-lg">📞 +91 8073290482</p>
                <p className="text-gray-700 font-medium mt-3">Prajeet Gurlahosur</p>
                <p className="text-blue-600 font-semibold text-lg">📞 +91 9845610718</p>
              </CardContent>
            </Card>

            <Card className="card-3d bg-white/90 backdrop-blur-sm border-2 hover:border-orange-300">
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <MapPin className="w-7 h-7 text-orange-600" />
                  <CardTitle className="text-xl">Location</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-gray-700 font-semibold">RV Institute of Technology and Management</p>
                <p className="text-gray-600 mt-2">Department of Physical Education & Sports</p>
                <p className="text-gray-600">Bengaluru, Karnataka</p>
              </CardContent>
            </Card>

            <Card className="card-3d bg-white/90 backdrop-blur-sm border-2 hover:border-blue-300">
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <MessageSquare className="w-7 h-7 text-blue-600" />
                  <CardTitle className="text-xl">Event Details</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-gray-700">🏃 5 Categories Available</p>
                <p className="text-gray-700">🏆 ₹30,000 Total Prize</p>
                <p className="text-gray-700">🎁 Medals & Certificates</p>
                <p className="text-gray-700">👕 Event T-Shirt Included</p>
              </CardContent>
            </Card>
          </div>

          <Card className="bg-white shadow-xl">
            <CardHeader>
              <CardTitle className="text-2xl">Send us a Message</CardTitle>
              <CardDescription>Fill out the form below and we'll respond within 24 hours</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    required
                    value={contactData.name}
                    onChange={(e) => setContactData({ ...contactData, name: e.target.value })}
                    data-testid="contact-name-input"
                  />
                </div>
                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    required
                    value={contactData.email}
                    onChange={(e) => setContactData({ ...contactData, email: e.target.value })}
                    data-testid="contact-email-input"
                  />
                </div>
                <div>
                  <Label htmlFor="subject">Subject</Label>
                  <Input
                    id="subject"
                    required
                    value={contactData.subject}
                    onChange={(e) => setContactData({ ...contactData, subject: e.target.value })}
                    data-testid="contact-subject-input"
                  />
                </div>
                <div>
                  <Label htmlFor="message">Message</Label>
                  <Textarea
                    id="message"
                    required
                    rows={5}
                    value={contactData.message}
                    onChange={(e) => setContactData({ ...contactData, message: e.target.value })}
                    data-testid="contact-message-input"
                  />
                </div>
                <Button
                  type="submit"
                  className="w-full bg-gradient-to-r from-teal-500 to-orange-500 hover:from-teal-600 hover:to-orange-600 text-white font-semibold text-lg py-6"
                  disabled={isSending}
                  data-testid="send-message-button"
                >
                  {isSending ? 'Sending...' : 'Send Message'}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
}

function Footer({ scrollToSection }) {
  return (
    <footer className="bg-gradient-to-r from-teal-900 via-blue-900 to-orange-900 text-white py-12 px-4 sm:px-6 lg:px-8" data-testid="footer">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <Droplets className="w-8 h-8" />
              <Sun className="w-8 h-8" />
              <span className="text-2xl font-bold">Run Kumbha 2.0</span>
            </div>
            <p className="text-gray-300 font-semibold">
              RV Institute of Technology and Management
            </p>
            <p className="text-gray-400 text-sm mt-2">
              Department of Physical Education & Sports
            </p>
            <p className="text-yellow-400 font-bold mt-3">
              🏆 ₹30,000 Cash Prize
            </p>
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-4">Quick Links</h3>
            <ul className="space-y-2">
              <li>
                <button onClick={() => scrollToSection('about')} className="text-gray-300 hover:text-white transition-colors">
                  About Event
                </button>
              </li>
              <li>
                <button onClick={() => scrollToSection('events')} className="text-gray-300 hover:text-white transition-colors">
                  Categories
                </button>
              </li>
              <li>
                <button onClick={() => scrollToSection('gallery')} className="text-gray-300 hover:text-white transition-colors">
                  Gallery
                </button>
              </li>
              <li>
                <button onClick={() => scrollToSection('contact')} className="text-gray-300 hover:text-white transition-colors">
                  Contact
                </button>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-4">Contact Information</h3>
            <p className="text-gray-300 mb-2">Lt. Raghu G M: +91 9743743618</p>
            <p className="text-gray-300 mb-2">Pranav: +91 8073290482</p>
            <p className="text-gray-300 mb-4">Prajeet: +91 9845610718</p>
            <p className="text-sm text-gray-400">Registration: 20 April - 15 May 2026</p>
          </div>
        </div>

        <div className="border-t border-white/20 mt-8 pt-8 text-center text-gray-300">
          <p className="font-semibold">© 2026-27 Run Kumbha - Monsoon Run 2.0</p>
          <p className="text-sm mt-2">RV Institute of Technology and Management | Where Monsoon Meets Energy 🌧️⚡</p>
        </div>
      </div>
    </footer>
  );
}

export default App;