/**
 * jobs.js — Jobs listing page with real API + fallback mock data
 */

const JOBS_PER_PAGE = 9;
let currentPage  = 1;
let filteredJobs = [];
let allJobs      = [];

// ── TOAST ─────────────────────────────────────────────────
function showToast(msg, type='info') {
  const c = document.getElementById('toast-container');
  if (!c) return;
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

// ── MOCK FALLBACK DATA ─────────────────────────────────────
const MOCK_JOBS = [
  { id:1,  title:'Frontend Developer',  company:'Google',    location:'Remote',    salary:'₹12 LPA', salaryNum:12, type:'Full-time', category:'Engineering', exp:'1-3 years', mode:'Remote',  logo:'https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg',    skills:['React','CSS','JavaScript'], posted:'2 days ago' },
  { id:2,  title:'Backend Developer',   company:'Microsoft', location:'Bangalore', salary:'₹15 LPA', salaryNum:15, type:'Full-time', category:'Engineering', exp:'3-5 years', mode:'Hybrid',  logo:'https://upload.wikimedia.org/wikipedia/commons/4/44/Microsoft_logo.svg', skills:['Node.js','Python','MongoDB'], posted:'1 day ago' },
  { id:3,  title:'UI/UX Designer',      company:'Amazon',    location:'Delhi',     salary:'₹10 LPA', salaryNum:10, type:'Contract',  category:'Design',       exp:'1-3 years', mode:'On-site', logo:'https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg',   skills:['Figma','Adobe XD','Sketch'], posted:'3 days ago' },
  { id:4,  title:'Data Scientist',      company:'Netflix',   location:'Mumbai',    salary:'₹20 LPA', salaryNum:20, type:'Full-time', category:'Data Science', exp:'3-5 years', mode:'Hybrid',  logo:'https://upload.wikimedia.org/wikipedia/commons/0/08/Netflix_2015_logo.svg', skills:['Python','ML','TensorFlow'], posted:'Today' },
  { id:5,  title:'DevOps Engineer',     company:'Apple',     location:'Remote',    salary:'₹18 LPA', salaryNum:18, type:'Full-time', category:'Engineering', exp:'3-5 years', mode:'Remote',  logo:'https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg', skills:['Docker','Kubernetes','AWS'], posted:'4 days ago' },
  { id:6,  title:'Android Developer',   company:'Google',    location:'Hyderabad', salary:'₹14 LPA', salaryNum:14, type:'Full-time', category:'Engineering', exp:'1-3 years', mode:'On-site', logo:'https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg', skills:['Kotlin','Java','Android'], posted:'2 days ago' },
  { id:7,  title:'Product Manager',     company:'Microsoft', location:'Gurgaon',   salary:'₹22 LPA', salaryNum:22, type:'Full-time', category:'Management',  exp:'5+ years',  mode:'Hybrid',  logo:'https://upload.wikimedia.org/wikipedia/commons/4/44/Microsoft_logo.svg', skills:['Strategy','Roadmap','Agile'], posted:'1 day ago' },
  { id:8,  title:'Digital Marketing',   company:'Amazon',    location:'Pune',      salary:'₹9 LPA',  salaryNum:9,  type:'Full-time', category:'Marketing',   exp:'3-5 years', mode:'On-site', logo:'https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg',   skills:['SEO','SEM','Analytics'], posted:'5 days ago' },
  { id:9,  title:'ML Engineer',         company:'Netflix',   location:'Remote',    salary:'₹25 LPA', salaryNum:25, type:'Full-time', category:'Data Science', exp:'5+ years',  mode:'Remote',  logo:'https://upload.wikimedia.org/wikipedia/commons/0/08/Netflix_2015_logo.svg', skills:['PyTorch','TensorFlow','Python'], posted:'Today' },
  { id:10, title:'iOS Developer',       company:'Apple',     location:'Bangalore', salary:'₹16 LPA', salaryNum:16, type:'Full-time', category:'Engineering', exp:'1-3 years', mode:'On-site', logo:'https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg', skills:['Swift','Xcode','iOS'], posted:'3 days ago' },
  { id:11, title:'React Native Dev',    company:'Google',    location:'Delhi',     salary:'₹13 LPA', salaryNum:13, type:'Contract',  category:'Engineering', exp:'1-3 years', mode:'Remote',  logo:'https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg', skills:['React Native','JS','Redux'], posted:'2 days ago' },
  { id:12, title:'Data Analyst',        company:'Microsoft', location:'Mumbai',    salary:'₹11 LPA', salaryNum:11, type:'Full-time', category:'Data Science', exp:'1-3 years', mode:'Hybrid',  logo:'https://upload.wikimedia.org/wikipedia/commons/4/44/Microsoft_logo.svg', skills:['SQL','Excel','Power BI'], posted:'Today' },
];

// Normalize API job to match frontend shape
function normalizeJob(j) {
  const salaryNum = parseFloat((j.salary || '0').replace(/[^\d.]/g, '')) || 0;
  return {
    id:       j.id,
    title:    j.title,
    company:  j.company,
    location: j.location,
    salary:   j.salary || '—',
    salaryNum,
    type:     j.type || j.job_type || 'Full-time',
    category: j.category || 'Engineering',
    exp:      j.exp || j.experience || '—',
    mode:     j.mode || j.work_mode || 'On-site',
    logo:     j.logo || j.logo_url || '',
    skills:   Array.isArray(j.skills) ? j.skills : [],
    posted:   j.posted || j.created_at || '',
  };
}

// ── LOAD JOBS FROM API ─────────────────────────────────────
async function loadJobsFromAPI() {
  try {
    const params = {};
    const q    = document.getElementById('searchInput')?.value.trim();
    const loc  = document.getElementById('locationInput')?.value.trim();
    if (q)   params.q        = q;
    if (loc) params.location = loc;

    const data = await JobsAPI.getAll(params);
    const jobs = (data.jobs || []).map(normalizeJob);
    if (jobs.length > 0) return jobs;
  } catch (_) {}
  return null;
}

// ── RENDER JOBS ────────────────────────────────────────────
function renderJobs(jobs) {
  const container = document.getElementById('jobsContainer');
  if (!container) return;

  const countEl = document.getElementById('jobCount');
  if (countEl) countEl.textContent = jobs.length;

  if (jobs.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column:1/-1">
        <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
        <h3>No jobs found</h3>
        <p>Try adjusting your search or clearing filters</p>
      </div>`;
    document.getElementById('pagination').innerHTML = '';
    return;
  }

  const start    = (currentPage - 1) * JOBS_PER_PAGE;
  const pageJobs = jobs.slice(start, start + JOBS_PER_PAGE);

  container.innerHTML = pageJobs.map(job => `
    <div class="job-card" onclick="location.href='job-details.html?id=${job.id}'">
      <div class="job-card-top">
        <img src="${job.logo}" alt="${job.company}" class="job-logo" onerror="this.style.display='none'">
        <span class="job-type-badge">${job.type}</span>
      </div>
      <h3 class="job-title">${job.title}</h3>
      <p class="job-company">${job.company}</p>
      <div class="job-meta">
        <span>📍 ${job.location}</span>
        <span>💼 ${job.exp}</span>
        <span>🏠 ${job.mode}</span>
      </div>
      <div class="job-skills">
        ${(job.skills||[]).slice(0,3).map(s=>`<span class="skill-chip">${s}</span>`).join('')}
      </div>
      <div class="job-salary">${job.salary}</div>
      <div class="job-card-actions">
        <button class="btn-apply" onclick="event.stopPropagation();goApply(${job.id})">Apply Now</button>
        <button class="btn-view"  onclick="event.stopPropagation();location.href='job-details.html?id=${job.id}'">Details</button>
      </div>
    </div>`).join('');

  renderPagination(jobs.length);
}

function goApply(jobId) {
  if (typeof Auth !== 'undefined' && !Auth.isLoggedIn()) {
    showToast('Please login to apply for jobs', 'info');
    setTimeout(() => window.location.href = 'login.html', 1200);
    return;
  }
  window.location.href = `apply.html?id=${jobId}`;
}
window.goApply = goApply;

function renderPagination(total) {
  const container = document.getElementById('pagination');
  if (!container) return;
  const pages = Math.ceil(total / JOBS_PER_PAGE);
  if (pages <= 1) { container.innerHTML = ''; return; }
  let html = '';
  if (currentPage > 1) html += `<button class="page-btn" onclick="goPage(${currentPage-1})">‹</button>`;
  for (let i = 1; i <= pages; i++) {
    html += `<button class="page-btn ${i===currentPage?'active':''}" onclick="goPage(${i})">${i}</button>`;
  }
  if (currentPage < pages) html += `<button class="page-btn" onclick="goPage(${currentPage+1})">›</button>`;
  container.innerHTML = html;
}

function goPage(p) {
  currentPage = p;
  renderJobs(filteredJobs);
  window.scrollTo({ top: 300, behavior: 'smooth' });
}
window.goPage = goPage;

// ── FILTER & SORT (client-side) ────────────────────────────
function applyFilters() {
  const query    = (document.getElementById('searchInput')?.value || '').toLowerCase().trim();
  const location = (document.getElementById('locationInput')?.value || '').toLowerCase().trim();
  const category = document.getElementById('categoryFilter')?.value || '';
  const exp      = document.getElementById('expFilter')?.value || '';
  const sort     = document.getElementById('sortSelect')?.value || 'latest';

  const typeChecks = [...document.querySelectorAll('.filter-checkboxes input[type="checkbox"]:checked')]
    .filter(c => ['Full-time','Part-time','Contract','Internship'].includes(c.value))
    .map(c => c.value);
  const modeChecks = [...document.querySelectorAll('.filter-checkboxes input[type="checkbox"]:checked')]
    .filter(c => ['Remote','Hybrid','On-site'].includes(c.value))
    .map(c => c.value);

  filteredJobs = allJobs.filter(job => {
    const matchQ    = !query    || job.title.toLowerCase().includes(query) || job.company.toLowerCase().includes(query) || (job.skills||[]).some(s=>s.toLowerCase().includes(query));
    const matchLoc  = !location || job.location.toLowerCase().includes(location);
    const matchCat  = !category || job.category === category;
    const matchExp  = !exp      || job.exp === exp;
    const matchType = typeChecks.length === 0 || typeChecks.includes(job.type);
    const matchMode = modeChecks.length === 0 || modeChecks.includes(job.mode);
    return matchQ && matchLoc && matchCat && matchExp && matchType && matchMode;
  });

  if (sort === 'salary-high') filteredJobs.sort((a,b) => b.salaryNum - a.salaryNum);
  else if (sort === 'salary-low') filteredJobs.sort((a,b) => a.salaryNum - b.salaryNum);

  currentPage = 1;
  renderJobs(filteredJobs);
}
window.applyFilters = applyFilters;
window.searchJobs   = applyFilters;

function clearFilters() {
  const si = document.getElementById('searchInput');
  const li = document.getElementById('locationInput');
  const cf = document.getElementById('categoryFilter');
  const ef = document.getElementById('expFilter');
  if (si) si.value = '';
  if (li) li.value = '';
  if (cf) cf.value = '';
  if (ef) ef.value = '';
  document.querySelectorAll('.filter-checkboxes input[type="checkbox"]').forEach(c => c.checked = false);
  filteredJobs = [...allJobs];
  currentPage  = 1;
  renderJobs(filteredJobs);
}
window.clearFilters = clearFilters;

// ── INIT ──────────────────────────────────────────────────
(async () => {
  // Pre-fill search from URL params
  const params = new URLSearchParams(window.location.search);
  const si = document.getElementById('searchInput');
  const li = document.getElementById('locationInput');
  if (params.get('q')        && si) si.value = params.get('q');
  if (params.get('location') && li) li.value = params.get('location');

  // Try API first, fall back to mock
  const apiJobs = await loadJobsFromAPI();
  if (apiJobs) {
    allJobs = apiJobs; // Already normalized by loadJobsFromAPI
  } else {
    allJobs = MOCK_JOBS.map(normalizeJob);
  }

  filteredJobs = [...allJobs];

  // Apply any URL-based filters
  if (params.get('q') || params.get('location')) {
    applyFilters();
  } else {
    renderJobs(filteredJobs);
  }
})();
