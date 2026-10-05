/* Responses live beside results; rejection produces a preserved candidate revision. */
function suggestionCard(advice){
  const responses=state.workspace.records.filter(r=>r.kind==='suggestion_response'&&r.version===state.workspace.revision.version&&r.advice_id===advice.id);
  const response=responses.at(-1);
  return `<article class="record"><h3>${esc(advice.title)}</h3>${list(advice.statements)}<p class="note">${esc(advice.limitations)}</p>${response?`<p>Response: <strong>${esc(response.disposition)}</strong>${response.reason?` · ${esc(response.reason)}`:''}</p>`:`<form data-suggestion="${esc(advice.id)}"><div class="toolbar"><button type="submit" name="disposition" value="accept" class="primary">Accept</button><button type="button" data-reject class="secondary">Reject</button></div><div data-reason hidden><label>Why is this suggestion unsuitable?<textarea name="reason" maxlength="4000" rows="3"></textarea></label><button type="submit" name="disposition" value="reject" class="primary">Generate updated suggestion</button></div></form>`}</article>`;
}
function suggestionPanel(){
  const kinds={simulation:['simulation'],decisionlab:['option_comparison'],researchpage:['research_memo'],foresightpage:['foresight_run','forecast_observation']};
  const items=(state.workspace.suggestions||[]).filter(a=>!kinds[state.page]||kinds[state.page].includes(a.kind)||a.kind==='updated_suggestion');
  return `<section class="panel" id="suggestion-results" aria-live="polite"><h2>Suggestions · accept or improve</h2>${items.map(suggestionCard).join('')||'<p>Generate a result to respond to its suggestion.</p>'}</section>`;
}
function experimentSuggestion(e){
  const original={id:`experiment:${e.id}:${e.version}`,title:'Suggestion after experiment results',statements:[`Observed ${e.actual} ${e.unit}; predicted ${e.predicted} ${e.unit}.`,`Recorded lesson: ${e.lesson}`,'Repeat a bounded test or revise the approach using this outcome before expanding it.'],limitations:'Outcome and lesson are self-reported; success criteria still need interpretation.'};
  const related=new Set([original.id]);
  for(const r of state.workspace.records)if(r.kind==='suggestion_response'&&related.has(r.advice_id))related.add(r.id);
  const updates=(state.workspace.suggestions||[]).filter(a=>a.kind==='updated_suggestion'&&related.has(a.id));
  return suggestionCard(original)+updates.map(suggestionCard).join('');
}
function bindSuggestions(){
  document.querySelectorAll('[data-suggestion]').forEach(form=>{
    form.querySelector('[data-reject]').onclick=()=>{form.querySelector('[data-reason]').hidden=false;form.elements.reason.focus();};
    form.onsubmit=e=>{e.preventDefault();const disposition=e.submitter.value;
      const reason=disposition==='reject'?form.elements.reason.value.trim():'';
      if(disposition==='reject'&&!reason){toast('Tell us why this suggestion is unsuitable.',true);form.elements.reason.focus();return;}
      busy(e.submitter,async()=>{await api(`/v2/decisions/${state.selected}/responses`,{base_version:state.workspace.revision.version,advice_id:form.dataset.suggestion,disposition,reason});await load();render();toast(disposition==='reject'?'Updated suggestion generated from your reason.':'Suggestion accepted.');});
    };
  });
}
