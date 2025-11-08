import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { CopilotKit } from '@copilotkit/react-core';
import Dashboard from './pages/Dashboard';
import { Toaster } from './components/ui/sonner';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  return (
    <CopilotKit runtimeUrl={`${BACKEND_URL}/api/copilot`}>
      <div className="App">
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Dashboard />} />
          </Routes>
        </BrowserRouter>
        <Toaster position="top-right" richColors />
      </div>
    </CopilotKit>
  );
}

export default App;