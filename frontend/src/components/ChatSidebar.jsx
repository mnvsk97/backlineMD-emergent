import React, { useState, useRef, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Send, Loader2, X, Maximize2, Minimize2 } from 'lucide-react';
import { Textarea } from './ui/textarea';

const ChatSidebar = ({ isOpen, onToggle }) => {
  const location = useLocation();
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Initialize chat based on current page
    initializeChat();
  }, [location.pathname]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const initializeChat = () => {
    const patientMatch = location.pathname.match(/\/patients\/(.+)/);
    
    if (patientMatch) {
      setMessages([
        {
          id: 1,
          type: 'assistant',
          content: "I'm here to help you with this patient. You can ask me questions, request actions, or get insights about their treatment.",
          timestamp: new Date()
        }
      ]);
    } else if (location.pathname === '/tasks') {
      setMessages([
        {
          id: 1,
          type: 'assistant',
          content: "I can help you review and manage tasks. Ask me about any pending approvals or task details.",
          timestamp: new Date()
        }
      ]);
    } else {
      setMessages([
        {
          id: 1,
          type: 'assistant',
          content: "Hi! I'm your BacklineMD assistant. How can I help you today?",
          timestamp: new Date()
        }
      ]);
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
      const aiMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: generateResponse(userMessage.content),
        timestamp: new Date()
      };
      setMessages(prev => [...prev, aiMessage]);
      setLoading(false);
    }, 1000);
  };

  const generateResponse = (query) => {
    const lowerQuery = query.toLowerCase();
    
    if (lowerQuery.includes('schedule') || lowerQuery.includes('appointment')) {
      return "I can help you schedule an appointment. What date and time works best? I'll coordinate with the patient and update their calendar.";
    } else if (lowerQuery.includes('insurance')) {
      return "Let me check the insurance status for this patient. I can verify coverage, check pre-authorizations, or contact the insurance provider for clarification.";
    } else if (lowerQuery.includes('document') || lowerQuery.includes('report')) {
      return "I can help you review documents, extract key information, or generate reports. What specific document or information do you need?";
    } else if (lowerQuery.includes('follow up') || lowerQuery.includes('followup')) {
      return "I'll create a follow-up task for this patient. What specific action should we follow up on, and when would you like this completed?";
    } else {
      return "I'm here to assist with patient management, scheduling, document review, and administrative tasks. What would you like me to help with?";
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={onToggle}
        className="fixed right-0 top-1/2 -translate-y-1/2 bg-gray-900 text-white p-3 rounded-l-lg shadow-lg hover:bg-gray-800 transition-colors z-50"
        title="Open Chat"
      >
        <Maximize2 className="w-5 h-5" />
      </button>
    );
  }

  return (
    <div className="fixed right-0 top-0 h-screen w-96 bg-white border-l border-gray-200 flex flex-col z-40">
      {/* Header */}
      <div className="border-b border-gray-200 p-4 flex items-center justify-between bg-gray-50">
        <div>
          <h3 className="font-semibold text-gray-900">AI Assistant</h3>
          <p className="text-xs text-gray-500">Always here to help</p>
        </div>
        <button
          onClick={onToggle}
          className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
          title="Minimize Chat"
        >
          <Minimize2 className="w-4 h-4 text-gray-600" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div key={message.id}>
            {message.type === 'user' ? (
              <div className="flex justify-end">
                <div className="bg-gray-900 text-white rounded-2xl rounded-tr-sm px-4 py-2 max-w-[85%]">
                  <p className="text-sm">{message.content}</p>
                </div>
              </div>
            ) : (
              <div className="flex justify-start">
                <div className="bg-gray-50 rounded-2xl rounded-tl-sm px-4 py-2 max-w-[85%] border border-gray-200">
                  <p className="text-sm text-gray-900">{message.content}</p>
                </div>
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-50 rounded-2xl rounded-tl-sm px-4 py-2 border border-gray-200">
              <div className="flex items-center gap-2 text-gray-600">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm">Thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4 bg-gray-50">
        <div className="flex items-end gap-2">
          <Textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask about patients, schedule appointments..."
            className="flex-1 resize-none min-h-[60px] text-sm"
            data-testid="chat-sidebar-input"
          />
          <button
            onClick={handleSend}
            disabled={!inputValue.trim() || loading}
            className="p-3 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            data-testid="chat-sidebar-send"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatSidebar;
