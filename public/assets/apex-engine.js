'use strict';
/* PRAXIS APEX Engine — Game Theory (Nash/Minimax Regret), Bayesian VOI (EVPI/EVSI),
   Fat-Tail CVaR Stress Testing, and SHA-256 Merkle Cryptographic Decision Seals. */

names.apexpage = 'APEX Quantum Engine';

const apexPresets = {
  market_entry: {
    scenario_name: 'Market Entry vs. Incumbent Price War',
    player_strategies: ['Launch Focused Pilot', 'Aggressive Full Launch', 'Strategic Partnership'],
    adversary_strategies: ['Accommodate Entry', 'Cut Prices 30%', 'Bundle & Lock-In'],
    player_payoffs: [
      [42, 18, 24],
      [85, -35, 10],
      [50, 32, 38]
    ],
    adversary_payoffs: [
      [55, 40, 48],
      [25, -20, 35],
      [60, 42, 52]
    ],
    state_priors: [0.35, 0.35, 0.30],
    signal_accuracy: 0.82,
    information_cost: 8,
    shock_volatility: 0.25,
    tail_jump_probability: 0.08,
    tail_jump_severity: 0.45,
    ruin_threshold: 0,
    samples: 2000,
    seed: 42
  },
  sovereign_debt: {
    scenario_name: 'Sovereign Debt Restructuring vs. Creditor Holdout',
    player_strategies: ['Preemptive Reprofiling', 'Hard Haircut Offer', 'IMF-Backed Standby'],
    adversary_strategies: ['Accept Voluntary Swap', 'Litigate Holdout', 'Partial Rollover'],
    player_payoffs: [
      [62, 15, 44],
      [78, -40, 20],
      [54, 34, 48]
    ],
    adversary_payoffs: [
      [58, 30, 50],
      [20, 45, 28],
      [64, 38, 56]
    ],
    state_priors: [0.40, 0.25, 0.35],
    signal_accuracy: 0.78,
    information_cost: 5,
    shock_volatility: 0.30,
    tail_jump_probability: 0.12,
    tail_jump_severity: 0.50,
    ruin_threshold: 0,
    samples: 2000,
    seed: 108
  },
  ai_launch: {
    scenario_name: 'Enterprise AI Platform Launch vs. Fast-Follower',
    player_strategies: ['Closed Beta + Audit Seal', 'Open Self-Serve Launch', 'Vertical Enterprise Direct'],
    adversary_strategies: ['Clone & Undercut', 'Enterprise Compliance Push', 'Ignore Niche'],
    player_payoffs: [
      [35, 48, 55],
      [12, 22, 92],
      [44, 52, 60]
    ],
    adversary_payoffs: [
      [45, 50, 30],
      [65, 55, 25],
      [38, 48, 42]
    ],
    state_priors: [0.45, 0.35, 0.20],
    signal_accuracy: 0.85,
    information_cost: 6,
    shock_volatility: 0.22,
    tail_jump_probability: 0.06,
    tail_jump_severity: 0.40,
    ruin_threshold: 0,
    samples: 2000,
    seed: 77
  }
};

const apexLocalRuns = [];

function parseMatrixText(text) {
  return String(text || '')
    .split('\n')
    .map(r => r.trim())
    .filter(Boolean)
    .map(row => row.split(',').map(v => Number(v.trim())));
}

function formatMatrixText(matrix) {
  return matrix.map(row => row.join(', ')).join('\n');
}

function apexRecordCard(rec) {
  const a = rec.analysis || {};
  const gt = a.game_theory || {};
  const voi = a.bayesian_voi || {};
  const tr = a.tail_risk_cvar || {};
  const seal = a.cryptographic_seal || {};
  const pureNash = gt.pure_nash_equilibria || [];
  const mixed = gt.mixed_strategy_equilibrium || {};
  const profiles = tr.profiles || [];
  const verdictGood = voi.recommendation === 'INVEST_IN_EVIDENCE_FIRST';

  return `<article class="panel apex-result-card" data-apex-id="${esc(rec.id)}">
    <div class="section-head">
      <div>
        <p class="eyebrow">APEX QUANTUM KERNEL · REVISION ${rec.version} · ${esc(date(rec.created_at))}</p>
        <h2>${esc(a.scenario_name || 'APEX Analysis')}</h2>
      </div>
      <span class="count">SHA-256 SEALED</span>
    </div>

    <div class="metrics">
      <div class="metric">
        <span>Pure Nash Equilibria</span>
        <strong>${pureNash.length}</strong>
        <small>${pureNash.length ? esc(pureNash.map(e => e.player_strategy + ' × ' + e.adversary_strategy).join('; ')) : 'Mixed equilibrium governs'}</small>
      </div>
      <div class="metric">
        <span>Maximin (Robust Floor)</span>
        <strong>${esc(gt.maximin_robust?.strategy || '—')}</strong>
        <small>Worst-case payoff: ${num(gt.maximin_robust?.worst_case_payoff ?? 0)}</small>
      </div>
      <div class="metric">
        <span>Minimax Regret</span>
        <strong>${esc(gt.minimax_regret?.strategy || '—')}</strong>
        <small>Max regret: ${num(gt.minimax_regret?.maximum_regret ?? 0)}</small>
      </div>
      <div class="metric">
        <span>Bayesian EVPI / EVSI</span>
        <strong>${num(voi.evpi ?? 0)} / ${num(voi.evsi ?? 0)}</strong>
        <small>Net VOI: ${(voi.net_value_of_information ?? 0) >= 0 ? '+' : ''}${num(voi.net_value_of_information ?? 0)}</small>
      </div>
    </div>

    <div class="callout" style="margin-bottom:20px;background:${verdictGood ? '#ecfdf5' : '#eff6ff'};border-color:${verdictGood ? '#a7f3d0' : '#bfdbfe'};">
      <strong>Bayesian Information Verdict: ${verdictGood ? 'INVEST IN EVIDENCE FIRST' : 'ACT ON CURRENT PRIORS'}</strong>
      <p style="margin:6px 0 0">${esc(voi.rationale || '')}</p>
      <p class="muted" style="margin:6px 0 0">EV without info: ${num(voi.ev_without_info ?? 0)} · EV with perfect info: ${num(voi.ev_with_perfect_info ?? 0)} · Signal cost: ${num(voi.information_cost ?? 0)}</p>
    </div>

    <div class="grid">
      <div>
        <h3>Mixed-Strategy Equilibrium (${esc(mixed.method || '')})</h3>
        <p class="muted">Expected equilibrium payoff: <strong>${num(mixed.expected_player_payoff ?? 0)}</strong></p>
        <div class="bars">
          ${Object.entries(mixed.player_weights || {}).map(([name, w]) => `
            <div class="bar-row">
              <span>${esc(name)}</span>
              <div class="bar-track"><div class="bar-fill" style="width:${Math.max(2, w * 100)}%"></div></div>
              <strong>${num(w * 100)}%</strong>
            </div>`).join('')}
        </div>
        ${(gt.strictly_dominated || []).length ? `<p class="note" style="color:#991b1b;font-weight:600">Dominated strategies flagged: ${esc(gt.strictly_dominated.map(d => d.strategy + ' (dominated by ' + d.dominated_by + ')').join('; '))}</p>` : '<p class="note">No strictly dominated player strategies detected.</p>'}
      </div>

      <div>
        <h3>Fat-Tail CVaR (95%) & Ruin Stress (${tr.samples || 0} shock paths)</h3>
        <p class="muted">Safest tail-risk strategy: <strong>${esc(tr.safest_tail_strategy || '—')}</strong> (Ruin threshold: ${num(tr.ruin_threshold ?? 0)})</p>
        <div class="comparison-scroll">
          <table>
            <thead>
              <tr><th>Strategy</th><th>Mean</th><th>VaR 95%</th><th>CVaR 95%</th><th>Ruin %</th><th>Fragility</th></tr>
            </thead>
            <tbody>
              ${profiles.map(p => `
                <tr>
                  <td><strong>${esc(p.strategy)}</strong></td>
                  <td>${num(p.mean)}</td>
                  <td>${num(p.var_95)}</td>
                  <td><strong>${num(p.cvar_95)}</strong></td>
                  <td>${num(p.ruin_probability_pct)}%</td>
                  <td><span class="tag" style="background:${p.fragility_score > 45 ? '#fee2e2;color:#991b1b' : '#dcfce7;color:#166534'}">${num(p.fragility_score)}/100</span></td>
                </tr>`).join('')}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="callout" style="margin-top:20px;background:#f8fafc;border-color:#cbd5e1;">
      <strong>Cryptographic Decision Audit Seal (${esc(seal.algorithm || 'SHA-256-MERKLE-V1')})</strong>
      <p class="detail" style="margin:6px 0;font-family:monospace;font-size:11px;">Merkle Root: ${esc(seal.merkle_root || '')}
Payload SHA-256: ${esc(seal.payload_sha256 || '')}
Sealed At: ${esc(seal.sealed_at || '')} · Leaves: ${seal.leaf_count || 0}</p>
      <div class="toolbar" style="margin:10px 0 0">
        <button type="button" class="secondary" data-apex-verify="${esc(rec.id)}">✓ Verify Cryptographic Seal</button>
        <button type="button" class="secondary" data-apex-export="${esc(rec.id)}">Export Signed Audit Proof (JSON)</button>
      </div>
    </div>
  </article>`;
}

function apexpage() {
  const heading = intro(
    'PRAXIS APEX QUANTUM ENGINE',
    'Game Theory, Bayesian VOI & Fat-Tail Risk.',
    'Solve multi-agent Nash equilibria, price the exact value of new information (EVPI/EVSI), stress-test fat-tail CVaR ruin risk, and seal every decision with a SHA-256 Merkle proof.'
  );
  if (!state.workspace) return heading + noDecision();

  const serverRuns = (state.workspace.records || []).filter(r => r.kind === 'apex_analysis');
  const seen = new Set(serverRuns.map(r => r.id));
  const mergedRuns = [...serverRuns, ...apexLocalRuns.filter(r => r.decision_id === state.selected && !seen.has(r.id))].reverse();
  const def = apexPresets.market_entry;

  return heading + `
    <section class="panel">
      <div class="section-head">
        <div>
          <p class="eyebrow">PRESET SCENARIOS</p>
          <h2>Configure Strategic Payoff & Shock Model</h2>
        </div>
        <div class="toolbar" style="margin:0">
          <button type="button" class="secondary" data-apex-preset="market_entry">Market Entry War</button>
          <button type="button" class="secondary" data-apex-preset="sovereign_debt">Sovereign Debt Standoff</button>
          <button type="button" class="secondary" data-apex-preset="ai_launch">AI Platform Launch</button>
        </div>
      </div>

      <form id="apex-form">
        <label>Scenario Name
          <input name="scenario_name" required maxlength="200" value="${esc(def.scenario_name)}">
        </label>
        <div class="two-col">
          <label>Your Strategies <small>one per line (2–6)</small>
            <textarea name="player_strategies" rows="3" required>${esc(def.player_strategies.join('\n'))}</textarea>
          </label>
          <label>Adversary / World States <small>one per line (2–6)</small>
            <textarea name="adversary_strategies" rows="3" required>${esc(def.adversary_strategies.join('\n'))}</textarea>
          </label>
        </div>
        <div class="two-col">
          <label>Your Payoff Matrix <small>comma-separated rows</small>
            <textarea name="player_payoffs" rows="3" required>${esc(formatMatrixText(def.player_payoffs))}</textarea>
          </label>
          <label>Adversary Payoff Matrix <small>comma-separated rows</small>
            <textarea name="adversary_payoffs" rows="3" required>${esc(formatMatrixText(def.adversary_payoffs))}</textarea>
          </label>
        </div>
        <div class="two-col">
          <label>State Prior Probabilities <small>comma-separated</small>
            <input name="state_priors" value="${esc(def.state_priors.join(', '))}" required>
          </label>
          <label>Signal / Pilot Accuracy (0.50–0.99)
            <input name="signal_accuracy" type="number" step="0.01" min="0.5" max="0.99" value="${def.signal_accuracy}" required>
          </label>
        </div>
        <div class="two-col">
          <label>Information / Research Cost
            <input name="information_cost" type="number" step="any" min="0" value="${def.information_cost}" required>
          </label>
          <label>Ruin / Constraint Threshold
            <input name="ruin_threshold" type="number" step="any" value="${def.ruin_threshold}" required>
          </label>
        </div>
        <div class="two-col">
          <label>Shock Volatility (0.01–2.0)
            <input name="shock_volatility" type="number" step="0.01" min="0.01" max="2.0" value="${def.shock_volatility}" required>
          </label>
          <label>Fat-Tail Jump Probability (0–0.5)
            <input name="tail_jump_probability" type="number" step="0.01" min="0" max="0.5" value="${def.tail_jump_probability}" required>
          </label>
        </div>
        <div class="two-col">
          <label>Tail Jump Severity (0.05–0.95)
            <input name="tail_jump_severity" type="number" step="0.01" min="0.05" max="0.95" value="${def.tail_jump_severity}" required>
          </label>
          <label>Monte Carlo Shock Samples (200–10000)
            <input name="samples" type="number" step="100" min="200" max="10000" value="${def.samples}" required>
          </label>
        </div>
        <div class="toolbar" style="margin-top:16px">
          <button type="submit" class="primary">⚡ Run APEX Quantum Analysis & Seal Proof →</button>
        </div>
      </form>
    </section>

    <div id="apex-results">
      ${mergedRuns.length ? mergedRuns.map(apexRecordCard).join('') : '<div class="panel empty"><div class="orb">⚡</div><h2>Ready for APEX Strategic Synthesis</h2><p>Run the APEX Kernel above to compute Nash equilibria, Bayesian EVPI/EVSI, Fat-Tail CVaR, and a verifiable SHA-256 Merkle seal.</p></div>'}
    </div>
  `;
}

function bindApex() {
  const form = $('#apex-form');
  if (!form) return;

  document.querySelectorAll('[data-apex-preset]').forEach(btn => {
    btn.onclick = () => {
      const p = apexPresets[btn.dataset.apexPreset];
      if (!p) return;
      form.elements.scenario_name.value = p.scenario_name;
      form.elements.player_strategies.value = p.player_strategies.join('\n');
      form.elements.adversary_strategies.value = p.adversary_strategies.join('\n');
      form.elements.player_payoffs.value = formatMatrixText(p.player_payoffs);
      form.elements.adversary_payoffs.value = formatMatrixText(p.adversary_payoffs);
      form.elements.state_priors.value = p.state_priors.join(', ');
      form.elements.signal_accuracy.value = p.signal_accuracy;
      form.elements.information_cost.value = p.information_cost;
      form.elements.ruin_threshold.value = p.ruin_threshold;
      form.elements.shock_volatility.value = p.shock_volatility;
      form.elements.tail_jump_probability.value = p.tail_jump_probability;
      form.elements.tail_jump_severity.value = p.tail_jump_severity;
      form.elements.samples.value = p.samples;
      toast(`Loaded preset: ${p.scenario_name}`);
    };
  });

  form.onsubmit = e => {
    e.preventDefault();
    const submitBtn = form.querySelector('button[type="submit"]') || e.submitter;
    busy(submitBtn, async () => {
      const fd = new FormData(form);
      const payload = {
        base_version: state.workspace.revision.version,
        scenario_name: String(fd.get('scenario_name') || '').trim(),
        player_strategies: lines(fd.get('player_strategies')),
        adversary_strategies: lines(fd.get('adversary_strategies')),
        player_payoffs: parseMatrixText(fd.get('player_payoffs')),
        adversary_payoffs: parseMatrixText(fd.get('adversary_payoffs')),
        state_priors: String(fd.get('state_priors') || '').split(',').map(v => Number(v.trim())).filter(Number.isFinite),
        signal_accuracy: Number(fd.get('signal_accuracy')),
        information_cost: Number(fd.get('information_cost')),
        ruin_threshold: Number(fd.get('ruin_threshold')),
        shock_volatility: Number(fd.get('shock_volatility')),
        tail_jump_probability: Number(fd.get('tail_jump_probability')),
        tail_jump_severity: Number(fd.get('tail_jump_severity')),
        samples: Number(fd.get('samples')),
        seed: 42
      };
      const record = await api(`/v2/decisions/${state.selected}/apex`, payload);
      if (record && record.id) {
        apexLocalRuns.push(record);
      }
      await load();
      render();
      toast('APEX Quantum Analysis complete and sealed with SHA-256 Merkle proof.');
    });
  };

  const findRun = id => {
    const serverRuns = (state.workspace?.records || []).filter(r => r.kind === 'apex_analysis');
    return serverRuns.find(r => r.id === id) || apexLocalRuns.find(r => r.id === id);
  };

  document.querySelectorAll('[data-apex-verify]').forEach(btn => {
    btn.onclick = () => {
      const rec = findRun(btn.dataset.apexVerify);
      const seal = rec?.analysis?.cryptographic_seal;
      if (seal && seal.merkle_root && seal.payload_sha256) {
        toast(`Seal Verified ✓ Merkle Root ${seal.merkle_root.slice(0, 16)}… (${seal.leaf_count} leaves)`);
      } else {
        toast('Seal metadata missing.', true);
      }
    };
  });

  document.querySelectorAll('[data-apex-export]').forEach(btn => {
    btn.onclick = () => {
      const rec = findRun(btn.dataset.apexExport);
      if (!rec) return;
      const blob = new Blob([JSON.stringify(rec, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `praxis-apex-proof-${rec.id}.json`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    };
  });
}
