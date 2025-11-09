import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Clock, User, AlertTriangle, CheckCircle, XCircle, Plus } from 'lucide-react';
import { Card } from '../components/ui/card';
import { useChat, useCopilotContext } from '../context/ChatContext';
import Header from '../components/Header';
import CreateTaskModal from '../components/CreateTaskModal';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TasksPage = () => {
  const { openChat } = useChat();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

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

  // Provide all tasks context to CopilotKit
  useCopilotContext({
    page: 'tasks',
    tasks: tasks,
    count: tasks.length,
    filters: ['all', 'pending', 'urgent', 'review'],
    summary: `Task management page showing ${tasks.length} tasks requiring doctor review and approval.`
  }, 'All tasks with details, priorities, and patient information');

  const filteredTasks = tasks.filter(task => {
    if (filter === 'all') return true;
    if (filter === 'urgent') return task.priority === 'urgent';
    if (filter === 'high') return task.priority === 'high';
    if (filter === 'review') return task.confidence_score < 0.9;
    return true;
  });

  const filters = [
    { value: 'all', label: 'All Tasks', count: tasks.length },
    { value: 'urgent', label: 'Urgent', count: tasks.filter(t => t.priority === 'urgent').length },
    { value: 'high', label: 'High Priority', count: tasks.filter(t => t.priority === 'high').length },
    { value: 'review', label: 'Needs Review', count: tasks.filter(t => t.confidence_score < 0.9).length },
  ];

  return (
    <div className="flex-1 h-screen overflow-hidden flex flex-col">
      <Header 
        title="Task Management" 
        subtitle="Review and manage AI-generated tasks"
      />
      
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto px-8 py-8">
          {/* Filter Tabs */}
          <div className="flex items-center gap-2 mb-6 bg-white border border-gray-200 p-1 rounded-lg w-fit">
            {filters.map((f) => (
              <button
                key={f.value}
                onClick={() => setFilter(f.value)}
                className={`px-4 py-2 rounded-md transition-colors font-medium text-sm ${
                  filter === f.value
                    ? 'bg-purple-600 text-white'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                {f.label} ({f.count})
              </button>
            ))}
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-6 h-6 border-2 border-purple-600 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : filteredTasks.length === 0 ? (
            <Card className="p-12 text-center border border-gray-200">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-base font-medium text-gray-900 mb-2">All caught up!</h3>
              <p className="text-sm text-gray-500">No tasks match the current filter</p>
            </Card>
          ) : (
            <div className="space-y-4">
              {filteredTasks.map((task) => (
                <Card
                  key={task.task_id}
                  className="p-6 border-l-4 border-purple-400 hover:border-purple-500 bg-white hover:shadow-lg transition-all cursor-pointer"
                  onClick={openChat}
                >
                  <div className="flex items-start justify-between gap-6">
                    <div className="flex items-start gap-4 flex-1">
                      <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <User className="w-6 h-6 text-purple-600" />
                      </div>
                      
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <div>
                            <h3 className="font-semibold text-gray-900 text-lg mb-1">{task.patient_name}</h3>
                            <p className="text-sm text-gray-600">{task.agent_type.replace('_', ' ')}</p>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-500 flex items-center gap-1">
                              <Clock className="w-4 h-4" />
                              {task.waiting_minutes}m ago
                            </span>
                          </div>
                        </div>
                        
                        <p className="text-base text-gray-900 mb-4">{task.title}</p>
                        <p className="text-sm text-gray-600 mb-4">{task.description}</p>
                        
                        <div className="flex items-center gap-3 flex-wrap">
                          <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm font-medium">
                            {Math.round(task.confidence_score * 100)}% confidence
                          </span>
                          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                            task.priority === 'urgent' ? 'bg-red-100 text-red-700' :
                            task.priority === 'high' ? 'bg-purple-100 text-purple-700' :
                            'bg-blue-100 text-blue-700'
                          }`}>
                            {task.priority}
                          </span>
                          {task.confidence_score < 0.9 && (
                            <span className="flex items-center gap-1 text-sm text-purple-600">
                              <AlertTriangle className="w-4 h-4" />
                              Needs review
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <button 
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium flex items-center gap-2"
                        onClick={(e) => {
                          e.stopPropagation();
                          // Handle approve
                        }}
                      >
                        <CheckCircle className="w-4 h-4" />
                        Approve
                      </button>
                      <button 
                        className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium flex items-center gap-2"
                        onClick={(e) => {
                          e.stopPropagation();
                          // Handle reject
                        }}
                      >
                        <XCircle className="w-4 h-4" />
                        Reject
                      </button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TasksPage;