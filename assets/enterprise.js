/* Authenticated enterprise source updates and human impact review. */
names.enterprise='Enterprise';
let enterpriseState={sources:[],impacts:[],capabilities:{},database:{},health:{sources:[]}};
async function loadEnterprise(){
  const [sources,impacts,capabilities,database,health]=await Promise.all([api('/v2/resources/source'),api('/v2/source-impacts'),api('/v2/enterprise/capabilities'),api('/v2/database/status'),api('/v2/sources/health')]);
  enterpriseState={sources,impacts,capabilities,database,health};
}
function enterprise(){
  return intro('CONNECTED SOURCES / HUMAN REVIEW','Keep decisions grounded in change.','Import source updates, preserve history and review affected decisions.',false)+
    `<div class="panel"><h2>Connection status</h2><p>Workspace: ${enterpriseState.capabilities.mode==='local_single_user'?'local single-user SQL database':'authenticated organization'}. Live vendor connections: ${enterpriseState.capabilities.vendor_pull_connectors?.length||0}.</p><p>AI provider: ${enterpriseState.capabilities.reasoning_provider_configured?'Configured':'Not configured'}. Real-world action execution is disabled.</p></div>
    <section class="panel"><h2>SQL database</h2><p><strong>${esc(enterpriseState.database.backend)} ${esc(enterpriseState.database.sql_version)}</strong> · ${esc(enterpriseState.database.status)}</p><p class="muted">Stored row counts include historical revisions.</p><div class="graph-list">${Object.entries(enterpriseState.database.table_rows||enterpriseState.database.resource_revision_counts||{}).map(([name,count])=>`<span class="tag">${esc(name)}: ${count}</span>`).join('')}</div>${enterpriseState.capabilities.mode==='local_single_user'?'<button class="secondary" id="database-backup">Create verified database backup</button><p id="backup-result" class="detail" aria-live="polite"></p>':'<p class="note">Database backups are managed by your deployment operator.</p>'}</section>
    <section class="panel"><h2>Source health</h2><p class="note">Review threshold: ${enterpriseState.health.max_age_days} days. ${esc(enterpriseState.health.note)}</p>${enterpriseState.health.sources.length?`<table><thead><tr><th>Source</th><th>Versions</th><th>Recency</th><th>Pending reviews</th></tr></thead><tbody>${enterpriseState.health.sources.map(s=>`<tr><td>${esc(s.name)}</td><td>${s.document_versions}</td><td>${esc(s.status.replaceAll('_',' '))}</td><td>${s.pending_impacts}</td></tr>`).join('')}</tbody></table>`:'<p>Register a source to track its ingestion history.</p>'}</section>
    <div class="grid"><section class="panel"><h2>Link a source to a decision</h2><form id="binding-form"><label>Source<select name="source_id" required><option value="">Choose source</option>${enterpriseState.sources.map(s=>`<option value="${s.id}">${esc(s.name)}</option>`).join('')}</select></label><label>Decision<select name="decision_id" required><option value="">Choose decision</option>${state.decisions.map(d=>`<option value="${d.decision_id}">${esc(d.decision.title)}</option>`).join('')}</select></label><label>Why this source matters<input name="purpose" required maxlength="2000"></label><button class="primary">Link source</button></form></section>
    <section class="panel"><h2>Import a source update</h2><p class="muted">Choose a normalized JSON export prepared for the registered source. Updates create review alerts; they do not change decision assumptions automatically.</p><form id="sync-form"><label>Source<select name="source_id" required><option value="">Choose source</option>${enterpriseState.sources.map(s=>`<option value="${s.id}">${esc(s.name)}</option>`).join('')}</select></label><label>Export file<input name="file" type="file" accept=".json,application/json" required></label><button class="primary">Import source update</button></form></section></div>
    <section class="panel"><h2>Source changes needing review</h2>${enterpriseState.impacts.length?enterpriseState.impacts.map(i=>`<article class="record"><h3>${esc(state.decisions.find(d=>d.decision_id===i.decision_id)?.decision.title||i.decision_id)}</h3><p>${esc(i.purpose)} · decision revision ${i.decision_version}</p><p>${i.changes.length} changed record(s) · ${esc(i.status)}</p>${i.changes.map(c=>`<details><summary>${esc(c.external_id)} · ${esc(c.kind)}</summary><pre class="detail">${esc(c.diff||"Change details were not recorded for this older import.")}</pre>${c.diff_truncated?"<p>Diff excerpt truncated; inspect full source versions.</p>":""}</details>`).join("")}${i.status==='review_required'?`<form data-impact="${i.id}"><label>Review result<select name="status"><option value="reviewed">Reviewed</option><option value="dismissed">Dismissed</option></select></label><label>Review note<input name="note" required></label><button class="secondary">Record review</button></form>`:`<p>${esc(i.note)} · ${esc(i.reviewer)}</p>`}</article>`).join(''):'<p>No source-change alerts yet.</p>'}</section>`;
}
function bindEnterprise(){
  $('#database-backup')?.addEventListener('click',e=>busy(e.target,async()=>{
    const backup=await api('/v2/database/backups',{});$('#backup-result').textContent='Verified backup saved in backups/'+backup.file+'. SHA-256: '+backup.sha256;
  }));
  $('#binding-form').onsubmit=e=>{e.preventDefault();busy(e.submitter,async()=>{
    await api('/v2/source-bindings',Object.fromEntries(new FormData(e.target)));e.target.reset();toast('Source linked to decision.');});};
  $('#sync-form').onsubmit=e=>{e.preventDefault();busy(e.submitter,async()=>{
    const data=new FormData(e.target),file=data.get('file');if(file.size>3000000)throw new Error('Export exceeds 3 MB.');
    const body=JSON.parse(await file.text());await api('/v2/sources/'+data.get('source_id')+'/sync',body);
    await loadEnterprise();render();toast('Source update saved. Review affected decisions below.');});};
  document.querySelectorAll('[data-impact]').forEach(f=>f.onsubmit=e=>{e.preventDefault();busy(e.submitter,async()=>{
    const item=enterpriseState.impacts.find(i=>i.id===f.dataset.impact);
    await api('/v2/source-impacts/'+item.id+'/review',{...Object.fromEntries(new FormData(f)),expected_version:item.version});
    await loadEnterprise();render();toast('Review recorded.');});});
}
document.addEventListener('DOMContentLoaded',async()=>{
  try{await api('/health');
    const button=document.createElement('button');button.dataset.page='enterprise';button.textContent='◇ Enterprise';
    button.onclick=()=>busy(button,async()=>{await load();await loadEnterprise();state.page='enterprise';render();});
    $('nav').appendChild(button);
  }catch{/* Normal sign-in/startup flow presents errors. */}
});
