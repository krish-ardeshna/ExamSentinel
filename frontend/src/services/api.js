/**
 * Central API client for OEPMS.
 * Handles bearer token headers, error parsing, and base URL resolution.
 */

export function getApiBaseUrl() {
  return localStorage.getItem('oepms_api_url') || import.meta.env.VITE_API_URL || 'http://localhost:8000';
}

export function setApiBaseUrl(url) {
  if (url && url.trim()) {
    localStorage.setItem('oepms_api_url', url.trim().replace(/\/$/, ''));
  } else {
    localStorage.removeItem('oepms_api_url');
  }
}

export async function apiRequest(endpoint, options = {}) {
  const token = localStorage.getItem('oepms_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const baseUrl = getApiBaseUrl();
  let response;
  try {
    response = await fetch(`${baseUrl}${endpoint}`, {
      ...options,
      headers,
    });
  } catch (err) {
    throw new Error(`Cannot connect to backend server at ${baseUrl}. Ensure backend is running and CORS is enabled.`);
  }

  if (response.status === 401) {
    // If unauthorized, clear token if expired
    localStorage.removeItem('oepms_token');
    localStorage.removeItem('oepms_user');
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg = data.detail || data.message || `Request failed with status ${response.status}`;
    throw new Error(errorMsg);
  }

  return data;
}

export const authApi = {
  login: (email, password) => apiRequest('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  }),
  logout: () => apiRequest('/auth/logout', { method: 'POST' }),
  getCurrentUser: () => apiRequest('/auth/me'),
};

export const userApi = {
  list: () => apiRequest('/users'),
  create: (data) => apiRequest('/users', { method: 'POST', body: JSON.stringify(data) }),
  update: (id, data) => apiRequest(`/users/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id) => apiRequest(`/users/${id}`, { method: 'DELETE' }),
};

export const examApi = {
  list: () => apiRequest('/exams'),
  get: (id) => apiRequest(`/exams/${id}`),
  listSubjects: () => apiRequest('/exams/subjects/list'),
  create: (data) => apiRequest('/exams', { method: 'POST', body: JSON.stringify(data) }),
  addQuestion: (examId, data) => apiRequest(`/exams/${examId}/questions`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  submitAnswerKey: (examId, answers) => apiRequest(`/exams/${examId}/answer-key`, {
    method: 'PUT',
    body: JSON.stringify({ answers }),
  }),
  publish: (examId) => apiRequest(`/exams/${examId}/publish`, { method: 'POST' }),
  getPaper: (examId) => apiRequest(`/exams/${examId}/paper`),
};

export const attemptApi = {
  start: (examId) => apiRequest(`/attempts?exam_id=${examId}`, { method: 'POST' }),
  get: (attemptId) => apiRequest(`/attempts/${attemptId}`),
  autosave: (attemptId, answers) => apiRequest(`/attempts/${attemptId}/answers`, {
    method: 'PUT',
    body: JSON.stringify({ answers }),
  }),
  postEvent: (attemptId, eventType) => apiRequest(`/attempts/${attemptId}/events`, {
    method: 'POST',
    body: JSON.stringify({
      event_type: eventType,
      timestamp: new Date().toISOString(),
    }),
  }),
  submit: (attemptId) => apiRequest(`/attempts/${attemptId}/submit`, { method: 'POST' }),
};

export const resultApi = {
  list: () => apiRequest('/results'),
  getByAttempt: (attemptId) => apiRequest(`/results/attempt/${attemptId}`),
};

export const dashboardApi = {
  student: () => apiRequest('/dashboard/student'),
  teacher: (subjectId) => apiRequest(`/dashboard/teacher${subjectId ? `?subject_id=${subjectId}` : ''}`),
  parent: (studentId) => apiRequest(`/dashboard/parent${studentId ? `?student_id=${studentId}` : ''}`),
  hodMonitor: (subjectId) => apiRequest(`/dashboard/hod/monitor${subjectId ? `?subject_id=${subjectId}` : ''}`),
  hodReports: (params) => {
    const qs = new URLSearchParams(params).toString();
    return apiRequest(`/dashboard/hod/reports?${qs}`);
  },
  admin: () => apiRequest('/dashboard/admin'),
};

export const aiHelpApi = {
  ask: (attemptId, questionId) => apiRequest('/ai-help', {
    method: 'POST',
    body: JSON.stringify({ attempt_id: attemptId, question_id: questionId }),
  }),
  history: () => apiRequest('/ai-help/history'),
};

export const settingsApi = {
  get: () => apiRequest('/settings'),
  update: (key, value) => apiRequest('/settings', {
    method: 'PUT',
    body: JSON.stringify({ key, value }),
  }),
};
