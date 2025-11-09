import React from 'react';
import { NavLink } from 'react-router-dom';
import { Activity, Users, ClipboardList } from 'lucide-react';

const Sidebar = () => {
  const navItems = [
    { path: '/', icon: Activity, label: 'Dashboard' },
    { path: '/patients', icon: Users, label: 'Patients' },
    { path: '/tasks', icon: ClipboardList, label: 'Tasks' },
  ];

  return (
    <div className="w-64 h-screen bg-white border-r border-gray-200 flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <Activity className="w-8 h-8 text-purple-600" />
          <span className="text-xl font-bold text-gray-900">backlineMD</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-purple-50 text-purple-600'
                    : 'text-gray-600 hover:bg-gray-50'
                }`
              }
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </div>
  );
};

export default Sidebar;