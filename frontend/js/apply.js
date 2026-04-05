/**
 * apply.js — Multi-step job application form with real API submission
 */

const urlParams = new URLSearchParams(window.location.search);
const jobId     = parseInt(urlParams.get('id')) || 1;

// Job preview data (try API, fallback to static)
const JOB_MAP = {
  1:{ title:'Frontend Developer',  company:'Google',    meta:'Google · Remote · ₹12 LPA',     logo:'https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg' },
  2:{ title:'Backend Developer',   company:'Microsoft', meta:'Microsoft · Bangalore · ₹15 LPA', logo:'https://upload.wikimedia.org/wikipedia/commons/4/44/Microsoft_logo.svg' },
  3:{ title:'UI/UX Designer',      company:'Amazon',    meta:'Amazon · Delhi · ₹10 LPA',       logo:'https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg' },
  4:{ title:'Data Scientist',      company:'Netflix',   meta:'Netflix · Mumbai · ₹20 LPA',     logo:'https://upload.wikimedia.org/wikipedia/commons/0/08/Netflix_2015_logo.svg' },
  5:{ title:'DevOps Engineer',     company:'Apple',     meta:'Apple · Remote · ₹18 LPA',       logo:'https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg' },
};

let jobPreview  = JOB_MAP[jobId] || { title:'Software Engineer', company:'Company', meta:'—', logo:'' };
let selectedFile = null;
let currentStep  = 1;

function showToast(msg, type='info') {
  const c = document.getElementById('toast-container');
  if (!c) return;
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => t.remove(), 4000);
}

// ── AUTH GUARD ────────────────────────────────────────────
if (typeof Auth !== 'undefined' && !Auth.isLoggedIn()) {
  showToast('Please login to apply', 'info');
  setTimeout(() => window.location.href = 'login.html', 1200);
}

if (typeof Auth !== 'undefined' && Auth.isRecruiter()) {
  showToast('Recruiters cannot apply for jobs', 'error');
  setTimeout(() => window.location.href = 'dashboard.html', 1500);
}

// ── SET JOB PREVIEW HEADER ────────────────────────────────
async function initJobPreview() {
  try {
    const data = await JobsAPI.getOne(jobId);
    const j    = data.job || data;
    jobPreview = {
      title:   j.title,
      company: j.company,
      meta:    `${j.company} · ${j.location} · ${j.salary}`,
      logo:    j.logo || j.logo_url || ''
    };
  } catch (_) {}

  const titleEl  = document.getElementById('applyJobTitle');
  const metaEl   = document.getElementById('applyJobMeta');
  const logoEl   = document.getElementById('applyLogo');
  const succComp = document.getElementById('successCompany');

  if (titleEl)  titleEl.textContent  = jobPreview.title;
  if (metaEl)   metaEl.textContent   = jobPreview.meta;
  if (logoEl)   logoEl.src           = jobPreview.logo;
  if (succComp) succComp.textContent = jobPreview.company;

  // Pre-fill user info
  if (typeof Auth !== 'undefined') {
    const user = Auth.getUser();
    if (user) {
      const nameEl  = document.getElementById('appName');
      const emailEl = document.getElementById('appEmail');
      if (nameEl  && !nameEl.value)  nameEl.value  = user.name  || '';
      if (emailEl && !emailEl.value) emailEl.value = user.email || '';
    }
  }
}
initJobPreview();

// ── MULTI-STEP NAVIGATION ─────────────────────────────────
function goStep(step) {
  if (step > currentStep && !validateStep(currentStep)) return;
  currentStep = step;

  [1,2,3].forEach(s => {
    const el = document.getElementById(`formStep${s}`);
    if (el) el.style.display = s === step ? 'block' : 'none';
  });

  [1,2,3].forEach(s => {
    const circle = document.getElementById(`step${s}`);
    if (!circle) return;
    const label = circle.nextElementSibling;
    if (s < step)       { circle.className = 'step-circle done';   circle.textContent = '✓'; if(label) label.className='step-label'; }
    else if (s === step){ circle.className = 'step-circle active'; circle.textContent = s;   if(label) label.classList.add('active'); }
    else                { circle.className = 'step-circle';        circle.textContent = s;   if(label) label.classList.remove('active'); }
  });

  if (step === 3) buildReview();
  updateChecklist();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}
window.goStep = goStep;

function validateStep(step) {
  if (step === 1) {
    const name  = document.getElementById('appName')?.value.trim();
    const email = document.getElementById('appEmail')?.value.trim();
    const phone = document.getElementById('appPhone')?.value.trim();
    if (!name)  { showToast('Full name is required', 'error'); return false; }
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      showToast('Valid email is required', 'error'); return false;
    }
    if (!phone) { showToast('Phone number is required', 'error'); return false; }
    return true;
  }
  if (step === 2) {
    if (!selectedFile) { showToast('Please upload your resume', 'error'); return false; }
    const cover = document.getElementById('coverLetter')?.value.trim();
    if (!cover || cover.length < 30) {
      showToast('Please write a cover letter (at least 30 characters)', 'error'); return false;
    }
    return true;
  }
  return true;
}

function buildReview() {
  const vals = {
    Name:       document.getElementById('appName')?.value        || '',
    Email:      document.getElementById('appEmail')?.value       || '',
    Phone:      document.getElementById('appPhone')?.value       || '',
    LinkedIn:   document.getElementById('appLinkedin')?.value    || '—',
    Portfolio:  document.getElementById('appPortfolio')?.value   || '—',
    Experience: document.getElementById('appExp')?.value         || '—',
    Resume:     selectedFile ? selectedFile.name                 : '—',
  };
  const cover = document.getElementById('coverLetter')?.value || '';
  const rc = document.getElementById('reviewContent');
  if (!rc) return;
  rc.innerHTML = `
    <div style="background:var(--surface-2);border-radius:12px;padding:22px;margin-bottom:14px">
      <h4 style="font-size:14px;font-weight:700;margin-bottom:12px;color:var(--primary)">📋 Personal Info</h4>
      ${Object.entries(vals).map(([k,v])=>`
        <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border);font-size:13px">
          <span style="color:var(--text-3)">${k}</span>
          <span style="font-weight:500">${v}</span>
        </div>`).join('')}
    </div>
    <div style="background:var(--surface-2);border-radius:12px;padding:22px">
      <h4 style="font-size:14px;font-weight:700;margin-bottom:12px;color:var(--primary)">✍️ Cover Letter Preview</h4>
      <p style="font-size:13px;color:var(--text-2);line-height:1.7">${(cover.substring(0,400))}${cover.length>400?'…':''}</p>
    </div>`;
}

function updateChecklist() {
  const name  = document.getElementById('appName')?.value.trim();
  const email = document.getElementById('appEmail')?.value.trim();
  const phone = document.getElementById('appPhone')?.value.trim();
  const cover = document.getElementById('coverLetter')?.value.trim();
  const c1 = document.getElementById('chk1');
  const c2 = document.getElementById('chk2');
  const c3 = document.getElementById('chk3');
  if (c1) c1.textContent = (name && email && phone) ? '✅' : '⬜';
  if (c2) c2.textContent = selectedFile ? '✅' : '⬜';
  if (c3) c3.textContent = (cover && cover.length >= 30) ? '✅' : '⬜';
}

// ── FILE UPLOAD ────────────────────────────────────────────
function handleFileSelect(event) {
  const file = event.target.files[0];
  if (file) processFile(file);
}
window.handleFileSelect = handleFileSelect;

function handleDragOver(e) {
  e.preventDefault();
  document.getElementById('dropZone')?.classList.add('drag-over');
}
window.handleDragOver = handleDragOver;

function handleDragLeave() {
  document.getElementById('dropZone')?.classList.remove('drag-over');
}
window.handleDragLeave = handleDragLeave;

function handleDrop(e) {
  e.preventDefault();
  document.getElementById('dropZone')?.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) processFile(file);
}
window.handleDrop = handleDrop;

function processFile(file) {
  const allowed = ['application/pdf','application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
  if (!allowed.includes(file.type) && !file.name.match(/\.(pdf|doc|docx)$/i)) {
    showToast('Only PDF, DOC, DOCX files allowed', 'error'); return;
  }
  if (file.size > 5 * 1024 * 1024) {
    showToast('File must be under 5MB', 'error'); return;
  }
  selectedFile = file;
  document.getElementById('dropZone').style.display      = 'none';
  document.getElementById('fileSelected').style.display  = 'flex';
  document.getElementById('fileName').textContent = file.name;
  document.getElementById('fileSize').textContent =
    file.size < 1048576
      ? (file.size/1024).toFixed(1)+' KB'
      : (file.size/1048576).toFixed(1)+' MB';
  updateChecklist();
}

function removeFile() {
  selectedFile = null;
  document.getElementById('resumeFile').value            = '';
  document.getElementById('dropZone').style.display      = 'block';
  document.getElementById('fileSelected').style.display  = 'none';
  updateChecklist();
}
window.removeFile = removeFile;

// ── SUBMIT ────────────────────────────────────────────────
async function submitApplication() {
  const btn = document.getElementById('submitBtn');
  if (btn) { btn.textContent = '⏳ Submitting…'; btn.disabled = true; }

  const formData = new FormData();
  formData.append('job_id',       jobId);
  formData.append('name',         document.getElementById('appName').value.trim());
  formData.append('email',        document.getElementById('appEmail').value.trim());
  formData.append('phone',        document.getElementById('appPhone').value.trim());
  formData.append('linkedin',     document.getElementById('appLinkedin')?.value.trim() || '');
  formData.append('portfolio',    document.getElementById('appPortfolio')?.value.trim() || '');
  formData.append('experience',   document.getElementById('appExp')?.value || '');
  formData.append('cover_letter', document.getElementById('coverLetter').value.trim());
  if (selectedFile) formData.append('resume', selectedFile);

  try {
    await ApplicationsAPI.apply(formData);
    showSuccess();
  } catch (err) {
    if (err.status === 409) {
      showToast('You have already applied for this job.', 'info');
      showSuccess(); // Still show success UI
    } else {
      showToast(err.message || 'Submission failed. Try again.', 'error');
      if (btn) { btn.textContent = 'Submit Application 🚀'; btn.disabled = false; }
    }
  }
}
window.submitApplication = submitApplication;

function showSuccess() {
  [1,2,3].forEach(s => {
    const el = document.getElementById(`formStep${s}`);
    if (el) el.style.display = 'none';
  });
  document.getElementById('successScreen')?.classList.add('show');
  [1,2,3].forEach(s => {
    const c = document.getElementById(`step${s}`);
    if (c) { c.className = 'step-circle done'; c.textContent = '✓'; }
  });
}
