/**
 * auth.js — Login & Register logic using real API
 */

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  const icons = { success: '✓', error: '✗', info: 'ℹ' };
  toast.innerHTML = `<span style="font-weight:700;margin-right:6px">${icons[type]||'ℹ'}</span>${message}`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

function setButtonLoading(btn, loading) {
  if (loading) {
    btn.dataset.originalText = btn.innerHTML;
    btn.innerHTML = '<div class="spinner"></div> Please wait...';
    btn.disabled = true;
  } else {
    btn.innerHTML = btn.dataset.originalText || 'Submit';
    btn.disabled = false;
  }
}

function showFieldError(fieldId, message) {
  const field = document.getElementById(fieldId);
  const errEl = document.getElementById(fieldId + 'Error');
  if (field) field.classList.add('error');
  if (errEl) { errEl.textContent = message; errEl.classList.add('show'); }
}

function clearErrors() {
  document.querySelectorAll('.form-error').forEach(e => e.classList.remove('show'));
  document.querySelectorAll('input.error, select.error').forEach(e => e.classList.remove('error'));
}

document.querySelectorAll('.toggle-pass').forEach(btn => {
  btn.addEventListener('click', () => {
    const wrap  = btn.closest('.input-with-icon');
    const input = wrap ? wrap.querySelector('input') : null;
    if (!input) return;
    input.type = input.type === 'password' ? 'text' : 'password';
    btn.innerHTML = input.type === 'password'
      ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>'
      : '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';
  });
});

const loginForm = document.getElementById('loginForm');
if (loginForm) {
  loginForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    clearErrors();

    const email    = document.getElementById('loginEmail')?.value.trim();
    const password = document.getElementById('loginPassword')?.value;

    let valid = true;
    if (!email)    { showFieldError('loginEmail',    'Email is required');    valid = false; }
    if (!password) { showFieldError('loginPassword', 'Password is required'); valid = false; }
    if (!valid) return;

    const btn = loginForm.querySelector('.auth-submit');
    setButtonLoading(btn, true);

    try {
      // ── Simple login: just verify credentials & return token ───
      const data = await AuthAPI.login(email, password);

      Auth.setSession(data.token, data.user);
      showToast('Login successful! Redirecting…', 'success');
      setTimeout(() => window.location.href = 'dashboard.html', 900);

    } catch (err) {
      if (err.status === 401) {
        showToast('Invalid email or password.', 'error');
        showFieldError('loginPassword', 'Invalid credentials');
      } else {
        showToast(err.message || 'Login failed. Is the server running?', 'error');
      }
    } finally {
      setButtonLoading(btn, false);
    }
  });
}


const registerForm = document.getElementById('registerForm');
if (registerForm) {
  registerForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    clearErrors();
    const name     = document.getElementById('regName')?.value.trim();
    const email    = document.getElementById('regEmail')?.value.trim();
    const password = document.getElementById('regPassword')?.value;
    const confirm  = document.getElementById('regConfirm')?.value;
    const role     = document.getElementById('roleInput')?.value;
    let valid = true;
    if (!name)  { showFieldError('regName', 'Full name is required'); valid = false; }
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      showFieldError('regEmail', 'Enter a valid email address'); valid = false;
    }
    if (!password || password.length < 6) {
      showFieldError('regPassword', 'Password must be at least 6 characters'); valid = false;
    }
    if (password !== confirm) {
      showFieldError('regConfirm', 'Passwords do not match'); valid = false;
    }
    if (!role) { showToast('Please select your role', 'error'); valid = false; }
    if (!valid) return;
    
    const btn = registerForm.querySelector('.auth-submit');
    setButtonLoading(btn, true);
    
    try {
      // ── Step 1: Send registration data → server generates OTP ───
      const data = await AuthAPI.sendOtp(name, email, password, role);

      // Store registration context in sessionStorage for OTP verification
      sessionStorage.setItem('reg_email', email);
      sessionStorage.setItem('reg_name', name);
      sessionStorage.setItem('reg_password', password);
      sessionStorage.setItem('reg_role', role);

      // Dev mode: server returned OTP in response (email not configured)
      if (data.dev_otp) {
        sessionStorage.setItem('reg_dev_otp', data.dev_otp);
        showToast('⚠️ Dev mode: OTP shown on next page (email not configured)', 'info');
      } else {
        showToast('Verification code sent to your email!', 'success');
      }

      // Switch to OTP verification step
      document.getElementById('regStep1').style.display = 'none';
      document.getElementById('regStep2').style.display = 'block';
      document.getElementById('regOtpCode').focus();

    } catch (err) {
      if (err.status === 409) {
        showFieldError('regEmail', 'This email is already registered');
        showToast('Email already registered. Please login.', 'error');
      } else if (err.status === 422 && err.data?.errors) {
        Object.entries(err.data.errors).forEach(([f, m]) => {
          showFieldError('reg' + f[0].toUpperCase() + f.slice(1), m);
        });
        showToast('Please fix the errors above.', 'error');
      } else {
        showToast(err.message || 'Registration failed. Please try again.', 'error');
      }
    } finally {
      setButtonLoading(btn, false);
    }
  });
}

const registerOtpForm = document.getElementById('registerOtpForm');
if (registerOtpForm) {
  registerOtpForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    clearErrors();

    const otp = document.getElementById('regOtpCode')?.value.trim();
    const email = sessionStorage.getItem('reg_email');

    if (!otp || otp.length !== 6) {
      showFieldError('regOtpCode', 'Please enter a valid 6-digit code');
      return;
    }

    const btn = registerOtpForm.querySelector('.auth-submit');
    setButtonLoading(btn, true);

    try {
      // ── Step 2: Verify OTP & create the account ───
      const data = await AuthAPI.verifyOtp(
        email, 
        otp,
        sessionStorage.getItem('reg_name'),
        sessionStorage.getItem('reg_password'),
        sessionStorage.getItem('reg_role')
      );
      
      // Account created, set session and redirect
      Auth.setSession(data.token, data.user);
      showToast('Welcome to JobHub! 🎉', 'success');
      
      // Clear session data
      sessionStorage.removeItem('reg_email');
      sessionStorage.removeItem('reg_name');
      sessionStorage.removeItem('reg_password');
      sessionStorage.removeItem('reg_role');
      sessionStorage.removeItem('reg_dev_otp');
      
      setTimeout(() => window.location.href = 'dashboard.html', 1000);

    } catch (err) {
      if (err.status === 401) {
        showFieldError('regOtpCode', 'Invalid or expired code');
        showToast('Invalid verification code. Please try again.', 'error');
      } else if (err.status === 404) {
        showToast('Registration session expired. Please register again.', 'error');
        setTimeout(() => window.location.reload(), 1500);
      } else {
        showToast(err.message || 'Verification failed. Please try again.', 'error');
      }
    } finally {
      setButtonLoading(btn, false);
    }
  });
}

function selectRole(card) {
  document.querySelectorAll('.role-card').forEach(c => c.classList.remove('selected'));
  card.classList.add('selected');
  const hidden = document.getElementById('roleInput');
  if (hidden) hidden.value = card.dataset.role;
}
window.selectRole = selectRole;

function backToRegStep1() {
  document.getElementById('regStep1').style.display = 'block';
  document.getElementById('regStep2').style.display = 'none';
  document.getElementById('registerOtpForm').reset();
  clearErrors();
}
window.backToRegStep1 = backToRegStep1;

async function resendRegOtp() {
  const email = sessionStorage.getItem('reg_email');
  if (!email) {
    showToast('Please complete the registration form first', 'error');
    return;
  }

  try {
    const data = await AuthAPI.sendOtp(
      sessionStorage.getItem('reg_name'),
      email,
      sessionStorage.getItem('reg_password'),
      sessionStorage.getItem('reg_role')
    );
    
    if (data.dev_otp) {
      sessionStorage.setItem('reg_dev_otp', data.dev_otp);
    }
    
    showToast('Verification code resent to your email!', 'success');
  } catch (err) {
    showToast(err.message || 'Failed to resend code. Please try again.', 'error');
  }
}
window.resendRegOtp = resendRegOtp;

// Show dev OTP if in dev mode
document.addEventListener('DOMContentLoaded', () => {
  const devOtp = sessionStorage.getItem('reg_dev_otp');
  if (devOtp && document.getElementById('regStep2')) {
    // Optionally show or log dev OTP - user can see it in browser console
    console.log('[DEV MODE] Verification code:', devOtp);
  }
});
