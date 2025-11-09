import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Mail, Phone, Flag } from 'lucide-react';
import { Card } from '../components/ui/card';
import { useChat, useCopilotContext } from '../context/ChatContext';
import Header from '../components/Header';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PatientsPage = () => {
  const navigate = useNavigate();
  const { openChat } = useChat();
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    try {
      const response = await axios.get(`${API}/patients`);
      setPatients(response.data);
    } catch (error) {
      console.error('Error fetching patients:', error);
    } finally {
      setLoading(false);
    }
  };

  // Provide all patients context to CopilotKit
  useCopilotContext({
    page: 'patients',
    patients: patients,
    count: patients.length,
    summary: `Patient list page showing ${patients.length} patients with their details, status, and task counts.`
  }, 'All patients list with complete information');

  const getStatusColor = (status) => {
    const colors = {
      'Processing': 'bg-yellow-100 text-yellow-700',
      'Approved': 'bg-green-100 text-green-700',
      'Active': 'bg-blue-100 text-blue-700',
      'Pending': 'bg-gray-100 text-gray-700',
    };
    return colors[status] || 'bg-gray-100 text-gray-700';
  };

  return (
    <div className="flex-1 h-screen overflow-hidden flex flex-col">
      <Header 
        title="Patients" 
        subtitle="Manage and view all patient information"
      />
      
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto px-8 py-8">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-6 h-6 border-2 border-purple-600 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <div className="space-y-4">
              {patients.map((patient) => (
                <Card
                  key={patient.patient_id}
                  onClick={() => navigate(`/patients/${patient.patient_id}`)}
                  className="p-6 hover:shadow-lg transition-all cursor-pointer bg-white border border-gray-200"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-4 flex-1">
                      {patient.profile_image ? (
                        <img 
                          src={patient.profile_image} 
                          alt={`${patient.first_name} ${patient.last_name}`}
                          className="w-14 h-14 rounded-full object-cover"
                        />
                      ) : (
                        <div className="w-14 h-14 bg-purple-100 rounded-full flex items-center justify-center text-xl font-semibold text-purple-600">
                          {patient.first_name[0]}{patient.last_name[0]}
                        </div>
                      )}
                      
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900 mb-1">
                          {patient.first_name} {patient.last_name}
                        </h3>
                        
                        <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
                          <span className="flex items-center gap-1">
                            <Mail className="w-4 h-4" />
                            {patient.email}
                          </span>
                          <span className="flex items-center gap-1">
                            <Phone className="w-4 h-4" />
                            {patient.phone}
                          </span>
                        </div>

                        <div className="flex items-center gap-4 text-sm">
                          <span className="text-purple-600">{patient.tasks_count} task(s)</span>
                          <span className="text-blue-600">{patient.appointments_count} appointment(s)</span>
                          {patient.flagged_count > 0 && (
                            <span className="flex items-center gap-1 text-yellow-600">
                              <Flag className="w-4 h-4" />
                              {patient.flagged_count} flagged
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(patient.status)}`}>
                      {patient.status}
                    </span>
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

export default PatientsPage;