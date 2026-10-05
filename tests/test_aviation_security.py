import pytest
from pydantic import ValidationError
from praxis.services.aviation_security import AviationSecurityReview, analyze_aviation_security


def project(**changes):
    return dict(name='Airport identity prototype',scope='airport',area='quantum_migration',
        asset_and_interface='Synthetic ground link',technology='post_quantum',review_on='2026-10-02')|changes


def analyze(*projects):
    return analyze_aviation_security(AviationSecurityReview(as_of='2026-10-04',projects=list(projects)))


def test_validation_stage_does_not_clear_missing_approval_and_tests():
    a=analyze(project(stage='validation'))['projects'][0]
    assert 'Missing safety and authority reference' in a['gaps']
    assert 'Missing fallback and rollback reference' in a['gaps']
    assert 'Security project review overdue' in a['gaps']
    assert not a['deployment_authorized'] and not a['quantum_protection_established']


def test_qkd_requires_link_and_failure_evidence_and_open_findings_persist():
    a=analyze(project(technology='qkd_research',findings_status='open'))['projects'][0]
    assert 'Missing qkd link and failure reference' in a['gaps'] and 'Open findings' in a['gaps']


def test_complete_handover_documentation_is_not_deployment_authority():
    fields={k:'Synthetic reference' for k in ('owner','commander_or_operations_role',
        'threat_and_requirements','inventory_reference','authentication_and_key_lifecycle_reference',
        'applicability_reference','isolated_test_plan','next_action','validation_reference',
        'performance_and_interoperability_reference','fallback_and_rollback_reference','safety_and_authority_reference')}
    a=analyze(project(stage='handover',findings_status='none_reported',review_on='2026-10-10',**fields))
    assert a['projects'][0]['gaps']==[]
    assert a['projects'][0]['review_status']=='documented_unverified'
    assert not a['projects'][0]['deployment_authorized']
    assert 'aircraft' in a['unrepresented_scopes']
    with pytest.raises(ValidationError):analyze(project(),project())
