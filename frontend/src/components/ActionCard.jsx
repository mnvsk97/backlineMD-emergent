import React from 'react';
import { User, Clock, AlertTriangle } from 'lucide-react';
import { Card } from './ui/card';

const ActionCard = ({ task, onClick }) => {
  const getPriorityColor = (priority) => {
    const colors = {
      urgent: 'bg-red-100 text-red-700 border-red-200',
      high: 'bg-orange-100 text-orange-700 border-orange-200',
      medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
      low: 'bg-blue-100 text-blue-700 border-blue-200'
    };
    return colors[priority] || colors.medium;
  };

  const getConfidenceColor = (score) => {
    if (score >= 0.9) return 'text-green-600 bg-green-50';
    if (score >= 0.7) return 'text-orange-600 bg-orange-50';
    return 'text-red-600 bg-red-50';
  };

  return (
    <Card
      className="min-w-[320px] p-4 cursor-pointer hover:shadow-lg transition-all border-2 border-gray-200 hover:border-blue-400"
      onClick={onClick}
      data-testid={`action-card-${task.task_id}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
            <User className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <p className="font-semibold text-gray-900 text-sm">{task.patient_name}</p>
            <p className="text-xs text-gray-500">{task.agent_type.replace('_', ' ')}</p>
          </div>
        </div>
        <div className={`w-2 h-2 rounded-full ${task.status === 'awaiting_approval' ? 'bg-orange-500 animate-pulse' : 'bg-gray-300'}`} />
      </div>

      {/* Title */}
      <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">{task.title}</h3>

      {/* Confidence Badge */}
      <div className="flex items-center justify-between mb-3">
        <div className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(task.confidence_score)}`}>
          {Math.round(task.confidence_score * 100)}% confidence
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getPriorityColor(task.priority)}`}>
          {task.priority}
        </span>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          <span>{task.waiting_minutes}m ago</span>
        </div>
        {task.confidence_score < 0.9 && (
          <div className="flex items-center gap-1 text-orange-600">
            <AlertTriangle className="w-3 h-3" />
            <span>Needs review</span>
          </div>
        )}
      </div>
    </Card>
  );
};

export default ActionCard;