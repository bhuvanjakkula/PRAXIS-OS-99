'use strict';
names.worldbankpage='World Bank Solutions';
if(location.hash==='#world-bank')state.page='worldbankpage';
document.querySelector('nav').insertAdjacentHTML('beforeend','<button data-page="worldbankpage"><span>◎</span> World Bank Solutions</button>');
document.querySelector('[data-page="worldbankpage"]').onclick=()=>busy(document.querySelector('[data-page="worldbankpage"]'),async()=>{await load();state.page='worldbankpage';render();});
const wbAreas={governance:['Governance and accountability','Explore transparent review workflows, procurement traceability and grievance resolution.'],debt_transparency:['Debt transparency','Explore contract registries, debt-data reconciliation and disclosure tools.'],development_finance:['Development finance','Explore project pipelines, financing comparisons and monitoring tools.'],public_goods:['Cross-border public goods','Explore regional climate, health and infrastructure coordination.'],knowledge_delivery:['Knowledge and service delivery','Explore evidence libraries, local-language access and reusable implementation lessons.']};
const wbFields={title:'Project title',geography:'Countries / regional scope',problem:'Problem and institutional constraints',beneficiaries:'Beneficiaries and affected groups',technology:'Proposed technology and dependencies',alternative:'Non-technology or existing-system alternative',owner:'Responsible owner',evidence:'Dated sources and evidence gaps',safeguards:'Privacy, equity, procurement and environmental safeguards',pilot:'Pilot scope, cost assumptions and stop criteria',baseline:'Baseline and measurement method',target:'Target outcome and evaluation plan',review_date:'Review date / schedule',prototype_evidence:'Prototype evidence (optional)',validation_evidence:'Independent validation evidence (optional)',handover_evidence:'Handover and maintenance evidence (optional)'};
function worldbankpage(){let html=intro('DEVELOPMENT SOLUTIONS','World Bank Solutions','Develop technology proposals and institutional solutions through owned, measurable pilots.');
if(!state.workspace)return html+noDecision();
return html+`<section class="panel"><h2>Solution areas</h2>${Object.values(wbAreas).map(([title,note])=>`<h3>${esc(title)}</h3><p>${esc(note)}</p>`).join('')}<p>Candidate approaches for investigation. This workspace is independent of the World Bank.</p></section><section class="panel"><h2>Develop a solution</h2><form id="world-bank-form"><label>Solution area<select name="area">${Object.entries(wbAreas).map(([k,v])=>`<option value="${k}">${esc(v[0])}</option>`).join('')}</select></label><div class="two-col">${Object.entries(wbFields).map(([k,v])=>`<label>${esc(v)}<textarea name="${k}" maxlength="4000" ${k.endsWith('_evidence')?'':'required'}></textarea></label>`).join('')}</div><label>Development stage<select name="stage">${['discovery','prototype','validation','handover'].map(s=>`<option>${s}</option>`).join('')}</select></label><button class="primary">Save solution proposal</button></form></section><section class="panel"><h2>Saved solution proposals</h2>${state.workspace.records.filter(r=>r.kind==='world_bank_solution').slice().reverse().map(r=>`<article class="record"><h3>${esc(r.inputs.title)}</h3><p>${esc(wbAreas[r.inputs.area][0])} · ${esc(r.inputs.stage)} · decision v${r.version}</p>${Object.entries(wbFields).filter(([k])=>r.inputs[k]).map(([k,v])=>`<p><strong>${esc(v)}:</strong> ${esc(r.inputs[k])}</p>`).join('')}${list(r.analysis.review_gaps)}<p>Human review required before implementation.</p><button class="secondary" data-wb-export="${esc(r.id)}">Export solution proposal</button></article>`).join('')||'<p>No proposals saved yet.</p>'}</section>`;}
function bindWorldBank(){const form=$('#world-bank-form');if(!form)return;
form.onsubmit=e=>{e.preventDefault();busy(form.querySelector('.primary'),async()=>{const data=Object.fromEntries(new FormData(form));const financing={};const result={};for(const key of ["name","kind","unit","baseline","target","actual","observed_on","source","owner"]){const value=data["result_"+key];delete data["result_"+key];if(value!==undefined)result[key]=["baseline","target","actual"].includes(key)?(value===""?null:Number(value)):value;}if(result.name){data.results=[result];}else{delete data.results_as_of;}for(const key of ['instrument','reported_milestone',...Object.keys(wbFinanceFields)]){if(data['finance_'+key]!==undefined)financing[key]=data['finance_'+key];delete data['finance_'+key];}financing.monitoring_enabled=$('#wb-monitoring-enabled').checked;delete data.finance_monitoring;delete data.finance_enabled;if($('#wb-finance-enabled').checked)data.financing=financing;data.base_version=state.workspace.revision.version;await api(`/v2/decisions/${state.selected}/world-bank-solutions`,data);await load();render();toast('Solution proposal saved for review.');});};
$('#wb-finance-enabled').onchange=()=>{const fields=$('#wb-finance-fields');fields.disabled=!$('#wb-finance-enabled').checked;fields.hidden=fields.disabled;};
document.querySelectorAll('[data-wb-export]').forEach(b=>b.onclick=()=>{const record=state.workspace.records.find(r=>r.id===b.dataset.wbExport);const url=URL.createObjectURL(new Blob([JSON.stringify(record,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='praxis-world-bank-solution.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});}
const wbFinanceFields={additionality:'Additionality evidence and lower-subsidy alternatives',public_exposure:'Public exposure, contingent liabilities and stress assumptions',access_covenants:'Access, pricing and equity covenants with monitoring owner',protected_resources:'Protected poverty/public-good resources and allocation evidence',country_ownership:'Country ownership, civic participation and disclosure evidence',sunset_terms:'Sunset date or trigger, review owner and exit arrangements',shock_response:'Shock-response liquidity and counter-cyclical contingency plan',independent_review:'Independent financial, legal and impact review references'};
const worldBankBeforeFinance=worldbankpage;
Object.assign(wbFinanceFields,{
supervisory_mandate:'Supervisory mandate, jurisdiction, dated authority and applicable audit/assurance scope',
audit_access_disclosure:'Evidence-access rights, record preservation, NDA restrictions and lawful disclosure',
commercial_independence:'Client fee dependence, non-audit services, contingent fees and conflict safeguards',
appointment_rotation:'Independent appointment/committee authority, tenure, rotation and continuity trade-offs',
inspection_capacity:'Inspection resources, findings, proportional procedures, costs and defensive-compliance risks',
regulatory_remediation:'Owned corrective action, deadline, appeal/stay, completion evidence and independent recheck'
});
Object.assign(wbFinanceFields,{
less_discriminatory_alternatives:'Alternative-model search, comparable evaluation, disparity/performance trade-offs and review rationale',
longitudinal_access_review:'Repeated-cycle access, intersectional outcomes, feedback effects and proxy-label uncertainty'
});
Object.assign(wbFinanceFields,{
appeal_change_trace:'Appeal/audit case reference to systemic change, owner, model versions, validation and recurrence review',
sensitive_audit_governance:'Independent auditor data access, lawful purpose, privacy controls, proxy-label uncertainty and retention'
});
Object.assign(wbFinanceFields,{
reviewer_capacity:'Reviewer workload, competence, independence, contextual evidence and automation-bias controls',
causal_proxy_review:'Causal proxy test design, identification assumptions, alternatives and explanation reliability',
structural_remediation:'Override/model-change authority, owned remediation, version validation and recurrence checks'
});
Object.assign(wbFinanceFields,{
recourse_feasibility:'Recourse cost, immutable features, attainable changes and subgroup feasibility evidence',
routing_calibration_audit:'Model routing, subgroup risk calibration, pricing, class imbalance and audit limitations',
access_after_remedy:'Owned remedy, actual review changes, follow-up access outcomes and defensive rationing evidence'
});
Object.assign(wbFinanceFields,{
adverse_disclosure:'Adverse-decision reasons, actionable correction options, explanation limits and comprehension evidence',
model_traceability:'Model/version documentation, independent audit access, explanation stability and drift review',
substantive_appeal:'Accessible appeal, independent qualified reviewer, authority to change outcomes and reasoned data correction'
});
Object.assign(wbFinanceFields,{
alternative_data_review:'Alternative-data consent, provenance, accuracy, minimization and missing-data alternatives',
outcome_bias_audit:'Approval, pricing and error disparities, proxy/intersectional bias, denominators and metric trade-offs',
threshold_review:'Proposed threshold alternatives, exclusion/default trade-offs, counterfactual limits and jurisdictional review'
});
wbAreas.financial_inclusion=['Consumer protection and financial access','Explore transparent lending, fair collections, inclusive identity checks and safe alternatives for excluded groups.'];
Object.assign(wbFinanceFields,{
consumer_protection:'Total borrowing costs, affordability, marketing, fair collection and complaint protections',
algorithmic_fairness:'Data permissions, scoring explanations, subgroup fairness and human appeal evidence',
identity_access:'e-KYC privacy, accessibility, thin-file or missing-ID alternatives and exclusion evidence',
licensing_review:'Jurisdiction-specific licensing, capital, sandbox boundaries and dated supervisory review',
safe_access_alternatives:'Who loses access under proposed protections, safe replacement services and transition plan',
literacy_support:'Accessible financial/digital literacy support, comprehension checks and subgroup outcomes'
});
Object.assign(wbFinanceFields,{
auditor_integrity:'Auditor/reviewer qualifications, political/financial ties, reciprocal arrangements and conflict mitigation'
});
Object.assign(wbFinanceFields,{
audit_precision:'Audit criteria, validation sample, false positives/negatives and measurement uncertainty',
adjudication_delays:'Intake-to-review timing, unresolved backlog, delay reasons and due-process safeguards',
sanction_impact_review:'Sanction credibility, proportionality, service harms, alternatives and recurrence evidence'
});
Object.assign(wbFinanceFields,{
acceleration_safeguards:'Acceleration and collateral safeguards, notice/cure, distress pricing and lender-abuse review',
misleading_terms_review:'Plain-language terms, statutory-rights conflicts, independent advice and challenged clauses',
automation_redress:'Automated monitoring/decision use, privacy limits, human review and accessible contestation'
});
Object.assign(wbFinanceFields,{
detection_assumptions:'Audit frequency, eligible population, coverage, detection assumptions and evidence limitations',
grievance_disposition:'Grievance disposition, decision reference, rationale, disputed findings and appeal status',
renegotiation_conflicts:'Renegotiation fees, lender conflicts, hold-up risks and stakeholder engagement effects'
});
Object.assign(wbFinanceFields,{
joint_audit_coordination:'Joint audit roles, coverage, evidence sharing, costs and free-riding controls',
grievance_independence:'Independent intake, accessibility, representation, retaliation protections and procedural conflicts',
detection_remedy_handoff:'Detection-to-redress-to-remedy handoffs, references, receiving owners and unresolved disputes',
post_monitor_followup:'Follow-up after monitor exit, recurrence evidence, service outcomes and responsible owner'
});
Object.assign(wbFinanceFields,{
grievance_record:'Grievance reference, channel, owner, privacy limits and complainant response',
breach_assessment:'Separate breach assessment, disputed evidence, reviewer and determination reference',
creditor_trigger:'Exact covenant/default linkage, notice, cure, waiver and counsel evidence',
creditor_coordination:'Creditor priority, syndicate voting, conflicts and authorized decision makers',
renegotiation_review:'Renegotiation alternatives, proposed terms, consents and liquidity consequences',
stakeholder_effects:'Worker, beneficiary and service-continuity impacts with grievance follow-up'
});
Object.assign(wbFinanceFields,{
consultation_sequence:'Inclusive consultation, agreed rules and sequencing before enforcement',
covenant_monitor_link:'Covenant clause to KPI, monitored population, reviewer and trigger mapping',
monitoring_resources:'Monitoring budget, staffing, independence, audit burden and coverage limits',
graduated_sanctions:'Proposed warning, cure, escalation and remedial steps with responsible authority',
proportionality_review:'Severity, ability to comply, vulnerable-group burden and service-continuity review',
appeal_followup:'Independent appeal, disputed findings, remedy follow-up and restoration evidence'
});
Object.assign(wbFinanceFields,{
governing_law:'Applicable governing law, jurisdiction, contract version and counsel reference',
covenant_binding:'Exact public-benefit clause, binding status review and commercial-protection comparison',
beneficiary_standing:'Who can enforce: beneficiary standing, representation and access barriers',
dispute_forum:'Dispute forum, arbitration/court access, appeal costs and timing',
remedy_authority:'Default triggers, cure periods, clawback limits and authorized remedy owner',
intermediary_accountability:'Responsibility across intermediaries, enforcement incentives and continuity'
});
Object.assign(wbFinanceFields,{
concessionality_calibration:'Concessionality amount and rationale, impact per unit, subsidy alternatives and taper assumptions',
covenant_enforcement:'Covenant monitoring authority, breach remedies, grievance process and legal review',
public_upside:'Public equity, warrants or profit-sharing terms, valuation and reinvestment accountability',
capacity_building:'Local technical assistance, domestic capacity, ownership and dependency exit plan'
});
Object.assign(wbFinanceFields,{
baseline_audit:'Monitoring baseline, population, KPI definition and audit reference',
outcome_observations:'Observed outcomes, period, distribution across groups and contrary evidence',
independent_verification:'Independent verifier, methodology, conflicts and verification findings',
counterfactual_review:'Counterfactual comparator, comparability, assumptions and attribution limits',
disclosure_record:'Disclosure of subsidies, pricing, investor returns and privacy restrictions',
remedy_review:'Disbursement or remedy terms, breach review, authority and appeal evidence'
});
worldbankpage=function(){let html=worldBankBeforeFinance();if(!state.workspace)return html;
const fields=`<h3>Public-interest financing review</h3><label><input type="checkbox" id="wb-finance-enabled" name="finance_enabled"> Include financing safeguards</label><fieldset id="wb-finance-fields" hidden disabled><label>Proposed instrument<select name="finance_instrument">${['grant','concessional_loan','guarantee','first_loss','co_lending','other'].map(v=>`<option>${v}</option>`).join('')}</select></label>${Object.entries(wbFinanceFields).map(([key,label])=>`<label>${esc(label)}<textarea name="finance_${key}" maxlength="4000"></textarea></label>`).join('')}<p>Record evidence or leave a gap visible. Supplied reviews do not authorize funding or establish compliance.</p></fieldset>`;
html=html.replace('<label>Development stage',fields+'<label>Development stage');
html=html.replace('<label>Supervisory mandate','<h3>Regulatory enforcement and auditor independence</h3><p>Any note enables six-area evidence review and linked independence/authority checks. Rules and declarations do not certify compliance.</p><label>Supervisory mandate');
html=html.replace('<label>Total borrowing costs','<h3>Consumer protection and financial access</h3><p>Review protection and exclusion together. Selecting financial inclusion requires all twenty-two evidence areas; enable financing safeguards to enter them.</p><label>Total borrowing costs');
html=html.replace('<label>Joint audit roles','<h3>Joint detection and redress review</h3><p>Any note enables cross-review evidence checks. Document handoffs and follow-up without inferring deterrence.</p><label>Joint audit roles');
html=html.replace('<label>Grievance reference','<h3>Grievance and creditor-rights review</h3><p>Any grievance note enables evidence-gap review. A complaint does not establish default or activate creditor powers.</p><label>Grievance reference');
html=html.replace('<label>Inclusive consultation','<h3>Covenant, monitoring and sanction coordination</h3><p>Any coordination note enables gap review. Link agreed rules and independent evidence before reviewing a proposed remedy.</p><label>Inclusive consultation');
html=html.replace('<label>Applicable governing law','<h3>Contract enforcement evidence</h3><p>Enter any enforcement field to review all six evidence areas. Notes do not establish enforceability.</p><label>Applicable governing law');
html=html.replace('<label>Monitoring baseline',`<h3>Outcome monitoring</h3><label><input type="checkbox" id="wb-monitoring-enabled" name="finance_monitoring"> Review monitoring evidence gaps</label><label>Reported milestone status<select name="finance_reported_milestone">${['not_reviewed','met','missed','disputed'].map(v=>`<option>${v}</option>`).join('')}</select></label><label>Monitoring baseline`);
for(const r of state.workspace.records.filter(r=>r.kind==='world_bank_solution'&&r.inputs.financing)){
const finance=r.inputs.financing;const details=`<h4>Public-interest financing review</h4><p>Instrument: ${esc(finance.instrument)}</p>${Object.entries(wbFinanceFields).map(([key,label])=>`<p><strong>${esc(label)}:</strong> ${esc(finance[key]||'Evidence missing')}</p>`).join('')}`;
html=html.replace(`<button class="secondary" data-wb-export="${esc(r.id)}">`,`<p>Monitoring review: ${finance.monitoring_enabled?'enabled':'not enabled'} · reported milestone: ${esc(finance.reported_milestone||'not_reviewed')}</p><button class="secondary" data-wb-export="${esc(r.id)}">`);
html=html.replace(`<button class="secondary" data-wb-export="${esc(r.id)}">`,details+`<button class="secondary" data-wb-export="${esc(r.id)}">`);
}return html;};
const wbBeforeResults=worldbankpage;
worldbankpage=function(){let html=wbBeforeResults();if(!state.workspace)return html;
const fields=`<h3>Measured results pilot</h3><p>Add one indicator here, or up to twenty through the API. Observation age is shown for reviewer judgment. Progress measures change toward a target; it does not establish causality.</p><label>Indicator name (optional)<input name="result_name" maxlength="4000"></label><label>Indicator type<select name="result_kind"><option>outcome</option><option>output</option></select></label>${['unit','baseline','target','actual','observed_on','source','owner'].map(k=>`<label>${esc(k.replaceAll('_',' '))}<input name="result_${k}" ${['baseline','target','actual'].includes(k)?'type="number" step="any"':k==='observed_on'?'type="date"':'maxlength="4000"'}></label>`).join('')}<label>Results review date<input name="results_as_of" type="date"></label>`;
html=html.replace('<label>Development stage',fields+'<label>Development stage');
for(const r of state.workspace.records.filter(r=>r.kind==='world_bank_solution')){
const results=(r.analysis.results||[]).map(v=>`<p><strong>${esc(v.name)}</strong> (${esc(v.kind)}): ${esc(v.status)}, ${v.progress_percent===null?'progress unavailable':esc(v.progress_percent.toFixed(1))+'% toward target'}, observation age ${esc(v.age_days)} days.</p>`).join('');
html=html.replace(`<button class="secondary" data-wb-export="${esc(r.id)}">`,results+`<button class="secondary" data-wb-export="${esc(r.id)}">`);
}return html;};

