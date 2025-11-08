import React, { useState } from 'react';
import { X, Phone } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Textarea } from './ui/textarea';
import { toast } from 'sonner';

const PhoneCallModal = ({ isOpen, onClose, patientName, patientPhone }) => {
  const [callIntent, setCallIntent] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);

  const handleScheduleCall = async () => {
    if (!callIntent.trim()) {
      toast.error('Please provide the call intent');
      return;
    }

    setLoading(true);
    
    setTimeout(() => {
      toast.success('AI phone call task created successfully!');
      onClose();
      setCallIntent('');
      setDescription('');
      setLoading(false);
    }, 1000);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Phone className="w-5 h-5" />
            Schedule AI Phone Call
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4 pt-4">
          <div>
            <p className="text-sm text-gray-600 mb-4">
              Create an AI-powered phone call task for <span className="font-semibold">{patientName}</span>
            </p>
            <p className="text-xs text-gray-500 mb-4">Phone: {patientPhone}</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">
              Call Intent <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={callIntent}
              onChange={(e) => setCallIntent(e.target.value)}
              placeholder="e.g., Follow-up on lab results, Schedule appointment"
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">
              Additional Details (Optional)
            </label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Provide any additional context for the AI assistant..."
              className="min-h-[100px] text-sm"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
            >
              Cancel
            </button>
            <button
              onClick={handleScheduleCall}
              disabled={loading || !callIntent.trim()}
              className="flex-1 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {loading ? 'Scheduling...' : 'Schedule Call'}
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default PhoneCallModal;
