import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, Activity, Calendar, User, Clock, AlertCircle } from 'lucide-react';
import ChatInterface from '../components/ChatInterface';
import ActionCard from '../components/ActionCard';
import { Card } from '../components/ui/card';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = () => {
  const [showChat, setShowChat] = useState(false);
  const [tasks, setTasks] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [tasksRes, appointmentsRes] = await Promise.all([
        axios.get(`${API}/tasks`),
        axios.get(`${API}/dashboard/appointments`)
      ]);
      setTasks(tasksRes.data);
      setAppointments(appointmentsRes.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickAction = (query) => {
    setShowChat(true);
  };

  if (showChat) {
    return <ChatInterface onBack={() => setShowChat(false)} />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900">BacklineMD</h1>
            </div>
            <div className="flex items-center gap-4">
              <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                <Search className="w-5 h-5 text-gray-600" />
              </button>
              <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                <User className="w-5 h-5 text-gray-600" />
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Greeting */}
        <div className="mb-8">
          <h2 className="text-4xl font-bold text-gray-900 mb-2">
            Good morning, Dr. O'Brien 👋
          </h2>
          <p className="text-lg text-gray-600">Here's what needs your attention today</p>
        </div>

        {/* Search/Chat Trigger */}
        <Card 
          className="p-6 mb-8 cursor-pointer hover:shadow-lg transition-shadow border-2 border-gray-200 hover:border-blue-300"
          onClick={() => setShowChat(true)}
          data-testid="chat-trigger"
        >
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-blue-50 rounded-full flex items-center justify-center">
              <Search className="w-6 h-6 text-blue-600" />
            </div>
            <div className="flex-1">
              <p className="text-gray-400 text-lg">Ask anything about your patients...</p>
            </div>
            <kbd className="px-3 py-1 bg-gray-100 text-gray-600 rounded-lg text-sm font-medium">⌘K</kbd>
          </div>
        </Card>

        {/* Quick Actions */}
        <div className="mb-8">
          <p className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">Quick Actions</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => handleQuickAction('What needs review today?')}
              className="p-4 bg-white border-2 border-gray-200 rounded-xl hover:border-blue-400 hover:shadow-md transition-all text-left group"
              data-testid="quick-action-review"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-orange-50 rounded-full flex items-center justify-center group-hover:bg-orange-100 transition-colors">
                  <AlertCircle className="w-5 h-5 text-orange-600" />
                </div>
                <span className="font-medium text-gray-900">What needs review today?</span>
              </div>
            </button>
            
            <button
              onClick={() => handleQuickAction('Any flagged documents?')}
              className="p-4 bg-white border-2 border-gray-200 rounded-xl hover:border-blue-400 hover:shadow-md transition-all text-left group"
              data-testid="quick-action-flagged"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-red-50 rounded-full flex items-center justify-center group-hover:bg-red-100 transition-colors">
                  <Activity className="w-5 h-5 text-red-600" />
                </div>
                <span className="font-medium text-gray-900">Any flagged documents?</span>
              </div>
            </button>
            
            <button
              onClick={() => handleQuickAction('Show pending insurance verifications')}
              className="p-4 bg-white border-2 border-gray-200 rounded-xl hover:border-blue-400 hover:shadow-md transition-all text-left group"
              data-testid="quick-action-insurance"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-50 rounded-full flex items-center justify-center group-hover:bg-blue-100 transition-colors">
                  <Clock className="w-5 h-5 text-blue-600" />
                </div>
                <span className="font-medium text-gray-900">Pending insurance verifications</span>
              </div>
            </button>
          </div>
        </div>

        {/* Actions Section */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-orange-600" />
              <h3 className="text-xl font-bold text-gray-900">Actions</h3>
              <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded-full text-sm font-medium">
                {tasks.length} pending
              </span>
            </div>
            <button className="text-blue-600 hover:text-blue-700 font-medium text-sm">
              View all {tasks.length}
            </button>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : tasks.length === 0 ? (
            <Card className="p-12 text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Activity className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">All caught up!</h3>
              <p className="text-gray-600">No pending actions at the moment</p>
            </Card>
          ) : (
            <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide">
              {tasks.map((task) => (
                <ActionCard 
                  key={task.task_id} 
                  task={task}
                  onClick={() => setShowChat(true)}
                />
              ))}
            </div>
          )}
        </div>

        {/* Today's Schedule */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Calendar className="w-5 h-5 text-purple-600" />
            <h3 className="text-xl font-bold text-gray-900">Today's Schedule</h3>
          </div>

          {appointments.length === 0 ? (
            <Card className="p-8 text-center">
              <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-600">No appointments scheduled for today</p>
            </Card>
          ) : (
            <Card className="p-6">
              <div className="space-y-4">
                {appointments.map((apt, index) => (
                  <div key={index} className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                    <div className="text-center min-w-[80px]">
                      <p className="text-lg font-bold text-blue-600">{apt.time}</p>
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold text-gray-900">{apt.type}</p>
                      <p className="text-sm text-gray-600">{apt.patient_name} • with {apt.doctor}</p>
                    </div>
                    <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium">
                      View
                    </button>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      </main>

      <style jsx>{`
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
        .scrollbar-hide {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>
    </div>
  );
};

export default Dashboard;