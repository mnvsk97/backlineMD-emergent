import React, { useState } from 'react';
import { Plus, User, Bot } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Textarea } from './ui/textarea';
import { toast } from 'sonner';

const CreateTaskModal = ({ isOpen, onClose }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [assignTo, setAssignTo] = useState('ai'); // 'ai' or 'doctor'
  const [priority, setPriority] = useState('medium');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!title.trim() || !description.trim()) {
      toast.error('Please fill in all required fields');
      return;
    }

    setLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      toast.success('Task created successfully!');
      onClose();
      setTitle('');
      setDescription('');
      setAssignTo('ai');
      setPriority('medium');
      setLoading(false);
    }, 1000);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Plus className="w-5 h-5" />
            Create New Task
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 pt-4">
          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">
              Task Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Verify insurance coverage for Emma Watson"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">
              Description <span className="text-red-500">*</span>
            </label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Provide details about what needs to be done..."
              className="min-h-[120px] text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-3">
              Assign To <span className="text-red-500">*</span>
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setAssignTo('ai')}
                className={`p-4 border-2 rounded-lg transition-all ${
                  assignTo === 'ai'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-blue-300'
                }`}
              >
                <div className="flex flex-col items-center gap-2">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                    assignTo === 'ai' ? 'bg-blue-500' : 'bg-gray-200'
                  }`}>
                    <Bot className={`w-6 h-6 ${assignTo === 'ai' ? 'text-white' : 'text-gray-600'}`} />
                  </div>
                  <div className="text-center">
                    <p className="font-medium text-sm text-gray-900">AI Agent</p>
                    <p className="text-xs text-gray-500">Automated processing</p>
                  </div>
                </div>
              </button>

              <button
                onClick={() => setAssignTo('doctor')}
                className={`p-4 border-2 rounded-lg transition-all ${
                  assignTo === 'doctor'
                    ? 'border-purple-500 bg-purple-50'
                    : 'border-gray-200 hover:border-purple-300'
                }`}
              >
                <div className="flex flex-col items-center gap-2">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                    assignTo === 'doctor' ? 'bg-purple-500' : 'bg-gray-200'
                  }`}>
                    <User className={`w-6 h-6 ${assignTo === 'doctor' ? 'text-white' : 'text-gray-600'}`} />
                  </div>
                  <div className="text-center">
                    <p className="font-medium text-sm text-gray-900">Doctor</p>
                    <p className="text-xs text-gray-500">Manual review</p>
                  </div>
                </div>
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">
              Priority
            </label>
            <div className="grid grid-cols-4 gap-2">
              {['low', 'medium', 'high', 'urgent'].map((p) => (
                <button
                  key={p}
                  onClick={() => setPriority(p)}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    priority === p
                      ? p === 'urgent'
                        ? 'bg-red-500 text-white'
                        : p === 'high'
                        ? 'bg-orange-500 text-white'
                        : p === 'medium'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-500 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {p.charAt(0).toUpperCase() + p.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-3 pt-4 border-t border-gray-200">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={loading || !title.trim() || !description.trim()}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {loading ? 'Creating...' : 'Create Task'}
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default CreateTaskModal;
