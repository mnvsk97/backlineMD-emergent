import React, { useState } from 'react';
import { X, User, Clock, AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { RadioGroup, RadioGroupItem } from './ui/radio-group';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { toast } from 'sonner';

const TaskDetailModal = ({ isOpen, onClose, task, onComplete }) => {
  const [decision, setDecision] = useState('');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);

  if (!task) return null;

  const handleSubmit = async () => {
    if (!decision) {
      toast.error('Please select a decision');
      return;
    }

    setLoading(true);
    try {
      await onComplete(task.task_id, decision, notes);
      toast.success('Task completed successfully!');
      onClose();
      setDecision('');
      setNotes('');
    } catch (error) {
      toast.error('Failed to complete task');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-orange-500" />
            Task Review Required
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6 pt-4">
          {/* Task Header */}
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-semibold text-gray-900 text-lg mb-1">{task.title}</h3>
                <p className="text-sm text-gray-600">{task.patient_name} • {task.agent_type.replace('_', ' ')}</p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-orange-600 mb-1">
                  {Math.round(task.confidence_score * 100)}%
                </div>
                <p className="text-xs text-gray-600">Confidence</p>
              </div>
            </div>
            <p className="text-sm text-gray-700">{task.description}</p>
          </div>

          {/* AI Context */}
          <div>
            <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <User className="w-4 h-4" />
              AI Analysis
            </h4>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-3">
              {Object.entries(task.ai_context).map(([key, value]) => {
                if (key === 'confidence_breakdown' && typeof value === 'object') {
                  return (
                    <div key={key}>
                      <p className="text-sm font-medium text-gray-700 mb-2">Confidence Breakdown:</p>
                      <div className="space-y-2 ml-4">
                        {Object.entries(value).map(([field, score]) => (
                          <div key={field} className="flex items-center justify-between">
                            <span className="text-sm text-gray-600 capitalize">{field.replace('_', ' ')}</span>
                            <div className="flex items-center gap-2">
                              <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                  className={`h-full rounded-full ${
                                    score >= 0.9 ? 'bg-green-500' :
                                    score >= 0.7 ? 'bg-orange-500' :
                                    'bg-red-500'
                                  }`}
                                  style={{ width: `${score * 100}%` }}
                                />
                              </div>
                              <span className="text-sm font-medium w-12 text-right">{Math.round(score * 100)}%</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                }
                if (Array.isArray(value)) {
                  return (
                    <div key={key}>
                      <p className="text-sm font-medium text-gray-700">{key.replace('_', ' ')}:</p>
                      <ul className="list-disc list-inside ml-4 text-sm text-gray-600">
                        {value.map((item, idx) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  );
                }
                return (
                  <div key={key}>
                    <span className="text-sm font-medium text-gray-700">{key.replace('_', ' ')}: </span>
                    <span className="text-sm text-gray-600">{typeof value === 'object' ? JSON.stringify(value) : value}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Suggested Actions */}
          {task.suggested_actions?.length > 0 && (
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Suggested Actions:</h4>
              <ul className="space-y-2">
                {task.suggested_actions.map((action, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
                    <span className="text-blue-600 font-bold">•</span>
                    {action}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Decision Form */}
          <div>
            <h4 className="font-semibold text-gray-900 mb-3">Your Decision:</h4>
            <RadioGroup value={decision} onValueChange={setDecision} className="space-y-3">
              <div className="flex items-center space-x-3 p-3 bg-white rounded-lg border-2 border-gray-200 hover:border-green-500 transition-colors cursor-pointer">
                <RadioGroupItem value="approve" id="approve" />
                <Label htmlFor="approve" className="flex-1 cursor-pointer">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-green-600" />
                    <div>
                      <p className="font-medium text-gray-900">Approve</p>
                      <p className="text-xs text-gray-500">Accept and proceed</p>
                    </div>
                  </div>
                </Label>
              </div>

              <div className="flex items-center space-x-3 p-3 bg-white rounded-lg border-2 border-gray-200 hover:border-orange-500 transition-colors cursor-pointer">
                <RadioGroupItem value="approve_with_followup" id="followup" />
                <Label htmlFor="followup" className="flex-1 cursor-pointer">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-orange-600" />
                    <div>
                      <p className="font-medium text-gray-900">Approve with Follow-up</p>
                      <p className="text-xs text-gray-500">Accept but mark for verification</p>
                    </div>
                  </div>
                </Label>
              </div>

              <div className="flex items-center space-x-3 p-3 bg-white rounded-lg border-2 border-gray-200 hover:border-red-500 transition-colors cursor-pointer">
                <RadioGroupItem value="reject" id="reject" />
                <Label htmlFor="reject" className="flex-1 cursor-pointer">
                  <div className="flex items-center gap-2">
                    <XCircle className="w-5 h-5 text-red-600" />
                    <div>
                      <p className="font-medium text-gray-900">Reject</p>
                      <p className="text-xs text-gray-500">Need more information</p>
                    </div>
                  </div>
                </Label>
              </div>
            </RadioGroup>

            <div className="mt-4">
              <Label htmlFor="notes" className="mb-2 block font-medium text-gray-900">Additional Notes (optional):</Label>
              <Textarea
                id="notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Add any additional context for your decision..."
                className="min-h-[100px]"
              />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4 border-t border-gray-200">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={loading || !decision}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {loading ? 'Processing...' : 'Submit Decision'}
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default TaskDetailModal;