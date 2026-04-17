import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Trash2, Edit2, Plus, X } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

function AdminPage({ toast }) {
  const [authenticated, setAuthenticated] = useState(false);
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  
  const [events, setEvents] = useState([]);
  const [registrations, setRegistrations] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [totalRegistrations, setTotalRegistrations] = useState(0);
  const [totalRevenue, setTotalRevenue] = useState(0);

  // Dialog states
  const [showAddEventDialog, setShowAddEventDialog] = useState(false);
  const [showEditEventDialog, setShowEditEventDialog] = useState(false);
  const [showAddRegDialog, setShowAddRegDialog] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState(null);

  // Form data
  const [eventForm, setEventForm] = useState({
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

  const [regForm, setRegForm] = useState({
    event_id: '',
    user_name: '',
    user_email: '',
    user_phone: '',
    gender: 'male',
    blood_group: 'A+',
    emergency_contact: ''
  });

  useEffect(() => {
    if (authenticated) {
      fetchData();
    }
  }, [authenticated]);

  const fetchData = async () => {
    try {
      const res = await axios.get(`${API}/admin/registrations`);
      setEvents(res.data.events || []);
      setRegistrations(res.data.registrations || []);
      setTransactions(res.data.transactions || []);
      setTotalRegistrations(res.data.total_registrations || 0);
      setTotalRevenue(res.data.total_revenue || 0);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await axios.post(`${API}/admin/login`, { password });
      if (res.data.token) {
        setAuthenticated(true);
        toast({ title: 'Login Successful', description: 'Welcome to Admin Dashboard' });
      }
    } catch (error) {
      toast({ title: 'Login Failed', description: 'Invalid password', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    setAuthenticated(false);
    setPassword('');
  };

  // Event Management
  const handleAddEvent = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/admin/events`, {
        ...eventForm,
        registration_fee: parseFloat(eventForm.registration_fee),
        max_participants: parseInt(eventForm.max_participants)
      });
      toast({ title: 'Success', description: 'Event added successfully' });
      setShowAddEventDialog(false);
      setEventForm({ title: '', description: '', date: '2026-05-30', location: 'RV Institute of Technology and Management, Bengaluru', distance: '', category: '', max_participants: '', image_url: '', registration_fee: '' });
      fetchData();
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to add event', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const handleEditEvent = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.put(`${API}/admin/events/${selectedEvent.id}`, {
        ...eventForm,
        registration_fee: parseFloat(eventForm.registration_fee),
        max_participants: parseInt(eventForm.max_participants)
      });
      toast({ title: 'Success', description: 'Event updated successfully' });
      setShowEditEventDialog(false);
      setSelectedEvent(null);
      fetchData();
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to update event', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteEvent = async (eventId) => {
    if (!window.confirm('Delete this event? This cannot be undone.')) return;
    try {
      await axios.delete(`${API}/api/admin/events/${eventId}`);
      toast({ title: 'Success', description: 'Event deleted' });
      fetchData();
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to delete event', variant: 'destructive' });
    }
  };

  // Registration Management
  const handleAddRegistration = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/admin/registrations`, regForm);
      toast({ title: 'Success', description: 'Registration added successfully' });
      setShowAddRegDialog(false);
      setRegForm({ event_id: '', user_name: '', user_email: '', user_phone: '', gender: 'male', blood_group: 'A+', emergency_contact: '' });
      fetchData();
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to add registration', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteRegistration = async (regId) => {
    if (!window.confirm('Delete this registration?')) return;
    try {
      await axios.delete(`${API}/admin/registrations/${regId}`);
      toast({ title: 'Success', description: 'Registration deleted' });
      fetchData();
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to delete registration', variant: 'destructive' });
    }
  };

  const handleUpdateStatus = async (regId, newStatus) => {
    try {
      await axios.put(`${API}/admin/registrations/${regId}`, { status: newStatus });
      toast({ title: 'Success', description: 'Status updated' });
      fetchData();
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to update status', variant: 'destructive' });
    }
  };

  // Transaction Management
  const handleDeleteTransaction = async (transId) => {
    if (!window.confirm('Delete this transaction?')) return;
    try {
      await axios.delete(`${API}/admin/transactions/${transId}`);
      toast({ title: 'Success', description: 'Transaction deleted' });
      fetchData();
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to delete transaction', variant: 'destructive' });
    }
  };

  const getEventName = (eventId) => {
    const event = events.find(e => e.id === eventId);
    return event ? event.title : 'Unknown';
  };

  // Login Screen
  if (!authenticated) {
    return (
      <div className="min-h-screen bg-gradient-light flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md">
          <h1 className="text-3xl font-bold text-gradient mb-6 text-center">Admin Login</h1>
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                placeholder="Enter admin password"
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-primary text-white py-3 rounded-lg font-semibold hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  // Admin Dashboard
  return (
    <div className="min-h-screen bg-gradient-light p-4">
      <div className="max-w-[1800px] mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-gradient">Admin Dashboard</h1>
            <p className="text-gray-600 mt-2">RunKumbh Registrations Management</p>
          </div>
          <button
            onClick={handleLogout}
            className="px-6 py-2 bg-white border-2 border-teal-600 text-teal-600 rounded-lg font-medium hover:bg-teal-50 transition-colors"
          >
            Logout
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Total Registrations</h3>
            <p className="text-4xl font-bold text-gradient">{totalRegistrations}</p>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Total Revenue</h3>
            <p className="text-4xl font-bold text-gradient">₹{totalRevenue}</p>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Total Events</h3>
            <p className="text-4xl font-bold text-gradient">{events.length}</p>
          </div>
        </div>

        {/* Manage Events */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-800">Manage Events</h2>
            <button
              onClick={() => setShowAddEventDialog(true)}
              className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg flex items-center gap-2 font-medium transition-colors"
            >
              <Plus className="w-5 h-5" />
              Add Event
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-gray-100 border-b-2 border-gray-200">
                  <th className="text-left p-4 font-semibold text-gray-700">Title</th>
                  <th className="text-left p-4 font-semibold text-gray-700">Category</th>
                  <th className="text-left p-4 font-semibold text-gray-700">Distance</th>
                  <th className="text-left p-4 font-semibold text-gray-700">Price</th>
                  <th className="text-left p-4 font-semibold text-gray-700 min-w-[220px]">Actions</th>
                </tr>
              </thead>
              <tbody>
                {events.map((event) => (
                  <tr key={event.id} className="border-b border-gray-200 hover:bg-teal-50 transition-colors">
                    <td className="p-4 font-medium text-gray-800">{event.title}</td>
                    <td className="p-4 text-gray-600">{event.category}</td>
                    <td className="p-4 text-gray-600">{event.distance}</td>
                    <td className="p-4 font-bold text-teal-600">₹{event.registration_fee}</td>
                    <td className="p-4">
                      <div className="flex gap-2">
                        <button
                          onClick={() => {
                            setSelectedEvent(event);
                            setEventForm({
                              title: event.title,
                              description: event.description,
                              date: event.date,
                              location: event.location,
                              distance: event.distance,
                              category: event.category,
                              max_participants: event.max_participants,
                              image_url: event.image_url,
                              registration_fee: event.registration_fee
                            });
                            setShowEditEventDialog(true);
                          }}
                          className="px-3 py-1.5 bg-teal-600 hover:bg-teal-700 text-white rounded text-sm font-medium flex items-center gap-1 transition-colors"
                        >
                          <Edit2 className="w-4 h-4" />
                          Edit
                        </button>
                        <button
                          onClick={() => handleDeleteEvent(event.id)}
                          className="px-3 py-1.5 bg-red-500 hover:bg-red-600 text-white rounded text-sm font-medium flex items-center gap-1 transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Manage Registrations */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-800">Confirmed Registrations</h2>
            <button
              onClick={() => setShowAddRegDialog(true)}
              className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg flex items-center gap-2 font-medium transition-colors"
            >
              <Plus className="w-5 h-5" />
              Add Registration
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-gray-100 border-b-2 border-gray-200">
                  <th className="text-left p-4 font-semibold text-gray-700">BIB</th>
                  <th className="text-left p-4 font-semibold text-gray-700">Name</th>
                  <th className="text-left p-4 font-semibold text-gray-700">Email</th>
                  <th className="text-left p-4 font-semibold text-gray-700">Phone</th>
                  <th className="text-left p-4 font-semibold text-gray-700">Event</th>
                  <th className="text-left p-4 font-semibold text-gray-700">Status</th>
                  <th className="text-left p-4 font-semibold text-gray-700 min-w-[120px]">Actions</th>
                </tr>
              </thead>
              <tbody>
                {registrations.map((reg) => (
                  <tr key={reg.id} className="border-b border-gray-200 hover:bg-teal-50 transition-colors">
                    <td className="p-4 font-bold text-teal-600">{reg.bib_number}</td>
                    <td className="p-4 text-gray-800">{reg.user_name}</td>
                    <td className="p-4 text-gray-600">{reg.user_email}</td>
                    <td className="p-4 text-gray-600">{reg.user_phone}</td>
                    <td className="p-4 text-gray-600">{getEventName(reg.event_id)}</td>
                    <td className="p-4">
                      <select
                        value={reg.status}
                        onChange={(e) => handleUpdateStatus(reg.id, e.target.value)}
                        className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm border border-green-200 focus:outline-none focus:ring-2 focus:ring-green-400"
                      >
                        <option value="confirmed">confirmed</option>
                        <option value="pending">pending</option>
                        <option value="cancelled">cancelled</option>
                      </select>
                    </td>
                    <td className="p-4">
                      <button
                        onClick={() => handleDeleteRegistration(reg.id)}
                        className="px-3 py-1.5 bg-red-500 hover:bg-red-600 text-white rounded text-sm font-medium flex items-center gap-1 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {registrations.length === 0 && (
              <p className="text-center text-gray-500 py-8">No registrations yet</p>
            )}
          </div>
        </div>

        {/* Payment Transactions */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">Payment Transactions</h2>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-gray-100 border-b-2 border-gray-200">
                  <th className="text-left p-4 font-semibold text-gray-700">BIB</th>
                  <th className="text-left p-4 font-semibold text-gray-700">Name</th>
                  <th className="text-left p-4 font-semibold text-gray-700">Email</th>
                  <th className="text-left p-4 font-semibold text-gray-700">Amount</th>
                  <th className="text-left p-4 font-semibold text-gray-700">Event</th>
                  <th className="text-left p-4 font-semibold text-gray-700">Status</th>
                  <th className="text-left p-4 font-semibold text-gray-700 min-w-[120px]">Actions</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((trans) => (
                  <tr key={trans.id} className="border-b border-gray-200 hover:bg-orange-50 transition-colors">
                    <td className="p-4 font-bold text-orange-600">{trans.bib_number}</td>
                    <td className="p-4 text-gray-800">{trans.user_name}</td>
                    <td className="p-4 text-gray-600">{trans.user_email}</td>
                    <td className="p-4 font-semibold text-gray-800">₹{trans.amount}</td>
                    <td className="p-4 text-gray-600">{getEventName(trans.event_id)}</td>
                    <td className="p-4">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                        trans.payment_status === 'paid' 
                          ? 'bg-green-100 text-green-800 border border-green-200' 
                          : 'bg-yellow-100 text-yellow-800 border border-yellow-200'
                      }`}>
                        {trans.payment_status}
                      </span>
                    </td>
                    <td className="p-4">
                      <button
                        onClick={() => handleDeleteTransaction(trans.id)}
                        className="px-3 py-1.5 bg-red-500 hover:bg-red-600 text-white rounded text-sm font-medium flex items-center gap-1 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {transactions.length === 0 && (
              <p className="text-center text-gray-500 py-8">No transactions yet</p>
            )}
          </div>
        </div>
      </div>

      {/* Add Event Modal */}
      {showAddEventDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold">Add New Event</h3>
              <button onClick={() => setShowAddEventDialog(false)} className="text-gray-500 hover:text-gray-700">
                <X className="w-6 h-6" />
              </button>
            </div>
            <form onSubmit={handleAddEvent} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Title</label>
                <input
                  type="text"
                  value={eventForm.title}
                  onChange={(e) => setEventForm({...eventForm, title: e.target.value})}
                  className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-teal-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea
                  value={eventForm.description}
                  onChange={(e) => setEventForm({...eventForm, description: e.target.value})}
                  className="w-full px-3 py-2 border rounded min-h-[80px] focus:ring-2 focus:ring-teal-500"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Distance</label>
                  <input
                    type="text"
                    value={eventForm.distance}
                    onChange={(e) => setEventForm({...eventForm, distance: e.target.value})}
                    className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-teal-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Category</label>
                  <input
                    type="text"
                    value={eventForm.category}
                    onChange={(e) => setEventForm({...eventForm, category: e.target.value})}
                    className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-teal-500"
                    required
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Price (₹)</label>
                  <input
                    type="number"
                    value={eventForm.registration_fee}
                    onChange={(e) => setEventForm({...eventForm, registration_fee: e.target.value})}
                    className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-teal-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Max Participants</label>
                  <input
                    type="number"
                    value={eventForm.max_participants}
                    onChange={(e) => setEventForm({...eventForm, max_participants: e.target.value})}
                    className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-teal-500"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Image URL</label>
                <input
                  type="text"
                  value={eventForm.image_url}
                  onChange={(e) => setEventForm({...eventForm, image_url: e.target.value})}
                  className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-teal-500"
                  required
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-teal-600 hover:bg-teal-700 text-white py-3 rounded-lg font-semibold transition-colors disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Event'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Edit Event Modal */}
      {showEditEventDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold">Edit Event</h3>
              <button onClick={() => setShowEditEventDialog(false)} className="text-gray-500 hover:text-gray-700">
                <X className="w-6 h-6" />
              </button>
            </div>
            <form onSubmit={handleEditEvent} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Title</label>
                <input
                  type="text"
                  value={eventForm.title}
                  onChange={(e) => setEventForm({...eventForm, title: e.target.value})}
                  className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-teal-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea
                  value={eventForm.description}
                  onChange={(e) => setEventForm({...eventForm, description: e.target.value})}
                  className="w-full px-3 py-2 border rounded min-h-[80px] focus:ring-2 focus:ring-teal-500"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Distance</label>
                  <input
                    type="text"
                    value={eventForm.distance}
                    onChange={(e) => setEventForm({...eventForm, distance: e.target.value})}
                    className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-teal-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Category</label>
                  <input
                    type="text"
                    value={eventForm.category}
                    onChange={(e) => setEventForm({...eventForm, category: e.target.value})}
                    className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-teal-500"
                    required
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Price (₹)</label>
                  <input
                    type="number"
                    value={eventForm.registration_fee}
                    onChange={(e) => setEventForm({...eventForm, registration_fee: e.target.value})}
                    className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-teal-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Max Participants</label>
                  <input
                    type="number"
                    value={eventForm.max_participants}
                    onChange={(e) => setEventForm({...eventForm, max_participants: e.target.value})}
                    className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-teal-500"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Image URL</label>
                <input
                  type="text"
                  value={eventForm.image_url}
                  onChange={(e) => setEventForm({...eventForm, image_url: e.target.value})}
                  className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-teal-500"
                  required
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-teal-600 hover:bg-teal-700 text-white py-3 rounded-lg font-semibold transition-colors disabled:opacity-50"
              >
                {loading ? 'Saving...' : 'Save Changes'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Add Registration Modal */}
      {showAddRegDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold">Add Registration</h3>
              <button onClick={() => setShowAddRegDialog(false)} className="text-gray-500 hover:text-gray-700">
                <X className="w-6 h-6" />
              </button>
            </div>
            <form onSubmit={handleAddRegistration} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Event</label>
                <select
                  value={regForm.event_id}
                  onChange={(e) => setRegForm({...regForm, event_id: e.target.value})}
                  className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-teal-500"
                  required
                >
                  <option value="">Select Event</option>
                  {events.map(event => (
                    <option key={event.id} value={event.id}>{event.title}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Name</label>
                <input
                  type="text"
                  value={regForm.user_name}
                  onChange={(e) => setRegForm({...regForm, user_name: e.target.value})}
                  className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-teal-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Email</label>
                <input
                  type="email"
                  value={regForm.user_email}
                  onChange={(e) => setRegForm({...regForm, user_email: e.target.value})}
                  className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-teal-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Phone</label>
                <input
                  type="tel"
                  value={regForm.user_phone}
                  onChange={(e) => setRegForm({...regForm, user_phone: e.target.value})}
                  className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-teal-500"
                  required
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-teal-600 hover:bg-teal-700 text-white py-3 rounded-lg font-semibold transition-colors disabled:opacity-50"
              >
                {loading ? 'Adding...' : 'Add Registration'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminPage;
