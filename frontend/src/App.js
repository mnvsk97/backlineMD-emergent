import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { CopilotKit } from '@copilotkit/react-core';
import { ChatProvider } from './context/ChatContext';
import CopilotChatPopup from './components/CopilotChatPopup';
import Sidebar from './components/Sidebar';
import DashboardPage from './pages/DashboardPage';
import PatientsPage from './pages/PatientsPage';
import PatientDetailsPage from './pages/PatientDetailsPage';
import TasksPage from './pages/TasksPage';
import TreasuryPage from './pages/TreasuryPage';
import { Toaster } from './components/ui/sonner';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  return (
    <CopilotKit runtimeUrl={`${BACKEND_URL}/api/copilot`}>
      <ChatProvider>
        <div className="App flex h-screen overflow-hidden">
          <BrowserRouter>
            <Sidebar />
            <div className="flex-1 flex flex-col overflow-hidden">
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/patients" element={<PatientsPage />} />
                <Route path="/patients/:patientId" element={<PatientDetailsPage />} />
                <Route path="/tasks" element={<TasksPage />} />
                <Route path="/treasury" element={<TreasuryPage />} />
              </Routes>
            </div>
            <CopilotChatPopup />
          </BrowserRouter>
          <Toaster position="top-right" richColors />
        </div>
      </ChatProvider>
    </CopilotKit>
  );
}

export default App;