import axios from 'axios';

// Base URL for your Flask backend
const API_BASE_URL = 'http://localhost:5000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false,
});
api.interceptors.request.use(
    config => {
      console.log('Request:', config.method?.toUpperCase(), config.url);
      return config;
    },
    error => {
      console.error('Request error:', error);
      return Promise.reject(error);
    }
  );
  
  api.interceptors.response.use(
    response => {
      console.log('Response:', response.status, response.config.url);
      return response;
    },
    error => {
      console.error('Response error:', error.message);
      return Promise.reject(error);
    }
  );
// API endpoints
export const fetchProjects = async () => {
    try {
      const response = await api.get('/api/projects');
      return response.data;
    } catch (error) {
      console.error('Error fetching projects:', error);
      return []; // Return empty array to prevent UI errors
    }
  };
export const fetchProject = async (projectId: string) => {
  const response = await api.get(`/api/projects/${projectId}`);
  return response.data;
};

export const createProject = async (formData: FormData) => {
  const response = await api.post('/api/projects', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const scanProject = async (projectId: string) => {
  const response = await api.post(`/api/projects/${projectId}/scan`);
  return response.data;
};

export const generatePom = async (projectId: string) => {
  const response = await api.post(`/api/projects/${projectId}/pom`);
  return response.data;
};

export const generateTests = async (projectId: string, pomId: string) => {
  const response = await api.post(`/api/projects/${projectId}/tests`, { pom_id: pomId });
  return response.data;
};

export const executeTest = async (projectId: string, testId: string) => {
  const response = await api.post(`/api/projects/${projectId}/tests/${testId}/execute`);
  return response.data;
};

export const getProjectElements = async (projectId: string) => {
  const response = await api.get(`/api/projects/${projectId}/elements`);
  return response.data;
};

export const getProjectPoms = async (projectId: string) => {
  const response = await api.get(`/api/projects/${projectId}/poms`);
  return response.data;
};

export const getProjectTests = async (projectId: string) => {
  const response = await api.get(`/api/projects/${projectId}/tests`);
  return response.data;
};

export const getProjectExecutions = async (projectId: string) => {
  const response = await api.get(`/api/projects/${projectId}/executions`);
  return response.data;
};

export const getTestCode = async (testId: string) => {
  const response = await api.get(`/api/tests/${testId}/code`);
  return response.data;
};

export const downloadFile = async (filePath: string) => {
  const response = await api.get(`/api/download/${filePath}`, {
    responseType: 'blob',
  });
  return response.data;
};

export default api;