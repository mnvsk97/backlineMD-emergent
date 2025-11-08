import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, Activity, Calendar, User, Clock, AlertCircle, Menu } from 'lucide-react';
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
    <div className="flex h-screen bg-white">
      {/* Dark Sidebar */}
      <div className="w-20 bg-gray-950 flex flex-col items-center py-8 space-y-8">
        <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
          <Activity className="w-6 h-6 text-gray-950" />
        </div>
        
        <div className="flex-1 flex flex-col items-center space-y-6 text-gray-400">
          <button className="p-3 hover:text-white transition-colors">
            <Search className="w-6 h-6" />
          </button>
          <button className="p-3 hover:text-white transition-colors">
            <Calendar className="w-6 h-6" />
          </button>
          <button className="p-3 hover:text-white transition-colors">
            <Activity className="w-6 h-6" />
          </button>
          <button className="p-3 hover:text-white transition-colors">
            <User className="w-6 h-6" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        {/* Header */}
        <header className="border-b border-gray-200 bg-white sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-8 py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Good morning, Dr. O'Brien</h1>
                <p className="text-sm text-gray-500 mt-1">Here's what needs your attention today</p>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 rounded-lg text-sm">
                  <span className="text-gray-500">Search</span>
                  <kbd className="px-2 py-0.5 bg-white text-gray-600 rounded text-xs font-medium border border-gray-300">⌘K</kbd>
                </div>
                <div className="w-9 h-9 bg-gray-200 rounded-full flex items-center justify-center">
                  <User className="w-5 h-5 text-gray-600" />
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="max-w-7xl mx-auto px-8 py-8">
          {/* Search/Chat Trigger */}
          <Card 
            className="p-5 mb-8 cursor-pointer hover:shadow-sm transition-all border border-gray-200 bg-gray-50"
            onClick={() => setShowChat(true)}
            data-testid="chat-trigger"
          >
            <div className="flex items-center gap-4">
              <Search className="w-5 h-5 text-gray-400" />
              <p className="text-gray-400 flex-1">Ask a question...</p>
              <span className="text-xs text-gray-400">Claude 3.7 Sonnet</span>
            </div>
          </Card>

          {/* Quick Actions */}
          <div className="mb-8">
            <div className="flex gap-3 mb-6">
              <button
                onClick={() => handleQuickAction('What needs review today?')}
                className="px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium text-gray-700"
                data-testid="quick-action-review"
              >
                What needs review today?
              </button>
              
              <button
                onClick={() => handleQuickAction('Any flagged documents?')}
                className="px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium text-gray-700"
                data-testid="quick-action-flagged"
              >
                Any flagged documents?
              </button>
              
              <button
                onClick={() => handleQuickAction('Pending insurance verifications')}
                className="px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium text-gray-700"
                data-testid="quick-action-insurance"
              >
                Pending insurance verifications
              </button>
            </div>
          </div>

          {/* Actions Section */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-gray-900" />
                <h3 className="text-lg font-semibold text-gray-900">Actions</h3>
              </div>
              <button className="text-sm text-gray-500 hover:text-gray-900 transition-colors">
                View all {tasks.length}
              </button>
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="w-6 h-6 border-2 border-gray-900 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : tasks.length === 0 ? (
              <Card className="p-12 text-center border border-gray-200">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Activity className="w-8 h-8 text-gray-400" />
                </div>
                <h3 className="text-base font-medium text-gray-900 mb-2">All caught up!</h3>
                <p className="text-sm text-gray-500">No pending actions at the moment</p>
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
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">June 1st, 2025</h3>
              <div className="flex items-center gap-2">
                <button className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 transition-colors">
                  Yesterday
                </button>
                <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                  <Calendar className="w-4 h-4 text-gray-600" />
                </button>
              </div>
            </div>

            {appointments.length === 0 ? (
              <Card className="p-8 text-center border border-gray-200">
                <Calendar className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                <p className="text-sm text-gray-500">No appointments scheduled for today</p>
              </Card>
            ) : (
              <div className="space-y-3">
                {appointments.map((apt, index) => (
                  <Card key={index} className="p-4 border border-gray-200 hover:border-gray-300 transition-colors">
                    <div className="flex items-center gap-4">
                      <div className="text-sm font-semibold text-gray-900 w-16">
                        {apt.time}
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-gray-900 text-sm">{apt.type}</p>
                        <p className="text-xs text-gray-500 mt-0.5">{apt.patient_name} • {apt.doctor}</p>
                      </div>
                      <button className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors text-xs font-medium text-gray-700">
                        Meeting prep
                      </button>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </main>
      </div>

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