import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { User, Mail, Phone, Clock, AlertCircle } from 'lucide-react';
import { Card } from '../components/ui/card';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PatientsPage = () => {
  const navigate = useNavigate();
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

  const getStatusBadge = (status) => {
    const badges = {
      intake: { bg: 'bg-gray-100', text: 'text-gray-700' },
      processing: { bg: 'bg-gray-100', text: 'text-gray-700' },
      review: { bg: 'bg-gray-100', text: 'text-gray-700' },
      approved: { bg: 'bg-gray-100', text: 'text-gray-700' },
      scheduled: { bg: 'bg-gray-100', text: 'text-gray-700' }
    };
    return badges[status] || badges.intake;
  };

  return (
    <div className="h-full">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Patients</h1>
            <p className="text-sm text-gray-500 mt-1">Manage and view all patient information</p>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-8 py-8">
        {loading ? (
          <div className="flex items-center justify-center py-24">
            <div className="w-8 h-8 border-2 border-gray-900 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : patients.length === 0 ? (
          <Card className="p-12 text-center border border-gray-200">
            <User className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-sm text-gray-500">No patients found</p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {patients.map((patient) => {
              const badge = getStatusBadge(patient.status);
              return (
                <Card
                  key={patient.patient_id}
                  className="p-5 border border-gray-200 hover:border-gray-900 transition-all cursor-pointer group"
                  onClick={() => navigate(`/patients/${patient.patient_id}`)}
                  data-testid={`patient-card-${patient.patient_id}`}
                >
                  <div className="flex items-start gap-4">
                    {patient.profile_image ? (
                      <img
                        src={patient.profile_image}
                        alt={`${patient.first_name} ${patient.last_name}`}
                        className="w-12 h-12 rounded-full object-cover flex-shrink-0"
                      />
                    ) : (
                      <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center flex-shrink-0 text-sm font-semibold text-gray-600">
                        {patient.first_name[0]}{patient.last_name[0]}
                      </div>
                    )}
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-semibold text-gray-900 text-base">
                          {patient.first_name} {patient.last_name}
                        </h3>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${badge.bg} ${badge.text}`}>
                          {patient.status}
                        </span>
                      </div>
                      
                      <div className="space-y-1 text-sm text-gray-600">
                        <div className="flex items-center gap-2">
                          <Mail className="w-3.5 h-3.5" />
                          <span className="truncate">{patient.email}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Phone className="w-3.5 h-3.5" />
                          <span>{patient.phone}</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                        <span>{patient.tasks_count} task(s)</span>
                        <span>{patient.appointments_count} appointment(s)</span>
                        {patient.flagged_items > 0 && (
                          <span className="flex items-center gap-1 text-gray-700">
                            <AlertCircle className="w-3 h-3" />
                            {patient.flagged_items} flagged
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
};

export default PatientsPage;