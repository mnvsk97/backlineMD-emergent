import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { ArrowLeft, Send, Loader2, User, Activity, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';
import { Card } from './ui/card';
import { RadioGroup, RadioGroupItem } from './ui/radio-group';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ChatInterface = ({ onBack }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [tasks, setTasks] = useState([]);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    initializeChat();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const initializeChat = async () => {
    // Initial greeting
    setMessages([
      {
        id: 1,
        type: 'assistant',
        content: "Hi Dr. O'Brien! I'm here to help you manage your patient workflows. What would you like to know?",
        timestamp: new Date()
      }
    ]);

    // Load pending tasks
    try {
      const response = await axios.get(`${API}/tasks`);
      setTasks(response.data);

      // If there are pending tasks, show them
      if (response.data.length > 0) {
        setTimeout(() => {
          setMessages(prev => [
            ...prev,
            {
              id: 2,
              type: 'assistant',
              content: `I notice you have ${response.data.length} pending action(s) that need your review. Would you like me to show you the details?`,
              timestamp: new Date()
            }
          ]);
        }, 500);
      }
    } catch (error) {
      console.error('Error loading tasks:', error);
    }
  };

  const handleSend = async () => {
    if (!inputValue.trim() || loading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setLoading(true);

    // Simulate AI response
    setTimeout(() => {
      handleBotResponse(userMessage.content);
      setLoading(false);
    }, 1000);
  };

  const handleBotResponse = (userQuery) => {
    const query = userQuery.toLowerCase();

    // Handle different queries
    if (query.includes('pending') || query.includes('review') || query.includes('need') || query.includes('yes')) {
      if (tasks.length > 0) {
        setMessages(prev => [
          ...prev,
          {
            id: Date.now(),
            type: 'assistant',
            content: `Here are the tasks that need your attention:`,
            tasks: tasks,
            timestamp: new Date()
          }
        ]);
      } else {
        setMessages(prev => [
          ...prev,
          {
            id: Date.now(),
            type: 'assistant',
            content: "Great news! There are no pending tasks at the moment. All your workflows are running smoothly.",
            timestamp: new Date()
          }
        ]);
      }
    } else if (query.includes('patient') || query.includes('emma') || query.includes('alex')) {
      setMessages(prev => [
        ...prev,
        {
          id: Date.now(),
          type: 'assistant',
          content: "Let me pull up the patient information for you...",
          patientInfo: true,
          timestamp: new Date()
        }
      ]);
    } else {
      setMessages(prev => [
        ...prev,
        {
          id: Date.now(),
          type: 'assistant',
          content: "I understand. I can help you with:\n\n• Reviewing pending tasks and approvals\n• Checking patient information\n• Managing insurance verifications\n• Scheduling and appointments\n\nWhat would you like to do?",
          timestamp: new Date()
        }
      ]);
    }
  };

  const handleTaskApproval = async (taskId, decision, notes = '') => {
    try {
      await axios.post(`${API}/tasks/${taskId}/complete`, {
        decision,
        notes
      });

      toast.success('Task completed successfully!');

      // Remove completed task from list
      setTasks(prev => prev.filter(t => t.task_id !== taskId));

      // Add confirmation message
      setMessages(prev => [
        ...prev,
        {
          id: Date.now(),
          type: 'assistant',
          content: `✅ Task approved! The agent has resumed processing. ${tasks.length - 1 > 0 ? `You have ${tasks.length - 1} more task(s) pending.` : 'All tasks are now complete!'}`,
          timestamp: new Date()
        }
      ]);
    } catch (error) {
      console.error('Error completing task:', error);
      toast.error('Failed to complete task');
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={onBack}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
              data-testid="back-button"
            >
              <ArrowLeft className="w-5 h-5" />
              <span className="font-medium">Back</span>
            </button>
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-gray-900" />
              <h1 className="text-lg font-bold text-gray-900">BacklineMD Assistant</h1>
            </div>
            <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
              <User className="w-5 h-5 text-gray-600" />
            </div>
          </div>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">
          {messages.map((message) => (
            <div key={message.id}>
              {message.type === 'user' ? (
                <div className="flex justify-end">
                  <div className="bg-blue-600 text-white rounded-2xl rounded-tr-sm px-6 py-3 max-w-2xl">
                    <p className="text-sm">{message.content}</p>
                  </div>
                </div>
              ) : (
                <div className="flex justify-start">
                  <div className="max-w-3xl w-full">
                    <div className="bg-white rounded-2xl rounded-tl-sm px-6 py-4 shadow-sm border border-gray-200">
                      <p className="text-sm text-gray-900 whitespace-pre-line">{message.content}</p>
                    </div>

                    {/* Render embedded task cards */}
                    {message.tasks && message.tasks.length > 0 && (
                      <div className="mt-4 space-y-4">
                        {message.tasks.map((task) => (
                          <TaskApprovalCard
                            key={task.task_id}
                            task={task}
                            onApprove={(decision, notes) => handleTaskApproval(task.task_id, decision, notes)}
                          />
                        ))}
                      </div>
                    )}

                    {/* Patient info card (mock) */}
                    {message.patientInfo && (
                      <div className="mt-4">
                        <PatientInfoCard />
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-white rounded-2xl rounded-tl-sm px-6 py-4 shadow-sm border border-gray-200">
                <div className="flex items-center gap-2 text-gray-600">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm">Thinking...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="bg-white border-t border-gray-200 sticky bottom-0">
        <div className="max-w-5xl mx-auto px-6 py-4">
          <div className="flex items-end gap-3">
            <div className="flex-1 bg-gray-100 rounded-xl p-2">
              <Textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Ask about patients, tasks, or anything else..."
                className="border-0 bg-transparent resize-none focus:ring-0 min-h-[60px]"
                data-testid="chat-input"
              />
            </div>
            <button
              onClick={handleSend}
              disabled={!inputValue.trim() || loading}
              className="p-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              data-testid="send-button"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Task Approval Card Component
const TaskApprovalCard = ({ task, onApprove }) => {
  const [decision, setDecision] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!decision) {
      toast.error('Please select a decision');
      return;
    }

    setSubmitting(true);
    await onApprove(decision, notes);
    setSubmitting(false);
  };

  const getConfidenceColor = (score) => {
    if (score >= 0.9) return 'text-green-600 bg-green-50';
    if (score >= 0.7) return 'text-orange-600 bg-orange-50';
    return 'text-red-600 bg-red-50';
  };

  return (
    <Card className="p-6 border-2 border-orange-200 bg-orange-50/30" data-testid={`task-approval-${task.task_id}`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-5 h-5 text-orange-600" />
            <h3 className="font-bold text-gray-900">Needs Your Approval</h3>
          </div>
          <p className="text-sm text-gray-600">{task.patient_name} • {task.agent_type.replace('_', ' ')}</p>
        </div>
        <div className={`px-3 py-1 rounded-full text-sm font-medium ${getConfidenceColor(task.confidence_score)}`}>
          {Math.round(task.confidence_score * 100)}% confidence
        </div>
      </div>

      {/* Task Details */}
      <div className="bg-white rounded-lg p-4 mb-4">
        <h4 className="font-semibold text-gray-900 mb-2">{task.title}</h4>
        <p className="text-sm text-gray-700 mb-3">{task.description}</p>

        {/* AI Context */}
        {task.ai_context && (
          <div className="border-t border-gray-200 pt-3 mt-3">
            <p className="text-xs font-semibold text-gray-500 uppercase mb-2">AI Analysis</p>
            <div className="space-y-2 text-sm text-gray-700">
              {Object.entries(task.ai_context).map(([key, value]) => {
                if (typeof value === 'object' && !Array.isArray(value)) return null;
                if (Array.isArray(value)) {
                  return (
                    <div key={key}>
                      <span className="font-medium capitalize">{key.replace('_', ' ')}:</span>
                      <ul className="list-disc list-inside ml-3">
                        {value.map((item, idx) => (
                          <li key={idx} className="text-xs">{item}</li>
                        ))}
                      </ul>
                    </div>
                  );
                }
                return (
                  <div key={key}>
                    <span className="font-medium capitalize">{key.replace('_', ' ')}:</span> {value}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Decision Form */}
      <div className="space-y-4">
        <RadioGroup value={decision} onValueChange={setDecision}>
          <div className="flex items-center space-x-3 p-3 bg-white rounded-lg border-2 border-gray-200 hover:border-green-400 transition-colors">
            <RadioGroupItem value="approve" id={`approve-${task.task_id}`} />
            <Label htmlFor={`approve-${task.task_id}`} className="flex-1 cursor-pointer">
              <span className="font-medium text-gray-900">Approve</span>
            </Label>
            <CheckCircle2 className="w-5 h-5 text-green-600" />
          </div>

          <div className="flex items-center space-x-3 p-3 bg-white rounded-lg border-2 border-gray-200 hover:border-orange-400 transition-colors">
            <RadioGroupItem value="approve_with_followup" id={`followup-${task.task_id}`} />
            <Label htmlFor={`followup-${task.task_id}`} className="flex-1 cursor-pointer">
              <span className="font-medium text-gray-900">Approve with Follow-up</span>
            </Label>
            <AlertTriangle className="w-5 h-5 text-orange-600" />
          </div>

          <div className="flex items-center space-x-3 p-3 bg-white rounded-lg border-2 border-gray-200 hover:border-red-400 transition-colors">
            <RadioGroupItem value="reject" id={`reject-${task.task_id}`} />
            <Label htmlFor={`reject-${task.task_id}`} className="flex-1 cursor-pointer">
              <span className="font-medium text-gray-900">Reject</span>
            </Label>
            <XCircle className="w-5 h-5 text-red-600" />
          </div>
        </RadioGroup>

        <Textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Add notes (optional)..."
          className="min-h-[80px]"
        />

        <button
          onClick={handleSubmit}
          disabled={!decision || submitting}
          className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          data-testid="submit-approval"
        >
          {submitting ? (
            <span className="flex items-center justify-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              Processing...
            </span>
          ) : (
            'Submit Decision'
          )}
        </button>
      </div>
    </Card>
  );
};

// Patient Info Card Component (Mock)
const PatientInfoCard = () => {
  return (
    <Card className="p-6 bg-blue-50/50 border-2 border-blue-200">
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
          <User className="w-6 h-6 text-blue-600" />
        </div>
        <div className="flex-1">
          <h3 className="font-bold text-gray-900 mb-1">Emma Watson</h3>
          <p className="text-sm text-gray-600 mb-3">emma.watson@example.com • +1 (415) 555-2222</p>
          
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Status</p>
              <p className="font-medium text-gray-900">Insurance Review</p>
            </div>
            <div>
              <p className="text-gray-500">Next Appointment</p>
              <p className="font-medium text-gray-900">Oct 15, 11:30 AM</p>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-blue-200">
            <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Recent Activity</p>
            <ul className="space-y-1 text-sm text-gray-700">
              <li>• Documents uploaded (2 hours ago)</li>
              <li>• Medical history extracted (45 min ago)</li>
              <li>• Insurance verification pending (now)</li>
            </ul>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default ChatInterface;