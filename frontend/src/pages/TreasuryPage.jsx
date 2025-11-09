import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { DollarSign, Mail, Phone, Calendar, CheckCircle, XCircle, Clock } from 'lucide-react';
import { Card } from '../components/ui/card';
import { useChat, useCopilotContext } from '../context/ChatContext';
import Header from '../components/Header';
import CreateTaskModal from '../components/CreateTaskModal';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TreasuryPage = () => {
  const { openChat } = useChat();
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [taskModalData, setTaskModalData] = useState({});

  useEffect(() => {
    fetchClaims();
    const interval = setInterval(fetchClaims, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchClaims = async () => {
    try {
      // Mock data for now - replace with actual API call
      const mockClaims = [
        {
          claim_id: 'C12345',
          patient_id: 'P78901',
          patient_name: 'Jane Doe',
          insurance_provider: 'Blue Shield',
          amount: 2500.00,
          status: 'Pending',
          submitted_date: '2023-08-15',
        },
        {
          claim_id: 'C67890',
          patient_id: 'P65432',
          patient_name: 'John Smith',
          insurance_provider: 'Aetna',
          amount: 1800.00,
          status: 'Approved',
          submitted_date: '2023-08-12',
        },
        {
          claim_id: 'C54321',
          patient_id: 'P54321',
          patient_name: 'Emily Carter',
          insurance_provider: 'UnitedHealthcare',
          amount: 3200.00,
          status: 'Denied',
          submitted_date: '2023-08-10',
        },
      ];
      setClaims(mockClaims);
    } catch (error) {
      console.error('Error fetching claims:', error);
    } finally {
      setLoading(false);
    }
  };

  // Provide all claims context to CopilotKit
  useCopilotContext({
    page: 'treasury',
    claims: claims,
    count: claims.length,
    filters: ['all', 'pending', 'approved', 'denied'],
    summary: `Treasury claims page showing ${claims.length} insurance claims with various statuses.`
  }, 'All insurance claims with details, amounts, and patient information');

  const filteredClaims = claims.filter(claim => {
    if (filter === 'all') return true;
    return claim.status.toLowerCase() === filter.toLowerCase();
  });

  const filters = [
    { value: 'all', label: 'All', count: claims.length },
    { value: 'pending', label: 'Pending', count: claims.filter(c => c.status === 'Pending').length },
    { value: 'approved', label: 'Approved', count: claims.filter(c => c.status === 'Approved').length },
    { value: 'denied', label: 'Denied', count: claims.filter(c => c.status === 'Denied').length },
  ];

  const getStatusColor = (status) => {
    const colors = {
      'Pending': 'bg-yellow-100 text-yellow-700',
      'Approved': 'bg-green-100 text-green-700',
      'Denied': 'bg-red-100 text-red-700',
    };
    return colors[status] || 'bg-gray-100 text-gray-700';
  };

  return (
    <div className="flex-1 h-screen overflow-hidden flex flex-col">
      <Header 
        title="Treasury Claims" 
        subtitle="Manage insurance claims and billing"
      />
      
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto px-8 py-8">
          {/* Filter Tabs */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2 bg-white border border-gray-200 p-1 rounded-lg">
              {filters.map((f) => (
                <button
                  key={f.value}
                  onClick={() => setFilter(f.value)}
                  className={`px-4 py-2 rounded-md transition-colors font-medium text-sm ${
                    filter === f.value
                      ? 'bg-purple-600 text-white'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  {f.label} ({f.count})
                </button>
              ))}
            </div>
            
            <button className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium flex items-center gap-2">
              <DollarSign className="w-4 h-4" />
              Create New Claim
            </button>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-6 h-6 border-2 border-purple-600 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : filteredClaims.length === 0 ? (
            <Card className="p-12 text-center border border-gray-200">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-base font-medium text-gray-900 mb-2">No claims found</h3>
              <p className="text-sm text-gray-500">No claims match the current filter</p>
            </Card>
          ) : (
            <div className="space-y-4">
              {filteredClaims.map((claim) => (
                <Card
                  key={claim.claim_id}
                  className="p-6 border-l-4 border-purple-400 hover:border-purple-500 bg-white hover:shadow-lg transition-all cursor-pointer"
                  onClick={openChat}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-6 flex-1">
                      {/* Patient Avatar */}
                      <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <span className="text-purple-600 font-semibold">
                          {claim.patient_name.split(' ').map(n => n[0]).join('')}
                        </span>
                      </div>
                      
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="font-semibold text-gray-900 text-lg">{claim.patient_name}</h3>
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(claim.status)}`}>
                            {claim.status}
                          </span>
                        </div>
                        
                        <div className="flex items-center gap-6 text-sm text-gray-600 mb-3">
                          <span className="flex items-center gap-1">
                            <DollarSign className="w-4 h-4" />
                            Claim ID: {claim.claim_id}
                          </span>
                          <span>Insurance: {claim.insurance_provider}</span>
                          <span className="flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            Submitted: {claim.submitted_date}
                          </span>
                        </div>

                        <div className="flex items-center gap-3">
                          <span className="text-2xl font-bold text-purple-600">
                            ${claim.amount.toFixed(2)}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <button 
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center gap-2"
                        onClick={(e) => {
                          e.stopPropagation();
                          openChat();
                        }}
                      >
                        <Mail className="w-4 h-4" />
                        AI Email
                      </button>
                      <button 
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium flex items-center gap-2"
                        onClick={(e) => {
                          e.stopPropagation();
                          openChat();
                        }}
                      >
                        <Phone className="w-4 h-4" />
                        AI Call
                      </button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TreasuryPage;
