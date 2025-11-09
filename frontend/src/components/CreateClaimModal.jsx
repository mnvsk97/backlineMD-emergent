'use client';

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { X, DollarSign } from 'lucide-react';
import { Card } from './ui/card';
import { toast } from 'sonner';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001';
const API = `${BACKEND_URL}/api`;

const CreateClaimModal = ({ isOpen, onClose }) => {
  const [formData, setFormData] = useState({
    patientId: '',
    insuranceProvider: '',
    amount: '',
    procedureCode: '',
    diagnosisCode: '',
    serviceDate: '',
    description: ''
  });
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchPatients();
      // Reset form when modal opens
      setFormData({
        patientId: '',
        insuranceProvider: '',
        amount: '',
        procedureCode: '',
        diagnosisCode: '',
        serviceDate: '',
        description: ''
      });
    }
  }, [isOpen]);

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
    if (!formData.patientId) {
      toast.error('Please select a patient');
      return;
    }
    if (!formData.insuranceProvider.trim()) {
      toast.error('Please enter insurance provider');
      return;
    }
    if (!formData.amount || parseFloat(formData.amount) <= 0) {
      toast.error('Please enter a valid claim amount');
      return;
    }
    if (!formData.serviceDate) {
      toast.error('Please select service date');
      return;
    }

    setLoading(true);
    try {
      // Mock API call - replace with actual backend endpoint
      const selectedPatient = patients.find(p => p.patient_id === formData.patientId);
      
      await axios.post(`${API}/claims`, {
        patient_id: formData.patientId,
        patient_name: `${selectedPatient.first_name} ${selectedPatient.last_name}`,
        insurance_provider: formData.insuranceProvider,
        amount: parseFloat(formData.amount),
        procedure_code: formData.procedureCode,
        diagnosis_code: formData.diagnosisCode,
        service_date: formData.serviceDate,
        description: formData.description,
        status: 'Pending',
        submitted_date: new Date().toISOString().split('T')[0]
      });
      
      toast.success('Claim created and submitted successfully!');
      onClose();
      // Trigger refresh
      setTimeout(() => window.location.reload(), 1000);
    } catch (error) {
      console.error('Error creating claim:', error);
      toast.error('Failed to create claim');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
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
      <Card className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between z-10">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Create New Insurance Claim</h2>
            <p className="text-sm text-gray-500 mt-1">Submit a new claim to insurance provider</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
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

          {/* Insurance Provider and Amount Row */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-gray-900 mb-2">
                Insurance Provider <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.insuranceProvider}
                onChange={(e) => handleChange('insuranceProvider', e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                <option value="">Select provider...</option>
                {insuranceProviders.map((provider) => (
                  <option key={provider} value={provider}>
                    {provider}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-900 mb-2">
                Claim Amount <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.amount}
                  onChange={(e) => handleChange('amount', e.target.value)}
                  placeholder="0.00"
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* Procedure Code and Diagnosis Code Row */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-gray-900 mb-2">
                Procedure Code (CPT)
              </label>
              <input
                type="text"
                value={formData.procedureCode}
                onChange={(e) => handleChange('procedureCode', e.target.value)}
                placeholder="e.g., 99213"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-500 mt-1">Optional: CPT procedure code</p>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-900 mb-2">
                Diagnosis Code (ICD-10)
              </label>
              <input
                type="text"
                value={formData.diagnosisCode}
                onChange={(e) => handleChange('diagnosisCode', e.target.value)}
                placeholder="e.g., Z00.00"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-500 mt-1">Optional: ICD-10 diagnosis code</p>
            </div>
          </div>

          {/* Service Date */}
          <div>
            <label className="block text-sm font-semibold text-gray-900 mb-2">
              Service Date <span className="text-red-500">*</span>
            </label>
            <input
              type="date"
              value={formData.serviceDate}
              onChange={(e) => handleChange('serviceDate', e.target.value)}
              max={new Date().toISOString().split('T')[0]}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-semibold text-gray-900 mb-2">
              Service Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => handleChange('description', e.target.value)}
              placeholder="Describe the medical service or procedure..."
              rows={4}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
            />
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
              className="flex-1 px-6 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <DollarSign className="w-4 h-4" />
              {loading ? 'Submitting...' : 'Submit Claim'}
            </button>
          </div>
        </form>
      </Card>
    </div>
  );
};

export default CreateClaimModal;
