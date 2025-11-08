import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { CopilotKit } from '@copilotkit/react-core';
import Layout from './components/Layout';
import DashboardPage from './pages/DashboardPage';
import PatientsPage from './pages/PatientsPage';
import PatientDetailsPage from './pages/PatientDetailsPage';
import TasksPage from './pages/TasksPage';
import { Toaster } from './components/ui/sonner';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  return (
    <CopilotKit runtimeUrl={`${BACKEND_URL}/api/copilot`}>
      <div className="App">
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<DashboardPage />} />
              <Route path="patients" element={<PatientsPage />} />
              <Route path="patients/:patientId" element={<PatientDetailsPage />} />
              <Route path="tasks" element={<TasksPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
        <Toaster position="top-right" richColors />
      </div>
    </CopilotKit>
  );
}

export default App;