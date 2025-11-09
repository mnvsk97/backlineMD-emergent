import React from 'react';
import { X, Calendar, DollarSign, FileText, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { Card } from './ui/card';

const ClaimDetailModal = ({ isOpen, onClose, claim }) => {
  if (!isOpen || !claim) return null;

  // Mock claim history/timeline
  const claimHistory = [
    {
      id: 1,
      status: 'Submitted',
      date: claim.submitted_date,
      time: '09:30 AM',
      description: `Claim submitted to ${claim.insurance_provider} for $${claim.amount.toFixed(2)}`,
      icon: FileText,
      color: 'blue'
    },
    {
      id: 2,
      status: 'Received',
      date: '2023-08-16',
      time: '02:15 PM',
      description: 'Claim received and acknowledged by insurance provider',
      icon: CheckCircle,
      color: 'green'
    },
    {
      id: 3,
      status: 'Under Review',
      date: '2023-08-18',
      time: '10:00 AM',
      description: 'Claim is being reviewed by claims department',
      icon: Clock,
      color: 'yellow'
    },
  ];

  // Add current status
  if (claim.status === 'Approved') {
    claimHistory.push({
      id: 4,
      status: 'Approved',
      date: '2023-08-22',
      time: '03:45 PM',
      description: `Claim approved. Payment of $${claim.amount.toFixed(2)} will be processed within 5-7 business days`,
      icon: CheckCircle,
      color: 'green'
    });
  } else if (claim.status === 'Denied') {
    claimHistory.push({
      id: 4,
      status: 'Denied',
      date: '2023-08-22',
      time: '03:45 PM',
      description: 'Claim denied due to insufficient documentation. Additional information required.',
      icon: AlertCircle,
      color: 'red'
    });
  } else if (claim.status === 'Pending') {
    claimHistory.push({
      id: 4,
      status: 'Pending Review',
      date: '2023-08-20',
      time: '11:30 AM',
      description: 'Awaiting additional review from medical team. Expected resolution: 3-5 business days',
      icon: Clock,
      color: 'yellow'
    });
  }

  const getStatusColor = (status) => {
    const colors = {
      'Pending': 'bg-yellow-100 text-yellow-700 border-yellow-300',
      'Approved': 'bg-green-100 text-green-700 border-green-300',
      'Denied': 'bg-red-100 text-red-700 border-red-300',
    };
    return colors[status] || 'bg-gray-100 text-gray-700 border-gray-300';
  };

  const getIconColor = (color) => {
    const colors = {
      'blue': 'bg-blue-100 text-blue-600',
      'green': 'bg-green-100 text-green-600',
      'yellow': 'bg-yellow-100 text-yellow-600',
      'red': 'bg-red-100 text-red-600',
    };
    return colors[color] || 'bg-gray-100 text-gray-600';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between z-10">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Claim Details</h2>
            <p className="text-sm text-gray-500 mt-1">Claim ID: {claim.claim_id}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Claim Overview */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500 mb-1">Patient</p>
              <p className="font-semibold text-gray-900">{claim.patient_name}</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500 mb-1">Insurance Provider</p>
              <p className="font-semibold text-gray-900">{claim.insurance_provider}</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500 mb-1">Claim Amount</p>
              <p className="text-2xl font-bold text-purple-600">${claim.amount.toFixed(2)}</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500 mb-1">Current Status</p>
              <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(claim.status)}`}>
                {claim.status}
              </span>
            </div>
          </div>

          {/* Claim Timeline */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Claim History</h3>
            <div className="space-y-4">
              {claimHistory.map((event, index) => {
                const Icon = event.icon;
                return (
                  <div key={event.id} className="flex gap-4">
                    <div className="flex flex-col items-center">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${getIconColor(event.color)}`}>
                        <Icon className="w-5 h-5" />
                      </div>
                      {index < claimHistory.length - 1 && (
                        <div className="w-0.5 h-12 bg-gray-200 my-1" />
                      )}
                    </div>
                    <div className="flex-1 pb-4">
                      <div className="flex items-center justify-between mb-1">
                        <h4 className="font-semibold text-gray-900">{event.status}</h4>
                        <div className="text-xs text-gray-500">
                          {event.date} • {event.time}
                        </div>
                      </div>
                      <p className="text-sm text-gray-600">{event.description}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Action Required Section */}
          {claim.status === 'Pending' && (
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-yellow-900 mb-1">Action Required</h4>
                  <p className="text-sm text-yellow-800">This claim is awaiting additional review. You can follow up with the insurance provider using the AI Email or AI Call buttons.</p>
                </div>
              </div>
            </div>
          )}

          {claim.status === 'Denied' && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-red-900 mb-1">Claim Denied</h4>
                  <p className="text-sm text-red-800">This claim has been denied. Please review the reason and submit additional documentation or appeal the decision.</p>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4">
          <button
            onClick={onClose}
            className="w-full px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
          >
            Close
          </button>
        </div>
      </Card>
    </div>
  );
};

export default ClaimDetailModal;
