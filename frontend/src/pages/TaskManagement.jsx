import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, AlertTriangle, CheckCircle2, Clock, FileCheck, Activity, User } from 'lucide-react';
import { Card } from '../components/ui/card';
import { RadioGroup, RadioGroupItem } from '../components/ui/radio-group';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TaskManagement = () => {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState([]);
  const [selectedTask, setSelectedTask] = useState(null);
  const [decision, setDecision] = useState('');
  const [notes, setNotes] = useState('');
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchTasks();
    fetchAgents();
    // Set up SSE for agent updates
    const eventSource = new EventSource(`${API}/agents/stream`);
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setAgents(data.agents || []);
    };
    return () => eventSource.close();
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await axios.get(`${API}/tasks`);
      setTasks(response.data);
      if (response.data.length > 0 && !selectedTask) {
        setSelectedTask(response.data[0]);
      }
    } catch (error) {
      console.error('Error fetching tasks:', error);
    }
  };

  const fetchAgents = async () => {
    try {
      const response = await axios.get(`${API}/agents/active`);
      setAgents(response.data);
    } catch (error) {
      console.error('Error fetching agents:', error);
    }
  };

  const handleCompleteTask = async () => {
    if (!decision) {
      toast.error('Please select a decision');
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API}/tasks/${selectedTask.task_id}/complete`, {
        decision,
        notes
      });

      toast.success('Task completed successfully! Agent resumed processing.');
      
      // Refresh tasks
      await fetchTasks();
      setDecision('');
      setNotes('');
    } catch (error) {
      console.error('Error completing task:', error);
      toast.error('Failed to complete task');
    } finally {
      setLoading(false);
    }
  };

  const getConfidenceColor = (score) => {
    if (score >= 0.9) return 'text-green-600';
    if (score >= 0.7) return 'text-orange-600';
    return 'text-red-600';
  };

  const getConfidenceBadge = (score) => {
    if (score >= 0.9) return { bg: 'bg-green-100', text: 'text-green-700', label: 'High' };
    if (score >= 0.7) return { bg: 'bg-orange-100', text: 'text-orange-700', label: 'Medium' };
    return { bg: 'bg-red-100', text: 'text-red-700', label: 'Low' };
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50 backdrop-blur-sm bg-white/90">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              <span className="font-medium">Back to Dashboard</span>
            </button>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Task Management - Human-in-the-Loop</h1>
              <p className="text-sm text-gray-500">Review and approve AI agent decisions</p>
            </div>
            <div className="flex items-center gap-2 px-3 py-2 bg-orange-50 text-orange-700 rounded-lg">
              <AlertTriangle className="w-4 h-4" />
              <span className="text-sm font-medium">{tasks.length} Pending</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Task List Sidebar */}
          <div className="lg:col-span-1">
            <Card className="p-4 bg-white border border-gray-200">
              <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                <FileCheck className="w-5 h-5 text-orange-600" />
                Awaiting Approval
              </h3>
              <div className="space-y-2">
                {tasks.length === 0 ? (
                  <div className="text-center py-8">
                    <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto mb-2" />
                    <p className="text-sm text-gray-600">No pending tasks!</p>
                    <p className="text-xs text-gray-500 mt-1">All agents running smoothly</p>
                  </div>
                ) : (
                  tasks.map((task) => {
                    const badge = getConfidenceBadge(task.confidence_score);
                    return (
                      <div
                        key={task.task_id}
                        className={`p-3 rounded-lg cursor-pointer transition-all ${
                          selectedTask?.task_id === task.task_id
                            ? 'bg-blue-50 border-2 border-blue-500'
                            : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent'
                        }`}
                        onClick={() => setSelectedTask(task)}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <h4 className="font-semibold text-sm text-gray-900">{task.title}</h4>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${badge.bg} ${badge.text}`}>
                            {Math.round(task.confidence_score * 100)}%
                          </span>
                        </div>
                        <p className="text-xs text-gray-600 mb-2">{task.patient_name}</p>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-500 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {task.waiting_minutes}m ago
                          </span>
                          <span className={`px-2 py-0.5 rounded-full font-medium ${
                            task.priority === 'urgent' ? 'bg-red-100 text-red-700' :
                            task.priority === 'high' ? 'bg-orange-100 text-orange-700' :
                            'bg-blue-100 text-blue-700'
                          }`}>
                            {task.priority}
                          </span>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </Card>
          </div>

          {/* Task Detail */}
          <div className="lg:col-span-2">
            {selectedTask ? (
              <div className="space-y-6">
                {/* Task Header */}
                <Card className="p-6 bg-gradient-to-r from-orange-50 to-white border-2 border-orange-200">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <div className="flex items-center gap-3 mb-2">
                        <AlertTriangle className="w-6 h-6 text-orange-600" />
                        <h2 className="text-2xl font-bold text-gray-900">PENDING APPROVAL</h2>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-gray-600">
                        <span className="flex items-center gap-1">
                          <Activity className="w-4 h-4" />
                          Agent: {selectedTask.agent_type.replace('_', ' ')}
                        </span>
                        <span className="flex items-center gap-1">
                          <User className="w-4 h-4" />
                          Patient: {selectedTask.patient_name}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          Waiting: {selectedTask.waiting_minutes} minutes
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`text-4xl font-bold ${getConfidenceColor(selectedTask.confidence_score)} mb-1`}>
                        {Math.round(selectedTask.confidence_score * 100)}%
                      </div>
                      <p className="text-sm text-gray-600">Confidence</p>
                    </div>
                  </div>
                  <div className="pt-4 border-t border-orange-200">
                    <h3 className="font-semibold text-gray-900 text-lg mb-2">{selectedTask.title}</h3>
                    <p className="text-gray-700">{selectedTask.description}</p>
                  </div>
                </Card>

                {/* AI Context */}
                <Card className="p-6 bg-white border border-gray-200">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                      <Activity className="w-5 h-5 text-blue-600" />
                    </div>
                    <h3 className="text-lg font-bold text-gray-900">AI Context & Analysis</h3>
                  </div>

                  {/* Context Details */}
                  <div className="space-y-4 mb-6">
                    {Object.entries(selectedTask.ai_context).map(([key, value]) => {
                      if (key === 'confidence_breakdown') {
                        return (
                          <div key={key}>
                            <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                              📊 Confidence Breakdown:
                            </h4>
                            <div className="space-y-2 ml-4">
                              {Object.entries(value).map(([field, score]) => (
                                <div key={field} className="flex items-center justify-between">
                                  <span className="text-sm text-gray-700 capitalize">{field.replace('_', ' ')}:</span>
                                  <div className="flex items-center gap-2">
                                    <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                                      <div
                                        className={`h-full rounded-full ${
                                          score >= 0.9 ? 'bg-green-500' :
                                          score >= 0.7 ? 'bg-orange-500' :
                                          'bg-red-500'
                                        }`}
                                        style={{ width: `${score * 100}%` }}
                                      />
                                    </div>
                                    <span className={`text-sm font-semibold ${
                                      score >= 0.9 ? 'text-green-600' :
                                      score >= 0.7 ? 'text-orange-600' :
                                      'text-red-600'
                                    }`}>
                                      {Math.round(score * 100)}%
                                    </span>
                                    {score >= 0.9 ? '✅' : score >= 0.7 ? '⚠️' : '❌'}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        );
                      }
                      
                      if (key === 'details' && Array.isArray(value)) {
                        return (
                          <div key={key}>
                            <h4 className="font-semibold text-gray-900 mb-2">⚠️ Issues Detected:</h4>
                            <ul className="list-disc list-inside space-y-1 ml-4">
                              {value.map((item, idx) => (
                                <li key={idx} className="text-sm text-gray-700">{item}</li>
                              ))}
                            </ul>
                          </div>
                        );
                      }

                      return (
                        <div key={key} className="text-sm">
                          <span className="font-semibold text-gray-900 capitalize">{key.replace('_', ' ')}: </span>
                          <span className="text-gray-700">{typeof value === 'object' ? JSON.stringify(value) : value}</span>
                        </div>
                      );
                    })}
                  </div>

                  {/* Suggested Actions */}
                  {selectedTask.suggested_actions.length > 0 && (
                    <div className="pt-4 border-t border-gray-200">
                      <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                        💡 Suggested Actions:
                      </h4>
                      <ul className="space-y-2">
                        {selectedTask.suggested_actions.map((action, idx) => (
                          <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
                            <span className="text-blue-600 font-bold">•</span>
                            {action}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </Card>

                {/* Decision Form */}
                <Card className="p-6 bg-white border border-gray-200">
                  <h3 className="text-lg font-bold text-gray-900 mb-4">✍️ Your Decision:</h3>
                  
                  <RadioGroup value={decision} onValueChange={setDecision} className="space-y-3 mb-6">
                    <div className="flex items-center space-x-3 p-3 rounded-lg border-2 border-gray-200 hover:border-green-500 hover:bg-green-50 transition-all cursor-pointer">
                      <RadioGroupItem value="approve_with_followup" id="approve_followup" />
                      <Label htmlFor="approve_followup" className="flex-1 cursor-pointer">
                        <span className="font-semibold text-gray-900">Approve with Manual Follow-up</span>
                        <p className="text-sm text-gray-600">Accept extraction but flag for verification call</p>
                      </Label>
                    </div>
                    
                    <div className="flex items-center space-x-3 p-3 rounded-lg border-2 border-gray-200 hover:border-red-500 hover:bg-red-50 transition-all cursor-pointer">
                      <RadioGroupItem value="reject" id="reject" />
                      <Label htmlFor="reject" className="flex-1 cursor-pointer">
                        <span className="font-semibold text-gray-900">Reject - Need More Info</span>
                        <p className="text-sm text-gray-600">Request additional documentation from patient</p>
                      </Label>
                    </div>
                    
                    <div className="flex items-center space-x-3 p-3 rounded-lg border-2 border-gray-200 hover:border-blue-500 hover:bg-blue-50 transition-all cursor-pointer">
                      <RadioGroupItem value="approve" id="approve" />
                      <Label htmlFor="approve" className="flex-1 cursor-pointer">
                        <span className="font-semibold text-gray-900">Approve as-is</span>
                        <p className="text-sm text-gray-600">Proceed with current information</p>
                      </Label>
                    </div>
                  </RadioGroup>

                  <div className="mb-6">
                    <Label htmlFor="notes" className="mb-2 block font-semibold text-gray-900">
                      📝 Add Notes (optional):
                    </Label>
                    <Textarea
                      id="notes"
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      placeholder="Add any additional notes or context for your decision..."
                      className="min-h-[100px]"
                    />
                  </div>

                  <div className="flex gap-3">
                    <button
                      onClick={handleCompleteTask}
                      disabled={loading || !decision}
                      className={`flex-1 py-3 px-6 rounded-lg font-semibold text-white transition-all ${
                        loading || !decision
                          ? 'bg-gray-300 cursor-not-allowed'
                          : 'bg-green-600 hover:bg-green-700 shadow-lg hover:shadow-xl'
                      }`}
                    >
                      {loading ? (
                        <span className="flex items-center justify-center gap-2">
                          <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          Processing...
                        </span>
                      ) : (
                        <span className="flex items-center justify-center gap-2">
                          <CheckCircle2 className="w-5 h-5" />
                          Approve & Resume Agent
                        </span>
                      )}
                    </button>
                    <button
                      onClick={() => {
                        setDecision('reject');
                        handleCompleteTask();
                      }}
                      disabled={loading}
                      className="px-6 py-3 border-2 border-red-600 text-red-600 rounded-lg font-semibold hover:bg-red-50 transition-colors"
                    >
                      ❌ Reject
                    </button>
                  </div>
                </Card>
              </div>
            ) : (
              <Card className="p-12 bg-white border border-gray-200 text-center">
                <CheckCircle2 className="w-16 h-16 text-green-500 mx-auto mb-4" />
                <h3 className="text-xl font-bold text-gray-900 mb-2">No Pending Tasks</h3>
                <p className="text-gray-600">All AI agents are running smoothly without requiring human intervention.</p>
              </Card>
            )}
          </div>
        </div>

        {/* Live Agent Activity */}
        {agents.length > 0 && (
          <Card className="p-6 bg-white border border-gray-200 mt-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center">
                <Activity className="w-5 h-5 text-green-600 animate-pulse" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900">🔄 LIVE AGENT ACTIVITY</h3>
                <p className="text-sm text-gray-500">Real-time agent execution status • {agents.length} active</p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {agents.map((agent) => (
                <div key={agent.execution_id} className="p-4 bg-gradient-to-r from-blue-50 to-transparent rounded-lg border border-blue-100">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <p className="font-semibold text-gray-900 text-sm">{agent.agent_type.replace('_', ' ').toUpperCase()}</p>
                      <p className="text-xs text-gray-600">{agent.patient_name}</p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      agent.status === 'running' ? 'bg-blue-100 text-blue-700' :
                      agent.status === 'completed' ? 'bg-green-100 text-green-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {agent.status === 'running' ? `Running | ${agent.progress}%` : agent.status}
                    </span>
                  </div>
                  {agent.current_step && (
                    <p className="text-xs text-gray-600 mb-2 italic">{agent.current_step}</p>
                  )}
                  {agent.status === 'running' && (
                    <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all duration-500"
                        style={{ width: `${agent.progress}%` }}
                      />
                    </div>
                  )}
                  {agent.status === 'completed' && (
                    <div className="flex items-center gap-2 text-xs text-gray-600">
                      <CheckCircle2 className="w-4 h-4 text-green-600" />
                      <span>Completed in {agent.duration_seconds}s</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </Card>
        )}
      </main>
    </div>
  );
};

export default TaskManagement;
