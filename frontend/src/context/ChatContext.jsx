import React, { createContext, useContext, useState, useCallback } from 'react';
import { useCopilotReadable } from '@copilotkit/react-core';

const ChatContext = createContext();

export const ChatProvider = ({ children }) => {
  const [isChatOpen, setIsChatOpen] = useState(true);
  const [pageContext, setPageContext] = useState(null);

  const openChat = useCallback(() => setIsChatOpen(true), []);
  const closeChat = useCallback(() => setIsChatOpen(false), []);
  const toggleChat = useCallback(() => setIsChatOpen(prev => !prev), []);

  const updateContext = useCallback((context) => {
    setPageContext(context);
  }, []);

  return (
    <ChatContext.Provider value={{ 
      isChatOpen, 
      openChat, 
      closeChat, 
      toggleChat,
      pageContext,
      updateContext
    }}>
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within ChatProvider');
  }
  return context;
};

// Hook to provide context to CopilotKit
export const useCopilotContext = (contextData, description) => {
  useCopilotReadable({
    description: description || 'Current page context',
    value: contextData,
  });
};