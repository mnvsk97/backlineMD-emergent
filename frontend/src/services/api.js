import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const api = axios.create({
  baseURL: `${BACKEND_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API Service
export const apiService = {
  // Patients
  getPatients: (params = {}) => api.get('/patients', { params }),
  getPatient: (patientId) => api.get(`/patients/${patientId}`),
  createPatient: (data) => api.post('/patients', data),
  updatePatient: (patientId, data) => api.patch(`/patients/${patientId}`, data),
  getPatientSummary: (patientId) => api.get(`/patients/${patientId}/summary`),

  // Documents
  getDocuments: (params = {}) => api.get('/documents', { params }),
  uploadDocument: (patientId, kind, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/documents/upload?patient_id=${patientId}&kind=${kind}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getDocument: (documentId) => api.get(`/documents/${documentId}`),
  updateDocument: (documentId, data) => api.patch(`/documents/${documentId}`, data),

  // Tasks
  getTasks: (params = {}) => api.get('/tasks', { params }),
  createTask: (data) => api.post('/tasks', data),
  updateTask: (taskId, data) => api.patch(`/tasks/${taskId}`, data),

  // Claims
  getClaims: (params = {}) => api.get('/claims', { params }),
  createClaim: (data) => api.post('/claims', data),
  getClaim: (claimId) => api.get(`/claims/${claimId}`),
  getClaimEvents: (claimId) => api.get(`/claims/${claimId}/events`),

  // Appointments
  getAppointments: (params = {}) => api.get('/appointments', { params }),
  createAppointment: (data) => api.post('/appointments', data),

  // Dashboard
  getDashboardStats: () => api.get('/dashboard/stats'),

  // Consent Forms
  getConsentForms: (params = {}) => api.get('/consent-forms', { params }),
  getFormTemplates: () => api.get('/form-templates', { params: {} }),
  sendConsentForms: (data) => api.post('/consent-forms/send', data),
};

export default api;
