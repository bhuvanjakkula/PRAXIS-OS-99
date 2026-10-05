"""Owned aviation security and technology-development reviews."""
from datetime import date
from typing import Literal
from pydantic import Field, model_validator
from praxis.services.research import Inputs


class AviationSecurityProject(Inputs):
    name: str = Field(min_length=1, max_length=200)
    scope: Literal['airport', 'aircraft', 'command_team', 'operations']
    area: Literal['identity_access', 'data_links', 'software_supply_chain',
                  'network_isolation', 'navigation_integrity', 'incident_recovery',
                  'quantum_migration']
    asset_and_interface: str = Field(min_length=1, max_length=2000)
    technology: Literal['existing_controls', 'post_quantum', 'hybrid_crypto', 'qkd_research', 'other']
    stage: Literal['discovery', 'prototype', 'validation', 'handover'] = 'discovery'
    owner: str = Field(default='', max_length=200)
    commander_or_operations_role: str = Field(default='', max_length=200)
    threat_and_requirements: str = Field(default='', max_length=2000)
    inventory_reference: str = Field(default='', max_length=2000)
    authentication_and_key_lifecycle_reference: str = Field(default='', max_length=2000)
    applicability_reference: str = Field(default='', max_length=2000)
    isolated_test_plan: str = Field(default='', max_length=2000)
    validation_reference: str = Field(default='', max_length=2000)
    performance_and_interoperability_reference: str = Field(default='', max_length=2000)
    fallback_and_rollback_reference: str = Field(default='', max_length=2000)
    safety_and_authority_reference: str = Field(default='', max_length=2000)
    qkd_link_and_failure_reference: str = Field(default='', max_length=2000)
    findings_status: Literal['unreviewed', 'open', 'none_reported'] = 'unreviewed'
    next_action: str = Field(default='', max_length=2000)
    review_on: date


class AviationSecurityReview(Inputs):
    as_of: date
    projects: list[AviationSecurityProject] = Field(min_length=1, max_length=20)

    @model_validator(mode='after')
    def consistent(self):
        names=[p.name.strip().casefold() for p in self.projects]
        if any(not n for n in names) or len(set(names))!=len(names):
            raise ValueError('Use distinct nonblank project names')
        return self


def analyze_aviation_security(review):
    rows=[]
    for p in review.projects:
        required=['owner','commander_or_operations_role','threat_and_requirements',
                  'inventory_reference','authentication_and_key_lifecycle_reference',
                  'applicability_reference','isolated_test_plan','next_action']
        if p.stage in ('validation','handover'):
            required += ['validation_reference','performance_and_interoperability_reference',
                         'fallback_and_rollback_reference','safety_and_authority_reference']
        if p.technology=='qkd_research':required.append('qkd_link_and_failure_reference')
        gaps=['Missing '+k.replace('_',' ') for k in required if not getattr(p,k).strip()]
        if p.findings_status!='none_reported':gaps.append('Open findings' if p.findings_status=='open' else 'Findings unreviewed')
        if p.review_on<review.as_of:gaps.append('Security project review overdue')
        rows.append(dict(**p.model_dump(mode='json'),gaps=gaps,
                         review_status='review_required' if gaps else 'documented_unverified',
                         requested_stage_documented=not gaps, deployment_authorized=False,
                         quantum_protection_established=False, flight_clearance=False))
    return dict(as_of=review.as_of.isoformat(),projects=rows,
                review_required_count=sum(bool(r['gaps']) for r in rows),
                unrepresented_scopes=[s for s in ('airport','aircraft','command_team','operations') if s not in {p.scope for p in review.projects}],
                security_effectiveness_established=False,execution_status='not_executed',
                references=[dict(title='NIST post-quantum cryptography standards',url='https://www.nist.gov/news-events/news/2024/08/announcing-approval-three-federal-information-processing-standards-fips'),
                            dict(title='NSA QKD limitations (National Security Systems scope)',url='https://www.nsa.gov/Cybersecurity/Quantum-Key-Distribution-QKD-and-Quantum-Cryptography-QC/')],
                limitations='Planning and supplied evidence review. No live airport/aircraft connections, cryptographic implementation, threat detection, commander authentication, roster change or operational approval. Documentation does not establish protection or certification.')
