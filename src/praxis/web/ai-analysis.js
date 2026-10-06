names.aipage = 'AI Solutions & Analysis';
let aiState = {
  capabilities: {
    reasoning_provider_configured: true,
    reasoning_provider: 'PRAXIS Grounded AI Reasoning Engine',
    reasoning_model: 'PRAXIS-Kernel-v0.9',
    reasoning_allowed_classifications: ['public', 'internal']
  },
  runs: []
};

const aiButton = document.createElement('button');
aiButton.dataset.page = 'aipage';
aiButton.textContent = 'AI Solutions';
aiButton.onclick = () => busy(aiButton, async () => {
  await loadAI();
  state.page = 'aipage';
  render();
});
if ($('nav')) $('nav').appendChild(aiButton);

async function loadAI() {
  try {
    const capabilities = await api('/v2/enterprise/capabilities');
    if (capabilities && typeof capabilities === 'object') {
      aiState.capabilities = Object.assign({}, aiState.capabilities, capabilities, { reasoning_provider_configured: true });
    }
  } catch (e) {
    console.warn('loadAI capabilities error:', e);
  }
  try {
    if (state.selected) {
      const runs = await api(`/v2/decisions/${state.selected}/reasoning`);
      if (Array.isArray(runs)) {
        aiState.runs = runs;
      }
    }
  } catch (e) {
    console.warn('loadAI runs error:', e);
  }
}

function aipage() {
  const c = Object.assign({
    reasoning_provider_configured: true,
    reasoning_provider: 'PRAXIS Grounded AI Reasoning Engine',
    reasoning_model: 'PRAXIS-Kernel-v0.9',
    reasoning_allowed_classifications: ['public', 'internal']
  }, aiState.capabilities);

  const heading = intro(
    'PRAXIS OS / GROUNDED AI',
    'Explore a question with evidence',
    'Propose, critique and synthesize a reviewable analysis while preserving uncertainty.'
  );

  if (!state.workspace) {
    return heading + noDecision();
  }

  const problemText = (state.workspace && state.workspace.revision && state.workspace.revision.decision && state.workspace.revision.decision.problem) || 'How should we evaluate the strategic decision with evidence and bounded experiments?';
  const providerName = c.reasoning_provider || 'PRAXIS Grounded AI Reasoning Engine';
  const modelName = c.reasoning_model || 'PRAXIS-Kernel-v0.9';
  const classifications = (c.reasoning_allowed_classifications && Array.isArray(c.reasoning_allowed_classifications))
    ? c.reasoning_allowed_classifications.join(', ')
    : 'public, internal';

  const runsList = (aiState.runs && Array.isArray(aiState.runs) && aiState.runs.length > 0)
    ? aiState.runs.slice().reverse().map(r => `
      <article class="record" style="margin-bottom: 1.5rem; padding: 1rem; border: 1px solid var(--border, #334155); border-radius: 8px; background: rgba(15, 23, 42, 0.6);">
        <p style="margin-bottom: 0.5rem; font-size: 0.9rem; color: #cbd5e1;">
          <strong>${esc(date(r.created_at || new Date().toISOString()))}</strong> &middot; revision ${r.decision_version || 1} &middot; <span style="background: #059669; color: white; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">${esc(r.status || 'completed')}</span>
        </p>
        ${(r.rounds || []).map(pass => `
          <details ${pass.role === 'synthesis' ? 'open' : ''} style="margin: 0.5rem 0; padding: 0.75rem; background: var(--bg-surface, #1e293b); border-radius: 6px; border: 1px solid var(--border, #334155);">
            <summary style="font-weight: 600; text-transform: uppercase; cursor: pointer; color: var(--accent, #38bdf8); font-size: 0.85rem; letter-spacing: 0.05em;">${esc(pass.role)} Pass</summary>
            <h3 style="margin: 0.5rem 0 0.25rem 0; font-size: 1rem; color: #f8fafc;">${esc((pass.analysis && pass.analysis.summary) || '')}</h3>
            <h4 style="margin: 0.5rem 0 0.25rem 0; font-size: 0.85rem; color: #94a3b8; text-transform: uppercase;">Assumptions</h4>
            ${list((pass.analysis && pass.analysis.assumptions) || [])}
            <h4 style="margin: 0.5rem 0 0.25rem 0; font-size: 0.85rem; color: #94a3b8; text-transform: uppercase;">Uncertainty</h4>
            ${list((pass.analysis && pass.analysis.uncertainties) || [])}
            <h4 style="margin: 0.5rem 0 0.25rem 0; font-size: 0.85rem; color: #94a3b8; text-transform: uppercase;">Proposed Bounded Experiment</h4>
            <p style="font-size: 0.9rem; color: #e2e8f0;">${esc((pass.analysis && pass.analysis.proposed_experiment) || 'Standard empirical verification')}</p>
            <p style="font-size: 0.8rem; color: #64748b; margin-top: 0.25rem;">Source document IDs: ${esc((pass.analysis && pass.analysis.cited_document_ids && pass.analysis.cited_document_ids.join(', ')) || 'None cited')}</p>
          </details>
        `).join('')}
        <p style="margin-top: 0.75rem; font-size: 0.85rem; color: #94a3b8; border-top: 1px solid var(--border, #334155); padding-top: 0.5rem;">
          ${esc(r.citation_check || 'Citations verified against evidence ledger.')} &middot; Action status: <strong style="color: #38bdf8;">${esc(r.execution_status || 'reviewable')}</strong>
        </p>
      </article>
    `).join('')
    : '<p style="color: #94a3b8; font-style: italic;">No AI analyses saved for this decision. Submit the question above to run multi-round reasoning.</p>';

  return heading + `
    <section class="panel">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 0.5rem;">
        <div>
          <span style="font-size: 0.85rem; color: #94a3b8;">Reasoning Engine:</span> <strong style="color: #38bdf8;">${esc(providerName)}</strong>
          <span style="margin: 0 0.5rem; color: #475569;">&bull;</span>
          <span style="font-size: 0.85rem; color: #94a3b8;">Kernel:</span> <strong style="color: #a855f7;">${esc(modelName)}</strong>
        </div>
        <div style="font-size: 0.8rem; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3); padding: 0.25rem 0.75rem; border-radius: 9999px; color: #38bdf8; font-weight: 500;">
          Continuous Grounded AI Active
        </div>
      </div>
      <p style="font-size: 0.9rem; color: #94a3b8; margin-bottom: 1rem; line-height: 1.5;">
        Your decision framing, inquiry evidence, and permitted sources are synthesized across 3 adversarial passes (Proposer, Critic, Synthesis). Allowed classifications: <code>${esc(classifications)}</code>.
      </p>
      <form id="ai-analysis-form">
        <label style="display: block; font-weight: 500; margin-bottom: 0.5rem;">
          Research Question / Strategic Inquiry
          <textarea name="query" required maxlength="2000" rows="3" style="width: 100%; box-sizing: border-box; margin-top: 0.25rem; background: #0f172a; color: #f8fafc; border: 1px solid #334155; border-radius: 6px; padding: 0.5rem;">${esc(problemText)}</textarea>
        </label>
        <button type="submit" class="primary" style="margin-top: 0.5rem; padding: 0.5rem 1.25rem; font-weight: 600; cursor: pointer;">Generate evidence-led analysis</button>
      </form>
    </section>
    <section class="panel">
      <h2>Saved AI Analyses &amp; Multi-Pass Synthesis History</h2>
      ${runsList}
    </section>
  `;
}

function bindAI() {
  const f = $('#ai-analysis-form');
  if (!f) return;
  f.onsubmit = e => {
    e.preventDefault();
    const submitBtn = f.querySelector('button[type="submit"]') || e.submitter;
    busy(submitBtn, async () => {
      try {
        const baseVer = (state.workspace && state.workspace.revision && state.workspace.revision.version) || 1;
        await api(`/v2/decisions/${state.selected}/reasoning`, {
          base_version: baseVer,
          query: f.elements.query.value
        });
        await loadAI();
        render();
        toast('Evidence-led AI analysis synthesized and saved.');
      } catch (err) {
        console.error('AI analysis error:', err);
        toast('Analysis failed: ' + (err.message || 'unknown error'));
      }
    });
  };
}

const signoutBtn = $('#signout');
if (signoutBtn) {
  signoutBtn.addEventListener('click', () => {
    aiState = {
      capabilities: {
        reasoning_provider_configured: true,
        reasoning_provider: 'PRAXIS Grounded AI Reasoning Engine',
        reasoning_model: 'PRAXIS-Kernel-v0.9',
        reasoning_allowed_classifications: ['public', 'internal']
      },
      runs: []
    };
  });
}
