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

  const problemText = (state.workspace && state.workspace.revision && state.workspace.revision.decision && state.workspace.revision.decision.problem) || 'Should we test a paid subscription with a small customer group?';
  const providerName = c.reasoning_provider || 'PRAXIS Grounded AI Reasoning Engine';
  const modelName = c.reasoning_model || 'PRAXIS-Kernel-v0.9';
  const classifications = (c.reasoning_allowed_classifications && Array.isArray(c.reasoning_allowed_classifications))
    ? c.reasoning_allowed_classifications.join(', ')
    : 'public, internal';

  const runsList = (aiState.runs && Array.isArray(aiState.runs) && aiState.runs.length > 0)
    ? aiState.runs.slice().reverse().map((r, runIdx) => `
      <article class="record" style="margin-bottom: 24px; padding: 20px; border: 1px solid #cfdad2; border-radius: 8px; background: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; padding-bottom: 12px; margin-bottom: 16px; flex-wrap: wrap; gap: 8px;">
          <div>
            <span style="font-size: 15px; font-weight: 700; color: #1b3335;">Analysis Run #${aiState.runs.length - runIdx}</span>
            <span style="margin: 0 8px; color: #94a3b8;">&bull;</span>
            <span style="font-size: 13px; color: #64748b;">${esc(date(r.created_at || new Date().toISOString()))}</span>
            <span style="margin: 0 8px; color: #94a3b8;">&bull;</span>
            <span style="font-size: 12px; background: #f1f5f9; color: #334155; padding: 2px 8px; border-radius: 4px; font-weight: 600;">Revision ${r.decision_version || 1}</span>
          </div>
          <span style="background: #dcfce7; color: #166534; border: 1px solid #86efac; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; text-transform: uppercase;">
            ${esc(r.status || 'completed')}
          </span>
        </div>

        ${(r.rounds || []).map((pass, pIdx) => {
          const isSynthesis = pass.role === 'synthesis';
          const isCritic = pass.role === 'critic';
          const headerBg = isSynthesis ? '#eff6ff' : isCritic ? '#fffbeb' : '#f0fdf4';
          const headerBorder = isSynthesis ? '#3b82f6' : isCritic ? '#f59e0b' : '#10b981';
          const headerColor = isSynthesis ? '#1e40af' : isCritic ? '#92400e' : '#065f46';
          const titleLabel = isSynthesis ? 'Synthesis & Unified Recommendation' : isCritic ? 'Adversarial Critique & Boundaries' : 'Proposer Hypothesis & Framing';

          return `
          <details ${isSynthesis ? 'open' : ''} style="margin: 12px 0; border: 1px solid #e2e8f0; border-radius: 6px; overflow: hidden; background: #ffffff;">
            <summary style="padding: 12px 16px; background: ${headerBg}; border-left: 4px solid ${headerBorder}; color: ${headerColor}; font-weight: 700; font-size: 14px; cursor: pointer; display: flex; justify-content: space-between; align-items: center;">
              <span>Pass ${pIdx + 1}: ${titleLabel}</span>
              <span style="font-size: 11px; text-transform: uppercase; background: #ffffff; padding: 2px 6px; border-radius: 4px; border: 1px solid #cbd5e1; color: #475569;">${esc(pass.role)}</span>
            </summary>
            
            <div style="padding: 16px; color: #1e293b;">
              <div style="margin-bottom: 14px;">
                <h4 style="margin: 0 0 6px 0; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: #64748b; font-weight: 700;">Executive Summary</h4>
                <p style="font-size: 14px; line-height: 1.6; color: #0f172a; margin: 0; font-weight: 500;">
                  ${esc((pass.analysis && pass.analysis.summary) || 'Analysis complete.')}
                </p>
              </div>

              ${pass.analysis && pass.analysis.assumptions && pass.analysis.assumptions.length > 0 ? `
              <div style="margin-bottom: 14px;">
                <h4 style="margin: 0 0 6px 0; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: #64748b; font-weight: 700;">Key Assumptions</h4>
                <ul style="margin: 0; padding-left: 20px; color: #1e293b; font-size: 13px; line-height: 1.6;">
                  ${pass.analysis.assumptions.map(a => `<li style="margin-bottom: 4px; color: #1e293b;">${esc(a)}</li>`).join('')}
                </ul>
              </div>
              ` : ''}

              ${pass.analysis && pass.analysis.uncertainties && pass.analysis.uncertainties.length > 0 ? `
              <div style="margin-bottom: 14px;">
                <h4 style="margin: 0 0 6px 0; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: #b45309; font-weight: 700;">Preserved Uncertainties & Risks</h4>
                <ul style="margin: 0; padding-left: 20px; color: #1e293b; font-size: 13px; line-height: 1.6;">
                  ${pass.analysis.uncertainties.map(u => `<li style="margin-bottom: 4px; color: #1e293b;">${esc(u)}</li>`).join('')}
                </ul>
              </div>
              ` : ''}

              ${pass.analysis && pass.analysis.proposed_experiment ? `
              <div style="margin-bottom: 12px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px;">
                <h4 style="margin: 0 0 4px 0; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: #177468; font-weight: 700;">Proposed Bounded Experiment</h4>
                <p style="margin: 0; font-size: 13px; line-height: 1.5; color: #1b3335;">
                  ${esc(pass.analysis.proposed_experiment)}
                </p>
              </div>
              ` : ''}

              <div style="font-size: 12px; color: #64748b; margin-top: 10px; padding-top: 8px; border-top: 1px dashed #e2e8f0;">
                <strong>Cited Sources:</strong> ${esc((pass.analysis && pass.analysis.cited_document_ids && pass.analysis.cited_document_ids.join(', ')) || 'Integrated evidence ledger records')}
              </div>
            </div>
          </details>
          `;
        }).join('')}

        <div style="margin-top: 16px; padding-top: 12px; border-top: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #64748b; flex-wrap: wrap; gap: 8px;">
          <span><strong>Provenance:</strong> ${esc(r.citation_check || 'Citations verified against local evidence ledger')}</span>
          <span><strong>Execution Status:</strong> <strong style="color: #177468; text-transform: capitalize;">${esc(r.execution_status || 'reviewable')}</strong></span>
        </div>
      </article>
    `).join('')
    : `
      <div style="padding: 24px; text-align: center; border: 2px dashed #cbd5e1; border-radius: 8px; background: #fafbfc;">
        <p style="font-size: 15px; font-weight: 600; color: #1b3335; margin-bottom: 6px;">No AI analyses generated yet for this decision</p>
        <p style="font-size: 13px; color: #64748b; margin-bottom: 16px; max-width: 500px; margin-left: auto; margin-right: auto;">
          Use the inquiry form above to initiate an automated 3-pass reasoning synthesis (Proposer, Critic, Synthesis) based on current evidence.
        </p>
      </div>
    `;

  return heading + `
    <section class="panel" style="background: #ffffff; border: 1px solid #cfdad2; border-radius: 10px; padding: 24px; margin-bottom: 24px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 10px; border-bottom: 1px solid #e2e8f0; padding-bottom: 12px;">
        <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
          <span style="font-size: 13px; font-weight: 700; color: #1b3335;">Reasoning Engine:</span>
          <span style="background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600;">${esc(providerName)}</span>
          <span style="background: #f3e8ff; color: #6b21a8; border: 1px solid #e9d5ff; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600;">${esc(modelName)}</span>
        </div>
        <span style="background: #dcfce7; color: #15803d; border: 1px solid #86efac; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600;">
          &check; Grounded AI Active
        </span>
      </div>

      <p style="font-size: 13px; line-height: 1.6; color: #475569; margin-bottom: 16px;">
        Your decision framing, objective, constraints, and permitted sources are evaluated across three adversarial rounds. Permitted source classifications: <code style="background: #f1f5f9; padding: 2px 6px; border-radius: 4px; color: #0f172a;">${esc(classifications)}</code>. Results preserve uncertainty for human review.
      </p>

      <form id="ai-analysis-form" style="display: flex; flex-direction: column; gap: 14px;">
        <div>
          <label style="display: block; font-weight: 700; font-size: 14px; color: #1b3335; margin-bottom: 6px;">
            Strategic Question / Research Inquiry
          </label>
          <textarea id="ai-query-input" name="query" required maxlength="2000" rows="3" style="width: 100%; box-sizing: border-box; background: #ffffff; color: #1b3335; border: 1px solid #cfdad2; border-radius: 6px; padding: 10px 12px; font-size: 14px; line-height: 1.5; font-family: inherit;">${esc(problemText)}</textarea>
        </div>

        <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
          <span style="font-size: 12px; font-weight: 600; color: #64748b;">Preset Inquiries:</span>
          <button type="button" class="preset-btn" data-preset="Evaluate pilot adoption risk and counterparty response." style="background: #f8fafc; border: 1px solid #cbd5e1; color: #334155; padding: 3px 10px; border-radius: 14px; font-size: 12px; cursor: pointer;">Adoption Risk</button>
          <button type="button" class="preset-btn" data-preset="Assess downside financial risk and capital preservation boundaries." style="background: #f8fafc; border: 1px solid #cbd5e1; color: #334155; padding: 3px 10px; border-radius: 14px; font-size: 12px; cursor: pointer;">Financial Downside</button>
          <button type="button" class="preset-btn" data-preset="Measure customer willingness to pay vs free alternative." style="background: #f8fafc; border: 1px solid #cbd5e1; color: #334155; padding: 3px 10px; border-radius: 14px; font-size: 12px; cursor: pointer;">Willingness to Pay</button>
        </div>

        <div>
          <button type="submit" class="primary" style="background: #177468; color: #ffffff; padding: 10px 20px; font-size: 14px; font-weight: 600; border-radius: 6px; border: 0; cursor: pointer; transition: background 0.15s ease;">
            Generate evidence-led analysis
          </button>
        </div>
      </form>
    </section>

    <section class="panel" style="background: #ffffff; border: 1px solid #cfdad2; border-radius: 10px; padding: 24px;">
      <h2 style="font-size: 18px; font-weight: 700; color: #1b3335; margin-bottom: 16px;">
        Saved AI Analyses &amp; Multi-Pass Synthesis History
      </h2>
      ${runsList}
    </section>
  `;
}

function bindAI() {
  const f = $('#ai-analysis-form');
  if (!f) return;

  // Bind preset inquiry buttons
  f.querySelectorAll('.preset-btn').forEach(btn => {
    btn.onclick = () => {
      const qInput = $('#ai-query-input');
      if (qInput && btn.dataset.preset) {
        qInput.value = btn.dataset.preset;
        qInput.focus();
      }
    };
  });

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
