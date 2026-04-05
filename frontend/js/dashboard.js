/**
 * dashboard.js — Role-based dashboard (Job Seeker + Recruiter) with real API
 */

// ── AUTH GUARD ────────────────────────────────────────────
const token = typeof Auth !== 'undefined' ? Auth.getToken() : localStorage.getItem('token');
let user    = typeof Auth !== 'undefined' ? Auth.getUser()  : JSON.parse(localStorage.getItem('user')||'null');

if (!token || !user) {
  window.location.href = 'login.html';
  throw new Error('Not authenticated — redirecting to login');
}

const isRecruiter = user?.role === 'recruiter';

// ── AVATAR HELPERS ────────────────────────────────────────
/**
 * Returns initials (up to 2 letters) from a name string.
 */
function getInitials(name) {
  if (!name) return '?';
  return name.trim().split(/\s+/).map(w => w[0]).slice(0, 2).join('').toUpperCase();
}

/**
 * Generates a deterministic pastel-ish hue from a string.
 */
function nameToHue(str) {
  let hash = 0;
  for (let i = 0; i < (str||'').length; i++) hash = str.charCodeAt(i) + ((hash << 5) - hash);
  return Math.abs(hash) % 360;
}

/**
 * Sets avatar on an element. If the user has a real photo URL, uses an <img>.
 * Otherwise renders a coloured circle with initials.
 * @param {HTMLElement} el  - container element
 * @param {object} userObj  - user object with .name, .email, .avatar
 * @param {number} size     - pixel size
 */
function setAvatar(el, userObj, size) {
  if (!el) return;
  const photoUrl = userObj?.avatar?.trim();
  if (photoUrl) {
    el.innerHTML = `<img src="${photoUrl}" alt="Avatar"
      style="width:${size}px;height:${size}px;border-radius:50%;object-fit:cover;display:block;"
      onerror="this.style.display='none'">`;
    el.style.background = '';
  } else {
    const initials = getInitials(userObj?.name || userObj?.email);
    const hue = nameToHue(userObj?.name || userObj?.email || '');
    el.innerHTML = `<span style="font-size:${Math.round(size*0.38)}px;font-weight:700;color:white;user-select:none;">${initials}</span>`;
    el.style.cssText += `;background:hsl(${hue},55%,48%);display:flex;align-items:center;justify-content:center;`;
  }
}

function showToast(msg, type='info') {
  const c = document.getElementById('toast-container');
  if (!c) return;
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

// ── INIT ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  setText('dashName',    user.name || 'User');
  setText('welcomeName', (user.name||'User').split(' ')[0]);
  setText('dashRoleBadge', isRecruiter ? 'Recruiter' : 'Job Seeker');

  const av = document.getElementById('dashAvatar');
  if (av) {
    av.style.width  = '56px';
    av.style.height = '56px';
    av.style.borderRadius = '50%';
    av.style.overflow = 'hidden';
    setAvatar(av, user, 56);
  }

  if (isRecruiter) {
    document.getElementById('seekerNav').style.display    = 'none';
    document.getElementById('recruiterNav').style.display = 'block';
    showPanel('rec-overview', null);
    loadRecruiterDash();
  } else {
    showPanel('overview', null);
    loadSeekerDash();
  }
  prefillProfile();
});

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val || '';
}

// ── PANEL SWITCHING ───────────────────────────────────────
function showPanel(name, linkEl) {
  document.querySelectorAll('.dash-panel').forEach(p => p.style.display='none');
  const panel = document.getElementById(`panel-${name}`);
  if (panel) panel.style.display = 'block';
  document.querySelectorAll('.dash-nav a').forEach(a => a.classList.remove('active'));
  if (linkEl) linkEl.classList.add('active');
  return false;
}
window.showPanel = showPanel;

// ══════════════════════════════════════════════════════════
// JOB SEEKER DASHBOARD
// ══════════════════════════════════════════════════════════
async function loadSeekerDash() {
  let apps = [];
  try {
    const data = await ApplicationsAPI.getMyApplications();
    apps = data.applications || [];
  } catch (_) {
    apps = JSON.parse(localStorage.getItem('myApplications') || '[]');
  }
  renderSeekerStats(apps);
  renderAppTable('recentAppBody', apps.slice(0,5), true);
  renderAppTable('allAppBody',    apps,             false);
  loadSavedJobs();
}

function renderSeekerStats(apps) {
  const el = document.getElementById('seekerStats');
  if (!el) return;
  const total  = apps.length;
  const review = apps.filter(a=>a.status==='Under Review').length;
  const short  = apps.filter(a=>a.status==='Shortlisted').length;
  el.innerHTML = [
    { num:total,  label:'Total Applied',  icon:'file',     color:'purple' },
    { num:review, label:'Under Review',   icon:'clock',    color:'yellow' },
    { num:short,  label:'Shortlisted',    icon:'check',    color:'green'  },
    { num:'—',    label:'Saved Jobs',     icon:'bookmark', color:'blue'   },
  ].map(s=>`
    <div class="stat-widget">
      <div class="stat-widget-icon ${s.color}">${svgIcon(s.icon)}</div>
      <div>
        <div class="stat-widget-num">${s.num}</div>
        <div class="stat-widget-label">${s.label}</div>
      </div>
    </div>`).join('');
}

function renderAppTable(tbodyId, apps, compact) {
  const tbody = document.getElementById(tbodyId);
  if (!tbody) return;
  if (!apps.length) {
    tbody.innerHTML = `<tr><td colspan="4" style="text-align:center;padding:40px;color:var(--text-3)">
      No applications yet. <a href="jobs.html" style="color:var(--primary)">Browse jobs →</a>
    </td></tr>`;
    return;
  }
  tbody.innerHTML = apps.map(app => {
    const cls = { 'Under Review':'badge-review','Shortlisted':'badge-short','Hired':'badge-hired','Rejected':'badge-rejected' }[app.status] || 'badge-review';
    const logo = app.logo || app.job_logo || '';
    return `<tr>
      <td>
        <div class="app-job-info">
          <img src="${logo}" class="app-logo" onerror="this.style.display='none'">
          <div>
            <div class="app-title">${app.title||app.job_title||'Job'}</div>
            <div class="app-company">${app.company||app.job_company||''}</div>
          </div>
        </div>
      </td>
      ${!compact?`<td class="app-date">${app.appliedDate||app.applied_at||'Recently'}</td>`:''}
      <td><span class="badge ${cls}">${app.status}</span></td>
      ${!compact?`<td><a href="job-details.html?id=${app.job_id||1}" style="color:var(--primary);font-size:13px;font-weight:500">View</a></td>`:''}
    </tr>`;
  }).join('');
}

async function loadSavedJobs() {
  const section = document.getElementById('savedJobsSection');
  if (!section) return;
  let jobs = [];
  try {
    const data = await JobsAPI.getSaved();
    jobs = data.jobs || [];
  } catch (_) { jobs = []; }

  if (!jobs.length) {
    section.innerHTML = `<div class="dash-empty">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/></svg>
      <h3>No saved jobs yet</h3>
      <a href="jobs.html" style="display:inline-block;padding:10px 24px;margin-top:14px;border-radius:10px;font-size:14px;font-weight:600;color:white;background:var(--primary)">Browse Jobs</a>
    </div>`;
    return;
  }
  section.innerHTML = `<div class="rec-jobs-grid">${jobs.map(j=>`
    <div class="rec-job-card">
      <div class="rec-job-title">${j.title}</div>
      <div class="rec-job-meta">${j.company} · ${j.location} · ${j.salary}</div>
      <div class="rec-job-actions">
        <button class="btn-sm primary" onclick="location.href='job-details.html?id=${j.id}'">View</button>
        <button class="btn-sm danger" onclick="unsaveJob(${j.id},this)">Remove</button>
      </div>
    </div>`).join('')}</div>`;
}

async function unsaveJob(id) {
  try {
    await JobsAPI.saveToggle(id);
    showToast('Removed from saved jobs', 'info');
    loadSavedJobs();
  } catch(_) { showToast('Could not remove job', 'error'); }
}
window.unsaveJob = unsaveJob;

// ══════════════════════════════════════════════════════════
// RECRUITER DASHBOARD
// ══════════════════════════════════════════════════════════
async function loadRecruiterDash() {
  let jobs = [];
  try {
    const data = await JobsAPI.getMyJobs();
    jobs = data.jobs || [];
  } catch (_) { jobs = []; }

  let applicants = [];
  try {
    const data = await ApplicationsAPI.getAllApplicants();
    applicants = data.applications || [];
  } catch (_) { applicants = []; }

  renderRecruiterStats(jobs, applicants);
  renderRecJobs('recJobsPreview', jobs.slice(0,3));
  renderRecJobs('recAllJobs',     jobs);
  renderApplicants(applicants);
}

function renderRecruiterStats(jobs, applicants) {
  const el = document.getElementById('recruiterStats');
  if (!el) return;
  const totalJobs  = jobs.length;
  const totalApps  = applicants.length;
  const shortlisted= applicants.filter(a=>a.status==='Shortlisted').length;
  const totalViews = jobs.reduce((s,j)=>s+(j.views||0), 0);
  el.innerHTML = [
    { num:totalJobs,   label:'Active Jobs',       icon:'briefcase', color:'purple' },
    { num:totalApps,   label:'Total Applicants',  icon:'users',     color:'blue'   },
    { num:totalViews,  label:'Job Views',         icon:'eye',       color:'yellow' },
    { num:shortlisted, label:'Shortlisted',       icon:'check',     color:'green'  },
  ].map(s=>`
    <div class="stat-widget">
      <div class="stat-widget-icon ${s.color}">${svgIcon(s.icon)}</div>
      <div>
        <div class="stat-widget-num">${s.num}</div>
        <div class="stat-widget-label">${s.label}</div>
      </div>
    </div>`).join('');
}

function renderRecJobs(elId, jobs) {
  const el = document.getElementById(elId);
  if (!el) return;
  if (!jobs.length) {
    el.innerHTML = `<div class="dash-empty" style="grid-column:1/-1">
      <h3>No jobs posted yet</h3>
      <a href="#" onclick="showPanel('post-job',null)" style="color:var(--primary)">Post your first job →</a>
    </div>`;
    return;
  }
  el.innerHTML = jobs.map(j=>`
    <div class="rec-job-card">
      <div class="rec-job-title">${j.title}</div>
      <div class="rec-job-meta">${j.location} · ${j.type||j.job_type} · ${j.salary||'—'}</div>
      <div class="rec-job-stats">
        <span>👥 ${j.applicants||0} applicants</span>
        <span>👁 ${j.views||0} views</span>
      </div>
      <div class="rec-job-actions">
        <button class="btn-sm primary" onclick="showPanel('applicants',null)">View Applicants</button>
        <button class="btn-sm danger"  onclick="deleteJob(${j.id},this)">Delete</button>
      </div>
    </div>`).join('');
}

function renderApplicants(applicants) {
  const tbody = document.getElementById('applicantsBody');
  if (!tbody) return;
  if (!applicants.length) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:40px;color:var(--text-3)">No applicants yet.</td></tr>`;
    return;
  }
  tbody.innerHTML = applicants.map(app=>{
    const cls = { 'Under Review':'badge-review','Shortlisted':'badge-short','Hired':'badge-hired','Rejected':'badge-rejected' }[app.status] || 'badge-review';
    const appInitials = getInitials(app.applicant_name||app.name||'A');
    const appHue = nameToHue(app.applicant_name||app.email||'');
    return `<tr class="applicant-row">
      <td>
        <div class="applicant-info">
          <div class="applicant-avatar" style="background:hsl(${appHue},55%,48%);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;color:white;">${appInitials}</div>
          <div>
            <div class="applicant-name">${app.applicant_name||app.name||'Applicant'}</div>
            <div class="applicant-email">${app.applicant_email||app.email||''}</div>
          </div>
        </div>
      </td>
      <td style="font-size:13px">${app.job_title||'—'}</td>
      <td class="app-date">${(app.applied_at||'').substring(0,10)||'Recently'}</td>
      <td><span class="badge ${cls}">${app.status}</span></td>
      <td>
        <div style="display:flex;gap:6px;flex-wrap:wrap">
          <button class="btn-sm primary" onclick="updateStatus(${app.id},'Shortlisted')">Shortlist</button>
          <button class="btn-sm"         onclick="updateStatus(${app.id},'Hired')">Hire</button>
          <button class="btn-sm danger"  onclick="updateStatus(${app.id},'Rejected')">Reject</button>
          ${app.resume_filename ? `<a class="btn-sm" href="/api/resume/${app.resume_path||app.resume_filename}?token=${token}" target="_blank">Resume</a>` : ''}
        </div>
      </td>
    </tr>`;
  }).join('');
}

async function updateStatus(appId, status) {
  try {
    await ApplicationsAPI.updateStatus(appId, status);
    showToast(`Status updated: ${status}`, 'success');
    loadRecruiterDash();
  } catch(err) {
    showToast(err.message || 'Update failed', 'error');
  }
}
window.updateStatus = updateStatus;

async function deleteJob(id) {
  if (!confirm('Delete this job listing?')) return;
  try {
    await JobsAPI.delete(id);
    showToast('Job deleted', 'info');
    loadRecruiterDash();
  } catch(err) {
    showToast(err.message || 'Could not delete job', 'error');
  }
}
window.deleteJob = deleteJob;

// ── POST JOB ──────────────────────────────────────────────
async function postJob() {
  const title    = document.getElementById('pjTitle')?.value.trim();
  const company  = document.getElementById('pjCompany')?.value.trim();
  const location = document.getElementById('pjLocation')?.value.trim();
  const salary   = document.getElementById('pjSalary')?.value.trim();
  const type     = document.getElementById('pjType')?.value;
  const exp      = document.getElementById('pjExp')?.value;
  const desc     = document.getElementById('pjDesc')?.value.trim();
  const skillsRaw= document.getElementById('pjSkills')?.value.trim();

  if (!title || !company || !location || !desc) {
    showToast('Please fill in all required fields', 'error'); return;
  }

  const skills = skillsRaw ? skillsRaw.split(',').map(s=>s.trim()).filter(Boolean) : [];

  try {
    await JobsAPI.create({ title, company, location, salary, job_type:type, experience:exp, description:desc, skills });
    showToast('Job posted successfully!', 'success');
    ['pjTitle','pjCompany','pjLocation','pjSalary','pjDesc','pjSkills'].forEach(id=>{
      const el = document.getElementById(id); if(el) el.value='';
    });
    showPanel('my-jobs', null);
    loadRecruiterDash();
  } catch(err) {
    showToast(err.message || 'Failed to post job', 'error');
  }
}
window.postJob = postJob;

// ── PROFILE ───────────────────────────────────────────────
function prefillProfile() {
  const profile = JSON.parse(localStorage.getItem('userProfile') || '{}');
  const setVal  = (id, val) => { const el=document.getElementById(id); if(el) el.value=val||''; };
  setVal('profName',      user.name);
  setVal('profEmail',     user.email);
  setVal('profPhone',     profile.phone    || user.phone    || '');
  setVal('profLocation',  profile.location || user.location || '');
  setVal('profBio',       profile.bio      || user.bio      || '');
  setVal('profLinkedin',  profile.linkedin || user.linkedin || '');
  setVal('profPortfolio', profile.portfolio|| user.portfolio|| '');

  // Set avatar preview
  const avatarPreview = document.getElementById('avatarPreview');
  if (avatarPreview) {
    setAvatar(avatarPreview, user, 120);
  }

  // Avatar file input event listener
  const avatarInput = document.getElementById('avatarInput');
  if (avatarInput) {
    avatarInput.addEventListener('change', function(e) {
      const file = e.target.files[0];
      if (file) {
        // Validate file size (5MB max)
        if (file.size > 5 * 1024 * 1024) {
          showToast('File too large! Maximum 5MB', 'error');
          avatarInput.value = '';
          return;
        }
        // Show preview
        const reader = new FileReader();
        reader.onload = function(event) {
          avatarPreview.innerHTML = `<img src="${event.target.result}" alt="Avatar" style="width:120px;height:120px;border-radius:50%;object-fit:cover;display:block;">`;
          avatarPreview.style.background = '';
          showToast('Image loaded. Click Save Changes to upload.', 'info');
        };
        reader.readAsDataURL(file);
      }
    });
  }
}

async function saveProfile() {
  const name      = document.getElementById('profName')?.value.trim();
  const phone     = document.getElementById('profPhone')?.value.trim();
  const location  = document.getElementById('profLocation')?.value.trim();
  const bio       = document.getElementById('profBio')?.value.trim();
  const linkedin  = document.getElementById('profLinkedin')?.value.trim();
  const portfolio = document.getElementById('profPortfolio')?.value.trim();
  const avatarInput = document.getElementById('avatarInput');

  localStorage.setItem('userProfile', JSON.stringify({ phone, location, bio, linkedin, portfolio }));
  if (name && user) {
    user.name = name;
    localStorage.setItem('user', JSON.stringify(user));
  }

  // Prepare FormData for file upload
  const formData = new FormData();
  formData.append('name', name);
  formData.append('phone', phone);
  formData.append('location', location);
  formData.append('bio', bio);
  formData.append('linkedin', linkedin);
  formData.append('portfolio', portfolio);

  if (avatarInput && avatarInput.files[0]) {
    formData.append('avatar', avatarInput.files[0]);
  }

  try {
    const authToken = typeof Auth !== 'undefined' ? Auth.getToken() : localStorage.getItem('token');
    const response = await fetch('/api/profile-upload', {
      method: 'PUT',
      headers: { 'Authorization': `Bearer ${authToken}` },
      body: formData
    });

    let result;
    try {
      result = await response.json();
    } catch (_) {
      result = {};
    }

    if (!response.ok) {
      showToast(result.error || 'Failed to update profile', 'error');
      return;
    }

    // Update in-memory user and localStorage
    if (result.user) {
      user = result.user;
      localStorage.setItem('user', JSON.stringify(user));
    }

    // Clear file input and refresh avatar displays
    if (avatarInput) avatarInput.value = '';
    const avatarPreview = document.getElementById('avatarPreview');
    if (avatarPreview) setAvatar(avatarPreview, user, 120);
    const sidebarAv = document.getElementById('dashAvatar');
    if (sidebarAv) setAvatar(sidebarAv, user, 56);

    // Sync name in sidebar
    if (user.name) {
      setText('dashName', user.name);
      setText('welcomeName', user.name.split(' ')[0]);
    }

    showToast('Profile updated successfully!', 'success');
  } catch (err) {
    console.error('Profile update error:', err);
    showToast('Network error — could not save profile', 'error');
  }
}
window.saveProfile = saveProfile;

// ── SVG ICONS ─────────────────────────────────────────────
function svgIcon(name) {
  const icons = {
    file:     '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
    clock:    '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    check:    '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>',
    bookmark: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/></svg>',
    briefcase:'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2"/></svg>',
    users:    '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>',
    eye:      '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>',
  };
  return icons[name] || '';
}

// ── AI RESUME HANDLERS ────────────────────────────────────
document.getElementById('resumeUploadInput')?.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        document.getElementById('resumeFileName').textContent = file.name;
        document.getElementById('resumeProcessBtn').style.display = 'inline-block';
        document.getElementById('aiResults').style.display = 'none';
        document.getElementById('aiError').style.display = 'none';
    }
});

async function processResume() {
    const fileInput = document.getElementById('resumeUploadInput');
    if (!fileInput.files || !fileInput.files[0]) return;
    
    document.getElementById('aiLoading').style.display = 'block';
    document.getElementById('resumeProcessBtn').style.display = 'none';
    document.getElementById('aiError').style.display = 'none';
    document.getElementById('aiResults').style.display = 'none';
    
    const formData = new FormData();
    formData.append('resume', fileInput.files[0]);
    
    try {
        const authToken = typeof Auth !== 'undefined' ? Auth.getToken() : localStorage.getItem('token');
        const res = await fetch('/api/upload-resume', {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + authToken },
            body: formData
        });
        
        const data = await res.json();
        document.getElementById('aiLoading').style.display = 'none';
        document.getElementById('resumeProcessBtn').style.display = 'inline-block';
        
        if (!res.ok) {
            document.getElementById('aiError').textContent = data.error || 'An error occurred during upload.';
            document.getElementById('aiError').style.display = 'block';
            return;
        }
        
        document.getElementById('aiResults').style.display = 'block';
        document.getElementById('aiExpLevel').textContent = data.experience || 'Not detected';
        
        const rolesGrid = document.getElementById('aiRoles');
        rolesGrid.innerHTML = '';
        (data.roles || []).forEach(r => {
            rolesGrid.innerHTML += `<span class="skill-chip" style="background:#f5f4ff; color:#4f2fe0; border:none; padding:4px 8px; font-size:12px; border-radius:4px;">${r}</span>`;
        });
        
        const skillsGrid = document.getElementById('aiSkillsList');
        skillsGrid.innerHTML = '';
        (data.skills || []).forEach(s => {
            skillsGrid.innerHTML += `<span class="skill-chip" style="background:var(--surface-2); color:var(--text-1); border:1px solid var(--surface-3); padding:4px 8px; font-size:12px; border-radius:4px;">${s}</span>`;
        });
        
        const matchingGrid = document.getElementById('aiMatchingJobsGrid');
        matchingGrid.innerHTML = '';
        
        if (!data.recommended_jobs || data.recommended_jobs.length === 0) {
            matchingGrid.innerHTML = '<div style="grid-column:1/-1; padding:30px; text-align:center; color:var(--text-3);"><p>No immediately matching jobs found for these skills.</p></div>';
        } else {
            data.recommended_jobs.forEach(match => {
                const job = match.job;
                const score = match.score;
                const missing = match.missing_skills.slice(0, 3).join(', ') + (match.missing_skills.length > 3 ? '...' : '');
                
                let missingHtml = '';
                if (missing) {
                     missingHtml = `<div style="font-size:12px; color:#d32f2f; margin-top:10px; line-height:1.4;"><b>Missing:</b> ${missing}</div>`;
                }
                
                matchingGrid.innerHTML += `
                    <div class="rec-job-card" style="position:relative; background:white;">
                        <span class="badge" style="position:absolute; top:16px; right:16px; background:#e8fdf5; color:#00a373; border:none;">${score}% Match</span>
                        <div class="rec-job-title" style="padding-right: 70px;">${job.title}</div>
                        <div class="rec-job-meta" style="margin-bottom: 8px;">${job.company} · ${job.location}</div>
                        <div style="font-size:13px; font-weight:600; color:var(--text-2);">${job.salary || 'Unspecified'}</div>
                        ${missingHtml}
                        <div style="margin-top:14px; border-top:1px solid var(--surface-2); padding-top:14px;">
                            <button class="btn-ghost" onclick="location.href='job-details.html?id=${job.id}'" style="width:100%; justify-content:center;">View Job Details</button>
                        </div>
                    </div>
                `;
            });
        }
    } catch(err) {
        document.getElementById('aiLoading').style.display = 'none';
        document.getElementById('resumeProcessBtn').style.display = 'inline-block';
        document.getElementById('aiError').textContent = 'Network or server error securely connecting to the AI system.';
        document.getElementById('aiError').style.display = 'block';
    }
}
window.processResume = processResume;

