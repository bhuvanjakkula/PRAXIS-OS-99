"""Inline accept/reject feedback with an append-only sequence of revised suggestions."""
from typing import Literal
from pydantic import Field, model_validator
from praxis.services.research import Inputs
from praxis.services.decision_loop import RevisionConflict
from praxis.services.human_review import advice_items


class SuggestionResponse(Inputs):
    base_version: int = Field(ge=1)
    advice_id: str = Field(min_length=1,max_length=150)
    disposition: Literal['accept','reject']
    reason: str = Field(default='',max_length=4000)
    @model_validator(mode='after')
    def rejection_reason(self):
        if self.disposition=='reject' and not self.reason:
            raise ValueError('Tell us why this suggestion is not suitable so it can be revised')
        return self


def result_advice(revision,records,experiment=None):
    items=advice_items(revision,records)
    for record in records:
        if record['version']!=revision.version:continue
        if record['kind']=='decision_compute':
            items.append({'id':record['id'],'title':'Computational decision suggestion','kind':'decision_compute',
                          'statements':record['analysis']['next_steps'],'analysis':record['analysis'],
                          'limitations':record['analysis']['limitations']})
        if record['kind']=='practical_inquiry':
            items.append({'id':record['id'],'title':'Practical inquiry suggestion','kind':'practical_inquiry',
                          'statements':record['analysis']['next_steps'],'analysis':record['analysis'],
                          'limitations':record['analysis']['limitations']})
        if record['kind']=='inquiry_observation':
            items.append({'id':record['id'],'title':'Suggestion after measured inquiry','kind':'inquiry_observation',
                          'statements':record['statements'],'result_snapshot':record,
                          'limitations':'Self-reported test outcome; repeat and verify before generalizing.'})
        if record['kind']=='simulation':
            items.append({'id':record['id'],'title':'Suggestion after simulation','kind':'simulation',
                          'statements':['Use the simulated outcomes to choose a bounded test before scaling.'],
                          'result_snapshot':record,'limitations':'Simulation results depend on supplied assumptions.'})
        if record['kind']=='forecast_observation':
            items.append({'id':record['id'],'title':'Suggestion after the observed forecast outcome','kind':'forecast_observation',
                          'statements':[f"Observed forecast error: {record['error']} {record['unit']}.",
                                        'Update the measurement history and retest the forecast before using it for a larger commitment.'],
                          'result_snapshot':record,'limitations':'The recorded observation is user-supplied.'})
        if record['kind']=='suggestion_response' and record.get('updated_suggestion'):
            items.append({'id':record['id'],'kind':'updated_suggestion',**record['updated_suggestion']})
    if experiment:
        if str(experiment['decision_id'])!=str(revision.decision_id) or experiment.get('status')!='observed':
            raise ValueError('An observed experiment from this decision is required')
        items.append({'id':f"experiment:{experiment['id']}:{experiment['version']}",'kind':'experiment',
                      'title':'Suggestion after experiment results',
                      'statements':[f"Observed {experiment['actual']} {experiment['unit']}; predicted {experiment['predicted']} {experiment['unit']}.",
                                    f"Recorded lesson: {experiment['lesson']}",
                                    'Repeat a bounded test or revise the approach using this outcome before expanding it.'],
                      'result_snapshot':experiment,'limitations':'Outcome and lesson are self-reported; success criteria still need interpretation.'})
    return items


def revise_suggestion(decision,advice,reason):
    previous=advice.get('feedback_considered',[])
    reasons=[*previous,reason][-20:]
    text=' '.join(reasons).casefold()
    changes=[]
    if any(word in text for word in ['cost','budget','expensive','afford','money']):
        changes.append('Reduce the scope to the smallest affordable test; require a cost estimate within your stated budget before proceeding.')
    if any(word in text for word in ['time','slow','deadline','urgent','delay']):
        changes.append('Split the work into a short first milestone and postpone optional steps; confirm the deadline and delivery estimate first.')
    if any(word in text for word in ['risk','safe','harm','danger','irreversible']):
        changes.append('Use a reversible trial with a stop condition and fallback; resolve the specific harm concern before expansion.')
    if any(word in text for word in ['evidence','data','wrong','result','accurate','uncertain']):
        changes.append('Gather a fresh measurement that tests the disputed assumption and recalculate the analysis before selecting an option.')
    if any(word in text for word in ['complex','difficult','skill','team','resource']):
        changes.append('Simplify the approach to one deliverable that the available team can test; remove or replace the hardest dependency.')
    prior_options=advice.get('considered_options',[])
    analysis=advice.get('analysis',{})
    rejected_options=analysis.get('leaders',[]) or analysis.get('leaders_under_supplied_inputs',[])
    considered=list(dict.fromkeys([*prior_options,*rejected_options]))
    alternative=next((o.name for o in decision.options if o.name not in considered),None)
    if alternative:considered.append(alternative)
    if not changes:
        changes.append('Redesign the first step around the stated concern, then test whether the revised approach meets that requirement before making a larger commitment.')
    statements=([f'Consider {alternative} as a candidate alternative for: {decision.objective}.'] if alternative else
                [f'Reframe the approach to achieve: {decision.objective}.'])+changes
    statements.append('Use your stated reason as an acceptance condition: '+reason)
    if decision.constraints:statements.append('Retain these decision constraints: '+'; '.join(decision.constraints))
    return {'title':'Updated suggestion','statements':statements,'feedback_considered':reasons,
            'considered_options':considered,'why_changed':reason,
            'limitations':'Feedback-guided candidate, not a recalculated forecast or verified solution. Confirm missing budgets, deadlines and acceptance criteria before acting.'}


def respond(studio,identifier,request,experiment=None,actor='local-user'):
    revision=studio.loop.latest(identifier)
    if revision.version!=request.base_version:raise RevisionConflict('The decision changed; reload before responding')
    records=studio.records(identifier)
    advice=next((a for a in result_advice(revision,records,experiment) if a['id']==request.advice_id),None)
    if not advice:raise ValueError('Suggestion must belong to this decision and current revision')
    responses=[r for r in records if r['version']==revision.version and r['kind']=='suggestion_response' and r['advice_id']==request.advice_id]
    if responses:raise RevisionConflict('This suggestion already has a response. Respond to the updated suggestion instead.')
    updated=revise_suggestion(revision.decision,advice,request.reason) if request.disposition=='reject' else None
    return studio._record(identifier,revision.version,'suggestion_response',{
        **request.model_dump(mode='json'),'author':actor,'advice_snapshot':advice,
        'updated_suggestion':updated,'execution_status':'not_executed'})
