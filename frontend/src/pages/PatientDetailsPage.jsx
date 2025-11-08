import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Mail, Phone, Calendar, Activity, FileText, Heart, Ruler, Weight, Droplet, Clock, Plus } from 'lucide-react';
import { Card } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Textarea } from '../components/ui/textarea';
import PhoneCallModal from '../components/PhoneCallModal';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PatientDetailsPage = () => {
  const { patientId } = useParams();
  const navigate = useNavigate();
  const [patient, setPatient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showPhoneModal, setShowPhoneModal] = useState(false);
  const [newNote, setNewNote] = useState('');
  const [savingNote, setSavingNote] = useState(false);

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

  const handleSaveNote = async () => {
    if (!newNote.trim()) {
      toast.error('Please enter a note');
      return;
    }

    setSavingNote(true);
    try {
      await axios.post(`${API}/patients/${patientId}/notes`, {
        patient_id: patientId,
        content: newNote,
        author: 'Dr. James O\'Brien'
      });
      toast.success('Note saved successfully!');
      setNewNote('');
    } catch (error) {
      console.error('Error saving note:', error);
      toast.error('Failed to save note');
    } finally {
      setSavingNote(false);
    }
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-gray-900 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!patient) {
    return (
      <div className="h-full flex flex-col items-center justify-center">
        <p className="text-gray-600 mb-4">Patient not found</p>
        <button
          onClick={() => navigate('/patients')}
          className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800"
        >
          Back to Patients
        </button>
      </div>
    );
  }

  const timeline = [
    { title: 'Initial Consultation', status: 'completed', date: '2024-09-25', description: 'First consultation completed successfully' },
    { title: 'Document Collection', status: 'completed', date: '2024-09-28', description: 'Medical history and insurance documents received' },
    { title: 'Insurance Verification', status: 'in-progress', date: '2024-10-01', description: 'Verifying coverage with insurance provider' },
    { title: 'Treatment Planning', status: 'pending', date: '2024-10-15', description: 'Schedule treatment plan discussion' }
  ];

  const notes = [
    { date: '2024-10-01', author: 'Dr. James O\'Brien', content: 'Patient presented with typical symptoms. Vitals within normal range. BP: 125/80, HR: 68 bpm. Discussed treatment options and next steps.' },
    { date: '2024-09-28', author: 'Nurse Sarah Chen', content: 'Intake completed. All required documents collected. Patient is cooperative and well-informed.' }
  ];

  const activities = [
    { type: 'document', message: 'Medical history document uploaded', time: '2 hours ago' },
    { type: 'insurance', message: 'Insurance verification initiated', time: '5 hours ago' },
    { type: 'appointment', message: 'Follow-up appointment scheduled', time: '1 day ago' },
    { type: 'note', message: 'Clinical note added by Dr. O\'Brien', time: '2 days ago' }
  ];

  const aiSummary = `${patient.age}-year-old ${patient.gender?.toLowerCase()} patient with documented family history of heart disease and elevated cholesterol levels. Currently under ${patient.status.toLowerCase()}. Initial consultation completed with comprehensive medical history review. Patient demonstrates good understanding of treatment options and shows commitment to lifestyle modifications including Mediterranean diet and regular exercise regimen. Recent vitals show stable condition with BP 125/80 and HR 68 bpm. Recommended follow-up in 4-6 weeks to assess progress and adjust treatment plan as needed.`;

  return (
    <div className="h-full overflow-y-auto">
      <PhoneCallModal
        isOpen={showPhoneModal}
        onClose={() => setShowPhoneModal(false)}
        patientName={`${patient.first_name} ${patient.last_name}`}
        patientPhone={patient.phone}
      />

      <header className="border-b border-gray-200 bg-white sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <button onClick={() => navigate('/patients')} className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors mb-4">
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm font-medium">Back to Patients</span>
          </button>

          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              {patient.profile_image ? (
                <img src={patient.profile_image} alt={`${patient.first_name} ${patient.last_name}`} className="w-16 h-16 rounded-full object-cover" />
              ) : (
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center text-xl font-semibold text-gray-600">
                  {patient.first_name[0]}{patient.last_name[0]}
                </div>
              )}
              <div>
                <h1 className="text-2xl font-bold text-gray-900 mb-1">{patient.first_name} {patient.last_name}</h1>
                <div className="flex items-center gap-4 text-sm text-gray-600">
                  <span className="flex items-center gap-1">
                    <Mail className="w-3.5 h-3.5" />
                    {patient.email}
                  </span>
                  <button onClick={() => setShowPhoneModal(true)} className="flex items-center gap-1 hover:text-gray-900 transition-colors" title="Schedule AI Phone Call">
                    <Phone className="w-3.5 h-3.5" />
                    {patient.phone}
                  </button>
                </div>
              </div>
            </div>
            <span className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded text-sm font-medium">{patient.status}</span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-8 py-8">
        <Tabs defaultValue="summary" className="w-full">
          <TabsList className="bg-white border border-gray-200 p-1 rounded-lg mb-6">
            <TabsTrigger value="summary" className="data-[state=active]:bg-gray-900 data-[state=active]:text-white">Summary</TabsTrigger>
            <TabsTrigger value="tasks" className="data-[state=active]:bg-gray-900 data-[state=active]:text-white">Tasks ({patient.tasks_count})</TabsTrigger>
            <TabsTrigger value="appointments" className="data-[state=active]:bg-gray-900 data-[state=active]:text-white">Appointments ({patient.appointments_count})</TabsTrigger>
            <TabsTrigger value="activities" className="data-[state=active]:bg-gray-900 data-[state=active]:text-white">Activities</TabsTrigger>
            <TabsTrigger value="docs" className="data-[state=active]:bg-gray-900 data-[state=active]:text-white">Docs (5)</TabsTrigger>
          </TabsList>

          <TabsContent value="summary" className="space-y-6">
            <Card className="p-6 border border-gray-200 bg-gradient-to-br from-gray-50 to-white">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-gray-900 rounded-lg flex items-center justify-center">
                  <Activity className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">AI-Generated Summary</h3>
                  <p className="text-xs text-gray-500">Powered by Hyperspell + Claude</p>
                </div>
              </div>
              <p className="text-sm text-gray-700 leading-relaxed">{aiSummary}</p>
            </Card>

            <Card className="p-6 border border-gray-200">
              <div className="flex items-center gap-3 mb-6">
                <h3 className="text-lg font-semibold text-gray-900">Patient Information</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <Calendar className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-500">Age / Gender</span>
                  </div>
                  <p className="text-base font-medium text-gray-900 ml-7">{patient.age || 34} years / {patient.gender || 'Male'}</p>
                </div>
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <Weight className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-500">Weight</span>
                  </div>
                  <p className="text-base font-medium text-gray-900 ml-7">175 lbs</p>
                </div>
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <Ruler className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-500">Height</span>
                  </div>
                  <p className="text-base font-medium text-gray-900 ml-7">5'10"</p>
                </div>
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <Droplet className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-500">Blood Type</span>
                  </div>
                  <p className="text-base font-medium text-gray-900 ml-7">O+</p>
                </div>
              </div>
              <div className="mt-6 pt-6 border-t border-gray-200">
                <div className="flex items-center gap-3 mb-3">
                  <Heart className="w-4 h-4 text-gray-900" />
                  <span className="text-sm font-semibold text-gray-900">Pre-conditions</span>
                </div>
                <div className="flex flex-wrap gap-2 ml-7">
                  <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">Family history of heart disease</span>
                  <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">Elevated cholesterol</span>
                </div>
              </div>
            </Card>

            <Card className="p-6 border border-gray-200">
              <div className="flex items-center gap-3 mb-6">
                <Activity className="w-5 h-5 text-gray-900" />
                <h3 className="text-lg font-semibold text-gray-900">Treatment Timeline</h3>
              </div>
              <div className="space-y-6">
                {timeline.map((item, index) => (
                  <div key={index} className="flex gap-4">
                    <div className="flex flex-col items-center">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${item.status === 'completed' ? 'bg-gray-900' : item.status === 'in-progress' ? 'bg-gray-400' : 'bg-gray-200'}`}>
                        {item.status === 'completed' ? (
                          <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                        ) : item.status === 'in-progress' ? <Activity className="w-4 h-4 text-white" /> : <div className="w-2 h-2 bg-gray-400 rounded-full" />}
                      </div>
                      {index < timeline.length - 1 && <div className={`w-0.5 h-12 ${item.status === 'completed' ? 'bg-gray-900' : 'bg-gray-200'}`} />}
                    </div>
                    <div className="flex-1 pb-6">
                      <div className="flex items-center justify-between mb-1">
                        <h4 className="font-medium text-gray-900">{item.title}</h4>
                        <span className="text-xs text-gray-500">{item.date}</span>
                      </div>
                      <p className="text-sm text-gray-600">{item.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="space-y-6">
                <Card className="p-6 border border-gray-200">
                  <div className="flex items-center gap-3 mb-4">
                    <FileText className="w-5 h-5 text-gray-900" />
                    <h3 className="text-base font-semibold text-gray-900">Recent Notes</h3>
                  </div>
                  <div className="space-y-4">
                    {notes.map((note, index) => (
                      <div key={index} className="pb-4 border-b border-gray-200 last:border-0 last:pb-0">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-medium text-gray-900">{note.author}</span>
                          <span className="text-xs text-gray-500">{note.date}</span>
                        </div>
                        <p className="text-sm text-gray-600">{note.content}</p>
                      </div>
                    ))}
                  </div>
                </Card>

                <Card className="p-6 border border-gray-200">
                  <div className="flex items-center gap-3 mb-4">
                    <Plus className="w-5 h-5 text-gray-900" />
                    <h3 className="text-base font-semibold text-gray-900">Create Note</h3>
                  </div>
                  <Textarea value={newNote} onChange={(e) => setNewNote(e.target.value)} placeholder="Add your clinical notes here..." className="min-h-[120px] mb-4" />
                  <button onClick={handleSaveNote} disabled={savingNote || !newNote.trim()} className="w-full py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium">
                    {savingNote ? 'Saving...' : 'Save Note'}
                  </button>
                </Card>
              </div>

              <Card className="p-6 border border-gray-200">
                <div className="flex items-center gap-3 mb-4">
                  <FileText className="w-5 h-5 text-gray-900" />
                  <h3 className="text-base font-semibold text-gray-900">Insurance Status</h3>
                </div>
                <div className="space-y-3">
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Provider</p>
                    <p className="text-sm font-medium text-gray-900">Aetna PPO</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Policy Number</p>
                    <p className="text-sm font-medium text-gray-900">AC-12345-XY</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Coverage Status</p>
                    <span className="inline-block px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs font-medium">Under Review</span>
                  </div>
                  <div className="pt-3 border-t border-gray-200">
                    <p className="text-xs text-gray-600">Last verified: October 1, 2024</p>
                  </div>
                </div>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="tasks">
            <Card className="p-8 text-center border border-gray-200">
              <p className="text-sm text-gray-500">Tasks for this patient will appear here</p>
            </Card>
          </TabsContent>

          <TabsContent value="appointments">
            <Card className="p-8 text-center border border-gray-200">
              <p className="text-sm text-gray-500">Appointments for this patient will appear here</p>
            </Card>
          </TabsContent>

          <TabsContent value="activities">
            <Card className="p-6 border border-gray-200">
              <div className="space-y-4">
                {activities.map((activity, index) => (
                  <div key={index} className="flex items-start gap-3 pb-4 border-b border-gray-200 last:border-0 last:pb-0">
                    <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center flex-shrink-0">
                      <Clock className="w-4 h-4 text-gray-600" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm text-gray-900">{activity.message}</p>
                      <p className="text-xs text-gray-500 mt-1">{activity.time}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="docs">
            <Card className="p-8 text-center border border-gray-200">
              <p className="text-sm text-gray-500">Documents for this patient will appear here</p>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default PatientDetailsPage;
