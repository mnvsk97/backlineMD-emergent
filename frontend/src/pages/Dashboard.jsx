import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Clock, MessageSquare, FileCheck, Calendar, Activity, User, Users, BarChart3 } from 'lucide-react';
import { Card } from '../components/ui/card';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [patients, setPatients] = useState([]);
  const [agents, setAgents] = useState([]);
  const [activityFeed, setActivityFeed] = useState([]);

  useEffect(() => {
    fetchDashboardData();
    // Set up SSE for agent updates
    const eventSource = new EventSource(`${API}/agents/stream`);
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setAgents(data.agents || []);
    };
    return () => eventSource.close();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, appointmentsRes, patientsRes, agentsRes] = await Promise.all([
        axios.get(`${API}/dashboard/stats`),
        axios.get(`${API}/dashboard/appointments`),
        axios.get(`${API}/patients`),
        axios.get(`${API}/agents/active`)
      ]);

      setStats(statsRes.data);
      setAppointments(appointmentsRes.data);
      setPatients(patientsRes.data.slice(0, 3));
      setAgents(agentsRes.data);

      // Mock activity feed
      setActivityFeed([
        {
          id: 1,
          message: 'Appointment rescheduled to 2023-10-15 14:00:00. Reason: Rescheduled via voice assistant',
          time: '2 minutes ago',
          icon: Calendar
        },
        {
          id: 2,
          message: 'Insurance verification completed for Emma Watson',
          time: '5 minutes ago',
          icon: FileCheck
        },
        {
          id: 3,
          message: 'Document extraction completed for Alex Rodriguez',
          time: '12 minutes ago',
          icon: Activity
        }
      ]);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  const getIconComponent = (iconName) => {
    const icons = {
      Clock,
      MessageSquare,
      FileCheck,
      Calendar
    };
    return icons[iconName] || Clock;
  };

  const getColorClasses = (color) => {
    const colors = {
      blue: 'bg-blue-50 text-blue-600',
      teal: 'bg-teal-50 text-teal-600',
      orange: 'bg-orange-50 text-orange-600',
      purple: 'bg-purple-50 text-purple-600'
    };
    return colors[color] || colors.blue;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50 backdrop-blur-sm bg-white/90">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">BacklineMD <span className="text-blue-600">CoPilot</span></h1>
                <p className="text-xs text-gray-500">AI-Powered Command Center</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate('/tasks')}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-lg shadow-blue-500/20"
              >
                <Users className="w-4 h-4 inline mr-2" />
                Patients
              </button>
              <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium">
                <BarChart3 className="w-4 h-4 inline mr-2" />
                Analytics
              </button>
              <div className="flex items-center gap-2 px-3 py-2 bg-green-50 text-green-700 rounded-lg">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span className="text-sm font-medium">Live</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-3">
            Medical Dashboard <span className="text-blue-600">Overview</span>
          </h2>
          <p className="text-gray-600 text-lg">AI-powered insights and real-time patient management analytics</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat, index) => {
            const IconComponent = getIconComponent(stat.icon);
            return (
              <Card key={index} className="p-6 bg-white border border-gray-200 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                <div className="flex items-center justify-between mb-4">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${getColorClasses(stat.color)}`}>
                    <IconComponent className="w-6 h-6" />
                  </div>
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center ${getColorClasses(stat.color)} opacity-20`}>
                    <IconComponent className="w-6 h-6" />
                  </div>
                </div>
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">{stat.title}</p>
                  <p className="text-3xl font-bold text-gray-900 mb-1">{stat.value}</p>
                  <p className="text-sm text-gray-600">{stat.subtitle}</p>
                </div>
              </Card>
            );
          })}
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Today's Appointments */}
          <Card className="p-6 bg-white border border-gray-200">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-purple-50 rounded-lg flex items-center justify-center">
                <Calendar className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900">Today's Appointments</h3>
                <p className="text-sm text-gray-500">Sunday, October 12 • {appointments.length} scheduled</p>
              </div>
            </div>
            <div className="space-y-3">
              {appointments.map((apt, index) => (
                <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                  <div className="flex items-center gap-4">
                    <div className="text-center">
                      <p className="text-lg font-bold text-blue-600">{apt.time}</p>
                      <p className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded-full font-medium">{apt.type}</p>
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900">{apt.patient_name}</p>
                      <p className="text-sm text-gray-600">with {apt.doctor}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* AI Activity Feed */}
          <Card className="p-6 bg-white border border-gray-200">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                <Activity className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900">AI Activity Feed</h3>
                <p className="text-sm text-gray-500">Real-time automated actions and insights</p>
              </div>
            </div>
            <div className="space-y-3">
              {activityFeed.map((activity) => {
                const IconComp = activity.icon;
                return (
                  <div key={activity.id} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                    <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center flex-shrink-0 shadow-sm">
                      <IconComp className="w-4 h-4 text-gray-600" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm text-gray-900">{activity.message}</p>
                      <p className="text-xs text-gray-500 mt-1">{activity.time}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>

        {/* Recent Patients */}
        <Card className="p-6 bg-white border border-gray-200">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
              <Users className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900">Recent Patients</h3>
              <p className="text-sm text-gray-500">Latest patient interactions and updates • {patients.length} total patients</p>
            </div>
          </div>
          <div className="space-y-4">
            {patients.map((patient) => (
              <div
                key={patient.patient_id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-all cursor-pointer group"
                onClick={() => navigate(`/patients/${patient.patient_id}`)}
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-100 to-blue-200 rounded-full flex items-center justify-center relative">
                    <User className="w-6 h-6 text-blue-600" />
                    <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white" />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">{patient.first_name} {patient.last_name}</p>
                    <p className="text-sm text-gray-600">{patient.email}</p>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="text-xs text-gray-500 flex items-center gap-1">
                        <FileCheck className="w-3 h-3" /> {patient.tasks_count} task(s)
                      </span>
                      <span className="text-xs text-gray-500 flex items-center gap-1">
                        <Calendar className="w-3 h-3" /> {patient.appointments_count} appointment(s)
                      </span>
                    </div>
                  </div>
                </div>
                <button className="px-4 py-2 bg-blue-600 text-white rounded-lg opacity-0 group-hover:opacity-100 transition-opacity font-medium">
                  View Details
                </button>
              </div>
            ))}
          </div>
        </Card>

        {/* Live Agent Activity */}
        {agents.length > 0 && (
          <Card className="p-6 bg-white border border-gray-200 mt-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center">
                <Activity className="w-5 h-5 text-green-600 animate-pulse" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900">Live Agent Activity</h3>
                <p className="text-sm text-gray-500">Real-time AI agents processing • {agents.length} active</p>
              </div>
            </div>
            <div className="space-y-4">
              {agents.map((agent) => (
                <div key={agent.execution_id} className="p-4 bg-gradient-to-r from-blue-50 to-transparent rounded-lg border border-blue-100">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <p className="font-semibold text-gray-900">{agent.agent_type.replace('_', ' ').toUpperCase()}</p>
                      <p className="text-sm text-gray-600">{agent.patient_name}</p>
                    </div>
                    <span className="px-3 py-1 bg-blue-100 text-blue-700 text-sm font-medium rounded-full">
                      {agent.status === 'running' ? 'Running' : agent.status}
                    </span>
                  </div>
                  {agent.current_step && (
                    <p className="text-sm text-gray-600 mb-3 italic">{agent.current_step}</p>
                  )}
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Progress</span>
                      <span className="text-gray-900 font-medium">{agent.progress}%</span>
                    </div>
                    <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all duration-500"
                        style={{ width: `${agent.progress}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
      </main>
    </div>
  );
};

export default Dashboard;