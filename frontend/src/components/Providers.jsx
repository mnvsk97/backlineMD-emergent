'use client';

import { CopilotKit } from '@copilotkit/react-core';
import { ChatProvider } from '@/context/ChatContext';
import Sidebar from '@/components/Sidebar';
import CopilotChatPopup from '@/components/CopilotChatPopup';
import { Toaster } from '@/components/ui/sonner';

// Use Next.js API route for CopilotKit runtime
// If you want to use the FastAPI backend instead, set NEXT_PUBLIC_USE_FASTAPI_BACKEND=true
const useFastAPIBackend = process.env.NEXT_PUBLIC_USE_FASTAPI_BACKEND === 'true';
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001';
const runtimeUrl = useFastAPIBackend 
  ? `${BACKEND_URL}/api/copilotkit` 
  : '/api/copilotkit';

export default function Providers({ children }) {
  return (
    <CopilotKit runtimeUrl={runtimeUrl} agent="orchestrator">
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

