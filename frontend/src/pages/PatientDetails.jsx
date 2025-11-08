import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Mail, Phone, User, Activity, Calendar, FileText, Heart, Ruler, Weight, Droplet, MessageSquare } from 'lucide-react';
import { Card } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PatientDetails = () => {
  const { patientId } = useParams();
  const navigate = useNavigate();
  const [patient, setPatient] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPatient();
  }, [patientId]);

  const fetchPatient = async () => {
    try {
      const response = await axios.get(`${API}/patients/${patientId}`);
      setPatient(response.data);
    } catch (error) {
      console.error('Error fetching patient:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading patient details...</p>
        </div>
      </div>
    );
  }

  if (!patient) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">Patient not found</p>
          <button onClick={() => navigate('/')} className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  // Mock data for timeline and other sections
  const timeline = [
    {
      title: 'Initial Consultation',
      status: 'completed',
      date: '2024-09-25',
      description: 'First consultation completed'
    },
    {
      title: 'Treatment Plan',
      status: 'completed',
      date: '2024-09-30',
      description: 'Mediterranean diet and exercise plan established'
    },
    {
      title: 'Progress Monitoring',
      status: 'in-progress',
      date: '2024-10-15',
      description: 'Regular check-ins and progress tracking'
    },
    {
      title: 'Follow-up Consultation',
      status: 'scheduled',
      date: '2024-11-01',
      description: 'Evaluate progress and adjust treatment if needed'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50 backdrop-blur-sm bg-white/90">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              <span className="font-medium">Back to Patients</span>
            </button>
            <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center gap-2">
              <MessageSquare className="w-4 h-4" />
              Chat about {patient.first_name}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Patient Header */}
        <Card className="p-6 bg-white border border-gray-200 mb-6">
          <div className="flex items-center gap-4">
            <div className="w-20 h-20 bg-gradient-to-br from-blue-100 to-blue-200 rounded-full flex items-center justify-center">
              <User className="w-10 h-10 text-blue-600" />
            </div>
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {patient.first_name} {patient.last_name}
              </h1>
              <div className="flex items-center gap-4 text-gray-600">
                <span className="flex items-center gap-2">
                  <Mail className="w-4 h-4" />
                  {patient.email}
                </span>
                <span className="flex items-center gap-2">
                  <Phone className="w-4 h-4" />
                  {patient.phone}
                </span>
              </div>
            </div>
            <div className="text-right">
              <span className={`px-4 py-2 rounded-full text-sm font-medium ${
                patient.status === 'approved' ? 'bg-green-100 text-green-700' :
                patient.status === 'review' ? 'bg-orange-100 text-orange-700' :
                'bg-blue-100 text-blue-700'
              }`}>
                {patient.status.toUpperCase()}
              </span>
            </div>
          </div>
        </Card>

        {/* Tabs */}
        <Tabs defaultValue="summary" className="w-full">
          <TabsList className="bg-white border border-gray-200 p-1 rounded-lg mb-6">
            <TabsTrigger value="summary" className="data-[state=active]:bg-blue-600 data-[state=active]:text-white">
              Summary
            </TabsTrigger>
            <TabsTrigger value="tasks" className="data-[state=active]:bg-blue-600 data-[state=active]:text-white">
              Tasks ({patient.tasks_count})
            </TabsTrigger>
            <TabsTrigger value="appointments" className="data-[state=active]:bg-blue-600 data-[state=active]:text-white">
              Appointments ({patient.appointments_count})
            </TabsTrigger>
            <TabsTrigger value="docs" className="data-[state=active]:bg-blue-600 data-[state=active]:text-white">
              Docs (5)
            </TabsTrigger>
          </TabsList>

          <TabsContent value="summary" className="space-y-6">
            {/* Patient Information */}
            <Card className="p-6 bg-white border border-gray-200">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                  <User className="w-5 h-5 text-blue-600" />
                </div>
                <h3 className="text-lg font-bold text-gray-900">Patient Information</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <Calendar className="w-5 h-5 text-gray-400" />
                    <span className="text-sm text-gray-600">Age / Gender</span>
                  </div>
                  <p className="text-lg font-semibold text-gray-900 ml-8">
                    {patient.age || 34} years / {patient.gender || 'Male'}
                  </p>
                </div>
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <Weight className="w-5 h-5 text-gray-400" />
                    <span className="text-sm text-gray-600">Weight</span>
                  </div>
                  <p className="text-lg font-semibold text-gray-900 ml-8">175 lbs</p>
                </div>
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <Ruler className="w-5 h-5 text-gray-400" />
                    <span className="text-sm text-gray-600">Height</span>
                  </div>
                  <p className="text-lg font-semibold text-gray-900 ml-8">5'10"</p>
                </div>
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <Droplet className="w-5 h-5 text-gray-400" />
                    <span className="text-sm text-gray-600">Blood Type</span>
                  </div>
                  <p className="text-lg font-semibold text-gray-900 ml-8">O+</p>
                </div>
              </div>
              <div className="mt-6 pt-6 border-t border-gray-200">
                <div className="flex items-center gap-3 mb-3">
                  <Heart className="w-5 h-5 text-red-500" />
                  <span className="text-sm font-semibold text-gray-700">Pre-conditions:</span>
                </div>
                <div className="flex flex-wrap gap-2 ml-8">
                  <span className="px-3 py-1 bg-red-50 text-red-700 rounded-full text-sm">Family history of heart disease</span>
                  <span className="px-3 py-1 bg-orange-50 text-orange-700 rounded-full text-sm">Elevated cholesterol</span>
                </div>
              </div>
            </Card>

            {/* Treatment Timeline */}
            <Card className="p-6 bg-white border border-gray-200">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 bg-purple-50 rounded-lg flex items-center justify-center">
                  <Activity className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900">Treatment Timeline</h3>
                  <p className="text-sm text-gray-500">Patient's treatment progress and upcoming milestones</p>
                </div>
              </div>
              <div className="space-y-6">
                {timeline.map((item, index) => (
                  <div key={index} className="flex gap-4">
                    <div className="flex flex-col items-center">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        item.status === 'completed' ? 'bg-green-500' :
                        item.status === 'in-progress' ? 'bg-blue-500' :
                        'bg-gray-300'
                      }`}>
                        {item.status === 'completed' ? (
                          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                        ) : item.status === 'in-progress' ? (
                          <Activity className="w-5 h-5 text-white animate-pulse" />
                        ) : (
                          <div className="w-3 h-3 bg-white rounded-full" />
                        )}
                      </div>
                      {index < timeline.length - 1 && (
                        <div className={`w-0.5 h-16 ${
                          item.status === 'completed' ? 'bg-green-500' : 'bg-gray-300'
                        }`} />
                      )}
                    </div>
                    <div className="flex-1 pb-8">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold text-gray-900">{item.title}</h4>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          item.status === 'completed' ? 'bg-green-100 text-green-700' :
                          item.status === 'in-progress' ? 'bg-blue-100 text-blue-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {item.status}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-1">{item.description}</p>
                      <p className="text-xs text-gray-500">{item.date}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Two Column Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Last Notes */}
              <Card className="p-6 bg-white border border-gray-200">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                    <FileText className="w-5 h-5 text-blue-600" />
                  </div>
                  <h3 className="text-lg font-bold text-gray-900">Last Consultation Notes</h3>
                </div>
                <div className="space-y-3">
                  <p className="text-sm text-gray-600">2024-10-01 - Dr. James O'Brien</p>
                  <div>
                    <p className="text-sm font-semibold text-gray-900 mb-2">Vitals</p>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>BP: <span className="font-semibold">125/80</span></div>
                      <div>HR: <span className="font-semibold">68 bpm</span></div>
                      <div>Temp: <span className="font-semibold">98.6°F</span></div>
                    </div>
                  </div>
                </div>
              </Card>

              {/* AI Summary */}
              <Card className="p-6 bg-gradient-to-br from-blue-50 to-white border border-blue-200">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                    <Activity className="w-5 h-5 text-white" />
                  </div>
                  <h3 className="text-lg font-bold text-gray-900">AI-Generated Summary</h3>
                </div>
                <p className="text-sm text-gray-700 leading-relaxed">
                  Executive with family history of heart disease. Recent stress test normal, cholesterol slightly elevated (LDL 120mg). 
                  Discussed Mediterranean diet and exercise plan. Enrolled in cardiac prevention program. Wears fitness tracker, 
                  logs 10,000 steps and 30 min cardio 5x/week.
                </p>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="tasks">
            <Card className="p-6 bg-white border border-gray-200">
              <p className="text-gray-600">Tasks for this patient will appear here.</p>
            </Card>
          </TabsContent>

          <TabsContent value="appointments">
            <Card className="p-6 bg-white border border-gray-200">
              <p className="text-gray-600">Appointments for this patient will appear here.</p>
            </Card>
          </TabsContent>

          <TabsContent value="docs">
            <Card className="p-6 bg-white border border-gray-200">
              <p className="text-gray-600">Documents for this patient will appear here.</p>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default PatientDetails;