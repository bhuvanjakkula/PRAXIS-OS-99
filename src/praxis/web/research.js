/* Explicit public queries, inspectable citations, revision-bound decision memos. */
names.researchpage='Search & decide';
let researchDraft={query:'',scope:'local',provider:'wikipedia',result:null};
function researchHits(result){
  if(!result)return '<p>Search your sources or choose a public provider.</p>';
  return `<p class="note">${esc(result.limitations)}</p><h3>PRAXIS documents · ${result.local.length}</h3>${result.local.map(h=>`<article class="record"><strong>${esc(h.source.name)}</strong><blockquote>${esc(h.excerpt)}</blockquote><small>${esc(h.citation_id)} · relevance ${num(h.score)}</small><p>${esc(h.source.uri)} · imported ${esc(date(h.ingested_at))}</p>${h.potential_conflicts.length?`<p>Potential conflicting statements: ${h.potential_conflicts.length}. Inspect Sources before relying on this excerpt.</p>`:''}</article>`).join('')||'<p>No local matches.</p>'}<h3>Public sources · ${esc(result.web.provider)}</h3><p role="status">${esc(result.web.status)}: ${esc(result.web.message)}</p>${result.web.hits.map(h=>`<article class="record"><a href="${esc(h.url)}" target="_blank" rel="noopener noreferrer">${esc(h.title)}</a><p>${esc(h.excerpt)}</p><small>${esc(h.citation_id)} · retrieved ${esc(date(h.retrieved_at))}</small></article>`).join('')}`;
}
function memoView(record){
  const a=record.analysis;
  return `<h3>Decision memo · revision ${record.version}</h3><p>${esc(a.method)}</p><p class="callout">${esc(a.limitations)}</p><h4>First principles</h4><p>${esc(a.first_principles.goal)}</p>${list(a.first_principles.constraints_to_verify)}<h4>Evidence gaps</h4>${list(a.evidence_gaps)}${a.domain_lenses.map(l=>`<details><summary>${esc(l.domain)} · ${esc(l.lens)}</summary>${list(l.questions)}</details>`).join('')}<h4>Challenge the conclusion</h4>${list(a.adversarial_questions)}${a.language_cues.map(c=>`<p>${esc(c.matched_phrase)}: ${esc(c.question)} (language cue only)</p>`).join('')}<h4>Options under supplied scenarios</h4>${a.option_evaluations.map(o=>`<article class="record"><strong>${esc(o.option)}</strong><p>Expected payoff: ${num(o.expected_value)} ${esc(a.payoff_unit)} · worst supplied outcome: ${num(o.worst_supplied_outcome)} · loss probability: ${num(o.loss_probability*100)}%</p><p>${o.eligible_under_supplied_inputs?'Eligible under supplied checks':esc(o.blocking_reasons.join('; '))}</p></article>`).join('')||'<p>No forecast supplied. No numerical ranking generated.</p>'}<p>Leading eligible options: ${a.leaders_under_supplied_inputs.map(esc).join(', ')||'None'}</p><h4>Next steps for human review</h4>${list(a.next_steps)}<details><summary>Sources preserved with this memo</summary>${researchHits(a.search)}</details>`;
}
function researchpage(){
  const history=(state.workspace?.records||[]).filter(r=>r.kind==='research_memo').slice().reverse();
  return intro('RESEARCH / CHALLENGE / DECIDE','Search with a decision in mind.','Find source material, test assumptions, and preserve a memo for human judgment.')+`<section class="panel"><form id="research-form"><label>Research question<input name="query" required maxlength="500" value="${esc(researchDraft.query)}" placeholder="e.g. reversible software rollout failure modes"></label><div class="two-col"><label>Search scope<select name="scope">${[['local','PRAXIS documents'],['both','Documents + public sources'],['web','Public sources']].map(([k,v])=>`<option value="${k}" ${researchDraft.scope===k?'selected':''}>${v}</option>`).join('')}</select></label><label>Public provider<select name="provider"><option value="wikipedia" ${researchDraft.provider==='wikipedia'?'selected':''}>Wikipedia · encyclopedia only</option><option value="brave" ${researchDraft.provider==='brave'?'selected':''}>Brave · general web (server API key required)</option></select></label></div><p class="note">Public search sends only the research question to the selected provider. Decision details and local documents are not sent. Results are snippets; open and verify the source.</p><details><summary>Local document filters</summary><label>Jurisdiction<input name="jurisdiction" maxlength="100" placeholder="Exact stored jurisdiction, e.g. IN"></label></details>${state.workspace?`<details><summary>Optional numerical option forecasts</summary><p>Supply one entry per decision option. Probabilities must sum to 1. Assess each stored constraint as pass, fail or unknown. Use a common payoff unit. Omitted and unknown outcomes are not modeled.</p><label>Payoff unit<input name="payoff_unit" maxlength="80" placeholder="e.g. USD net cash after 12 months"></label><label>Maximum acceptable loss (optional)<input name="maximum_loss" type="number" min="0" max="1000000000000" step="any"></label><label>Forecasts (JSON)<textarea name="forecasts" rows="8" placeholder='[{"option":"Pilot","scenarios":[{"name":"Success","probability":0.6,"payoff":100},{"name":"Failure","probability":0.4,"payoff":-40}],"constraints":{"Within budget":"unknown"}}]'></textarea></label></details>`:''}<div class="toolbar"><button class="primary" type="submit">Search sources</button>${state.workspace?'<button class="secondary" type="button" id="save-research">Build & save decision memo</button>':''}</div></form></section><section class="panel" id="research-results" aria-live="polite">${researchHits(researchDraft.result)}</section><section class="panel"><div class="section-head"><h2>Saved decision memos</h2></div>${history.map(r=>`<details class="record"><summary>${esc(r.inputs.query)} · revision ${r.version}${r.version!==state.workspace.revision.version?' · historical':''}</summary>${memoView(r)}</details>`).join('')||'<p>Select or create a decision, then build a memo. Saved memos retain sources and can be accepted, rejected, modified or deferred in Human review.</p>'}</section>`;
}
function bindResearch(){
  const form=$('#research-form');
  const body=()=>{const data=Object.fromEntries(new FormData(form));return {query:data.query,scope:data.scope,provider:data.provider,jurisdiction:data.jurisdiction||null};};
  form.onsubmit=e=>{e.preventDefault();busy(e.submitter,async()=>{
    const input=body();researchDraft={...researchDraft,...input};
    const result=await api('/v2/search',input);researchDraft.result=result;
    if(state.page==='researchpage')$('#research-results').innerHTML=researchHits(result);
  });};
  $('#save-research')?.addEventListener('click',e=>busy(e.target,async()=>{
    if(!form.reportValidity())return;
    const input=body(),data=Object.fromEntries(new FormData(form));
    const id=state.selected,version=state.workspace.revision.version;
    let forecasts=[];try{forecasts=JSON.parse(data.forecasts||'[]');}catch{throw new Error('Forecasts must be valid JSON.');}
    const result=await api(`/v2/decisions/${id}/research`,{...input,base_version:version,forecasts,payoff_unit:data.payoff_unit||'',maximum_loss:data.maximum_loss?Number(data.maximum_loss):null});
    if(state.selected!==id||state.page!=='researchpage')return;
    researchDraft={...researchDraft,...input,result:result.analysis.search};await load();render();toast('Memo saved. Open Human review to record your decision.');
  }));
}
document.addEventListener('DOMContentLoaded',()=>{
  $('#signout').addEventListener('click',()=>{researchDraft={query:'',scope:'local',provider:'wikipedia',result:null};});
  const button=document.createElement('button');button.dataset.page='researchpage';button.textContent='⌕ Search & decide';
  button.onclick=()=>busy(button,async()=>{await load();state.page='researchpage';render();});$('nav').appendChild(button);
});
