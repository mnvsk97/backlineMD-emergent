import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileCheck, Calendar, Clock, User, AlertTriangle } from 'lucide-react';
import { Card } from '../components/ui/card';
import { useChat, useCopilotContext } from '../context/ChatContext';
import Header from '../components/Header';
import { apiService } from '../services/api';
import { toast } from 'sonner';

const DashboardPage = () => {
  const navigate = useNavigate();
  const { openChat } = useChat();
  const [tasks, setTasks] = useState([]);
  const [patients, setPatients] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = useCallback(async () => {
    try {
      const [tasksRes, patientsRes, appointmentsRes] = await Promise.all([
        apiService.getTasks(),
        apiService.getPatients(),
        apiService.getAppointments({ date: 'today' })
      ]);
      setTasks(tasksRes.data);
      setPatients(patientsRes.data);
      setAppointments(appointmentsRes.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, [fetchDashboardData]);

  // Provide context to CopilotKit
  useCopilotContext({
    page: 'dashboard',
    tasks: tasks,
    patients: patients,
    appointments: appointments,
    summary: `Dashboard overview with ${tasks.length} pending tasks, ${patients.length} patients, and ${appointments.length} appointments today.`
  }, 'Dashboard context with all patients, tasks, and appointments');

  return (
    <div className="flex-1 h-screen overflow-hidden flex flex-col">
      <Header />
      
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto px-8 py-8">
          {/* Greeting */}
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">Good morning, Dr. O'Brien</h2>
            <p className="text-gray-600">Here's what needs your attention today</p>
          </div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Actions Feed */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse" />
                  <h3 className="text-lg font-semibold text-gray-900">Actions Feed</h3>
                  <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-semibold">
                    {tasks.length} pending
                  </span>
                </div>
                <button 
                  onClick={() => navigate('/tasks')}
                  className="text-sm text-purple-600 hover:text-purple-700 transition-colors font-medium"
                >
                  View all →
                </button>
              </div>

              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="w-6 h-6 border-2 border-purple-600 border-t-transparent rounded-full animate-spin" />
                </div>
              ) : tasks.length === 0 ? (
                <Card className="p-12 text-center border border-gray-200">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <FileCheck className="w-8 h-8 text-green-600" />
                  </div>
                  <h3 className="text-base font-medium text-gray-900 mb-2">All caught up!</h3>
                  <p className="text-sm text-gray-500">No pending actions at the moment</p>
                </Card>
              ) : (
                <div className="space-y-3">
                  {tasks.slice(0, 5).map((task) => (
                    <Card
                      key={task.task_id}
                      className="p-4 border-l-4 border-purple-400 hover:border-purple-500 bg-white hover:shadow-md transition-all cursor-pointer"
                      onClick={() => navigate('/tasks')}
                    >
                      <div className="flex items-start gap-4">
                        <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                          <User className="w-5 h-5 text-purple-600" />
                        </div>
                        
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <h4 className="font-medium text-gray-900 text-sm">{task.patient_name}</h4>
                            <span className="text-xs text-gray-500 flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {task.waiting_minutes}m ago
                            </span>
                          </div>
                          <p className="text-xs text-gray-600 mb-2">{task.agent_type.replace('_', ' ')}</p>
                          <p className="text-sm text-gray-900 mb-2">{task.title}</p>
                          
                          <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs font-medium">
                              {Math.round(task.confidence_score * 100)}% confidence
                            </span>
                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                              task.priority === 'urgent' ? 'bg-red-100 text-red-700' :
                              task.priority === 'high' ? 'bg-purple-100 text-purple-700' :
                              'bg-blue-100 text-blue-700'
                            }`}>
                              {task.priority}
                            </span>
                            {task.confidence_score < 0.9 && (
                              <span className="flex items-center gap-1 text-xs text-purple-600">
                                <AlertTriangle className="w-3 h-3" />
                                Needs review
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </div>

            {/* Today's Schedule */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-purple-600" />
                  <h3 className="text-lg font-semibold text-gray-900">Today's Schedule</h3>
                </div>
                <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                  <Calendar className="w-4 h-4 text-gray-600" />
                </button>
              </div>

              {appointments.length === 0 ? (
                <Card className="p-8 text-center border border-gray-200">
                  <Calendar className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                  <p className="text-sm text-gray-500">No appointments scheduled for today</p>
                </Card>
              ) : (
                <div className="space-y-3">
                  {appointments.map((apt, index) => (
                    <Card key={index} className="p-4 border-l-4 border-purple-400 bg-white hover:shadow-md transition-all">
                      <div className="flex items-center gap-4">
                        <div className="text-center min-w-[60px]">
                          <p className="text-lg font-bold text-purple-600">{apt.time}</p>
                        </div>
                        <div className="flex-1">
                          <p className="font-medium text-gray-900 text-sm">{apt.type}</p>
                          <p className="text-xs text-gray-500 mt-0.5">{apt.patient_name} • {apt.doctor}</p>
                        </div>
                        <button className="px-3 py-1.5 bg-purple-100 hover:bg-purple-200 text-purple-700 rounded-lg transition-colors text-xs font-medium">
                          Join
                        </button>
                      </div>
                    </Card>
                  ))}
                  <p className="text-sm text-gray-500 text-center mt-4">No more appointments today.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;