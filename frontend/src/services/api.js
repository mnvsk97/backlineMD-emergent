import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const api = axios.create({
  baseURL: `${BACKEND_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for centralized error handling
api.interceptors.response.use(
  (response) => {
    // Return successful responses as-is
    return response;
  },
  (error) => {
    // Handle different error types
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response;

      switch (status) {
        case 400:
          console.error('Bad Request:', data.detail || 'Invalid request data');
          break;
        case 401:
          console.error('Unauthorized:', data.detail || 'Authentication required');
          // Could redirect to login here if needed
          break;
        case 403:
          console.error('Forbidden:', data.detail || 'Access denied');
          break;
        case 404:
          console.error('Not Found:', data.detail || 'Resource not found');
          break;
        case 500:
          console.error('Server Error:', data.detail || 'Internal server error');
          break;
        default:
          console.error(`Error ${status}:`, data.detail || 'An error occurred');
      }
    } else if (error.request) {
      // Request made but no response received
      console.error('Network Error: No response from server');
    } else {
      // Error in request configuration
      console.error('Request Error:', error.message);
    }

    return Promise.reject(error);
  }
);

// Request interceptor for adding auth tokens (if needed in future)
api.interceptors.request.use(
  (config) => {
    // Can add auth token here if needed
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

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
