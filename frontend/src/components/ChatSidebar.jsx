import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { Minimize2, Maximize2, Send, Loader2 } from 'lucide-react';
import { Textarea } from './ui/textarea';

const ChatSidebar = ({ isOpen, onToggle }) => {
  const location = useLocation();
  const [suggestedQuestions, setSuggestedQuestions] = useState([]);

  useEffect(() => {
    // Set suggested questions based on current page
    const patientMatch = location.pathname.match(/\/patients\/(.+)/);
    
    if (patientMatch) {
      setSuggestedQuestions([
        'What needs review for this patient?',
        'Schedule a follow-up appointment',
        'Check insurance status',
        'Generate patient summary'
      ]);
    } else if (location.pathname === '/tasks') {
      setSuggestedQuestions([
        'Show pending approvals',
        'What tasks need urgent attention?',
        'Review high priority tasks'
      ]);
    } else {
      setSuggestedQuestions([
        'What needs review today?',
        'Any flagged documents?',
        'Pending insurance verifications',
        'Show today\'s appointments'
      ]);
    }
  }, [location.pathname]);

  const handleQuestionClick = (question) => {
    // For now, just log the question - can be enhanced later
    console.log('Question clicked:', question);
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
          <p className="text-xs text-gray-500">Powered by Claude</p>
        </div>
        <button
          onClick={onToggle}
          className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
          title="Minimize Chat"
        >
          <Minimize2 className="w-4 h-4 text-gray-600" />
        </button>
      </div>

      {/* Suggested Questions */}
      {suggestedQuestions.length > 0 && (
        <div className="p-4 border-b border-gray-200 bg-white">
          <p className="text-xs font-semibold text-gray-500 uppercase mb-3">Suggested Questions</p>
          <div className="space-y-2">
            {suggestedQuestions.map((question, index) => (
              <button
                key={index}
                className="w-full text-left px-3 py-2 text-sm bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors text-gray-700 border border-gray-200"
                onClick={() => {
                  // CopilotKit will handle this
                  const input = document.querySelector('.copilotkit-chat-input textarea');
                  if (input) {
                    input.value = question;
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                  }
                }}
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* CopilotKit Chat */}
      <div className="flex-1 overflow-hidden">
        <CopilotChat
          className="h-full"
          instructions="You are a helpful medical assistant for BacklineMD. Help doctors manage patients, review tasks, schedule appointments, and provide insights. Be concise and professional."
          labels={{
            title: "BacklineMD Assistant",
            initial: "Hi! I'm here to help you manage patients and workflows. What can I assist you with?"
          }}
        />
      </div>
    </div>
  );
};

export default ChatSidebar;