/**
 * api.js — Centralized API client for JobHub
 * All HTTP calls go through this module.
 * Automatically attaches JWT token to every authenticated request.
 */

const API_BASE = '';  // Same origin — Flask serves both frontend and API

// ── TOKEN HELPERS ──────────────────────────────────────────────────
const Auth = {
  getToken:  ()      => localStorage.getItem('token'),
  getUser:   ()      => JSON.parse(localStorage.getItem('user') || 'null'),
  setSession:(token, user) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
  },
  clear:     ()      => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },
  isLoggedIn:()      => !!localStorage.getItem('token'),
  isRecruiter:()     => Auth.getUser()?.role === 'recruiter',
};

// ── BASE FETCH ─────────────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const token = Auth.getToken();
  const headers = { ...options.headers };

  // Add auth header if token present
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Only set Content-Type for JSON (not FormData)
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  try {
    const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
    const contentType = res.headers.get('content-type') || '';
    const data = contentType.includes('application/json') ? await res.json() : {};

    if (res.status === 401) {
      // Token expired or invalid — clear session.
      // But don't redirect if we're on an auth page (login, verify-otp, register)
      const authPages = ['login.html', 'verify-otp.html', 'register.html'];
      const onAuthPage = authPages.some(p => window.location.pathname.endsWith(p));
      if (!onAuthPage) {
        Auth.clear();
        showGlobalToast('Session expired. Please login again.', 'info');
        setTimeout(() => window.location.href = 'login.html', 1500);
      }
      throw new ApiError('Unauthorized', 401, data);
    }

    if (!res.ok) {
      throw new ApiError(data.error || data.message || 'Request failed', res.status, data);
    }

    return data;

  } catch (err) {
    if (err instanceof ApiError) throw err;
    // Network error — throw with info
    throw new ApiError('Network error: server may be offline', 0, {});
  }
}

class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.status = status;
    this.data   = data;
  }
}

// ── AUTH API ───────────────────────────────────────────────────────
const AuthAPI = {
  async sendOtp(name, email, password, role) {
    return apiFetch('/api/send-otp', {
      method: 'POST',
      body: JSON.stringify({ name, email, password, role })
    });
  },

  async verifyOtp(email, otp, name, password, role) {
    return apiFetch('/api/verify-otp', {
      method: 'POST',
      body: JSON.stringify({ email, otp, name, password, role })
    });
  },

  async login(email, password) {
    return apiFetch('/api/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
  },

  async getMe() {
    return apiFetch('/api/me');
  },

  async updateProfile(data) {
    return apiFetch('/api/profile', {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },

  async changePassword(old_password, new_password) {
    return apiFetch('/api/change-password', {
      method: 'PUT',
      body: JSON.stringify({ old_password, new_password })
    });
  },

  logout() {
    Auth.clear();
    window.location.href = 'index.html';
  }
};

// ── JOBS API ───────────────────────────────────────────────────────
const JobsAPI = {
  async getAll(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(`/api/jobs${qs ? '?' + qs : ''}`);
  },

  async getOne(id) {
    return apiFetch(`/api/jobs/${id}`);
  },

  async create(data) {
    return apiFetch('/api/jobs', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  async update(id, data) {
    return apiFetch(`/api/jobs/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },

  async delete(id) {
    return apiFetch(`/api/jobs/${id}`, { method: 'DELETE' });
  },

  async getMyJobs() {
    return apiFetch('/api/recruiter/jobs');
  },

  async saveToggle(id) {
    return apiFetch(`/api/jobs/${id}/save`, { method: 'POST' });
  },

  async getSaved() {
    return apiFetch('/api/saved-jobs');
  }
};

// ── APPLICATIONS API ───────────────────────────────────────────────
const ApplicationsAPI = {
  async apply(formData) {
    // formData is FormData (multipart) for resume upload
    return apiFetch('/api/apply', {
      method: 'POST',
      body: formData
      // NO Content-Type header — browser sets multipart boundary automatically
    });
  },

  async getMyApplications() {
    return apiFetch('/api/my-applications');
  },

  async getJobApplications(jobId) {
    return apiFetch(`/api/recruiter/jobs/${jobId}/applications`);
  },

  async getAllApplicants() {
    return apiFetch('/api/recruiter/applicants');
  },

  async updateStatus(appId, status) {
    return apiFetch(`/api/application/${appId}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status })
    });
  },

  resumeUrl(filename) {
    return `/api/resume/${filename}`;
  }
};

// ── GLOBAL TOAST ───────────────────────────────────────────────────
function showGlobalToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  const icons = {
    success: '✓',
    error:   '✗',
    info:    'ℹ',
  };
  toast.innerHTML = `<span style="font-weight:700">${icons[type] || 'ℹ'}</span> ${message}`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

// ── EXPORTS (global) ───────────────────────────────────────────────
window.Auth         = Auth;
window.AuthAPI      = AuthAPI;
window.JobsAPI      = JobsAPI;
window.ApplicationsAPI = ApplicationsAPI;
window.showGlobalToast = showGlobalToast;
window.ApiError     = ApiError;
