'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { ArrowLeft, Mail, Phone, Calendar, Activity, FileText, Heart, Ruler, Weight, Droplet, Clock, Plus, Send, CheckCircle, XCircle, AlertCircle, RefreshCw, User, Bot } from 'lucide-react';
import { Card } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Textarea } from '../components/ui/textarea';
import { useChat, useCopilotContext } from '../context/ChatContext';
import { toast } from 'sonner';
import Header from '../components/Header';
import SendFormsModal from '../components/SendFormsModal';
import CreateClaimModal from '../components/CreateClaimModal';
import CreateTaskModal from '../components/CreateTaskModal';
import InsuranceDetailsModal from '../components/InsuranceDetailsModal';
import { apiService } from '../services/api';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001';
const API = `${BACKEND_URL}/api`;

const PatientDetailsPage = ({ params }) => {
  const patientId = params?.patientId;
  const router = useRouter();
  const { openChat } = useChat();
  const [patient, setPatient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [newNote, setNewNote] = useState('');
  const [savingNote, setSavingNote] = useState(false);
  const [showSendFormsModal, setShowSendFormsModal] = useState(false);
  const [patientSummary, setPatientSummary] = useState(null);
  const [patientTasks, setPatientTasks] = useState([]);
  const [patientAppointments, setPatientAppointments] = useState([]);
  const [patientDocuments, setPatientDocuments] = useState([]);
  const [patientNotes, setPatientNotes] = useState([]);
  const [patientActivities, setPatientActivities] = useState([]);
  const [documentsSummary, setDocumentsSummary] = useState(null);
  const [regeneratingSummary, setRegeneratingSummary] = useState(false);
  const [patientClaims, setPatientClaims] = useState([]);
  const [showClaimModal, setShowClaimModal] = useState(false);
  const [showInsuranceModal, setShowInsuranceModal] = useState(false);
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [taskModalPrefilledData, setTaskModalPrefilledData] = useState({});

  useEffect(() => {
    if (patientId) {
      fetchPatientData();
    }
  }, [patientId]);

  const fetchPatientData = async () => {
    setLoading(true);
    try {
      // Fetch all patient-related data in parallel
      const [patientRes, summaryRes, tasksRes, appointmentsRes, documentsRes, notesRes, activitiesRes, docsSummaryRes, claimsRes] = await Promise.allSettled([
        axios.get(`${API}/patients/${patientId}`),
        apiService.getPatientSummary(patientId).catch(() => null),
        apiService.getTasks({ patient_id: patientId }).catch(() => ({ data: [] })),
        apiService.getAppointments({ patient_id: patientId }).catch(() => ({ data: [] })),
        apiService.getDocuments({ patient_id: patientId }).catch(() => ({ data: [] })),
        apiService.getPatientNotes(patientId).catch(() => ({ data: [] })),
        apiService.getPatientActivities(patientId).catch(() => ({ data: [] })),
        apiService.getDocumentsSummary(patientId).catch(() => null),
        apiService.getClaims({ patient_id: patientId }).catch(() => ({ data: [] })),
      ]);

      if (patientRes.status === 'fulfilled') {
        setPatient(patientRes.value.data);
      }

      if (summaryRes.status === 'fulfilled' && summaryRes.value) {
        setPatientSummary(summaryRes.value.data);
      }

      if (tasksRes.status === 'fulfilled') {
        setPatientTasks(tasksRes.value.data || []);
      }

      if (appointmentsRes.status === 'fulfilled') {
        setPatientAppointments(appointmentsRes.value.data || []);
      }

      if (documentsRes.status === 'fulfilled') {
        setPatientDocuments(documentsRes.value.data || []);
      }

      if (notesRes.status === 'fulfilled') {
        setPatientNotes(notesRes.value.data || []);
      }

      if (activitiesRes.status === 'fulfilled') {
        setPatientActivities(activitiesRes.value.data || []);
      }

      if (docsSummaryRes.status === 'fulfilled' && docsSummaryRes.value) {
        setDocumentsSummary(docsSummaryRes.value.data);
      }

      if (claimsRes.status === 'fulfilled') {
        setPatientClaims(claimsRes.value.data || []);
      }
    } catch (error) {
      console.error('Error fetching patient data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Provide comprehensive patient context to CopilotKit
  useCopilotContext(patient ? {
    page: 'patient_details',
    pageType: 'patient_detail',
    patient: {
      id: patient.patient_id,
      name: `${patient.first_name} ${patient.last_name}`,
      email: patient.email,
      phone: patient.phone,
      status: patient.status,
      age: patient.age,
      gender: patient.gender,
      dateOfBirth: patient.date_of_birth,
      address: patient.address,
    },
    summary: patientSummary || `Patient ${patient.first_name} ${patient.last_name} is currently in ${patient.status} status.`,
    tasks: patientTasks.map(t => ({
      id: t.task_id,
      title: t.title,
      description: t.description,
      status: t.status,
      priority: t.priority,
      agentType: t.agent_type,
      confidenceScore: t.confidence_score,
    })),
    appointments: patientAppointments.map(a => ({
      id: a.appointment_id,
      date: a.starts_at || a.date,
      type: a.appointment_type || a.type,
      status: a.status,
    })),
    documents: patientDocuments.map(d => ({
      id: d.document_id,
      kind: d.kind,
      title: d.title,
      uploadedAt: d.uploaded_at,
    })),
    notes: patientNotes.map(n => ({
      date: n.date || n.created_at,
      author: n.author,
      content: n.content,
    })),
    statistics: {
      totalTasks: patientTasks.length,
      totalAppointments: patientAppointments.length,
      totalDocuments: patientDocuments.length,
      totalNotes: patientNotes.length,
      pendingTasks: patientTasks.filter(t => t.status === 'pending').length,
      urgentTasks: patientTasks.filter(t => t.priority === 'urgent').length,
    },
    fullSummary: `Patient ${patient.first_name} ${patient.last_name} (${patient.age} years old, ${patient.gender}) is in ${patient.status} status. Has ${patientTasks.length} tasks (${patientTasks.filter(t => t.priority === 'urgent').length} urgent), ${patientAppointments.length} appointments, ${patientDocuments.length} documents, and ${patientNotes.length} clinical notes.`
  } : null, 'Complete patient details including all medical information, tasks, appointments, documents, notes, and summary');

  const handleSaveNote = async () => {
    if (!newNote.trim()) {
      toast.error('Please enter a note');
      return;
    }

    setSavingNote(true);
    try {
      await apiService.createPatientNote(patientId, {
        content: newNote,
        author: "Dr. James O'Brien"
      });
      toast.success('Note saved successfully!');
      setNewNote('');
      // Refresh patient data to include new note
      fetchPatientData();
    } catch (error) {
      console.error('Error saving note:', error);
      toast.error('Failed to save note');
    } finally {
      setSavingNote(false);
    }
  };

  const handleRegenerateSummary = async () => {
    setRegeneratingSummary(true);
    try {
      const response = await apiService.regeneratePatientSummary(patientId);
      setPatientSummary(response.data);
      toast.success('Summary regenerated successfully!');
      // Refresh patient data
      fetchPatientData();
    } catch (error) {
      console.error('Error regenerating summary:', error);
      toast.error('Failed to regenerate summary');
    } finally {
      setRegeneratingSummary(false);
    }
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-purple-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!patient) {
    return (
      <div className="h-full flex flex-col items-center justify-center">
        <p className="text-gray-600 mb-4">Patient not found</p>
        <button
          onClick={() => router.push('/patients')}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
        >
          Back to Patients
        </button>
      </div>
    );
  }

  // Standard treatment timeline stages - always shown for all patients
  const standardTimelineStages = [
    {
      title: 'Initial Consultation',
      description: 'Patient intake and initial medical assessment',
      stage: 1
    },
    {
      title: 'Medical History Review',
      description: 'Comprehensive review of patient medical history and records',
      stage: 2
    },
    {
      title: 'Diagnostic Tests',
      description: 'Order and review diagnostic tests and lab results',
      stage: 3
    },
    {
      title: 'Treatment Plan Development',
      description: 'Create personalized treatment plan based on diagnosis',
      stage: 4
    },
    {
      title: 'Insurance Verification',
      description: 'Verify insurance coverage and submit claims',
      stage: 5
    },
    {
      title: 'Follow-up Appointment',
      description: 'Schedule and conduct follow-up consultation',
      stage: 6
    },
    {
      title: 'Treatment Monitoring',
      description: 'Monitor patient progress and adjust treatment as needed',
      stage: 7
    }
  ];

  // Build timeline from activities
  const activityTimeline = patientActivities
    .filter(a => a.type === 'appointment' || a.type === 'task')
    .map(activity => {
      const date = activity.created_at ? new Date(activity.created_at).toISOString().split('T')[0] : '';
      return {
        title: activity.title,
        status: activity.status === 'completed' || activity.status === 'done' ? 'completed' :
                activity.status === 'in_progress' || activity.status === 'scheduled' ? 'in-progress' : 'pending',
        date: date,
        description: activity.description || activity.title,
        isActivity: true
      };
    })
    .sort((a, b) => new Date(b.date) - new Date(a.date));

  // Determine which standard stages are completed based on activities
  // For new patients, start from stage 1 (pending)
  const patientCreatedDate = patient?.created_at ? new Date(patient.created_at) : new Date();
  const hasActivities = activityTimeline.length > 0;
  
  // Map standard stages with status based on activities
  const timeline = standardTimelineStages.map((stage, index) => {
    // For new patients with no activities, only first stage is in-progress
    if (!hasActivities) {
      return {
        ...stage,
        status: index === 0 ? 'in-progress' : 'pending',
        date: index === 0 ? patientCreatedDate.toISOString().split('T')[0] : '',
        isStandard: true
      };
    }
    
    // For patients with activities, determine status based on stage progression
    // Simple logic: if we have activities, mark stages as completed up to a certain point
    // This is a simplified version - you can enhance this based on actual activity matching
    const completedStages = Math.min(Math.floor(activityTimeline.length / 2) + 1, standardTimelineStages.length);
    
    if (index < completedStages - 1) {
      // Find the most recent activity date for completed stages
      const recentActivity = activityTimeline[0];
      return {
        ...stage,
        status: 'completed',
        date: recentActivity?.date || patientCreatedDate.toISOString().split('T')[0],
        isStandard: true
      };
    } else if (index === completedStages - 1) {
      const recentActivity = activityTimeline[0];
      return {
        ...stage,
        status: 'in-progress',
        date: recentActivity?.date || patientCreatedDate.toISOString().split('T')[0],
        isStandard: true
      };
    } else {
      return {
        ...stage,
        status: 'pending',
        date: '',
        isStandard: true
      };
    }
  });

  const aiSummary = `${patient.age || 34}-year-old ${(patient.gender || 'Male').toLowerCase()} patient with documented family history of heart disease and elevated cholesterol levels. Currently under ${patient.status.toLowerCase()}. Initial consultation completed with comprehensive medical history review. Patient demonstrates good understanding of treatment options and shows commitment to lifestyle modifications including Mediterranean diet and regular exercise regimen. Recent vitals show stable condition with BP 125/80 and HR 68 bpm. Recommended follow-up in 4-6 weeks to assess progress and adjust treatment plan as needed.`;

  // Available consent forms for sending
  const availableForms = [
    { id: 1, name: 'Insurance Information Release', description: 'Authorization to release medical information to insurance provider', purpose: 'Insurance verification' },
    { id: 2, name: 'Medical Records Request - Lab', description: 'Request medical records from external laboratory', purpose: 'Lab data collection' },
    { id: 3, name: 'HIPAA Authorization Form', description: 'HIPAA compliant authorization for information disclosure', purpose: 'Legal compliance' },
    { id: 4, name: 'Consent for Treatment', description: 'Patient consent for proposed treatment plan', purpose: 'Treatment authorization' },
  ];

  return (
    <div className="flex-1 h-screen overflow-hidden flex flex-col">
      <SendFormsModal
        isOpen={showSendFormsModal}
        onClose={() => setShowSendFormsModal(false)}
        patientEmail={patient?.email}
        availableForms={availableForms}
      />
      <CreateClaimModal
        isOpen={showClaimModal}
        onClose={() => setShowClaimModal(false)}
        patientId={patientId}
        onSuccess={() => {
          // Refresh claims after creating a new one
          apiService.getClaims({ patient_id: patientId })
            .then((response) => {
              setPatientClaims(response.data || []);
            })
            .catch((error) => {
              console.error('Error refreshing claims:', error);
            });
        }}
      />
      <InsuranceDetailsModal
        isOpen={showInsuranceModal}
        onClose={() => setShowInsuranceModal(false)}
        patientId={patientId}
        patient={patient}
        onSuccess={() => {
          // Refresh patient data after updating insurance
          fetchPatientData();
        }}
      />
      <CreateTaskModal
        isOpen={showTaskModal}
        onClose={() => setShowTaskModal(false)}
        prefilledData={taskModalPrefilledData}
        onSuccess={() => {
          // Refresh tasks after creating a new one
          apiService.getTasks({ patient_id: patientId })
            .then((response) => {
              setPatientTasks(response.data || []);
            })
            .catch((error) => {
              console.error('Error refreshing tasks:', error);
            });
        }}
      />
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <button onClick={() => router.push('/patients')} className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors mb-4">
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm font-medium">Back to Patients</span>
          </button>

          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              {patient.profile_image ? (
                <img src={patient.profile_image} alt={`${patient.first_name} ${patient.last_name}`} className="w-16 h-16 rounded-full object-cover" />
              ) : (
                <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center text-xl font-semibold text-purple-600">
                  {patient.first_name[0]}{patient.last_name[0]}
                </div>
              )}
              <div>
                <h1 className="text-2xl font-bold text-gray-900 mb-1">{patient.first_name} {patient.last_name}</h1>
                <div className="flex items-center gap-4 text-sm text-gray-600">
                  <button 
                    onClick={() => {
                      setTaskModalPrefilledData({
                        patientId: patientId,
                        name: `Send email to ${patient.first_name} ${patient.last_name}`,
                        description: `Follow up with ${patient.first_name} ${patient.last_name} via email at ${patient.email}`,
                        assignedTo: 'AI - Care Coordinator Agent',
                        priority: 'medium'
                      });
                      setShowTaskModal(true);
                    }}
                    className="flex items-center gap-1 hover:text-gray-900 transition-colors cursor-pointer"
                    title="Create task to send email"
                  >
                    <Mail className="w-3.5 h-3.5" />
                    {patient.email}
                  </button>
                  <button 
                    onClick={() => {
                      setTaskModalPrefilledData({
                        patientId: patientId,
                        name: `Call ${patient.first_name} ${patient.last_name}`,
                        description: `Follow up with ${patient.first_name} ${patient.last_name} via phone call at ${patient.phone}`,
                        assignedTo: 'AI - Care Coordinator Agent',
                        priority: 'medium'
                      });
                      setShowTaskModal(true);
                    }}
                    className="flex items-center gap-1 hover:text-gray-900 transition-colors cursor-pointer"
                    title="Create task to make phone call"
                  >
                    <Phone className="w-3.5 h-3.5" />
                    {patient.phone}
                  </button>
                </div>
              </div>
            </div>
            <span className="px-3 py-1.5 bg-purple-100 text-purple-700 rounded text-sm font-medium">{patient.status}</span>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto px-8 py-8">
          <Tabs defaultValue="summary" className="w-full">
            <TabsList className="bg-white border border-gray-200 p-1 rounded-lg mb-6">
              <TabsTrigger value="summary" className="data-[state=active]:bg-purple-600 data-[state=active]:text-white">Summary</TabsTrigger>
              <TabsTrigger value="tasks" className="data-[state=active]:bg-purple-600 data-[state=active]:text-white">Tasks ({patientTasks.length})</TabsTrigger>
              <TabsTrigger value="appointments" className="data-[state=active]:bg-purple-600 data-[state=active]:text-white">Appointments ({patientAppointments.length})</TabsTrigger>
              <TabsTrigger value="activities" className="data-[state=active]:bg-purple-600 data-[state=active]:text-white">Activities ({patientActivities.length})</TabsTrigger>
              <TabsTrigger value="docs" className="data-[state=active]:bg-purple-600 data-[state=active]:text-white">Docs ({patientDocuments.length})</TabsTrigger>
            </TabsList>

            <TabsContent value="summary" className="space-y-6">
              <Card className="p-6 border border-gray-200 bg-gradient-to-br from-purple-50 to-white">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-purple-600 rounded-lg flex items-center justify-center">
                      <Activity className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">AI-Generated Summary</h3>
                    </div>
                  </div>
                  <button
                    onClick={handleRegenerateSummary}
                    disabled={regeneratingSummary}
                    className="px-4 py-2 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <RefreshCw className={`w-4 h-4 ${regeneratingSummary ? 'animate-spin' : ''}`} />
                    {regeneratingSummary ? 'Regenerating...' : 'Regenerate Summary'}
                  </button>
                </div>
                <p className="text-sm text-gray-700 leading-relaxed">
                  {patientSummary?.summary || aiSummary}
                </p>
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
                    <Heart className="w-4 h-4 text-purple-600" />
                    <span className="text-sm font-semibold text-gray-900">Pre-conditions</span>
                  </div>
                  <div className="flex flex-wrap gap-2 ml-7">
                    <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm">Family history of heart disease</span>
                    <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm">Elevated cholesterol</span>
                  </div>
                </div>
              </Card>

              <Card className="p-6 border border-gray-200">
                <div className="flex items-center gap-3 mb-6">
                  <Activity className="w-5 h-5 text-purple-600" />
                  <h3 className="text-lg font-semibold text-gray-900">Treatment Timeline</h3>
                </div>
                <div className="space-y-6">
                  {timeline.length > 0 ? (
                    timeline.map((item, index) => (
                      <div key={index} className="flex gap-4">
                        <div className="flex flex-col items-center">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                            item.status === 'completed' ? 'bg-purple-600' : 
                            item.status === 'in-progress' ? 'bg-purple-400' : 
                            'bg-gray-200'
                          }`}>
                            {item.status === 'completed' ? (
                              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                            ) : item.status === 'in-progress' ? 
                              <Activity className="w-4 h-4 text-white" /> : 
                              <div className="w-2 h-2 bg-gray-400 rounded-full" />
                            }
                          </div>
                          {index < timeline.length - 1 && <div className={`w-0.5 h-12 ${item.status === 'completed' ? 'bg-purple-600' : 'bg-gray-200'}`} />}
                        </div>
                        <div className="flex-1 pb-6">
                          <div className="flex items-center justify-between mb-1">
                            <h4 className="font-medium text-gray-900">{item.title}</h4>
                            {item.date && <span className="text-xs text-gray-500">{item.date}</span>}
                          </div>
                          <p className="text-sm text-gray-600">{item.description}</p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-gray-500 text-center py-4">No timeline data available</p>
                  )}
                </div>
              </Card>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-6">
                  <Card className="p-6 border border-gray-200">
                    <div className="flex items-center gap-3 mb-4">
                      <FileText className="w-5 h-5 text-purple-600" />
                      <h3 className="text-base font-semibold text-gray-900">Recent Notes</h3>
                    </div>
                    <div className="space-y-4">
                      {patientNotes.length > 0 ? (
                        patientNotes.map((note) => (
                          <div key={note.note_id} className="pb-4 border-b border-gray-200 last:border-0 last:pb-0">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-xs font-medium text-gray-900">{note.author}</span>
                              <span className="text-xs text-gray-500">{note.date || new Date(note.created_at).toLocaleDateString()}</span>
                            </div>
                            <p className="text-sm text-gray-600">{note.content}</p>
                          </div>
                        ))
                      ) : (
                        <p className="text-sm text-gray-500">No notes yet</p>
                      )}
                    </div>
                  </Card>

                  <Card className="p-6 border border-gray-200">
                    <div className="flex items-center gap-3 mb-4">
                      <Plus className="w-5 h-5 text-purple-600" />
                      <h3 className="text-base font-semibold text-gray-900">Create Note</h3>
                    </div>
                    <Textarea value={newNote} onChange={(e) => setNewNote(e.target.value)} placeholder="Add your clinical notes here..." className="min-h-[120px] mb-4" />
                    <button onClick={handleSaveNote} disabled={savingNote || !newNote.trim()} className="w-full py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium">
                      {savingNote ? 'Saving...' : 'Save Note'}
                    </button>
                  </Card>
                </div>

                <Card className="p-6 border border-gray-200">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-purple-600" />
                      <h3 className="text-base font-semibold text-gray-900">Insurance Status</h3>
                    </div>
                    <button
                      onClick={() => setShowInsuranceModal(true)}
                      className="px-3 py-1.5 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2"
                    >
                      <Plus className="w-4 h-4" />
                      Add Insurance
                    </button>
                  </div>
                  <div className="space-y-3">
                    {patient?.insurance?.provider ? (
                      <div>
                        <div>
                          <p className="text-xs text-gray-500 mb-1">Provider</p>
                          <p className="text-sm font-medium text-gray-900">{patient.insurance.provider}</p>
                        </div>
                        {patient.insurance.policy_number && (
                          <div className="mt-2">
                            <p className="text-xs text-gray-500 mb-1">Policy Number</p>
                            <p className="text-sm font-medium text-gray-900">{patient.insurance.policy_number}</p>
                          </div>
                        )}
                        {patient.insurance.group_number && (
                          <div className="mt-2">
                            <p className="text-xs text-gray-500 mb-1">Group Number</p>
                            <p className="text-sm font-medium text-gray-900">{patient.insurance.group_number}</p>
                          </div>
                        )}
                        {patient.insurance.effective_date && (
                          <div className="mt-2">
                            <p className="text-xs text-gray-500 mb-1">Effective Date</p>
                            <p className="text-sm font-medium text-gray-900">{patient.insurance.effective_date}</p>
                          </div>
                        )}
                        {patient.insurance.expiry_date && (
                          <div className="mt-2">
                            <p className="text-xs text-gray-500 mb-1">Expiry Date</p>
                            <p className="text-sm font-medium text-gray-900">{patient.insurance.expiry_date}</p>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Provider</p>
                        <p className="text-sm font-medium text-gray-900">No insurance details found</p>
                      </div>
                    )}
                  </div>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="tasks">
              <div className="space-y-4">
                {patientTasks.length > 0 ? (
                  patientTasks.map((task) => (
                    <Card key={task.task_id} className="p-4 border border-gray-200 hover:shadow-md transition-all">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h4 className="font-medium text-gray-900">{task.title}</h4>
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              task.priority === 'urgent' ? 'bg-red-100 text-red-700' :
                              task.priority === 'high' ? 'bg-orange-100 text-orange-700' :
                              task.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                              'bg-gray-100 text-gray-700'
                            }`}>
                              {task.priority}
                            </span>
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              task.state === 'done' ? 'bg-green-100 text-green-700' :
                              task.state === 'in_progress' ? 'bg-blue-100 text-blue-700' :
                              'bg-gray-100 text-gray-700'
                            }`}>
                              {task.state}
                            </span>
                            {task.agent_type === 'ai_agent' && (
                              <span className="px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-700 flex items-center gap-1">
                                <Bot className="w-3 h-3" />
                                AI
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 mb-2">{task.description}</p>
                          <div className="flex items-center gap-4 text-xs text-gray-500">
                            <span>Assigned to: {task.assigned_to}</span>
                            {task.confidence_score && (
                              <span>Confidence: {(task.confidence_score * 100).toFixed(0)}%</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </Card>
                  ))
                ) : (
                  <Card className="p-8 text-center border border-gray-200">
                    <p className="text-gray-500">No tasks found for this patient</p>
                  </Card>
                )}
              </div>
            </TabsContent>

            <TabsContent value="appointments">
              <div className="space-y-4">
                {patientAppointments.length > 0 ? (
                  patientAppointments.map((apt) => (
                    <Card key={apt.appointment_id} className="p-4 border border-gray-200 hover:shadow-md transition-all">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h4 className="font-medium text-gray-900">{apt.title || apt.type || 'Appointment'}</h4>
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              apt.status === 'completed' ? 'bg-green-100 text-green-700' :
                              apt.status === 'scheduled' ? 'bg-blue-100 text-blue-700' :
                              apt.status === 'cancelled' ? 'bg-red-100 text-red-700' :
                              'bg-gray-100 text-gray-700'
                            }`}>
                              {apt.status}
                            </span>
                          </div>
                          <div className="flex items-center gap-4 text-sm text-gray-600 mb-2">
                            <span className="flex items-center gap-1">
                              <Calendar className="w-4 h-4" />
                              {apt.starts_at ? new Date(apt.starts_at).toLocaleString() : 'Date TBD'}
                            </span>
                            {apt.location && (
                              <span>{apt.location}</span>
                            )}
                          </div>
                          <div className="text-xs text-gray-500">
                            Provider: {apt.provider_name || 'Dr. James O\'Brien'}
                          </div>
                        </div>
                      </div>
                    </Card>
                  ))
                ) : (
                  <Card className="p-8 text-center border border-gray-200">
                    <p className="text-gray-500">No appointments found for this patient</p>
                  </Card>
                )}
              </div>
            </TabsContent>

            <TabsContent value="activities">
              <div className="space-y-6">
                {/* Human Activities */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <User className="w-5 h-5 text-purple-600" />
                    Human Activities
                  </h3>
                  <Card className="p-6 border border-gray-200">
                    <div className="space-y-4">
                      {patientActivities.filter(a => a.agent_type === 'human').length > 0 ? (
                        patientActivities.filter(a => a.agent_type === 'human').map((activity) => (
                          <div key={activity.activity_id} className="flex items-start gap-4 pb-4 border-b border-gray-200 last:border-0">
                            <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                              <Activity className="w-4 h-4 text-purple-600" />
                            </div>
                            <div className="flex-1">
                              <p className="text-sm font-medium text-gray-900">{activity.title}</p>
                              <p className="text-sm text-gray-600 mt-1">{activity.description}</p>
                              <div className="flex items-center gap-3 mt-2">
                                <span className="text-xs text-gray-500">{activity.time_ago}</span>
                                <span className={`px-2 py-1 rounded text-xs font-medium ${
                                  activity.status === 'completed' || activity.status === 'done' ? 'bg-green-100 text-green-700' :
                                  activity.status === 'in_progress' ? 'bg-blue-100 text-blue-700' :
                                  'bg-gray-100 text-gray-700'
                                }`}>
                                  {activity.status}
                                </span>
                              </div>
                            </div>
                          </div>
                        ))
                      ) : (
                        <p className="text-sm text-gray-500">No human activities found</p>
                      )}
                    </div>
                  </Card>
                </div>

                {/* AI Activities */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <Bot className="w-5 h-5 text-purple-600" />
                    AI Activities
                  </h3>
                  <Card className="p-6 border border-gray-200">
                    <div className="space-y-4">
                      {patientActivities.filter(a => a.agent_type === 'ai' || a.agent_type === 'ai_agent').length > 0 ? (
                        patientActivities.filter(a => a.agent_type === 'ai' || a.agent_type === 'ai_agent').map((activity) => (
                          <div key={activity.activity_id} className="flex items-start gap-4 pb-4 border-b border-gray-200 last:border-0">
                            <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                              <Bot className="w-4 h-4 text-purple-600" />
                            </div>
                            <div className="flex-1">
                              <p className="text-sm font-medium text-gray-900">{activity.title}</p>
                              <p className="text-sm text-gray-600 mt-1">{activity.description}</p>
                              <div className="flex items-center gap-3 mt-2">
                                <span className="text-xs text-gray-500">{activity.time_ago}</span>
                                <span className={`px-2 py-1 rounded text-xs font-medium ${
                                  activity.status === 'completed' || activity.status === 'done' ? 'bg-green-100 text-green-700' :
                                  activity.status === 'in_progress' ? 'bg-blue-100 text-blue-700' :
                                  'bg-gray-100 text-gray-700'
                                }`}>
                                  {activity.status}
                                </span>
                              </div>
                            </div>
                          </div>
                        ))
                      ) : (
                        <p className="text-sm text-gray-500">No AI activities found</p>
                      )}
                    </div>
                  </Card>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="docs" className="space-y-6">
              {/* Medical Records Section */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">Medical Records</h3>
                  <button className="px-4 py-2 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium">
                    Upload Record
                  </button>
                </div>
                
                {documentsSummary && (
                  <div className="mb-6 p-4 bg-purple-50 rounded-lg border border-purple-200">
                    <h4 className="text-sm font-semibold text-gray-900 mb-2">Documents Summary</h4>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Total Documents:</span>
                        <span className="ml-2 font-medium text-gray-900">{documentsSummary.total_documents}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">By Kind:</span>
                        <span className="ml-2 font-medium text-gray-900">
                          {Object.entries(documentsSummary.by_kind).map(([kind, count]) => `${kind}: ${count}`).join(', ')}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
                <div className="space-y-3">
                  {patientDocuments.length > 0 ? (
                    patientDocuments.map((doc) => (
                      <Card key={doc.document_id} className="p-4 border border-gray-200 hover:shadow-md transition-all">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                              <FileText className="w-6 h-6 text-purple-600" />
                            </div>
                            <div>
                              <h4 className="font-medium text-gray-900">
                                {doc.file?.name || `${doc.kind?.replace('_', ' ').toUpperCase() || 'Document'}`}
                              </h4>
                              <div className="flex items-center gap-3 text-sm text-gray-500 mt-1">
                                <span>{doc.kind?.replace('_', ' ') || 'Unknown'}</span>
                                <span>•</span>
                                <span>{doc.created_at ? new Date(doc.created_at).toLocaleDateString() : 'Date unknown'}</span>
                                {doc.file?.size && (
                                  <>
                                    <span>•</span>
                                    <span>{(doc.file.size / 1024 / 1024).toFixed(2)} MB</span>
                                  </>
                                )}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                              doc.status === 'ingested' 
                                ? 'bg-green-100 text-green-700' 
                                : doc.status === 'ingesting'
                                ? 'bg-blue-100 text-blue-700'
                                : 'bg-yellow-100 text-yellow-700'
                            }`}>
                              {doc.status}
                            </span>
                            <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                              <FileText className="w-4 h-4 text-gray-600" />
                            </button>
                          </div>
                        </div>
                      </Card>
                    ))
                  ) : (
                    <Card className="p-8 text-center border border-gray-200">
                      <p className="text-gray-500">No documents found for this patient</p>
                    </Card>
                  )}
                </div>
              </div>

              {/* Forms Section */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">Consent Forms</h3>
                  <button 
                    onClick={() => setShowSendFormsModal(true)}
                    className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center gap-2"
                  >
                    <Send className="w-4 h-4" />
                    Send Forms
                  </button>
                </div>
                
                <div className="space-y-3">
                  {[
                    { id: 1, name: 'Insurance Information Release', sentDate: '2024-10-10', status: 'Signed', signedDate: '2024-10-12' },
                    { id: 2, name: 'Medical Records Request - Lab', sentDate: '2024-10-05', status: 'Sent', signedDate: null },
                    { id: 3, name: 'HIPAA Authorization Form', sentDate: null, status: 'To-Do', signedDate: null },
                    { id: 4, name: 'Consent for Treatment', sentDate: '2024-09-20', status: 'Signed', signedDate: '2024-09-22' },
                  ].map((form) => (
                    <Card key={form.id} className="p-4 border border-gray-200 hover:shadow-md transition-all">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                            form.status === 'Signed' ? 'bg-green-100' :
                            form.status === 'Sent' ? 'bg-blue-100' :
                            'bg-gray-100'
                          }`}>
                            {form.status === 'Signed' ? (
                              <CheckCircle className="w-6 h-6 text-green-600" />
                            ) : form.status === 'Sent' ? (
                              <Send className="w-6 h-6 text-blue-600" />
                            ) : (
                              <AlertCircle className="w-6 h-6 text-gray-600" />
                            )}
                          </div>
                          <div>
                            <h4 className="font-medium text-gray-900">{form.name}</h4>
                            <div className="flex items-center gap-2 text-sm text-gray-500 mt-1">
                              {form.status === 'Signed' && form.signedDate && (
                                <span>Signed on {form.signedDate}</span>
                              )}
                              {form.status === 'Sent' && form.sentDate && (
                                <span>Sent on {form.sentDate}</span>
                              )}
                              {form.status === 'To-Do' && (
                                <span>Not yet sent</span>
                              )}
                            </div>
                          </div>
                        </div>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          form.status === 'Signed' ? 'bg-green-100 text-green-700' :
                          form.status === 'Sent' ? 'bg-blue-100 text-blue-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {form.status}
                        </span>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
};

export default PatientDetailsPage;