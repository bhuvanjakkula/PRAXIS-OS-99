// PRAXIS OS Technology-Aligned Pricing & Subscription Manager
// Tiers: Core Studio ($99), APEX Intelligence ($349), Command & Sovereign ($1,250), Quantum Sovereign Dedicated ($3,900)

(function() {
  'use strict';

  const AUTH_STORAGE_KEY = 'praxis_auth_token';
  const USER_STORAGE_KEY = 'praxis_auth_user';
  let billingCycle = 'monthly'; // 'monthly' | 'annual'

  const PLANS = [
    {
      id: 'core_studio',
      name: 'Core Studio',
      monthly_price: 99,
      annual_price: 79,
      stripe_url: 'https://buy.stripe.com/fZu00b41gfWtbTh58a2oE0z',
      badge: 'Individual Strategist',
      popular: false,
      tagline: 'For solo founders, strategic analysts, and quantitative researchers.',
      features: [
        'Decision Canvas & 5-Engine Structured Inquiry',
        'Up to 50 Active Decision Models',
        'Monte Carlo, Causal & Sensitivity Simulation',
        'AI Solutions (3-Pass Grounded Synthesis)',
        'Exportable Decision Dossiers (JSON / Print PDF)',
        'Standard Email & Documentation Support'
      ]
    },
    {
      id: 'apex_intelligence',
      name: 'APEX Intelligence',
      monthly_price: 349,
      annual_price: 279,
      stripe_url: 'https://buy.stripe.com/bJefZ99lA25Df5t58a2oE0y',
      badge: 'Most Popular · APEX Engine',
      popular: true,
      tagline: 'Unlocks the PRAXIS APEX Kernel: Game Theory, Bayesian VOI & Fat-Tail CVaR.',
      features: [
        'Everything in Core Studio + Unlimited Models',
        'APEX Multi-Agent Nash & Minimax Regret Solver',
        'Bayesian EVPI / EVSI Value-of-Information Engine',
        'Fat-Tail CVaR (95%) & Ruin Stress Testing',
        'SHA-256 Merkle Cryptographic Decision Seals',
        'Executive Cockpits (CEO, CFO, CTO & CMO)',
        'Up to 5 Team Operator Seats'
      ]
    },
    {
      id: 'command_sovereign',
      name: 'Command & Sovereign',
      monthly_price: 1250,
      annual_price: 999,
      stripe_url: 'https://buy.stripe.com/8x24gr41geSp6yX1VY2oE0x',
      badge: 'Institutional & Macro',
      popular: false,
      tagline: 'For investment funds, policy ministries, aviation/maritime ops, and enterprise risk teams.',
      features: [
        'Everything in APEX Intelligence + Unlimited Seats',
        'IMF, World Bank & 217-Country National Strategy',
        'Policy Scorecard & Multi-Criteria Appraisal',
        'Aviation Security & Maritime Fusion Replay Labs',
        'Enterprise Source-Change Impact Audit Ledger',
        'Priority SLA & Dedicated Onboarding Specialist'
      ]
    },
    {
      id: 'quantum_sovereign',
      name: 'Quantum Sovereign Dedicated',
      monthly_price: 3900,
      annual_price: 3120,
      stripe_url: 'https://buy.stripe.com/dRmeV50P4h0x1eD1VY2oE0w',
      badge: 'Dedicated · Airgap Ready',
      popular: false,
      tagline: 'For central banks, defense agencies, and regulated global financial institutions.',
      features: [
        'Everything in Command & Sovereign',
        'Dedicated Isolated Tenant & PostgreSQL Cluster',
        'Post-Quantum Cryptographic (PQC) Audit Signing',
        'Custom Real-Time Telemetry & Sensor Ingress',
        'Custom Quantitative & APEX Kernel Calibration',
        '24/7 Executive War-Room SLA & Airgap Option'
      ]
    }
  ];

  const COMPARISON_ROWS = [
    ['Decision Canvas, Inquiry & 3-Pass AI Solutions', 'Included', 'Included', 'Included', 'Included'],
    ['Active Decision Models', 'Up to 50', 'Unlimited', 'Unlimited', 'Unlimited'],
    ['APEX Game Theory (Nash & Minimax Regret)', '—', 'Included', 'Included', 'Custom Calibration'],
    ['Bayesian EVPI / EVSI Information Valuation', '—', 'Included', 'Included', 'Custom Calibration'],
    ['Fat-Tail CVaR (95%) & Ruin Stress Engine', '—', 'Up to 10k paths', 'Up to 10k paths', 'Dedicated Compute'],
    ['SHA-256 Merkle Cryptographic Decision Seals', '—', 'Included', 'Included', 'PQC + Airgap HSM'],
    ['Executive Cockpits (CEO / CFO / CTO / CMO)', '—', 'Included', 'Included', 'Included'],
    ['IMF, World Bank & 217-Country Macro Suite', '—', '—', 'Included', 'Included'],
    ['Aviation Security & Maritime Fusion Labs', '—', '—', 'Included', 'Live Telemetry Ingress'],
    ['Operator Seats', '1 Seat', 'Up to 5 Seats', 'Unlimited', 'Unlimited + Isolated Tenant']
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
    const isAnnual = billingCycle === 'annual';

    let trialNotice = '';
    if (!isSubscribed) {
      if (daysLeft > 0) {
        trialNotice = `
          <div class="trial-banner">
            <span class="trial-icon">⏱</span>
            <div>
              <strong>30-Day Complimentary Trial Active</strong>
              <p>You have <strong>${daysLeft} days remaining</strong> of full PRAXIS OS + APEX Quantum Engine access. Select a licensing tier below at any time.</p>
            </div>
          </div>
        `;
      } else {
        trialNotice = `
          <div class="trial-banner expired">
            <span class="trial-icon">🔒</span>
            <div>
              <strong>Your 30-Day Free Trial Has Concluded</strong>
              <p>Activate Core Studio, APEX Intelligence, Command &amp; Sovereign, or Quantum Sovereign Dedicated below to restore access.</p>
            </div>
          </div>
        `;
      }
    } else {
      const activePlanObj = PLANS.find(p => p.id === currentPlan);
      const activeLabel = activePlanObj ? activePlanObj.name : (currentPlan ? currentPlan.toUpperCase() : 'ACTIVE');
      trialNotice = `
        <div class="trial-banner active">
          <span class="trial-icon">✓</span>
          <div>
            <strong>Active Subscription: ${activeLabel}</strong>
            <p>Your workspace license is active with all included analytical kernels unlocked.</p>
          </div>
        </div>
      `;
    }

    const cardsHtml = PLANS.map(plan => {
      const isCurrent = currentPlan === plan.id && isSubscribed;
      const displayPrice = isAnnual ? plan.annual_price : plan.monthly_price;
      const annualSavings = (plan.monthly_price - plan.annual_price) * 12;
      const cardClass = `pricing-card ${plan.popular ? 'popular' : ''} ${isCurrent ? 'current' : ''}`;
      const buttonText = isCurrent
        ? '✓ Active Plan'
        : `Subscribe with Stripe ($${displayPrice.toLocaleString()}/mo) →`;

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
            <span class="price-amount">${displayPrice.toLocaleString()}</span>
            <span class="price-period">/ month${isAnnual ? ' · billed annually' : ''}</span>
          </div>
          ${isAnnual ? `<p class="plan-savings-note">Save $${annualSavings.toLocaleString()} / year with annual licensing</p>` : ''}

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
            <div class="features-label">INCLUDED TECHNOLOGY & CAPABILITIES:</div>
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
          <p class="eyebrow">NEXT-GENERATION DECISION INTELLIGENCE LICENSING</p>
          <h2>Technology-Aligned Plans for Every Decision Scale</h2>
          <p class="pricing-desc">
            From individual quantitative strategists to sovereign ministries and airgapped central banks.
            Every new account includes a <strong>30-day complimentary trial</strong> of the full platform including the <strong>APEX Quantum Engine</strong>.
          </p>

          <div class="billing-toggle-wrap" role="group" aria-label="Billing cycle">
            <button type="button" class="billing-toggle-btn ${!isAnnual ? 'active' : ''}" data-cycle="monthly">Monthly Billing</button>
            <button type="button" class="billing-toggle-btn ${isAnnual ? 'active' : ''}" data-cycle="annual">Annual Billing <span class="save-badge">Save 20%</span></button>
          </div>

          ${trialNotice}
        </div>

        <div class="pricing-grid pricing-grid-4">
          ${cardsHtml}
        </div>

        <div class="stripe-badge-bar">
          <span class="stripe-secure-icon">🔒</span>
          <span>Cryptographically auditable licensing · Instant workspace activation · Customer Support &amp; Enterprise SLA: <a href="mailto:contact@apolloaiglobalcompany.com"><strong>contact@apolloaiglobalcompany.com</strong></a>.</span>
        </div>

        <section class="panel" style="margin-bottom:2.5rem">
          <div class="section-head">
            <div>
              <p class="eyebrow">CAPABILITY MATRIX</p>
              <h2>Compare PRAXIS OS &amp; APEX Technology Across Tiers</h2>
            </div>
          </div>
          <div class="comparison-scroll">
            <table>
              <thead>
                <tr>
                  <th>Technology / Capability</th>
                  <th>Core Studio ($99)</th>
                  <th>APEX Intelligence ($349)</th>
                  <th>Command &amp; Sovereign ($1,250)</th>
                  <th>Quantum Sovereign ($3,900)</th>
                </tr>
              </thead>
              <tbody>
                ${COMPARISON_ROWS.map(row => `
                  <tr>
                    <td><strong>${row[0]}</strong></td>
                    <td>${row[1]}</td>
                    <td>${row[2]}</td>
                    <td>${row[3]}</td>
                    <td>${row[4]}</td>
                  </tr>`).join('')}
              </tbody>
            </table>
          </div>
        </section>

        <div class="pricing-faq">
          <h3>Frequently Asked Questions</h3>
          <div class="faq-grid">
            <div class="faq-card">
              <h4>What is included in the APEX Quantum Engine?</h4>
              <p>APEX Intelligence unlocks multi-agent Nash &amp; Minimax Regret game-theory solving, Bayesian EVPI/EVSI information valuation, 95% Fat-Tail CVaR ruin stress testing, and SHA-256 Merkle cryptographic decision seals.</p>
            </div>
            <div class="faq-card">
              <h4>How does the 30-day complimentary trial work?</h4>
              <p>Every newly registered operator gets 30 days of full access to test Core Studio, APEX Intelligence, and Sovereign modules before selecting a commercial plan.</p>
            </div>
            <div class="faq-card">
              <h4>Can we upgrade or switch billing cycles later?</h4>
              <p>Yes. You can move between Core Studio, APEX Intelligence, Command &amp; Sovereign, and Quantum Sovereign Dedicated at any time, or switch to annual billing for a 20% discount.</p>
            </div>
            <div class="faq-card">
              <h4>Is airgapped or Post-Quantum (PQC) deployment supported?</h4>
              <p>Yes. Quantum Sovereign Dedicated includes isolated tenant PostgreSQL hosting, PQC audit signing, custom telemetry ingestion, and on-premises airgap deployment.</p>
            </div>
          </div>
        </div>
      </div>
    `;

    // Billing cycle toggle
    container.querySelectorAll('.billing-toggle-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        billingCycle = btn.dataset.cycle || 'monthly';
        renderPricingView(container);
      });
    });

    // Stripe checkout links: record subscription intent if signed in while opening live Stripe Checkout
    container.querySelectorAll('.stripe-checkout-link').forEach(link => {
      link.addEventListener('click', async () => {
        const planId = link.getAttribute('data-plan-id');
        const activeUser = getActiveUser();
        const token = getAuthToken();

        if (activeUser && token) {
          try {
            await fetch('/v1/billing/subscribe', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
              },
              body: JSON.stringify({ plan_id: planId, user_id: activeUser.id })
            });
          } catch (_) {}
        }
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
      badge.style.cursor = 'pointer';
      badge.onclick = () => navigateToPricing();
      return;
    }

    if (user.subscription_status === 'active') {
      const pObj = PLANS.find(p => p.id === user.subscription_plan);
      badge.textContent = `★ ${(pObj ? pObj.name : (user.subscription_plan || 'PAID')).toUpperCase()} ACTIVE`;
      badge.className = 'pill trial-countdown-pill active';
      badge.title = 'Active Commercial Subscription';
    } else {
      const days = user.days_remaining !== undefined ? user.days_remaining : 30;
      if (days > 0) {
        badge.textContent = `⏱ Trial: ${days} Days Left`;
        badge.className = 'pill trial-countdown-pill';
        badge.title = `${days} days remaining on complimentary trial. Click to view plans.`;
      } else {
        badge.textContent = '🔒 Trial Expired';
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
    if (typeof state !== 'undefined') state.page = 'pricing';
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
      btn.innerHTML = '<span>💎</span> Plans & Pricing';
      nav.appendChild(btn);
    }

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
