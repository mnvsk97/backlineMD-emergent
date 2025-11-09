import React from 'react';
import { CopilotPopup } from '@copilotkit/react-ui';
import { useChat } from '../context/ChatContext';
import '@copilotkit/react-ui/styles.css';

const CopilotChatPopup = () => {
  const { isChatOpen } = useChat();

  if (!isChatOpen) return null;

  return (
    <CopilotPopup
      labels={{
        title: "AI Assistant",
        initial: "Hi! I'm here to help you with BacklineMD. I have the context of the current page, so feel free to ask me anything.",
      }}
      defaultOpen={true}
      clickOutsideToClose={false}
      className="copilot-popup"
    />
  );
};

export default CopilotChatPopup;