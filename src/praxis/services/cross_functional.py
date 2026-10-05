"""Owned knowledge transfer and operational follow-up, with explicit evidence gaps."""
from datetime import date
from typing import Literal
from pydantic import Field, model_validator
from praxis.services.research import Inputs


class Handoff(Inputs):
    title: str = Field(min_length=1,max_length=200)
    sending_team: str = Field(min_length=1,max_length=200)
    receiving_team: str = Field(min_length=1,max_length=200)
    owner: str = Field(default='',max_length=200)
    due_on: date
    stage: Literal['captured','shared','trial','reviewed']
    source: str = Field(default='',max_length=2000)
    interpretation: str = Field(default='',max_length=2000)
    acceptance: str = Field(default='',max_length=2000)
    experiment: str = Field(default='',max_length=2000)
    result: str = Field(default='',max_length=2000)
    reviewer: str = Field(default='',max_length=200)
    result_reference: str = Field(default='',max_length=2000)


class IntegrationReview(Inputs):
    as_of: date
    shared_objective: str = Field(min_length=1,max_length=2000)
    escalation_owner: str = Field(min_length=1,max_length=200)
    handoffs: list[Handoff] = Field(min_length=1,max_length=30)

    @model_validator(mode='after')
    def distinct(self):
        if len({h.title.casefold() for h in self.handoffs})!=len(self.handoffs):raise ValueError('Use distinct handoff titles')
        return self


def analyze_integration(p):
    rows=[]
    required={'captured':['owner','source'],
              'shared':['owner','source','interpretation','acceptance'],
              'trial':['owner','source','interpretation','acceptance','experiment'],
              'reviewed':['owner','source','interpretation','acceptance','experiment','result','reviewer','result_reference']}
    for h in p.handoffs:
        missing=[key for key in required[h.stage] if not getattr(h,key)]
        complete=h.stage=='reviewed' and not missing
        overdue=h.due_on<p.as_of and not complete
        rows.append(dict(title=h.title,sending_team=h.sending_team,receiving_team=h.receiving_team,
                         owner=h.owner or None,stage=h.stage,due_on=h.due_on.isoformat(),
                         status='review_documented' if complete else 'overdue' if overdue else 'evidence_missing' if missing else 'in_progress',
                         missing=missing,escalation_owner=p.escalation_owner if overdue or not h.owner else None,
                         next_step='Record a later outcome review if conditions change.' if complete else
                         'Supply '+', '.join(missing)+'.' if missing else
                         {'captured':'Translate the source into a shared interpretation and obtain receiving-team acceptance.',
                          'shared':'Define a bounded test, responsible owner and acceptance criteria.',
                          'trial':'Record the measured result, evidence reference and responsible review.'}.get(h.stage,'Review outstanding evidence.')))
    return dict(shared_objective=p.shared_objective,as_of=p.as_of.isoformat(),handoffs=rows,
                overdue_count=sum(r['status']=='overdue' for r in rows),
                documented_reviews=sum(r['status']=='review_documented' for r in rows),
                limitations='Workflow completeness from supplied records, not independent confirmation of acceptance, successful innovation, effective hazard control or permission to operate. Recorded results may be negative or inconclusive. No messages, alerts or background monitoring are sent.')
