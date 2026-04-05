/**
 * admin.js — Admin Panel JavaScript
 * Handles all API calls and UI rendering for the admin dashboard.
 */

// ── AUTH GUARD ────────────────────────────────────────────────────────
const token = localStorage.getItem('token');
const user  = JSON.parse(localStorage.getItem('user') || 'null');

if (!token || !user || user.role !== 'admin') {
  alert('Access denied. Admin login required.');
  window.location.href = 'login.html';
}

// ── HELPERS ───────────────────────────────────────────────────────────
function showToast(msg, type = 'info') {
  const c = document.getElementById('toast-container');
  if (!c) return;
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  const icons = { success: '✓', error: '✗', info: 'ℹ' };
  t.innerHTML = `<span style="font-weight:700;margin-right:6px">${icons[type]||'ℹ'}</span>${msg}`;
  c.appendChild(t);
  setTimeout(() => t.remove(), 4000);
}

async function adminFetch(path, options = {}) {
  const headers = { 'Authorization': `Bearer ${token}`, ...options.headers };
  if (!(options.body instanceof FormData)) headers['Content-Type'] = 'application/json';
  const res  = await fetch(path, { ...options, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'Request failed');
  return data;
}

function fmt(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return isNaN(d) ? dateStr : d.toLocaleDateString('en-IN', { day:'numeric', month:'short', year:'numeric' });
}

// ── PANEL SWITCHING ───────────────────────────────────────────────────
function showPanel(name) {
  document.querySelectorAll('.admin-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.admin-nav-item').forEach(b => b.classList.remove('active'));
  const panel = document.getElementById(`panel-${name}`);
  const btn   = document.getElementById(`nav-${name}`);
  if (panel) panel.classList.add('active');
  if (btn)   btn.classList.add('active');

  // Lazy-load panel data
  if (name === 'overview') loadStats();
  if (name === 'users')    loadUsers();
  if (name === 'jobs')     loadAdminJobs();
  if (name === 'apps')     loadAdminApps();
}
window.showPanel = showPanel;

// ── SET ADMIN USER INFO ───────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const nameEl   = document.getElementById('adminUserName');
  const avatarEl = document.getElementById('adminAvatar');
  if (nameEl) nameEl.textContent = user.name || 'Admin';
  if (avatarEl) {
    const initials = (user.name || 'A').trim().split(/\s+/).map(w => w[0]).slice(0,2).join('').toUpperCase();
    let hash = 0;
    for (let i = 0; i < (user.name||'').length; i++) hash = user.name.charCodeAt(i) + ((hash << 5) - hash);
    avatarEl.style.background = `hsl(${Math.abs(hash)%360},55%,48%)`;
    avatarEl.textContent = initials;
  }
  showPanel('overview');
});

// ── OVERVIEW STATS ────────────────────────────────────────────────────
async function loadStats() {
  const grid = document.getElementById('statsGrid');
  if (!grid) return;
  grid.innerHTML = `<div class="admin-loading" style="grid-column:1/-1"><div class="admin-spinner"></div> Loading stats...</div>`;

  try {
    const data = await adminFetch('/api/admin/stats');
    grid.innerHTML = [
      { label:'Total Users',     num: data.total_users,      icon:'users',     color:'purple' },
      { label:'Job Seekers',     num: data.total_seekers,    icon:'seeker',    color:'teal'   },
      { label:'Recruiters',      num: data.total_recruiters, icon:'briefcase', color:'blue'   },
      { label:'Total Jobs',      num: data.total_jobs,       icon:'jobs',      color:'yellow' },
      { label:'Active Jobs',     num: data.active_jobs,      icon:'active',    color:'green'  },
      { label:'Applications',    num: data.total_apps,       icon:'apps',      color:'purple' },
      { label:'Shortlisted',     num: data.shortlisted,      icon:'short',     color:'teal'   },
      { label:'Hired',           num: data.hired,            icon:'hired',     color:'green'  },
    ].map(s => `
      <div class="admin-stat-card">
        <div class="stat-icon ${s.color}">${statSvg(s.icon)}</div>
        <div class="stat-info">
          <div class="stat-num">${s.num}</div>
          <div class="stat-label">${s.label}</div>
        </div>
      </div>`).join('');
  } catch (err) {
    grid.innerHTML = `<div class="admin-empty" style="grid-column:1/-1"><p>${err.message}</p></div>`;
  }
}

function statSvg(name) {
  const m = {
    users:     '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>',
    seeker:    '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
    briefcase: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2"/></svg>',
    jobs:      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6h16M4 10h16M4 14h16M4 18h16"/></svg>',
    active:    '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>',
    apps:      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
    short:     '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    hired:     '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
  };
  return m[name] || m.jobs;
}

// ── USERS TABLE ───────────────────────────────────────────────────────
let allUsers = [];

async function loadUsers() {
  const tbody = document.getElementById('usersBody');
  const count = document.getElementById('userCount');
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="6"><div class="admin-loading"><div class="admin-spinner"></div> Loading...</div></td></tr>`;

  try {
    const data = await adminFetch('/api/admin/users');
    allUsers = data.users || [];
    if (count) count.textContent = `${allUsers.length} users`;
    renderUsersTable(allUsers);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="admin-empty"><p>${err.message}</p></td></tr>`;
  }
}

function renderUsersTable(users) {
  const tbody = document.getElementById('usersBody');
  if (!tbody) return;
  if (!users.length) {
    tbody.innerHTML = `<tr><td colspan="6"><div class="admin-empty"><h3>No users found</h3></div></td></tr>`;
    return;
  }
  tbody.innerHTML = users.map(u => `
    <tr>
      <td><strong>${escHtml(u.name)}</strong></td>
      <td>${escHtml(u.email)}</td>
      <td><span class="role-badge ${u.role}">${u.role}</span></td>
      <td>${escHtml(u.location || '—')}</td>
      <td>${fmt(u.created_at)}</td>
      <td>${u.role !== 'admin' ? `<button class="btn-sm-danger" onclick="deleteUser(${u.id},'${escHtml(u.name)}')">Delete</button>` : '—'}</td>
    </tr>`).join('');
}

function filterUsers() {
  const q = (document.getElementById('userSearch')?.value || '').toLowerCase();
  const role = document.getElementById('userRoleFilter')?.value || '';
  const filtered = allUsers.filter(u =>
    (!q    || u.name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q)) &&
    (!role || u.role === role)
  );
  renderUsersTable(filtered);
}
window.filterUsers = filterUsers;

async function deleteUser(id, name) {
  if (!confirm(`Delete user "${name}"? This will also remove all their jobs and applications.`)) return;
  try {
    await adminFetch(`/api/admin/users/${id}`, { method: 'DELETE' });
    showToast(`User "${name}" deleted.`, 'success');
    loadUsers();
  } catch (err) {
    showToast(err.message, 'error');
  }
}
window.deleteUser = deleteUser;

// ── JOBS TABLE ────────────────────────────────────────────────────────
let allAdminJobs = [];

async function loadAdminJobs() {
  const tbody = document.getElementById('jobsBody');
  const count = document.getElementById('jobCount');
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="7"><div class="admin-loading"><div class="admin-spinner"></div> Loading...</div></td></tr>`;

  try {
    const data = await adminFetch('/api/admin/jobs');
    allAdminJobs = data.jobs || [];
    if (count) count.textContent = `${allAdminJobs.length} jobs`;
    renderJobsTable(allAdminJobs);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7"><div class="admin-empty"><p>${err.message}</p></div></td></tr>`;
  }
}

function renderJobsTable(jobs) {
  const tbody = document.getElementById('jobsBody');
  if (!tbody) return;
  if (!jobs.length) {
    tbody.innerHTML = `<tr><td colspan="7"><div class="admin-empty"><h3>No jobs found</h3></div></td></tr>`;
    return;
  }
  tbody.innerHTML = jobs.map(j => `
    <tr>
      <td><strong>${escHtml(j.title)}</strong></td>
      <td>${escHtml(j.company)}</td>
      <td>${escHtml(j.recruiter_name)}</td>
      <td>${j.applicant_count}</td>
      <td>${j.views}</td>
      <td>
        <button class="btn-sm-toggle ${j.is_active ? 'active-job' : 'inactive-job'}"
                onclick="toggleJob(${j.id}, this)">
          ${j.is_active ? 'Active' : 'Inactive'}
        </button>
      </td>
      <td><button class="btn-sm-danger" onclick="deleteJob(${j.id},'${escHtml(j.title)}')">Delete</button></td>
    </tr>`).join('');
}

function filterJobs() {
  const q = (document.getElementById('jobSearch')?.value || '').toLowerCase();
  const filtered = allAdminJobs.filter(j =>
    !q || j.title.toLowerCase().includes(q) || j.company.toLowerCase().includes(q)
  );
  renderJobsTable(filtered);
}
window.filterJobs = filterJobs;

async function toggleJob(id, btn) {
  try {
    const data = await adminFetch(`/api/admin/jobs/${id}/toggle`, { method: 'PUT' });
    showToast(`Job ${data.is_active ? 'activated' : 'deactivated'}.`, 'success');
    btn.textContent  = data.is_active ? 'Active' : 'Inactive';
    btn.className    = `btn-sm-toggle ${data.is_active ? 'active-job' : 'inactive-job'}`;
  } catch (err) {
    showToast(err.message, 'error');
  }
}
window.toggleJob = toggleJob;

async function deleteJob(id, title) {
  if (!confirm(`Delete job "${title}"? This will also remove all applications.`)) return;
  try {
    await adminFetch(`/api/admin/jobs/${id}`, { method: 'DELETE' });
    showToast(`Job "${title}" deleted.`, 'success');
    loadAdminJobs();
  } catch (err) {
    showToast(err.message, 'error');
  }
}
window.deleteJob = deleteJob;

// ── APPLICATIONS TABLE ────────────────────────────────────────────────
let allAdminApps = [];

async function loadAdminApps() {
  const tbody = document.getElementById('appsBody');
  const count = document.getElementById('appCount');
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="6"><div class="admin-loading"><div class="admin-spinner"></div> Loading...</div></td></tr>`;

  try {
    const data = await adminFetch('/api/admin/applications');
    allAdminApps = data.applications || [];
    if (count) count.textContent = `${allAdminApps.length} applications`;
    renderAppsTable(allAdminApps);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6"><div class="admin-empty"><p>${err.message}</p></div></td></tr>`;
  }
}

function renderAppsTable(apps) {
  const tbody = document.getElementById('appsBody');
  if (!tbody) return;
  if (!apps.length) {
    tbody.innerHTML = `<tr><td colspan="6"><div class="admin-empty"><h3>No applications yet</h3></div></td></tr>`;
    return;
  }
  const cls = { 'Under Review':'badge-review','Shortlisted':'badge-short','Hired':'badge-hired','Rejected':'badge-rejected' };
  tbody.innerHTML = apps.map(a => `
    <tr>
      <td><strong>${escHtml(a.applicant_name)}</strong><br><span style="font-size:11px;color:var(--text-3)">${escHtml(a.applicant_email)}</span></td>
      <td>${escHtml(a.job_title)}</td>
      <td>${escHtml(a.company)}</td>
      <td>${fmt(a.applied_at)}</td>
      <td><span class="badge ${cls[a.status]||'badge-review'}">${a.status}</span></td>
    </tr>`).join('');
}

function filterApps() {
  const q = (document.getElementById('appSearch')?.value || '').toLowerCase();
  const s = document.getElementById('appStatusFilter')?.value || '';
  const filtered = allAdminApps.filter(a =>
    (!q || a.applicant_name.toLowerCase().includes(q) || a.job_title.toLowerCase().includes(q)) &&
    (!s || a.status === s)
  );
  renderAppsTable(filtered);
}
window.filterApps = filterApps;

// ── LOGOUT ────────────────────────────────────────────────────────────
function adminLogout() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  window.location.href = 'login.html';
}
window.adminLogout = adminLogout;

// ── UTILS ─────────────────────────────────────────────────────────────
function escHtml(str) {
  return String(str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
