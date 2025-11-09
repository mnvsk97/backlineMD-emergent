import React, { useState } from 'react';
import { X, Mail, FileText } from 'lucide-react';
import { Card } from './ui/card';
import { toast } from 'sonner';

const SendFormsModal = ({ isOpen, onClose, patientEmail, availableForms = [] }) => {
  const [selectedForms, setSelectedForms] = useState([]);
  const [sending, setSending] = useState(false);

  const handleToggleForm = (formId) => {
    setSelectedForms(prev => 
      prev.includes(formId) 
        ? prev.filter(id => id !== formId)
        : [...prev, formId]
    );
  };

  const handleSendForms = async () => {
    if (selectedForms.length === 0) {
      toast.error('Please select at least one form to send');
      return;
    }

    setSending(true);
    try {
      // Mock API call - replace with actual DocuSign/email integration
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      toast.success(`${selectedForms.length} form(s) sent to ${patientEmail} via DocuSign`);
      onClose();
      setSelectedForms([]);
      
      // Trigger refresh
      setTimeout(() => window.location.reload(), 1000);
    } catch (error) {
      console.error('Error sending forms:', error);
      toast.error('Failed to send forms');
    } finally {
      setSending(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between z-10">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Send Consent Forms</h2>
            <p className="text-sm text-gray-500 mt-1">Select forms to send to {patientEmail}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          {availableForms.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">No forms available</p>
            </div>
          ) : (
            availableForms.map((form) => (
              <label
                key={form.id}
                className={`flex items-start gap-4 p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  selectedForms.includes(form.id)
                    ? 'border-purple-500 bg-purple-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <input
                  type="checkbox"
                  checked={selectedForms.includes(form.id)}
                  onChange={() => handleToggleForm(form.id)}
                  className="mt-1 w-5 h-5 text-purple-600 rounded focus:ring-2 focus:ring-purple-500"
                />
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">{form.name}</h3>
                  <p className="text-sm text-gray-600 mt-1">{form.description}</p>
                  <p className="text-xs text-gray-500 mt-2">Required for: {form.purpose}</p>
                </div>
              </label>
            ))
          )}
        </div>

        <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-6 py-3 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSendForms}
            disabled={sending || selectedForms.length === 0}
            className="flex-1 px-6 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <Mail className="w-4 h-4" />
            {sending ? 'Sending...' : `Send ${selectedForms.length > 0 ? selectedForms.length : ''} Form${selectedForms.length !== 1 ? 's' : ''}`}
          </button>
        </div>
      </Card>
    </div>
  );
};

export default SendFormsModal;
