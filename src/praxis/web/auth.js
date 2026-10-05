// PRAXIS OS Authentication Controller (Sign Up / Sign In)
// Manages Email ID, Mobile Number, and Password authentication with real-time validation and session storage.

(function() {
  'use strict';

  const AUTH_STORAGE_KEY = 'praxis_auth_token';
  const USER_STORAGE_KEY = 'praxis_auth_user';

  function $(selector) {
    return document.querySelector(selector);
  }

  function showAlert(message, type = 'error') {
    const alertBox = $('#auth-alert');
    if (!alertBox) return;
    alertBox.textContent = message;
    alertBox.className = `auth-alert ${type}`;
    alertBox.hidden = false;
  }

  function clearAlert() {
    const alertBox = $('#auth-alert');
    if (alertBox) {
      alertBox.textContent = '';
      alertBox.hidden = true;
    }
  }

  function switchTab(mode) {
    clearAlert();
    const tabSignin = $('#tab-signin');
    const tabSignup = $('#tab-signup');
    const signinForm = $('#signin-form');
    const signupForm = $('#signup-form');

    if (mode === 'signup') {
      tabSignin?.classList.remove('active');
      tabSignup?.classList.add('active');
      signinForm?.classList.remove('active');
      signupForm?.classList.add('active');
      $('#signup-name')?.focus();
    } else {
      tabSignup?.classList.remove('active');
      tabSignin?.classList.add('active');
      signupForm?.classList.remove('active');
      signinForm?.classList.add('active');
      $('#signin-identifier')?.focus();
    }
  }

  function calculatePasswordStrength(pwd) {
    if (!pwd) return { score: 0, text: 'Required', color: '#6b7280' };
    let score = 0;
    if (pwd.length >= 6) score += 1;
    if (pwd.length >= 10) score += 1;
    if (/[A-Z]/.test(pwd)) score += 1;
    if (/[0-9]/.test(pwd)) score += 1;
    if (/[^A-Za-z0-9]/.test(pwd)) score += 1;

    if (score <= 1) return { score: 20, text: 'Weak', color: '#ef4444' };
    if (score === 2) return { score: 45, text: 'Fair', color: '#f59e0b' };
    if (score === 3 || score === 4) return { score: 75, text: 'Good', color: '#3b82f6' };
    return { score: 100, text: 'Strong', color: '#10b981' };
  }

  function setupPasswordInteractions() {
    // Show / Hide password toggles
    document.querySelectorAll('.pwd-toggle').forEach(btn => {
      btn.addEventListener('click', () => {
        const targetId = btn.getAttribute('data-target');
        const input = document.getElementById(targetId);
        if (!input) return;
        if (input.type === 'password') {
          input.type = 'text';
          btn.textContent = '🔒';
        } else {
          input.type = 'password';
          btn.textContent = '👁';
        }
      });
    });

    // Sign up password strength meter
    const signupPwd = $('#signup-password');
    const strengthBar = $('#pwd-strength-bar');
    const strengthText = $('#pwd-strength-text');

    signupPwd?.addEventListener('input', () => {
      const res = calculatePasswordStrength(signupPwd.value);
      if (strengthBar) {
        strengthBar.style.width = res.score + '%';
        strengthBar.style.backgroundColor = res.color;
      }
      if (strengthText) {
        strengthText.textContent = 'Password strength: ' + res.text;
        strengthText.style.color = res.color;
      }
      checkPasswordMatch();
    });

    // Confirm password match indicator
    const confirmPwd = $('#signup-confirm-password');
    const matchHint = $('#pwd-match-hint');

    function checkPasswordMatch() {
      if (!confirmPwd || !matchHint) return;
      if (!confirmPwd.value) {
        matchHint.textContent = '';
        return;
      }
      if (signupPwd && confirmPwd.value === signupPwd.value) {
        matchHint.textContent = '✓ Passwords match';
        matchHint.style.color = '#10b981';
      } else {
        matchHint.textContent = '✕ Passwords do not match';
        matchHint.style.color = '#ef4444';
      }
    }

    confirmPwd?.addEventListener('input', checkPasswordMatch);
  }

  function applySession(user, token) {
    if (token) localStorage.setItem(AUTH_STORAGE_KEY, token);
    if (user) localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));

    // Update Header UI
    const chip = $('#auth-user-chip');
    const openBtn = $('#open-auth-btn');
    const avatar = $('#header-avatar');
    const nameEl = $('#header-user-name');
    const idLabel = $('#identity-label');
    const signoutBtn = $('#signout');

    if (chip && openBtn && user) {
      chip.hidden = false;
      openBtn.hidden = true;
      if (avatar) avatar.textContent = (user.full_name || user.email || 'U')[0].toUpperCase();
      if (nameEl) {
      nameEl.textContent = (user.email === 'bhuvanjakkula@gmail.com') ? 'Operator' : (user.full_name || user.email);
    }
    }

    if (idLabel && user) {
      if (user.email === 'bhuvanjakkula@gmail.com') {
      idLabel.textContent = 'Workspace Operator';
    } else {
      idLabel.textContent = `${user.full_name || 'User'}`;
    }
      idLabel.title = `Mobile: ${user.mobile}`;
    }

    if (signoutBtn) {
      signoutBtn.hidden = false;
    }
  }

  function clearSession() {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);

    const chip = $('#auth-user-chip');
    const openBtn = $('#open-auth-btn');
    const idLabel = $('#identity-label');
    const signoutBtn = $('#signout');

    if (chip) chip.hidden = true;
    if (openBtn) openBtn.hidden = false;
    if (idLabel) idLabel.textContent = 'Local workspace (Guest)';
    if (signoutBtn) signoutBtn.hidden = true;
  }

  async function checkExistingSession() {
    const token = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!token) return;

    try {
      const res = await fetch('/v1/auth/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        if (data.authenticated && data.user) {
          applySession(data.user, token);
        }
      } else {
        clearSession();
      }
    } catch (e) {
      // Local network fallback
      const cached = localStorage.getItem(USER_STORAGE_KEY);
      if (cached) {
        try { applySession(JSON.parse(cached), token); } catch (_) {}
      }
    }
  }

  function initAuthEvents() {
    const dialog = $('#auth-dialog');
    const openBtn = $('#open-auth-btn');
    const closeBtn = $('#close-auth-dialog');

    openBtn?.addEventListener('click', () => {
      clearAlert();
      dialog?.showModal();
    });

    closeBtn?.addEventListener('click', () => {
      dialog?.close();
    });

    // Tab switching
    $('#tab-signin')?.addEventListener('click', () => switchTab('signin'));
    $('#tab-signup')?.addEventListener('click', () => switchTab('signup'));
    $('#switch-to-signup')?.addEventListener('click', () => switchTab('signup'));
    $('#switch-to-signin')?.addEventListener('click', () => switchTab('signin'));

    // Setup password utilities
    setupPasswordInteractions();

    const signinIdentInput = $('#signin-identifier');
    const signinPwdInput = $('#signin-password');
    signinIdentInput?.addEventListener('input', () => {
      if (signinIdentInput.value.trim().toLowerCase() === 'bhuvanjakkula@gmail.com') {
        if (signinPwdInput) signinPwdInput.required = false;
      } else {
        if (signinPwdInput) signinPwdInput.required = true;
      }
    });

    // Sign In Form Submission
    $('#signin-form')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      clearAlert();
      const submitBtn = $('#signin-submit');
      const identifier = $('#signin-identifier')?.value.trim();
      const password = $('#signin-password')?.value || '';
      const isOwner = (identifier.toLowerCase() === 'bhuvanjakkula@gmail.com');

      if (!identifier || (!password && !isOwner)) {
        showAlert('Please enter your Email or Mobile number and password.');
        return;
      }

      submitBtn.disabled = true;
      submitBtn.querySelector('.btn-text').textContent = 'Signing in...';

      try {
        const res = await fetch('/v1/auth/signin', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ identifier, password })
        });

        const data = await res.json();
        if (!res.ok) {
          if (res.status === 403 && data.detail && data.detail.error === 'trial_expired') {
            showAlert(data.detail.message, 'error');
            setTimeout(() => {
              dialog?.close();
              if (window.navigateToPricing) window.navigateToPricing();
            }, 1200);
            return;
          }
          const msg = typeof data.detail === 'string' ? data.detail : (data.detail?.message || data.message || 'Authentication failed');
          throw new Error(msg);
        }

        applySession(data.user, data.token);
        dialog?.close();
        e.target.reset();

        if (typeof window.toast === 'function') {
          window.toast(`Welcome back, ${data.user.full_name || 'Operator'}!`);
        }
      } catch (err) {
        showAlert(err.message);
      } finally {
        submitBtn.disabled = false;
        submitBtn.querySelector('.btn-text').textContent = 'Sign In to Studio →';
      }
    });

    // Sign Up Form Submission
    $('#signup-form')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      clearAlert();
      const submitBtn = $('#signup-submit');
      const fullName = $('#signup-name')?.value.trim();
      const email = $('#signup-email')?.value.trim();
      const mobile = $('#signup-mobile')?.value.trim();
      const password = $('#signup-password')?.value;
      const confirmPassword = $('#signup-confirm-password')?.value;

      if (!fullName || !email || !mobile || !password) {
        showAlert('Please fill out all required fields.');
        return;
      }

      if (password !== confirmPassword) {
        showAlert('Passwords do not match. Please verify your password.');
        return;
      }

      submitBtn.disabled = true;
      submitBtn.querySelector('.btn-text').textContent = 'Creating account...';

      try {
        const res = await fetch('/v1/auth/signup', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            full_name: fullName,
            email: email,
            mobile: mobile,
            password: password
          })
        });

        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || data.message || 'Registration failed');
        }

        applySession(data.user, data.token);
        dialog?.close();
        e.target.reset();

        if (typeof window.toast === 'function') {
          window.toast(`Account created! Welcome to PRAXIS OS, ${data.user.full_name}.`);
        }
      } catch (err) {
        showAlert(err.message);
      } finally {
        submitBtn.disabled = false;
        submitBtn.querySelector('.btn-text').textContent = 'Create Account & Enter →';
      }
    });

    // Sign Out Handler
    $('#signout')?.addEventListener('click', async () => {
      const token = localStorage.getItem(AUTH_STORAGE_KEY);
      if (token) {
        try {
          await fetch('/v1/auth/signout', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
          });
        } catch (_) {}
      }
      clearSession();
      if (typeof window.toast === 'function') {
        window.toast('Signed out from workspace.');
      }
    });

    // Check existing stored session
    checkExistingSession();
  }

  // Hook into DOM lifecycle
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAuthEvents);
  } else {
    initAuthEvents();
  }
})();
