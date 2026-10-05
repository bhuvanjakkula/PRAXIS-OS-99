/* Human-supplied tradeoffs, transparent review prompts, portable decision briefs. */
names.decisionlab='Decision lab';
let radarState={decisions:[],total:0,needs_review:0,with_gaps:0,note:''};
let comparisonDraft=null;
async function loadDecisionLab(){radarState=await api('/v2/decisions/radar');}
function getComparisonDraft(){
  const revision=state.workspace?.revision;
  if(!revision)return null;
  const key=revision.decision_id+':'+revision.version;
  if(comparisonDraft?.key!==key)comparisonDraft={key,criteria:['Benefit','Feasibility','Stakeholder impact'],weights:[1,1,1],scores:revision.decision.options.map(()=>['','','']),rationales:revision.decision.options.map(()=>''),result:null};
  return comparisonDraft;
}
function comparisonResults(result){
  if(!result)return '<p class="muted">Enter your assessments, then preview the tradeoffs.</p>';
  const analysis=result.analysis;
  return `<h3>Comparison results</h3><p>${esc(analysis.method)}</p><div class="bars">${analysis.ranking.map(row=>`<div class="comparison-bar"><span>${esc(row.option)}</span><meter min="0" max="10" value="${row.score}" aria-label="${esc(row.option)} score">${num(row.score)}</meter><strong>${num(row.score)} / 10</strong></div>${row.dominated_by.length?`<p class="note">${esc(row.option)} scores no better on any criterion than ${row.dominated_by.map(esc).join(', ')}.</p>`:''}`).join('')}</div><p><strong>${analysis.leaders.length>1?'Tied at the top':'Highest supplied score'}:</strong> ${analysis.leaders.map(esc).join(', ')}</p><p><strong>${analysis.leader_changes} of ${analysis.sensitivity.length}</strong> individual weight changes alter the leading option(s).</p><details><summary>Inspect weight sensitivity</summary>${analysis.sensitivity.map(s=>`<p>${esc(s.criterion)} ${s.weight_change_percent>0?'+':''}${s.weight_change_percent}% → ${s.leaders.map(esc).join(', ')}</p>`).join('')}</details><p class="callout">${esc(analysis.limitations)}</p>${result.id?'<p class="tag">Saved to this decision revision</p>':''}`;
}
function decisionlab(){
  const draft=getComparisonDraft(),revision=state.workspace?.revision,options=revision?.decision.options||[];
  const radar=`<div class="metrics"><div class="metric"><span>Decisions tracked</span><strong>${radarState.total}</strong></div><div class="metric"><span>Changes or challenged evidence</span><strong>${radarState.needs_review}</strong></div><div class="metric"><span>Missing review inputs</span><strong>${radarState.with_gaps}</strong></div></div><section class="panel"><div class="section-head"><h2>Review radar</h2><button class="secondary" id="refresh-radar">Refresh</button></div><p class="note">${esc(radarState.note)}</p>${radarState.decisions.map(item=>`<article class="record"><button class="quiet radar-choice" data-radar-id="${esc(item.decision_id)}">${esc(item.title)} · revision ${item.version}</button><div>${item.flags.map(flag=>`<span class="tag">${esc(flag.message)}${Number(flag.count)>1?' ('+Number(flag.count)+')':''}</span>`).join('')||'<span class="tag">No rule-based flags</span>'}</div></article>`).join('')||'<p>Create a decision to start tracking review needs.</p>'}</section>`;
  if(!draft)return intro('REVIEW / COMPARE / LEARN','Make tradeoffs visible.','Understand what needs review and how your priorities shape a decision.',false)+radar+noDecision();
  const saved=state.workspace.records.filter(record=>record.kind==='option_comparison').slice().reverse();
  return intro('REVIEW / COMPARE / LEARN','Make tradeoffs visible.','Compare human assessments, test priorities, and preserve the reasoning.')+radar+
    `<section class="panel"><div class="section-head"><div><h2>Option comparison</h2><p>Decision revision ${revision.version} · All scores are your assessments.</p></div><button class="secondary" id="download-brief">Download decision brief</button></div><p class="note">The JSON brief contains this decision, claims, source impacts and recorded analyses. Review it before sharing.</p>${options.length<2||options.length>20?'<p>Add between 2 and 20 distinct options to the decision before comparing.</p>':`
    <label>Evaluation criteria, one per line<textarea id="comparison-criteria" rows="3" maxlength="810">${draft.criteria.map(esc).join('\n')}</textarea></label><button class="secondary" id="apply-criteria">Apply criteria</button><p class="note">Changing criteria resets scores. Rate desirability from 0 to 10; higher must always mean better. For cost or risk, score affordability or safety, not the raw amount.</p>
    <form id="comparison-form"><div class="comparison-scroll"><table><thead><tr><th>Option</th>${draft.criteria.map((name,index)=>`<th><label>${esc(name)} weight<input data-weight="${index}" aria-label="${esc(name)} weight" type="number" min="0.01" max="100" step="any" value="${draft.weights[index]}" required></label></th>`).join('')}</tr></thead><tbody>${options.map((option,row)=>`<tr><th scope="row">${esc(option.name)}</th>${draft.criteria.map((criterion,col)=>`<td><input type="number" min="0" max="10" step="any" data-score-row="${row}" data-score-col="${col}" aria-label="${esc(option.name)}: ${esc(criterion)}" value="${esc(draft.scores[row][col])}" required></td>`).join('')}</tr>`).join('')}</tbody></table></div>${options.map((option,row)=>`<label>Why these scores for ${esc(option.name)}?<textarea data-rationale="${row}" maxlength="4000" required>${esc(draft.rationales[row])}</textarea></label>`).join('')}<div class="toolbar"><button class="primary" type="submit">Preview tradeoffs</button><button class="secondary" type="button" id="save-comparison" ${draft.result?'':'disabled'}>Save comparison</button></div></form><div id="comparison-result" aria-live="polite">${comparisonResults(draft.result)}</div>`}</section>
    <section class="panel"><h2>Saved comparison history</h2>${saved.map(record=>`<details class="record"><summary>${date(record.created_at)} · revision ${record.version}${record.version!==revision.version?' · historical':''}</summary><p>Recorded by ${esc(record.author)}</p>${comparisonResults(record)}</details>`).join('')||'<p>No comparisons saved yet.</p>'}</section>`;
}
function comparisonBody(draft){return {base_version:state.workspace.revision.version,criteria:draft.criteria.map((name,index)=>({name,weight:Number(draft.weights[index])})),options:state.workspace.revision.decision.options.map((option,row)=>({option:option.name,scores:Object.fromEntries(draft.criteria.map((name,col)=>[name,Number(draft.scores[row][col])])),rationale:draft.rationales[row]}))};}
function bindDecisionLab(){
  $('#refresh-radar').onclick=e=>busy(e.target,async()=>{await load();await loadDecisionLab();render();});
  document.querySelectorAll('[data-radar-id]').forEach(button=>button.onclick=()=>busy(button,async()=>{await select(button.dataset.radarId);}));
  $('#download-brief')?.addEventListener('click',e=>busy(e.target,async()=>{
    const identifier=state.selected,brief=await api('/v2/decisions/'+identifier+'/brief');
    const url=URL.createObjectURL(new Blob([JSON.stringify(brief,null,2)],{type:'application/json'}));
    const link=document.createElement('a');link.href=url;link.download='praxis-decision-'+identifier+'-v'+brief.decision_version+'.json';document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }));
  const draft=getComparisonDraft();if(!$('#comparison-form'))return;
  const changed=()=>{draft.result=null;$('#save-comparison').disabled=true;$('#comparison-result').innerHTML=comparisonResults(null);};
  document.querySelectorAll('[data-weight]').forEach(input=>input.oninput=()=>{draft.weights[Number(input.dataset.weight)]=input.value;changed();});
  document.querySelectorAll('[data-score-row]').forEach(input=>input.oninput=()=>{draft.scores[Number(input.dataset.scoreRow)][Number(input.dataset.scoreCol)]=input.value;changed();});
  document.querySelectorAll('[data-rationale]').forEach(input=>input.oninput=()=>{draft.rationales[Number(input.dataset.rationale)]=input.value;changed();});
  $('#apply-criteria').onclick=()=>{
    const criteria=lines($('#comparison-criteria').value);
    if(!criteria.length||criteria.length>10||criteria.some(name=>name.length>80)||new Set(criteria.map(name=>name.toLowerCase())).size!==criteria.length){toast('Use 1–10 distinct criteria, at most 80 characters each.',true);return;}
    draft.criteria=criteria;draft.weights=criteria.map(()=>1);draft.scores=state.workspace.revision.decision.options.map(()=>criteria.map(()=>''));draft.result=null;render();
  };
  $('#comparison-form').onsubmit=e=>{e.preventDefault();busy(e.submitter,async()=>{
    const result=await api('/v2/decisions/'+state.selected+'/comparisons/preview',comparisonBody(draft));
    if(comparisonDraft!==draft||state.page!=='decisionlab')return;
    draft.result=result;render();
  });};
  $('#save-comparison').onclick=e=>busy(e.target,async()=>{
    if(!$('#comparison-form').reportValidity())return;
    const result=await api('/v2/decisions/'+state.selected+'/comparisons',comparisonBody(draft));
    if(comparisonDraft!==draft||state.page!=='decisionlab')return;
    draft.result=result;await load();render();toast('Comparison preserved with its inputs and decision revision.');
  });
}
document.addEventListener('DOMContentLoaded',()=>{
  $('#signout').addEventListener('click',()=>{comparisonDraft=null;radarState={decisions:[],total:0,needs_review:0,with_gaps:0,note:''};});
  const button=document.createElement('button');button.dataset.page='decisionlab';button.textContent='◎ Decision lab';
  button.onclick=()=>busy(button,async()=>{await load();await loadDecisionLab();state.page='decisionlab';render();});
  $('nav').appendChild(button);
});
