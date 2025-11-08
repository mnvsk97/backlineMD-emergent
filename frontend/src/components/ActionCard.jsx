import React from 'react';
import { User, Clock, AlertTriangle } from 'lucide-react';
import { Card } from './ui/card';

const ActionCard = ({ task, onClick }) => {
  const getPriorityBadge = (priority) => {
    const badges = {
      urgent: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
      high: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' },
      medium: { bg: 'bg-gray-100', text: 'text-gray-700', border: 'border-gray-200' },
      low: { bg: 'bg-gray-50', text: 'text-gray-600', border: 'border-gray-200' }
    };
    return badges[priority] || badges.medium;
  };

  const getConfidenceBadge = (score) => {
    if (score >= 0.9) return { bg: 'bg-gray-100', text: 'text-gray-700' };
    if (score >= 0.7) return { bg: 'bg-gray-100', text: 'text-gray-700' };
    return { bg: 'bg-gray-100', text: 'text-gray-700' };
  };

  const badge = getPriorityBadge(task.priority);
  const confidence = getConfidenceBadge(task.confidence_score);

  return (
    <Card
      className="min-w-[300px] p-4 cursor-pointer hover:shadow-md transition-all border border-gray-200 bg-white"
      onClick={onClick}
      data-testid={`action-card-${task.task_id}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
            <User className="w-4 h-4 text-gray-600" />
          </div>
          <div>
            <p className="font-medium text-gray-900 text-sm">{task.patient_name}</p>
            <p className="text-xs text-gray-500">{task.agent_type.replace('_', ' ')}</p>
          </div>
        </div>
      </div>

      {/* Title */}
      <h3 className="font-medium text-gray-900 mb-3 text-sm line-clamp-2">{task.title}</h3>

      {/* Tags */}
      <div className="flex items-center gap-2 mb-3">
        <span className={`px-2 py-1 rounded text-xs font-medium ${confidence.bg} ${confidence.text}`}>
          {Math.round(task.confidence_score * 100)}% confidence
        </span>
        <span className={`px-2 py-1 rounded text-xs font-medium border ${badge.bg} ${badge.text} ${badge.border}`}>
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
          <div className="flex items-center gap-1 text-gray-600">
            <AlertTriangle className="w-3 h-3" />
            <span>Needs review</span>
          </div>
        )}
      </div>
    </Card>
  );
};

export default ActionCard;