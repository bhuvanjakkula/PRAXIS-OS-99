'use strict';
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const lines = s => String(s).split('\n').map(x => x.trim()).filter(Boolean);
const list = items => `<ul class="list">${items.map(s => `<li>${esc(s)}</li>`).join('')}</ul>`;
const num = x => Number(x).toLocaleString(undefined, {maximumFractionDigits:2});
const date = x => new Date(x).toLocaleString();
const names = {
  dashboard: 'Dashboard',
  chat: 'Structured Inquiry',
  canvas: 'Decision Canvas',
  simulation: 'Quantitative Simulation',
  reports: 'Decision Reports',
  pricing: 'Plans & Pricing',
  decisionlab: 'Decision Lab',
  inquirypage: 'Practical Inquiry',
  computepage: 'Decision Compute',
  aipage: 'AI Solutions & Analysis',
  researchpage: 'Grounded Research',
  foresightpage: 'Foresight & Prediction',
  enterprise: 'Enterprise Operations',
  sources: 'Document Sources',
  labs: 'Labs Registry',
  imfpage: 'IMF Macro Solutions',
  worldbankpage: 'World Bank Development',
  nationalpage: 'National Strategy',
  policypage: 'Policy Comparison & Scorecard',
  cmopage: 'CMO Marketing & Growth',
  ceopage: 'Executive CEO Cockpit',
  cfopage: 'Executive CFO Capital',
  ctopage: 'Executive CTO Architecture',
  aircrewpage: 'Aviation Security Operations',
  shipcaptainpage: 'Maritime Fusion Coordination'
};
const state = {page:location.hash==='#maritime'?'shipcaptainpage':location.hash==='#aircrew'?'aircrewpage':location.hash==='#cto'?'ctopage':location.hash==='#country'?'nationalpage':location.hash==='#cmo'?'cmopage':location.hash==='#policy'?'policypage':location.hash==='#foresight'?'foresightpage':location.hash==='#research'?'researchpage':'dashboard', decisions:[], selected:null, workspace:null, mode:'scenario', simulation:null};
let toastTimer;
let accessToken=null;
function toast(message, error=false) { const t=$('#toast'); t.textContent=message; t.hidden=false; t.classList.toggle('error',error); clearTimeout(toastTimer); toastTimer=setTimeout(()=>t.hidden=true,7000); }
async function api(path, body) {
  const headers = accessToken ? { Authorization: 'Bearer ' + accessToken } : {};
  const response = await fetch(path, {
    method: body === undefined ? 'GET' : 'POST',
    headers: body === undefined ? headers : { ...headers, 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
    credentials: 'same-origin'
  });
  if (response.status === 401) {
    accessToken = null;
    $('#login-dialog').showModal();
    throw new Error('Sign in with a valid, unexpired credential.');
  }
  const contentType = response.headers.get('content-type') || '';
  if (!response.ok) {
    let detail = `Server error (${response.status})`;
    if (contentType.includes('application/json')) {
      try {
        const data = await response.json();
        detail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      } catch (_) {}
    }
    throw new Error(detail);
  }
  if (!contentType.includes('application/json')) {
    const text = await response.text();
    if (text.includes('Vercel Authentication') || text.includes('sso-api')) {
      throw new Error('Vercel Deployment Protection (SSO) is active on this URL. Please disable Vercel Authentication in Project Settings -> Deployment Protection.');
    }
    throw new Error(`Unexpected non-JSON response from server (${response.status})`);
  }
  return response.json();
}
async function busy(button, work) { button.disabled=true; try { await work(); } catch(e) { toast(e.message,true); } finally { button.disabled=false; } }
async function load() { state.decisions=await api('/v1/decision-models'); if(!state.selected && state.decisions.length) state.selected=state.decisions[0].decision_id; if(state.selected) state.workspace=await api(`/v1/decision-models/${state.selected}/workspace`); }
async function select(id) { state.selected=id; state.simulation=null; state.workspace=await api(`/v1/decision-models/${id}/workspace`); if(typeof loadAI==='function')await loadAI(); render(); }
function selector() { return `<label class="decision-selector"><span class="muted">Active decision</span><select id="active-decision" aria-label="Active decision">${state.decisions.map(d=>`<option value="${esc(d.decision_id)}" ${d.decision_id===state.selected?'selected':''}>${esc(d.decision.title)} · v${d.version}</option>`).join('')}</select></label>`; }
function intro(eyebrow,title,description,choose=true) {return `<div class="intro"><div><p class="eyebrow">${esc(eyebrow)}</p><h1>${esc(title)}</h1><p>${esc(description)}</p></div>${choose&&state.decisions.length?selector():''}</div>`;}
function noDecision() {return `<div class="panel empty"><div class="orb">◇</div><h2>Every decision starts with a question.</h2><p>Frame the problem, name your values, and explore the consequences before committing.</p><button class="primary" data-new>Create your first decision →</button></div>`;}
function perspectiveName(name){return ({newton:'Evidence',geometer:'Systems',blake:'Human values',dewey:'Experiment & learning','Human / Blake':'Human values',Geometer:'Systems',Dewey:'Experiment & learning'})[name]||name;}
function perspectiveFinding(text){return String(text).replace(/^(newton|geometer|blake|dewey):/i,(_,name)=>perspectiveName(name.toLowerCase())+':');}
function engines(){return `<div class="panel"><div class="section-head"><h3>Domain perspectives</h3><span class="count">5 ENGINES</span></div><div class="engine-list">${[['B','Business','Value, demand & strategy'],['F','Finance','Cash, capital & downside'],['T','Technology','Architecture & dependencies'],['L','Law','Obligations & source review'],['H','Human values','Values & lived consequences']].map(([a,b,c])=>`<div class="engine"><b>${a}</b><div><strong>${b}</strong><small>${c}</small></div></div>`).join('')}</div><p class="note">Deterministic inquiry engines. Autonomous agents and live connectors are not active.</p></div>`;}
function dashboard(){
  const total=state.decisions.length, evidence=state.decisions.reduce((n,d)=>n+d.decision.evidence.length,0), feedback=state.decisions.reduce((n,d)=>n+d.version-1,0), risks=state.decisions.reduce((n,d)=>n+d.risks.length,0);
  return intro('DECISION INTELLIGENCE','A clearer view. A better decision.','Connect perspectives. Test assumptions. Learn from what happens.',false)+
  `<div class="metrics">${[['Decision models',total,'Stored in your local workspace'],['Model evidence',evidence,'User-supplied claims & assumptions'],['Risk prompts',risks,'Review before commitment'],['Feedback revisions',feedback,'Learning preserved over time']].map(([label,value,note])=>`<div class="metric"><span>${label}</span><strong>${value.toString().padStart(2,'0')}</strong><small>${note}</small></div>`).join('')}</div>
  <div class="grid"><div><div class="panel"><div class="section-head"><h2>Your decisions</h2><span class="count">${total} MODELS</span></div>${total?state.decisions.map(r=>`<button class="decision-row" data-open="${r.decision_id}"><span><strong>${esc(r.decision.title)}</strong><small>${esc(r.decision.objective)}</small></span><span class="tag">Revision ${r.version} ↗</span></button>`).join(''):noDecision()}</div>
  <div class="panel"><p class="eyebrow">THE PRAXIS OS LOOP</p><h2>Reason across the whole system.</h2><p class="muted">Human values connect every stage, from the first question to the next revision.</p><div class="path"><span>Values</span>→<span>Domain inquiry</span>→<span>Knowledge graph</span>→<span>Simulation</span>→<span>Human judgment</span>→<span>Feedback ↺</span></div></div></div><div>${engines()}<div class="callout"><strong>Built for inquiry, guided by people.</strong>Models expose assumptions. Simulations explore possibilities. You own the final judgment.</div></div></div>`;
}
function chat(){
  let html=intro('STRUCTURED INQUIRY','Think through the decision.','A guided conversation with your model. No language model is connected.');
  if(!state.workspace)return html+noDecision();
  const {revision:r,plan}=state.workspace;
  return html+`<div class="grid"><div><div class="message"><p class="eyebrow">YOUR QUESTION</p><h2>${esc(r.decision.problem)}</h2><p class="muted">Objective: ${esc(r.decision.objective)}</p></div><div class="panel"><div class="section-head"><h2>Orchestrator response</h2><span class="count">REVISION ${r.version}</span></div><p class="muted">Rule-based perspectives and review questions, grounded in the model inputs.</p>${r.report.insights.map(i=>`<details class="insight" ${i.engine==='geometer'?'open':''}><summary>${esc(perspectiveName(i.engine))} perspective</summary>${list(i.findings.map(perspectiveFinding))}<p class="eyebrow">QUESTIONS TO EXPLORE</p>${list(i.questions)}</details>`).join('')}</div>
  <div class="panel"><h2>Add an observation</h2><p class="muted">Record what happened and what you learned. This creates a new model revision.</p><form id="feedback-form"><label>Observed outcome<textarea name="summary" required rows="2" placeholder="What actually happened?"></textarea></label><label>Source<input name="source" required placeholder="Report, interview, experiment or observation record"></label><label>Learning<textarea name="learning" required rows="2" placeholder="What should the next inquiry take into account?"></textarea></label><button class="primary">Save feedback & update model →</button></form></div></div>
  <div><div class="panel"><h2>Inquiry plan</h2>${plan.map(p=>`<div class="step"><b>${p.step}</b><div><p>${esc(p.task)}</p><small>${esc(perspectiveName(p.engine))}</small></div></div>`).join('')}</div><div class="panel"><p class="eyebrow">HUMAN VALUES</p><h2>Values that guide this inquiry</h2>${r.values.length?list(r.values):'<p class="muted">No values were supplied. Review this gap before committing.</p>'}</div></div></div>`;
}
function graphMarkup(graph){
  const nodes=graph.nodes.slice(0,13), root=nodes[0], n=nodes.length-1;
  if(!root)return '<p class="muted">No graph nodes yet.</p>';
  const positions=new Map([[root.id,{x:370,y:300}]]);
  nodes.slice(1).forEach((node,i)=>{const side=i%2,row=Math.floor(i/2),rows=Math.ceil(n/2);positions.set(node.id,{x:side?625:115,y:rows<=1?300:50+row*500/(rows-1)});});
  return `<svg class="graph" viewBox="0 0 740 600" role="group" aria-label="Decision knowledge graph">${graph.edges.filter(e=>positions.has(e.source_id)&&positions.has(e.target_id)).map(e=>{const a=positions.get(e.source_id),b=positions.get(e.target_id);return `<line class="edge" x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}"><title>${esc(e.relation)}</title></line>`;}).join('')}${nodes.map((node,i)=>{const p=positions.get(node.id);return `<g class="node ${i===0?'root':''}" tabindex="0" role="button" aria-label="${esc(node.node_type+': '+node.label)}" data-node="${esc(node.id)}" transform="translate(${p.x-73},${p.y-22})"><rect width="146" height="44" rx="7"/><text x="73" y="16" text-anchor="middle" style="font-size:8px;letter-spacing:1px">${esc(node.node_type.toUpperCase())}</text><text x="73" y="32" text-anchor="middle">${esc(node.label.length>22?node.label.slice(0,21)+'…':node.label)}</text></g>`;}).join('')}</svg>`;
}
function canvas(){
  let html=intro('SYSTEMS & DEPENDENCIES','The decision, connected.','Explore evidence, values, risks, options and the relationships between them.');
  if(!state.workspace)return html+noDecision();
  const w=state.workspace,r=w.revision,judgments=w.records.filter(x=>x.kind==='judgment');
  return html+`<div class="grid"><div><div class="panel"><div class="section-head"><h2>PRAXIS OS knowledge graph</h2><span class="count">${w.graph.nodes.length} NODES · ${w.graph.edges.length} LINKS</span></div><div class="canvas-wrap">${graphMarkup(w.graph)}</div><p class="note">Select a node to inspect its source and properties. Lines represent model relationships, not proven causation.${w.graph.nodes.length>13?' The visual shows the first 13 nodes; every node is listed below.':''}</p><div class="graph-list">${w.graph.nodes.map(n=>`<button data-node="${esc(n.id)}">${esc(n.node_type)} · ${esc(n.label)}</button>`).join('')}</div></div>
  <div class="panel"><h2>Evidence management</h2><p class="muted">Ledger claims retain epistemic type, provenance and review status.</p>${w.claims.length?list(w.claims.map(c=>`${c.claim_type} · ${c.statement} (${c.status})`)):'<p class="muted">No ledger claims added yet.</p>'}<form id="evidence-form"><label>Statement<input name="statement" required></label><div class="two-col"><label>Type<select name="claim_type"><option value="assumption">Assumption</option><option value="hypothesis">Hypothesis</option><option value="fact">Declared fact</option><option value="prediction">Prediction</option><option value="inference">Inference</option><option value="human_judgment">Human judgment</option><option value="value">Value</option></select></label><label>Source title<input name="source" required></label></div><button class="secondary">Add unverified claim</button></form></div>
  </div>
  <div><div class="panel"><h2>Node inspector</h2><div id="node-inspector" class="detail muted">Select any node in the graph.</div></div><div class="panel"><h2>Uncertainty & conflicts</h2>${w.conflicts.length?list(w.conflicts.map(c=>`${c.subject}: ${c.values.join(' versus ')} — needs human review`)):'<p class="muted">No explicit “subject = value” disagreements found. This is not a semantic conflict audit.</p>'}${list(r.report.uncertainties.slice(0,4))}</div><div class="panel"><h2>Proposed actions</h2>${list(r.proposed_actions)}</div></div></div>`;
}
function bars(items){ const maximum=Math.max(1,...items.map(x=>Math.abs(x[1])));return `<div class="bars">${items.map(([name,value])=>`<div class="bar-row"><span>${esc(name)}</span><div class="bar-track"><div class="bar-fill ${value<0?'negative':''}" style="width:${Math.max(1,Math.abs(value)/maximum*100)}%"></div></div><strong>${num(value)}</strong></div>`).join('')}</div>`; }
function simulationResult(record){
  const r=record.result; let points=[];
  if(r.rows)points=r.rows.map(x=>[x.scenario_name,x.values.profit.value]);
  else if(r.points)points=r.points.map(x=>[`${num(x.input_value)} clients`,x.output_value]);
  else if(r.p05!==undefined)points=[['P05',r.p05],['Median',r.p50],['P95',r.p95]];
  else points=[['Baseline',r.baseline],['Counterfactual',r.counterfactual]];
  return `<p class="eyebrow">${esc(record.mode.replace('_',' '))} · MODEL V${record.version}</p><h2>Conditional profit outcomes</h2>${bars(points)}<p class="note">All amounts in consistent currency units.${record.mode==='monte_carlo'?` ${r.samples} samples · seed ${r.seed} · uniform customer range.`:''}</p><div class="callout" style="margin-top:24px"><strong>What this model assumes</strong>${list(record.assumptions)}${record.coverage?`<h3>${esc(record.coverage.review_prompt)}</h3>${list(record.coverage.unmodeled_factors)}`:""}${r.note?`<p>${esc(r.note)}</p>`:''}</div>`;
}
function simulation(){
  let html=intro('EXPLORE BEFORE COMMITTING','Test the possibilities.','Compare outcomes under explicit assumptions—not narrative confidence.');
  if(!state.workspace)return html+noDecision();
  const r=state.workspace.revision,records=state.workspace.records.filter(x=>x.kind==='simulation');
  const active=state.simulation||records.at(-1);
  return html+`<div class="tab-strip" role="group" aria-label="Simulation mode">${[['scenario','Scenario'],['monte_carlo','Monte Carlo'],['causal','Causal'],['sensitivity','Sensitivity'],['stress','Stress test'],['five_cases','Five cases']].map(([key,label])=>`<button data-mode="${key}" class="${state.mode===key?'active':''}">${label}</button>`).join('')}</div><div class="grid"><div class="panel"><p class="eyebrow">PILOT ECONOMICS / ${esc(state.mode.replace('_',' '))}</p><h2>Set your assumptions</h2><p class="muted">Revenue = customers × price. Operating result = revenue − variable, fixed, technology, compliance and training costs.</p><form id="simulation-form"><div class="two-col"><label>Customers<input name="customers" type="number" min="0" max="1000000000" step="any" required value="100"></label><label>Price per customer<input name="price" type="number" min="0" max="1000000000" step="any" required value="25"></label></div><div class="two-col"><label>Fixed cost<input name="cost" type="number" min="0" max="1000000000000" step="any" required value="1500"></label><label>Customer change / uncertainty (%)<input name="change" type="number" min="-100" max="500" step="any" required value="-20"></label></div><div class="two-col"><label>Variable cost per customer<input name="variable_cost" type="number" min="0" max="1000000000" step="any" required value="0"></label><label>Technology cost<input name="technology_cost" type="number" min="0" max="1000000000000" step="any" required value="0"></label></div><div class="two-col"><label>Legal / compliance cost<input name="legal_cost" type="number" min="0" max="1000000000000" step="any" required value="0"></label><label>Human / training cost<input name="human_cost" type="number" min="0" max="1000000000000" step="any" required value="0"></label></div><div class="two-col"><label>Monte Carlo samples<input name="samples" type="number" min="10" max="5000" required value="500"></label><label>Random seed<input name="seed" type="number" step="1" required value="42"></label></div><p class="muted">Scenario/causal: change customer demand. Monte Carlo: uniform range ± absolute change. Stress: also raise fixed cost by the absolute change. Sensitivity: fixed −40% to +40% grid.</p><button class="primary">Run ${esc(state.mode.replace('_',' '))} →</button></form></div><div class="panel" id="simulation-results">${active?simulationResult(active):'<div class="empty"><div class="orb">∿</div><h2>Make uncertainty explicit.</h2><p>Run a simulation to see its conditional outcomes. Inputs and results will be saved with this decision revision.</p></div>'}</div></div>
  <div class="panel"><div class="section-head"><h2>Saved simulation runs</h2><span class="count">${records.length} RUNS</span></div>${records.length?`<table><thead><tr><th>Mode</th><th>Revision</th><th>Run time</th><th></th></tr></thead><tbody>${records.slice().reverse().map(x=>`<tr><td>${esc(x.mode.replace('_',' '))}</td><td>v${x.version}</td><td>${esc(date(x.created_at))}</td><td><button class="secondary" data-run="${x.id}">View</button></td></tr>`).join('')}</tbody></table>`:'<p class="muted">No simulation runs yet.</p>'}</div>`;
}
function reports(){
  let html=intro('REASONING, PRESERVED','From inquiry to judgment.','Review the evidence, assumptions, simulations and learning behind a decision.');
  if(!state.workspace)return html+noDecision();
  const w=state.workspace,r=w.revision,d=r.decision;
  const review=w.review;
  if(review)html+=`<section class="panel"><h2>Decision review</h2><div class="two-col"><section><h3>Expected benefits</h3>${list(review.expected_benefits)}<h3>Critical assumptions</h3>${list(review.critical_assumptions)}</section><section><h3>Known uncertainties</h3>${list(review.known_uncertainties)}<h3>Missing information</h3>${list(review.missing_information)}</section></div><p>Reversibility: ${esc(review.reversibility)}</p><h3>Stakeholder consequences</h3>${d.stakeholders.map(s=>`<details><summary>${esc(s.name)}</summary>${Object.entries(s).filter(([key])=>key!=='name').map(([key,value])=>`<p><strong>${esc(key.replaceAll('_',' '))}:</strong> ${esc(Array.isArray(value)?value.join('; ')||'Not supplied':value)}</p>`).join('')}</details>`).join('')}<p>${esc(review.coverage_prompt)}</p><p class="note">${esc(review.scope)}</p></section>`;
  return html+`<div class="toolbar"><button class="primary" id="print-report">Print / Save PDF</button><button class="secondary" id="export-report">Export JSON</button></div><article class="panel"><div class="report-title"><p class="eyebrow">PRAXIS OS / DECISION REPORT · REVISION ${r.version}</p><h1>${esc(d.title)}</h1><p>${esc(d.problem)}</p><small>${esc(date(r.created_at))} · ${esc(r.decision_id)}</small></div><h2>Objective & human values</h2><p>${esc(d.objective)}</p>${list(d.values)}<h2>Options & trade-offs</h2>${d.options.length?`<table><thead><tr><th>Option</th><th>Reversibility</th><th>Stated assumptions</th></tr></thead><tbody>${d.options.map(o=>`<tr><td>${esc(o.name)}</td><td>${o.reversible?'Declared reversible':'Declared irreversible'}</td><td>${esc(o.assumptions.join('; ')||'Not supplied')}</td></tr>`).join('')}</tbody></table><p class="note">Trade-offs require human review; the model does not rank or choose options.</p>`:'<p class="muted">No options supplied.</p>'}<h2 style="margin-top:24px">Evidence & confidence</h2>${list(d.evidence.map(e=>`${e.kind}: ${e.statement} · supplied confidence ${num(e.confidence*100)}% · source: ${e.source||'not supplied'}`))}${list(w.claims.map(c=>`${c.claim_type}: ${c.statement} · ${c.status} · source: ${c.source?.title||'not supplied'}`))}<p class="note">Confidence values are user-supplied, not calibrated likelihoods. No overall decision confidence is inferred.</p><div class="two-col" style="margin-top:25px"><section><h2>Risks</h2>${list(r.risks)}</section><section><h2>Next actions</h2>${list(r.proposed_actions)}</section></div><h2>Simulations & judgments</h2>${w.records.length?w.records.map(x=>`<div class="record"><strong>${esc(x.kind)} · ${esc(x.mode||x.disposition)} · v${x.version}</strong><p>${esc(x.rationale||'Inputs and outputs preserved in the JSON export and Simulation view.')}</p><small>${esc(date(x.created_at))}${x.reviewer?' · '+esc(x.reviewer):''}</small></div>`).join(''):'<p class="muted">No simulations or human judgments recorded.</p>'}<h2 style="margin-top:24px">Latest observed outcome & feedback</h2>${r.feedback?`<p>${esc(r.feedback.outcome.summary)}</p><p>Source: ${esc(r.feedback.outcome.source)}</p><p>Learning: ${esc(r.feedback.learning)}</p>`:'<p class="muted">No outcome observations recorded yet.</p>'}<div class="callout">This report documents a local inquiry. Domain findings are deterministic review prompts, not externally verified conclusions. Actions have not been executed by this interface.</div></article>`;
}
function render(){
  $('#breadcrumb').textContent=names[state.page];
  document.querySelectorAll('[data-page]').forEach(b=>{b.classList.toggle('active',b.dataset.page===state.page);b.setAttribute('aria-current',b.dataset.page===state.page?'page':'false');});
  $('#main').innerHTML=({dashboard,chat,canvas,simulation,reports,labs,sources,enterprise,decisionlab,researchpage,foresightpage,inquirypage,computepage,aircrewpage,shipcaptainpage,ceopage,cfopage,ctopage,cmopage,nationalpage,policypage,aipage,worldbankpage,imfpage})[state.page]();
  if(state.workspace && ['chat','canvas','simulation','reports','decisionlab','researchpage','foresightpage'].includes(state.page))$('#main').insertAdjacentHTML('beforeend',suggestionPanel());
  if(state.page==='decisionlab')bindDecisionLab();
  if(state.page==='inquirypage')bindInquiry();
  if(state.page==='computepage')bindCompute();
  if(state.page==='worldbankpage')bindWorldBank();
  if(state.page==='imfpage')bindIMF();
  if(state.page==='nationalpage')bindNational();
  if(state.page==='policypage')bindPolicy();
  if(state.page==='aipage')bindAI();
  if(state.page==='cmopage')bindMarketing();
  if(['ceopage','cfopage','ctopage'].includes(state.page))bindExecutive();
  if(['aircrewpage','shipcaptainpage'].includes(state.page))bindOperations();
  bindSuggestions();
  if(state.page==='researchpage')bindResearch();
  if(state.page==='foresightpage')bindForesight();
  if(state.page==='enterprise')bindEnterprise();
  if(state.page==='sources')$('#main').insertAdjacentHTML('beforeend',sourceSearch());
  if(state.page==='labs'||state.page==='sources')bindLabs();
  $('#active-decision')?.addEventListener('change',e=>select(e.target.value).catch(err=>toast(err.message,true)));
  document.querySelectorAll('[data-new]').forEach(b=>b.onclick=()=>$('#decision-dialog').showModal());
  document.querySelectorAll('[data-open]').forEach(b=>b.onclick=async()=>{state.page='canvas';try{await select(b.dataset.open);}catch(e){toast(e.message,true);}});
  document.querySelectorAll('[data-node]').forEach(b=>{const inspect=()=>{const node=state.workspace.graph.nodes.find(n=>n.id===b.dataset.node);$('#node-inspector').textContent=`${node.node_type.toUpperCase()}\n\n${node.label}\n\n${JSON.stringify(node.properties||{},null,2)}`;};b.onclick=inspect;b.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();inspect();}};});
  document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{state.mode=b.dataset.mode;render();});
  document.querySelectorAll('[data-run]').forEach(b=>b.onclick=()=>{state.simulation=state.workspace.records.find(x=>x.id===b.dataset.run);state.mode=state.simulation.mode;render();});
  $('#feedback-form')?.addEventListener('submit',e=>{e.preventDefault();const data=Object.fromEntries(new FormData(e.target));busy(e.submitter,async()=>{await api(`/v1/decision-models/${state.selected}/feedback`,{base_version:state.workspace.revision.version,outcome:{summary:data.summary,source:data.source},learning:data.learning});await load();render();toast('Feedback saved. A new model revision is ready.');});});
  $('#evidence-form')?.addEventListener('submit',e=>{e.preventDefault();const data=Object.fromEntries(new FormData(e.target));busy(e.submitter,async()=>{await api('/v1/evidence/claims',{decision_id:state.selected,statement:data.statement,claim_type:data.claim_type,source:{title:data.source}});await load();render();toast('Claim saved with unverified status.');});});
  $('#judgment-form')?.addEventListener('submit',e=>{e.preventDefault();const data=Object.fromEntries(new FormData(e.target));busy(e.submitter,async()=>{await api(`/v1/decision-models/${state.selected}/judgments`,{...data,selected_option:data.selected_option||null,base_version:state.workspace.revision.version});await load();render();toast('Human judgment recorded. No action executed.');});});
  if(state.page==='simulation' && state.simulation){for(const [key,value]of Object.entries(state.simulation.inputs)){const field=$('#simulation-form')?.elements.namedItem(key);if(field)field.value=key==='change'?value*100:value;}}
  $('#simulation-form')?.addEventListener('submit',e=>{e.preventDefault();const data=Object.fromEntries([...new FormData(e.target)].map(([k,v])=>[k,Number(v)]));data.change/=100;busy(e.submitter,async()=>{state.simulation=await api(`/v1/decision-models/${state.selected}/simulations`,{...data,mode:state.mode,base_version:state.workspace.revision.version});await load();render();toast('Simulation complete. Inputs and results saved.');});});
  $('#print-report')?.addEventListener('click',()=>window.print());
  $('#export-report')?.addEventListener('click',()=>{const blob=new Blob([JSON.stringify(state.workspace,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`praxis-decision-${state.selected}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
}
document.querySelectorAll('[data-page]').forEach(b=>b.onclick=()=>{state.page=b.dataset.page;render();});
$('#new-decision').onclick=()=>$('#decision-dialog').showModal();
$('#close-dialog').onclick=()=>$('#decision-dialog').close();
$('#example').onclick=()=>{const f=$('#decision-form');const values={title:'Paid pilot for a new service',problem:'Should we test a paid subscription with a small customer group?',objective:'Measure willingness to pay before a full launch',values:'Customer privacy\nTransparent pricing',constraints:'Pilot budget under 10,000\nNo irreversible commitments',options:'Run a small paid pilot\nInterview more customers first',assumptions:'Customers will pay for the service\nThe team can support a small pilot'};for(const[k,v]of Object.entries(values))f.elements[k].value=v;};
$('#decision-form').addEventListener('submit',e=>{e.preventDefault();const data=Object.fromEntries(new FormData(e.target));busy(e.submitter,async()=>{const model=await api('/v1/decision-models',{title:data.title,problem:data.problem,objective:data.objective,values:lines(data.values),constraints:lines(data.constraints),options:lines(data.options).map(name=>({name})),evidence:lines(data.assumptions).map(statement=>({statement,kind:'assumption'}))});state.selected=model.decision_id;state.page='chat';state.simulation=null;await load();$('#decision-dialog').close();e.target.reset();render();toast('Decision model created. Explore the inquiry below.');});});
async function startStudio(){try{const health=await api('/health');if(health.authentication){$('#login-dialog').showModal();return;}await load();render();}catch(e){$('#main').innerHTML=`<div class="panel error-panel"><h2>Workspace could not load</h2><p>${esc(e.message)}</p><button class="secondary" id="retry">Retry</button></div>`;$('#retry').onclick=()=>location.reload();}}
$('#login-dialog').addEventListener('cancel',e=>e.preventDefault());
$('#login-form').addEventListener('submit',e=>{e.preventDefault();accessToken=new FormData(e.target).get('credential');busy(e.submitter,async()=>{const me=await api('/v1/me');await load();if(state.page==='labs'||state.page==='sources')await loadLabs();$('#identity-label').textContent=me.tenant+' / '+me.subject;$('#signout').hidden=false;$('#login-dialog').close();e.target.reset();render();});});
$('#signout').onclick=()=>{accessToken=null;state.decisions=[];state.workspace=null;state.selected=null;state.page='dashboard';for(const key of Object.keys(labState))labState[key]=[];$('#main').innerHTML='';$('#login-dialog').showModal();};

document.addEventListener('click', e => {
  const btn = e.target.closest('[data-page]');
  if (btn && btn.dataset.page) {
    e.preventDefault();
    state.page = btn.dataset.page;
    if (state.page === 'aipage' && typeof loadAI === 'function') {
      loadAI().then(() => { if (state.page === 'aipage') render(); });
    }
    render();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
});

document.addEventListener('DOMContentLoaded',startStudio);


