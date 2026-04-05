/**
 * job-details.js — Full job detail page, loads from API with fallback
 */

const urlParams = new URLSearchParams(window.location.search);
const jobId     = parseInt(urlParams.get('id')) || 1;

function showToastJD(msg, type='info') {
  const c = document.getElementById('toast-container');
  if (!c) return;
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

// ── MOCK FALLBACK ──────────────────────────────────────────
const MOCK_DETAILS = {
  1: { id:1, title:'Frontend Developer', company:'Google', location:'Remote', salary:'₹12 LPA', type:'Full-time', category:'Engineering', exp:'1-3 years', mode:'Remote', posted:'2 days ago', logo:'https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg', skills:['React','TypeScript','CSS','JavaScript','Redux'], description:'We are looking for a talented Frontend Developer to build amazing web experiences for millions of users worldwide.', responsibilities:['Build responsive UIs with React','Optimize performance','Write clean, testable code','Collaborate with designers'], requirements:['2+ years React experience','TypeScript proficiency','CSS/HTML expertise','REST API integration knowledge'] },
  2: { id:2, title:'Backend Developer', company:'Microsoft', location:'Bangalore', salary:'₹15 LPA', type:'Full-time', category:'Engineering', exp:'3-5 years', mode:'Hybrid', posted:'1 day ago', logo:'https://upload.wikimedia.org/wikipedia/commons/4/44/Microsoft_logo.svg', skills:['Python','Flask','MySQL','Docker','REST APIs'], description:'Join our backend team to build scalable microservices and REST APIs powering enterprise applications.', responsibilities:['Design REST APIs','Build microservices','Write unit tests','Database optimization'], requirements:['3+ years Python/Node.js','MySQL/MongoDB','Docker knowledge','AWS basics'] },
  3: { id:3, title:'UI/UX Designer', company:'Amazon', location:'Delhi', salary:'₹10 LPA', type:'Contract', category:'Design', exp:'1-3 years', mode:'On-site', posted:'3 days ago', logo:'https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg', skills:['Figma','Adobe XD','Prototyping','User Research'], description:'Design beautiful and intuitive user experiences for our suite of products used by millions daily.', responsibilities:['Create wireframes and prototypes','Conduct user research','Maintain design systems'], requirements:['2+ years UI/UX','Figma expert','Strong portfolio','Accessibility knowledge'] },
};

function getMockJob(id) {
  return MOCK_DETAILS[id] || {
    id, title:`Software Engineer`, company:'Tech Company', location:'Remote',
    salary:'₹12 LPA', type:'Full-time', category:'Engineering', exp:'1-3 years',
    mode:'Remote', posted:'Today',
    logo:'https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg',
    skills:['JavaScript','Python','SQL'],
    description:'An exciting opportunity to join a fast-growing team.',
    responsibilities:['Build software features','Collaborate with teams','Write tests'],
    requirements:['2+ years experience','Strong problem-solving skills']
  };
}

// ── LOAD JOB ───────────────────────────────────────────────
async function loadJob() {
  let job = null;
  try {
    const data = await JobsAPI.getOne(jobId);
    job = data.job || data;
  } catch (_) {
    job = getMockJob(jobId);
  }
  if (!job) job = getMockJob(jobId);
  renderJob(job);
}

// ── RENDER ─────────────────────────────────────────────────
function renderJob(job) {
  document.title = `${job.title} at ${job.company} — JobHub`;

  const bc = document.getElementById('breadcrumbTitle');
  if (bc) bc.textContent = job.title;

  // Hero
  const logo = document.getElementById('jdLogo');
  if (logo) { logo.src = job.logo || ''; logo.alt = job.company; }
  setText('jdTitle',   job.title);
  setText('jdCompany', job.company);

  const tags = document.getElementById('jdTags');
  if (tags) {
    tags.innerHTML = [
      `📍 ${job.location}`,
      `💰 ${job.salary}`,
      `💼 ${job.type}`,
      `🏠 ${job.mode}`,
      `📅 Posted ${job.posted || job.created_at || 'Recently'}`
    ].map(t=>`<span class="jd-tag">${t}</span>`).join('');
  }

  // Sidebar
  setText('sdSalary',   job.salary);
  setText('sdLocation', job.location);
  setText('sdType',     job.type);
  setText('sdExp',      job.exp || job.experience);
  setText('sdMode',     job.mode || job.work_mode);
  setText('sdCategory', job.category);
  setText('sdPosted',   job.posted || job.created_at || 'Recently');

  // Content
  setText('jdDescription', job.description || 'No description available.');

  const resp = Array.isArray(job.responsibilities)
    ? job.responsibilities
    : (typeof job.responsibilities === 'string' ? JSON.parse(job.responsibilities || '[]') : []);
  const req = Array.isArray(job.requirements)
    ? job.requirements
    : (typeof job.requirements === 'string' ? JSON.parse(job.requirements || '[]') : []);
  const skills = Array.isArray(job.skills)
    ? job.skills
    : (typeof job.skills === 'string' ? JSON.parse(job.skills || '[]') : []);

  renderList('jdResponsibilities', resp);
  renderList('jdRequirements', req);

  const skillsEl = document.getElementById('jdSkills');
  if (skillsEl) skillsEl.innerHTML = skills.map(s=>`<li>${s}</li>`).join('');

  renderSimilarJobs(job);
}

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val || '';
}

function renderList(id, items) {
  const el = document.getElementById(id);
  if (!el) return;
  if (!items || items.length === 0) {
    el.innerHTML = '<li>Details will be shared during the interview process.</li>';
    return;
  }
  el.innerHTML = items.map(i=>`<li>${i}</li>`).join('');
}

function renderSimilarJobs(currentJob) {
  const container = document.getElementById('similarJobs');
  if (!container) return;
  const similar = Object.values(MOCK_DETAILS)
    .filter(j => j.id !== currentJob.id && j.category === currentJob.category)
    .slice(0, 3);
  if (!similar.length) {
    container.innerHTML = '<p style="font-size:13px;color:var(--text-3)">No similar jobs found.</p>';
    return;
  }
  container.innerHTML = similar.map(j=>`
    <div class="similar-job" onclick="location.href='job-details.html?id=${j.id}'">
      <img src="${j.logo}" alt="${j.company}">
      <div class="similar-job-info">
        <div class="similar-job-title">${j.title}</div>
        <div class="similar-job-company">${j.company} · ${j.salary}</div>
      </div>
    </div>`).join('');
}

// ── ACTIONS ───────────────────────────────────────────────
function goApply() {
  if (typeof Auth !== 'undefined' && !Auth.isLoggedIn()) {
    showToastJD('Please login to apply for this job', 'info');
    setTimeout(() => window.location.href = 'login.html', 1300);
    return;
  }
  window.location.href = `apply.html?id=${jobId}`;
}
window.goApply = goApply;

async function saveJob() {
  if (typeof Auth !== 'undefined' && !Auth.isLoggedIn()) {
    showToastJD('Please login to save jobs', 'info');
    return;
  }
  try {
    const data = await JobsAPI.saveToggle(jobId);
    showToastJD(data.saved ? 'Job saved!' : 'Removed from saved jobs', 'success');
  } catch (_) {
    showToastJD('Could not save job. Try again.', 'error');
  }
}
window.saveJob = saveJob;

loadJob();
