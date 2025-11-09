import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { CheckSquare, User, Clock, AlertTriangle, Plus } from 'lucide-react';
import { Card } from '../components/ui/card';
import TaskDetailModal from '../components/TaskDetailModal';
import CreateTaskModal from '../components/CreateTaskModal';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TasksPage = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTask, setSelectedTask] = useState(null);
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await axios.get(`${API}/tasks`);
      setTasks(response.data);
    } catch (error) {
      console.error('Error fetching tasks:', error);
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
      await fetchTasks();
    } catch (error) {
      console.error('Error completing task:', error);
      throw error;
    }
  };

  const getPriorityBadge = (priority) => {
    const badges = {
      urgent: { bg: 'bg-gray-900', text: 'text-white' },
      high: { bg: 'bg-gray-700', text: 'text-white' },
      medium: { bg: 'bg-gray-100', text: 'text-gray-700' },
      low: { bg: 'bg-gray-50', text: 'text-gray-600' }
    };
    return badges[priority] || badges.medium;
  };

  return (
    <div className="h-full">
      <TaskDetailModal
        isOpen={showTaskModal}
        onClose={() => setShowTaskModal(false)}
        task={selectedTask}
        onComplete={handleCompleteTask}
      />
      <CreateTaskModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
      />

      {/* Header */}
      <header className="border-b border-gray-200 bg-white sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Tasks</h1>
              <p className="text-sm text-gray-500 mt-1">Manage tasks requiring human review and approval</p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center gap-2"
              data-testid="create-task-button"
            >
              <Plus className="w-4 h-4" />
              Create Task
            </button>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-8 py-8">
        {loading ? (
          <div className="flex items-center justify-center py-24">
            <div className="w-8 h-8 border-2 border-gray-900 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : tasks.length === 0 ? (
          <Card className="p-12 text-center border border-gray-200">
            <CheckSquare className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <h3 className="text-base font-medium text-gray-900 mb-2">All caught up!</h3>
            <p className="text-sm text-gray-500">No pending tasks at the moment</p>
          </Card>
        ) : (
          <div className="space-y-4">
            {tasks.map((task) => {
              const badge = getPriorityBadge(task.priority);
              return (
                <Card
                  key={task.task_id}
                  className="p-5 border border-gray-200 hover:border-gray-900 transition-all cursor-pointer"
                  data-testid={`task-card-${task.task_id}`}
                >
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center flex-shrink-0">
                      <User className="w-5 h-5 text-gray-600" />
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <h3 className="font-semibold text-gray-900 text-base mb-1">{task.title}</h3>
                          <p className="text-sm text-gray-600">
                            {task.patient_name} • {task.agent_type.replace('_', ' ')}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs font-medium">
                            {Math.round(task.confidence_score * 100)}% confidence
                          </span>
                          <span className={`px-2 py-1 rounded text-xs font-medium ${badge.bg} ${badge.text}`}>
                            {task.priority}
                          </span>
                        </div>
                      </div>

                      <p className="text-sm text-gray-600 mb-3">{task.description}</p>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1 text-xs text-gray-500">
                          <Clock className="w-3 h-3" />
                          <span>Waiting {task.waiting_minutes}m</span>
                        </div>
                        {task.confidence_score < 0.9 && (
                          <div className="flex items-center gap-1 text-xs text-gray-600">
                            <AlertTriangle className="w-3 h-3" />
                            <span>Needs review</span>
                          </div>
                        )}
                        {task.status === 'awaiting_approval' && (
                          <button className="px-3 py-1.5 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors text-xs font-medium">
                            Review Task
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
};

export default TasksPage;