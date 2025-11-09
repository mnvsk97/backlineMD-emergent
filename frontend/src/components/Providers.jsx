'use client';

import { CopilotKit } from '@copilotkit/react-core';
import { ChatProvider } from '@/context/ChatContext';
import Sidebar from '@/components/Sidebar';
import CopilotChatPopup from '@/components/CopilotChatPopup';
import { Toaster } from '@/components/ui/sonner';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001';

export default function Providers({ children }) {
  return (
    <CopilotKit runtimeUrl="http://localhost:3000/api/copilotkit" agent="orchestrator">
      <ChatProvider>
        <div className="App flex h-screen overflow-hidden">
          <Sidebar />
          <div className="flex-1 flex flex-col overflow-hidden">
            {children}
          </div>
          <CopilotChatPopup />
          <Toaster position="top-right" richColors />
        </div>
      </ChatProvider>
    </CopilotKit>
  );
}

