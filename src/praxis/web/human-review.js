/* Human decisions remain explicit, attributed and separate from advisory output. */
names.humanreview='Human review';
const mentalModelFields=[
  ['expected_behavior','What do you expect the system to do, and why?'],
  ['failure_boundaries','When could this advice fail or miss important context?'],
  ['analogous_example','A comparable example and where this case differs'],
  ['observed_outcome','Observed outcome and its source (if available)'],
  ['mental_model_update','What did you learn, and how has your understanding changed?']
];
function humanreview(){
  if(!state.workspace)return intro('HUMAN AUTHORITY','You decide.','Review advice, question its assumptions and record your own judgment.',false)+noDecision();
  const w=state.workspace,control=w.human_control;
  return intro('HUMAN AUTHORITY','The final judgment is yours.','Accept, reject, modify or defer the advice. You can change your mind with a later review.')+
    `<section class="panel"><h2>Think independently</h2><p>Consider your own view before opening the advice. Assess evidence and context rather than trusting or dismissing a result because a computer produced it.</p>${list(w.review.scientific_review_prompts)}<p class="callout">${esc(control.notice)}</p></section>
    <section class="panel"><h2>Record your review</h2><form id="human-review-form">
    <label>Your independent assessment<textarea name="independent_assessment" maxlength="10000" rows="3" placeholder="What would you choose, and why?"></textarea></label>
    <details><summary>Mental model and learning notes (optional)</summary><p>Record expectations before inspecting advice. On a later review, compare them with observed outcomes; distinguish observations from predictions.</p>${mentalModelFields.map(([key,label])=>`<label>${esc(label)}<textarea name="${key}" maxlength="10000" rows="2"></textarea></label>`).join('')}</details>
    <label>Advice to review<select name="advice_id" required><option value="">Choose a specific advisory result</option>${control.advice.map(a=>`<option value="${esc(a.id)}">${esc(a.title)} · ${esc(a.id)}</option>`).join('')}</select></label>
    <div id="human-advice-details" aria-live="polite"><p class="muted">Choose advice to inspect its contents and previous review.</p></div>
    <div class="two-col"><label>Your decision<select name="disposition" required><option value="">Choose your response</option><option value="accept">Accept advice</option><option value="reject">Reject advice</option><option value="modify">Request changes / choose a different approach</option><option value="defer">Defer pending more evidence</option></select></label><label>Your preferred option (optional)<select name="selected_option"><option value="">No option selected</option>${w.revision.decision.options.map(o=>`<option>${esc(o.name)}</option>`).join('')}</select></label></div>
    <label>Reviewer<input name="reviewer" required maxlength="200" placeholder="Your name; signed identity is used in authenticated workspaces"></label>
    <label>Reason for your decision<textarea name="rationale" required maxlength="10000" rows="3"></textarea></label>
    <label>Evidence checked, including contradictory observations<textarea name="evidence_review" maxlength="10000" rows="2"></textarea></label>
    <label>Uncertainty, alternative explanations and affected people<textarea name="uncertainty_review" maxlength="10000" rows="2"></textarea></label>
    <label>What result would change your mind? When will you review it?<textarea name="reconsider_when" maxlength="10000" rows="2"></textarea></label>
    <p class="note">Accepting advice does not claim it is true or approve an external action. A later review preserves this record in history.</p><button class="primary">Save human review</button></form></section>
    <section class="panel"><h2>Human review history</h2>${control.history.slice().reverse().map(r=>`<article class="record"><strong>${esc(r.disposition)} · revision ${r.version} · ${r.applies_to_current_revision?'current revision':'historical revision'}</strong><p>${esc(r.rationale)}</p><small>${esc(r.reviewer)} · ${esc(r.attribution)} · ${esc(date(r.created_at))}</small>${r.advice_snapshot?`<p>Reviewed: ${esc(r.advice_snapshot.title)}</p>`:''}${r.reconsider_when?`<p>Reconsider when: ${esc(r.reconsider_when)}</p>`:''}<details><summary>Review evidence and original advice</summary><p>Independent assessment: ${esc(r.independent_assessment||'Not supplied')}</p><p>Evidence: ${esc(r.evidence_review||'Not supplied')}</p><p>Uncertainty: ${esc(r.uncertainty_review||'Not supplied')}</p>${mentalModelFields.map(([key,label])=>`<p>${esc(label)}: ${esc(r[key]||'Not supplied')}</p>`).join('')}${r.advice_snapshot?list(r.advice_snapshot.statements):'<p>General decision judgment</p>'}</details></article>`).join('')||'<p>No human reviews yet. System output does not count as human approval.</p>'}</section>`;
}
function bindHumanReview(){
  const form=$('#human-review-form');if(!form)return;
  form.elements.advice_id.onchange=()=>{
    const advice=state.workspace.human_control.advice.find(a=>a.id===form.elements.advice_id.value);
    $('#human-advice-details').innerHTML=advice?`<article class="record"><h3>${esc(advice.title)}</h3>${list(advice.statements)}<p>${esc(advice.limitations)}</p><details><summary>How this advice works and when to question it</summary>${list(advice.behavior_notes||[])}</details><p>Latest response: <strong>${esc(advice.status)}</strong></p>${advice.analysis?`<details><summary>Inspect all advisory inputs and results</summary><pre class="human-review-json">${esc(JSON.stringify({inputs:advice.inputs,analysis:advice.analysis},null,2))}</pre></details>`:''}</article>`:'<p>Choose advice to inspect it.</p>';
  };
  form.onsubmit=e=>{e.preventDefault();const data=Object.fromEntries(new FormData(form));const id=state.selected;
    busy(e.submitter,async()=>{
      await api(`/v1/decision-models/${id}/judgments`,{...data,selected_option:data.selected_option||null,base_version:state.workspace.revision.version});
      await load();render();toast('Your review is saved. You remain in control; no action was executed.');
    });
  };
}
document.addEventListener('DOMContentLoaded',()=>{
  const button=document.createElement('button');button.dataset.page='humanreview';button.textContent='✓ Human review';
  button.onclick=()=>busy(button,async()=>{await load();state.page='humanreview';render();});$('nav').appendChild(button);
});
