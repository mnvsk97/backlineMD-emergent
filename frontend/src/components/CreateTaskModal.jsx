import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { X } from 'lucide-react';
import { Card } from './ui/card';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CreateTaskModal = ({ isOpen, onClose, prefilledData = {} }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    assignedTo: '',
    priority: 'medium',
    patientId: '',
    ...prefilledData
  });
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchPatients();
      // Reset form with prefilled data when modal opens
      setFormData({
        name: '',
        description: '',
        assignedTo: '',
        priority: 'medium',
        patientId: '',
        ...prefilledData
      });
    }
  }, [isOpen, prefilledData]);

  const fetchPatients = async () => {
    try {
      const response = await axios.get(`${API}/patients`);
      setPatients(response.data);
    } catch (error) {
      console.error('Error fetching patients:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!formData.name.trim()) {
      toast.error('Task name is required');
      return;
    }
    if (!formData.description.trim()) {
      toast.error('Task description is required');
      return;
    }
    if (!formData.assignedTo) {
      toast.error('Please select who to assign this task to');
      return;
    }
    if (!formData.patientId) {
      toast.error('Please select a patient');
      return;
    }

    setLoading(true);
    try {
      // Create task via API
      await axios.post(`${API}/tasks`, {
        title: formData.name,
        description: formData.description,
        assigned_to: formData.assignedTo,
        priority: formData.priority,
        patient_id: formData.patientId,
        status: 'pending',
        agent_type: formData.assignedTo.includes('AI') ? 'ai_agent' : 'human',
        confidence_score: 1.0,
        waiting_minutes: 0
      });
      
      toast.success('Task created successfully!');
      onClose();
      // Trigger a page refresh or callback to update task list
      window.location.reload();
    } catch (error) {
      console.error('Error creating task:', error);
      toast.error('Failed to create task');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  if (!isOpen) return null;

  const assigneeOptions = [
    { value: '', label: 'Select assignee...' },
    { value: 'Dr. James O\'Brien', label: 'Dr. James O\'Brien' },
    { value: 'Dr. Sarah Chen', label: 'Dr. Sarah Chen' },
    { value: 'Nurse Sarah Chen', label: 'Nurse Sarah Chen' },
    { value: 'AI - Insurance Agent', label: 'AI - Insurance Agent' },
    { value: 'AI - Document Extractor', label: 'AI - Document Extractor' },
    { value: 'AI - Verification Agent', label: 'AI - Verification Agent' },
    { value: 'Back Office Staff', label: 'Back Office Staff' },
  ];

  const priorityOptions = [
    { value: 'urgent', label: 'Urgent', color: 'text-red-600' },
    { value: 'high', label: 'High', color: 'text-orange-600' },
    { value: 'medium', label: 'Medium', color: 'text-blue-600' },
    { value: 'low', label: 'Low', color: 'text-gray-600' },
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between z-10">
          <h2 className="text-xl font-bold text-gray-900">Create New Task</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Task Name */}
          <div>
            <label className="block text-sm font-semibold text-gray-900 mb-2">
              Task Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              placeholder="e.g., Follow up on insurance claim"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-semibold text-gray-900 mb-2">
              Description <span className="text-red-500">*</span>
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => handleChange('description', e.target.value)}
              placeholder="Describe the task in detail..."
              rows={4}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
            />
          </div>

          {/* Patient Selection */}
          <div>
            <label className="block text-sm font-semibold text-gray-900 mb-2">
              Patient <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.patientId}
              onChange={(e) => handleChange('patientId', e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="">Select patient...</option>
              {patients.map((patient) => (
                <option key={patient.patient_id} value={patient.patient_id}>
                  {patient.first_name} {patient.last_name} - {patient.email}
                </option>
              ))}
            </select>
          </div>

          {/* Assign To */}
          <div>
            <label className="block text-sm font-semibold text-gray-900 mb-2">
              Assign To <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.assignedTo}
              onChange={(e) => handleChange('assignedTo', e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              {assigneeOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Priority */}
          <div>
            <label className="block text-sm font-semibold text-gray-900 mb-2">
              Priority <span className="text-red-500">*</span>
            </label>
            <div className="grid grid-cols-4 gap-3">
              {priorityOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => handleChange('priority', option.value)}
                  className={`px-4 py-3 border-2 rounded-lg font-medium transition-all ${
                    formData.priority === option.value
                      ? 'border-purple-600 bg-purple-50 text-purple-700'
                      : 'border-gray-300 hover:border-gray-400 text-gray-700'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-6 py-3 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-6 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating...' : 'Create Task'}
            </button>
          </div>
        </form>
      </Card>
    </div>
  );
};

export default CreateTaskModal;
