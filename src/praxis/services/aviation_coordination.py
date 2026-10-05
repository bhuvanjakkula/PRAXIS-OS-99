"""Organizational aviation preparation reviews, never operational clearance."""
from datetime import date
from typing import Literal
from pydantic import Field, model_validator
from praxis.services.research import Inputs
from praxis.services.cross_functional import IntegrationReview, analyze_integration
from praxis.services.aviation_evidence import AviationEvidence, analyze_aviation_evidence
from praxis.services.aviation_security import AviationSecurityReview, analyze_aviation_security

AVIATION_AREAS={
 'fatigue':'Review the documented interface between rostering, fatigue reports and the responsible fatigue-management process; retain the applicable approved policy reference.',
 'crm':'Record flight-deck, cabin, dispatch and ground-team communication responsibilities and joint-training follow-up.',
 'support':'Document the approved occupational-health or peer-support referral route and its confidentiality boundaries; keep clinical details in the authorized system.',
 'environment':'Assign cabin-environment and ergonomic reports to the responsible maintenance or occupational-health process, with observation provenance.',
 'procedures':'Have the authorized reviewer check the procedure reference, applicability and revision in the controlled source.',
 'assurance':'Record how de-identified audit or occurrence findings lead to owned corrective actions and a later effectiveness review.',
 'reporting':'Document accessible reporting channels, escalation ownership and applicable information-sharing protections without promising absolute confidentiality.'}


class AviationCheck(Inputs):
    area: Literal['fatigue','crm','support','environment','procedures','assurance','reporting']
    status: Literal['unknown','gap','pass']
    owner: str = Field(default='',max_length=200)
    reference: str = Field(default='',max_length=2000)
    review_on: date


class AviationCoordination(Inputs):
    security_review: AviationSecurityReview | None = None
    evidence_review: AviationEvidence | None = None
    as_of: date
    checks: list[AviationCheck] = Field(min_length=7,max_length=7)
    integration: IntegrationReview | None = None

    @model_validator(mode='after')
    def consistent(self):
        if self.security_review and self.security_review.as_of!=self.as_of:
            raise ValueError('Security and coordination dates must match')
        if {c.area for c in self.checks}!=set(AVIATION_AREAS):raise ValueError('Review each aviation coordination area once')
        if self.integration and self.integration.as_of!=self.as_of:raise ValueError('Coordination dates must match')
        if self.evidence_review:
            if self.evidence_review.as_of!=self.as_of:raise ValueError('Evidence and coordination dates must match')
            handoffs={h.title for h in self.integration.handoffs} if self.integration else set()
            if any(not set(e.followup_handoffs)<=handoffs for e in self.evidence_review.exercises):
                raise ValueError('Exercise follow-up must name handoffs in this review exactly')
        return self


def analyze_aviation_coordination(p):
    actions=[]
    for c in p.checks:
        reasons=[]
        if c.status!='pass':reasons.append('Reported gap' if c.status=='gap' else 'Status unknown')
        if not c.owner:reasons.append('Missing responsible owner')
        if not c.reference:reasons.append('Missing approved process or evidence reference')
        if c.review_on<p.as_of:reasons.append('Review overdue')
        if reasons:actions.append(dict(area=c.area,reasons=reasons,owner=c.owner or None,review_on=c.review_on.isoformat(),action=AVIATION_AREAS[c.area]))
    return dict(security_review=analyze_aviation_security(p.security_review) if p.security_review else None,evidence_review=analyze_aviation_evidence(p.evidence_review) if p.evidence_review else None,
                actions=actions,integration=analyze_integration(p.integration) if p.integration else None,
                status='organizational_review_only',flight_clearance=False,fitness_assessment=False,
                limitations='Training, preparation and de-identified organizational follow-up only. This software does not evaluate personal medical fitness, compute fatigue scores, determine legal duty limits, approve schedules, certify SMS/FRMS compliance or issue flight instructions. Supplied process confirmations are unverified. Use the operator’s authorized processes and responsible professionals for actual decisions.',
                references=[{'title':'FAA SMS components','url':'https://www.faa.gov/about/initiatives/sms/explained/components'},
                            {'title':'ICAO flight operations and fatigue management','url':'https://www.icao.int/operational-safety/flight-ops'}])
