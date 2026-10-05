// PRAXIS OS Pricing & Subscription Manager
// Integrates live Stripe Payment Links:
// Starter ($49/mo): https://buy.stripe.com/test_3cIeV5fXt229e7L7CfcjS07
// Firm ($499/mo): https://buy.stripe.com/test_bJecMX26D229fbPg8LcjS08
// Enterprise ($1,500/mo): https://buy.stripe.com/test_aFacMXfXt5eld3HaOrcjS09

(function() {
  'use strict';

  const AUTH_STORAGE_KEY = 'praxis_auth_token';
  const USER_STORAGE_KEY = 'praxis_auth_user';

  const PLANS = [
    {
      id: 'starter',
      name: 'Starter',
      price: 49,
      period: 'month',
      badge: 'Individual',
      popular: false,
      stripe_url: 'https://buy.stripe.com/test_3cIeV5fXt229e7L7CfcjS07',
      tagline: 'For individual researchers, quantitative operators, and strategic analysts.',
      features: [
        'Full Decision Canvas & Inquiry Engine',
        'Up to 25 Active Decision Models',
        'Newton, Dewey & Blake Analytical Engines',
        'Monte Carlo & Sensitivity Calculations',
        'Exportable Decision Dossiers (JSON / Markdown)',
        'Standard Email & Community Support'
      ]
    },
    {
      id: 'firm',
      name: 'Firm',
      price: 499,
      period: 'month',
      badge: 'Most Popular',
      popular: true,
      stripe_url: 'https://buy.stripe.com/test_bJecMX26D229fbPg8LcjS08',
      tagline: 'For boutique investment firms, advisory partnerships, and risk teams.',
      features: [
        'Everything in Starter',
        'Unlimited Active Decision Models',
        'Full Cockpit Simulation & Replay Lab',
        'Maritime Coordination & AIS Telemetry',
        'IMF & World Bank Macroeconomic Lenses',
        'Priority Support & Dedicated Account Specialist',
        'Shared Team Workspace & Multi-User Governance'
      ]
    },
    {
      id: 'enterprise',
      name: 'Enterprise',
      price: 1500,
      period: 'month',
      badge: 'Institutional Grade',
      popular: false,
      stripe_url: 'https://buy.stripe.com/test_aFacMXfXt5eld3HaOrcjS09',
      tagline: 'For global financial institutions, regulatory bodies, and defense agencies.',
      features: [
        'Everything in Firm',
        'Post-Quantum Cryptography (PQC) Security',
        'Custom Telemetry Ingress & Real-Time Sensors',
        'Isolated PostgreSQL & Dedicated Tenant Hosting',
        'Custom ML & Quantitative Model Calibrations',
        '24/7 SLA Guarantee & Airgap Deployment Option',
        'Executive Advisory & Strategic Support Sessions'
      ]
    }
  ];

  function getActiveUser() {
    try {
      const raw = localStorage.getItem(USER_STORAGE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (_) {
      return null;
    }
  }

  function getAuthToken() {
    return localStorage.getItem(AUTH_STORAGE_KEY);
  }

  function renderPricingView(container) {
    if (!container) return;

    const user = getActiveUser();
    const currentPlan = user?.subscription_plan || null;
    const isSubscribed = user?.subscription_status === 'active';
    const daysLeft = user?.days_remaining !== undefined ? user.days_remaining : 30;

    let trialNotice = '';
    if (!isSubscribed) {
      if (daysLeft > 0) {
        trialNotice = `
          <div class="trial-banner">
            <span class="trial-icon">⏱</span>
            <div>
              <strong>30-Day Complimentary Trial Active</strong>
              <p>You have <strong>${daysLeft} days remaining</strong> of complimentary full platform access. After 30 days, an active subscription via Stripe is required to log in.</p>
            </div>
          </div>
        `;
      } else {
        trialNotice = `
          <div class="trial-banner expired">
            <span class="trial-icon">🔒</span>
            <div>
              <strong>Your 30-Day Free Trial Has Concluded</strong>
              <p>Subscribe via Stripe to Starter ($49), Firm ($499), or Enterprise ($1,500) below to reactivate workspace access.</p>
            </div>
          </div>
        `;
      }
    } else {
      trialNotice = `
        <div class="trial-banner active">
          <span class="trial-icon">✓</span>
          <div>
            <strong>Active Subscription: ${currentPlan ? currentPlan.toUpperCase() : 'PRO'} Plan</strong>
            <p>Your workspace is fully unlocked and operating with all institutional capabilities.</p>
          </div>
        </div>
      `;
    }

    const cardsHtml = PLANS.map(plan => {
      const isCurrent = currentPlan === plan.id && isSubscribed;
      const cardClass = `pricing-card ${plan.popular ? 'popular' : ''} ${isCurrent ? 'current' : ''}`;
      const buttonText = isCurrent ? '✓ Active Plan' : `Subscribe with Stripe ($${plan.price}/mo) →`;

      let checkoutUrl = plan.stripe_url;
      if (user && user.email) {
        checkoutUrl += `?prefilled_email=${encodeURIComponent(user.email)}&client_reference_id=${encodeURIComponent(user.id || '')}`;
      }

      return `
        <div class="${cardClass}" data-plan="${plan.id}">
          ${plan.popular ? '<div class="popular-ribbon">MOST POPULAR</div>' : ''}
          <div class="plan-header">
            <span class="plan-badge">${plan.badge}</span>
            <h3 class="plan-name">${plan.name}</h3>
            <p class="plan-tagline">${plan.tagline}</p>
          </div>

          <div class="plan-price-block">
            <span class="price-currency">$</span>
            <span class="price-amount">${plan.price.toLocaleString()}</span>
            <span class="price-period">/ month</span>
          </div>

          ${isCurrent ? `
            <button type="button" class="plan-action-btn secondary" disabled>
              ✓ Currently Active
            </button>
          ` : `
            <a href="${checkoutUrl}" target="_blank" rel="noopener noreferrer" 
               class="plan-action-btn ${plan.popular ? 'primary' : 'secondary'} stripe-checkout-link" 
               data-plan-id="${plan.id}">
              ${buttonText}
            </a>
          `}

          <div class="plan-features">
            <div class="features-label">INCLUDED CAPABILITIES:</div>
            <ul>
              ${plan.features.map(f => `<li><span class="check-icon">✓</span> <span>${f}</span></li>`).join('')}
            </ul>
          </div>
        </div>
      `;
    }).join('');

    container.innerHTML = `
      <div class="pricing-container">
        <div class="pricing-hero">
          <p class="eyebrow">COMMERCIAL LICENSING & SUBSCRIPTIONS</p>
          <h2>Predictable, Transparent Pricing</h2>
          <p class="pricing-desc">
            All registered operators receive an automated <strong>30-day complimentary trial</strong> with full studio access.
            After 30 days, an active subscription is required to continue accessing your decision models.
          </p>
          ${trialNotice}
        </div>

        <div class="pricing-grid">
          ${cardsHtml}
        </div>

        <div class="stripe-badge-bar">
          <span class="stripe-secure-icon">🔒</span>
          <span>Guaranteed secure payment processing via <strong>Stripe Checkout</strong>. Cancel anytime.</span>
        </div>

        <div class="pricing-faq">
          <h3>Frequently Asked Questions</h3>
          <div class="faq-grid">
            <div class="faq-card">
              <h4>How does the 30-day free trial work?</h4>
              <p>Every newly registered account gets 30 days of full platform access with zero upfront credit card required. On day 31, a subscription plan is required to log in.</p>
            </div>
            <div class="faq-card">
              <h4>Can I switch plans later?</h4>
              <p>Yes, you can upgrade from Starter ($49/mo) to Firm ($499/mo) or Enterprise ($1,500/mo) at any time. Prorated adjustments are applied automatically in Stripe.</p>
            </div>
            <div class="faq-card">
              <h4>What payment methods are supported?</h4>
              <p>Stripe Checkout supports all major credit cards (Visa, Mastercard, Amex), Apple Pay, Google Pay, and bank wire transfers.</p>
            </div>
            <div class="faq-card">
              <h4>Is data private and secure?</h4>
              <p>Yes. All decision models, simulations, and evidence claims are stored in your secure workspace with optional Post-Quantum Cryptography (PQC) validation.</p>
            </div>
          </div>
        </div>
      </div>
    `;

    // Intercept checkout clicks to verify user and update status
    container.querySelectorAll('.stripe-checkout-link').forEach(link => {
      link.addEventListener('click', async (e) => {
        const planId = link.getAttribute('data-plan-id');
        const user = getActiveUser();
        const token = getAuthToken();

        // If not logged in, prompt sign in first
        if (!user || !token) {
          e.preventDefault();
          if (typeof window.toast === 'function') {
            window.toast('Please sign in or register before subscribing.');
          }
          const authDialog = document.getElementById('auth-dialog');
          authDialog?.showModal();
          return;
        }

        // Inform user and record subscription intent
        try {
          await fetch('/v1/billing/subscribe', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ plan_id: planId, user_id: user.id })
          });

          // Optimistically update session
          user.subscription_status = 'active';
          user.subscription_plan = planId;
          localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
          updateTrialHeaderBadge();
        } catch (_) {}
      });
    });
  }

  function updateTrialHeaderBadge() {
    const user = getActiveUser();
    let badge = document.getElementById('trial-countdown-badge');

    if (!badge) {
      const headerActions = document.querySelector('.header-actions');
      if (headerActions) {
        badge = document.createElement('span');
        badge.id = 'trial-countdown-badge';
        badge.className = 'pill trial-countdown-pill';
        headerActions.insertBefore(badge, headerActions.firstChild);
      }
    }

    if (!badge) return;

    if (!user) {
      badge.textContent = '30 Days Free Trial';
      badge.className = 'pill trial-countdown-pill';
      badge.title = 'Register to start your 30-day free trial.';
      return;
    }

    if (user.subscription_status === 'active') {
      badge.textContent = `★ ${user.subscription_plan ? user.subscription_plan.toUpperCase() : 'PAID'} ACTIVE`;
      badge.className = 'pill trial-countdown-pill active';
      badge.title = 'Active Commercial Subscription';
    } else {
      const days = user.days_remaining !== undefined ? user.days_remaining : 30;
      if (days > 0) {
        badge.textContent = `⏱ Trial: ${days} Days Left`;
        badge.className = 'pill trial-countdown-pill';
        badge.title = `${days} days remaining on complimentary trial. Click to view plans.`;
      } else {
        badge.textContent = `🔒 Trial Expired`;
        badge.className = 'pill trial-countdown-pill expired';
        badge.title = 'Trial expired. Subscription required to log in.';
      }
    }

    badge.style.cursor = 'pointer';
    badge.onclick = () => {
      navigateToPricing();
    };
  }

  function navigateToPricing() {
    document.querySelectorAll('.sidebar nav button').forEach(b => b.classList.remove('active'));
    const pricingBtn = document.querySelector('.sidebar nav button[data-page="pricing"]');
    if (pricingBtn) pricingBtn.classList.add('active');

    const breadcrumb = document.getElementById('breadcrumb');
    if (breadcrumb) breadcrumb.textContent = 'Plans & Pricing';

    const main = document.getElementById('main');
    if (main) renderPricingView(main);
  }

  function setupNavigation() {
    const nav = document.querySelector('.sidebar nav');
    if (!nav) return;

    if (!nav.querySelector('button[data-page="pricing"]')) {
      const btn = document.createElement('button');
      btn.setAttribute('data-page', 'pricing');
      btn.innerHTML = '<span>💎</span> Pricing & Plans';
      nav.appendChild(btn);
    }

    nav.addEventListener('click', (e) => {
      const targetBtn = e.target.closest('button[data-page]');
      if (!targetBtn) return;
      if (targetBtn.getAttribute('data-page') === 'pricing') {
        e.preventDefault();
        e.stopPropagation();
        navigateToPricing();
      }
    });

    updateTrialHeaderBadge();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      setupNavigation();
      updateTrialHeaderBadge();
    });
  } else {
    setupNavigation();
    updateTrialHeaderBadge();
  }

  window.renderPricingView = renderPricingView;
  window.navigateToPricing = navigateToPricing;
  window.updateTrialHeaderBadge = updateTrialHeaderBadge;
})();
