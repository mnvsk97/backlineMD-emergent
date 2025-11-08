import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Users, Activity, CheckSquare } from 'lucide-react';
import ChatSidebar from './ChatSidebar';

const Layout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [chatOpen, setChatOpen] = useState(true);

  const isActive = (path) => {
    if (path === '/patients') {
      return location.pathname.startsWith('/patients');
    }
    return location.pathname === path;
  };

  return (
    <div className="flex h-screen bg-white">
      {/* Dark Sidebar */}
      <div className="w-20 bg-gray-950 flex flex-col items-center py-8 space-y-8">
        <button 
          onClick={() => navigate('/patients')}
          className="w-10 h-10 bg-white rounded-lg flex items-center justify-center hover:bg-gray-100 transition-colors cursor-pointer"
          title="Home"
          data-testid="home-logo"
        >
          <Activity className="w-6 h-6 text-gray-950" />
        </button>
        
        <div className="flex-1 flex flex-col items-center space-y-6 text-gray-400">
          <button
            onClick={() => navigate('/patients')}
            className={`p-3 rounded-lg transition-colors relative ${
              isActive('/patients') ? 'text-white bg-gray-800' : 'hover:text-white hover:bg-gray-800'
            }`}
            title="Patients"
            data-testid="nav-patients"
          >
            <Users className="w-6 h-6" />
            {isActive('/patients') && (
              <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-white rounded-r" />
            )}
          </button>
          
          <button
            onClick={() => navigate('/tasks')}
            className={`p-3 rounded-lg transition-colors relative ${
              isActive('/tasks') ? 'text-white bg-gray-800' : 'hover:text-white hover:bg-gray-800'
            }`}
            title="Tasks"
            data-testid="nav-tasks"
          >
            <CheckSquare className="w-6 h-6" />
            {isActive('/tasks') && (
              <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-white rounded-r" />
            )}
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className={`flex-1 flex overflow-hidden ${chatOpen ? 'mr-96' : ''}`}>
        <div className="flex-1 overflow-y-auto">
          <Outlet />
        </div>
      </div>

      {/* Chat Sidebar */}
      <ChatSidebar isOpen={chatOpen} onToggle={() => setChatOpen(!chatOpen)} />
    </div>
  );
};

export default Layout;