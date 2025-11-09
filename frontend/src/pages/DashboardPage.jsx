import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Activity, Calendar, User, AlertTriangle, Clock, FileCheck } from 'lucide-react';
import { Card } from '../components/ui/card';
import TaskDetailModal from '../components/TaskDetailModal';
import { CopilotChat } from '@copilotkit/react-ui';
import '@copilotkit/react-ui/styles.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DashboardPage = () => {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTask, setSelectedTask] = useState(null);
  const [showTaskModal, setShowTaskModal] = useState(false);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
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

  const handleTaskClick = (task) => {
    setSelectedTask(task);
    setShowTaskModal(true);
  };

  const handleCompleteTask = async (taskId, decision, notes) => {
    try {
      await axios.post(`${API}/tasks/${taskId}/complete`, { decision, notes });
      await fetchDashboardData();
    } catch (error) {
      console.error('Error completing task:', error);
      throw error;
    }
  };

  const stats = [
    { title: 'PENDING', value: tasks.length.toString(), subtitle: 'Need Review', icon: FileCheck, color: 'orange', bgColor: 'bg-orange-50', iconColor: 'text-orange-600' },
    { title: 'APPOINTMENTS', value: appointments.length.toString(), subtitle: 'Today', icon: Calendar, color: 'purple', bgColor: 'bg-purple-50', iconColor: 'text-purple-600' }
  ];

  return (
    <div className="h-full overflow-y-auto">
      <TaskDetailModal
        isOpen={showTaskModal}
        onClose={() => setShowTaskModal(false)}
        task={selectedTask}
        onComplete={handleCompleteTask}
      />

      <header className="border-b border-gray-200 bg-white sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Good morning, Dr. O'Brien</h1>
              <p className="text-sm text-gray-500 mt-1">Here's what needs your attention today</p>
            </div>
            <div className="w-9 h-9 bg-gray-200 rounded-full flex items-center justify-center">
              <User className="w-5 h-5 text-gray-600" />
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {stats.map((stat, index) => {
            const IconComponent = stat.icon;
            return (
              <Card key={index} className="p-6 bg-white border border-gray-200 hover:shadow-lg transition-all">
                <div className="flex items-center justify-between mb-4">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${stat.bgColor}`}>
                    <IconComponent className={`w-6 h-6 ${stat.iconColor}`} />
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

        {/* Actions Section */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-orange-500 rounded-full animate-pulse" />
              <h3 className="text-lg font-semibold text-gray-900">Actions</h3>
              <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded-full text-xs font-semibold">
                {tasks.length} pending
              </span>
            </div>
            <button 
              onClick={() => navigate('/tasks')}
              className="text-sm text-blue-600 hover:text-blue-700 transition-colors font-medium"
            >
              View all →
            </button>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : tasks.length === 0 ? (
            <Card className="p-12 text-center border border-gray-200">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Activity className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-base font-medium text-gray-900 mb-2">All caught up!</h3>
              <p className="text-sm text-gray-500">No pending actions at the moment</p>
            </Card>
          ) : (
            <div className="space-y-3">
              {tasks.slice(0, 3).map((task) => (
                <Card
                  key={task.task_id}
                  className="p-4 border-l-4 border-orange-400 hover:border-orange-500 bg-white hover:shadow-md transition-all cursor-pointer"
                  onClick={() => handleTaskClick(task)}
                  data-testid={`dashboard-task-${task.task_id}`}
                >
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center flex-shrink-0">
                      <User className="w-5 h-5 text-orange-600" />
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
                          task.priority === 'high' ? 'bg-orange-100 text-orange-700' :
                          'bg-blue-100 text-blue-700'
                        }`}>
                          {task.priority}
                        </span>
                        {task.confidence_score < 0.9 && (
                          <span className="flex items-center gap-1 text-xs text-orange-600">
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
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default DashboardPage;