'use client';

import React, { useState, useEffect } from 'react';
import { X, Shield } from 'lucide-react';
import { Card } from './ui/card';
import { toast } from 'sonner';
import { apiService } from '../services/api';

const InsuranceDetailsModal = ({ isOpen, onClose, patientId, patient, onSuccess }) => {
  const [formData, setFormData] = useState({
    insurance_provider: '',
    insurance_policy_number: '',
    insurance_group_number: '',
    insurance_effective_date: '',
    insurance_expiry_date: ''
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && patient) {
      // Pre-fill form with existing insurance data
      const insurance = patient.insurance || {};
      setFormData({
        insurance_provider: insurance.provider || '',
        insurance_policy_number: insurance.policy_number || '',
        insurance_group_number: insurance.group_number || '',
        insurance_effective_date: insurance.effective_date || '',
        insurance_expiry_date: insurance.expiry_date || ''
      });
    }
  }, [isOpen, patient]);

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!formData.insurance_provider.trim()) {
      toast.error('Please enter insurance provider');
      return;
    }

    setLoading(true);
    try {
      await apiService.updatePatient(patientId, {
        insurance_provider: formData.insurance_provider,
        insurance_policy_number: formData.insurance_policy_number || null,
        insurance_group_number: formData.insurance_group_number || null,
        insurance_effective_date: formData.insurance_effective_date || null,
        insurance_expiry_date: formData.insurance_expiry_date || null
      });
      
      toast.success('Insurance details updated successfully!');
      onClose();
      if (onSuccess) {
        onSuccess();
      }
    } catch (error) {
      console.error('Error updating insurance details:', error);
      toast.error(error.response?.data?.detail || 'Failed to update insurance details');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const insuranceProviders = [
    'Blue Shield',
    'Aetna',
    'UnitedHealthcare',
    'Cigna',
    'Humana',
    'Kaiser Permanente',
    'Medicare',
    'Medicaid',
    'Other'
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <Shield className="w-5 h-5 text-purple-600" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900">Insurance Details</h2>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Insurance Provider <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.insurance_provider}
                onChange={(e) => handleChange('insurance_provider', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                required
              >
                <option value="">Select provider</option>
                {insuranceProviders.map(provider => (
                  <option key={provider} value={provider}>{provider}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Policy Number
              </label>
              <input
                type="text"
                value={formData.insurance_policy_number}
                onChange={(e) => handleChange('insurance_policy_number', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                placeholder="Enter policy number"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Group Number
              </label>
              <input
                type="text"
                value={formData.insurance_group_number}
                onChange={(e) => handleChange('insurance_group_number', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                placeholder="Enter group number"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Effective Date
                </label>
                <input
                  type="date"
                  value={formData.insurance_effective_date}
                  onChange={(e) => handleChange('insurance_effective_date', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Expiry Date
                </label>
                <input
                  type="date"
                  value={formData.insurance_expiry_date}
                  onChange={(e) => handleChange('insurance_expiry_date', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-sm font-medium text-white bg-purple-600 rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                disabled={loading}
              >
                {loading ? 'Saving...' : 'Save Insurance Details'}
              </button>
            </div>
          </form>
        </div>
      </Card>
    </div>
  );
};

export default InsuranceDetailsModal;

