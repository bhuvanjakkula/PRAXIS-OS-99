import pytest
from pydantic import ValidationError
from praxis.services.maritime_coordination import LedgerProposalReview, review_ledger


def proposal(**changes):
    return LedgerProposalReview(architecture_and_scope='Synthetic permissioned ledger', **changes)


def test_latency_requires_both_values_and_provenance():
    with pytest.raises(ValidationError):proposal(measured_latency_ms=20)
    with pytest.raises(ValidationError):proposal(measured_latency_ms=20,latency_budget_ms=0)
    a=review_ledger(proposal(measured_latency_ms=20,latency_budget_ms=10))
    assert a['latency_margin_ms'] is None
    a=review_ledger(proposal(measured_latency_ms=20,latency_budget_ms=10,
        latency_measurement_reference='Synthetic test',latency_budget_reference='Owner requirement'))
    assert a['latency_margin_ms']==-10
    assert 'Supplied latency exceeds reviewer budget' in a['gaps']


def test_complete_proposal_remains_unverified():
    fields={k:'Synthetic reference' for k in ('sensor_validation_reference',
        'administrator_and_membership_reference','contract_upgrade_reference',
        'offline_recovery_reference','privacy_reference','resource_measurement_reference',
        'non_ledger_alternative','latency_measurement_reference','latency_budget_reference')}
    a=review_ledger(proposal(measured_latency_ms=5,latency_budget_ms=10,**fields))
    assert a['gaps']==[] and a['latency_margin_ms']==5
    assert a['status']=='documented_unverified'
    assert not a['sensor_truth_established'] and not a['deployment_authorized']


def test_message_evidence_cannot_silently_clear_physical_signal_gaps():
    a=review_ledger(proposal(spoofing_threat_scope='Message signature test',
        message_authentication_reference='Synthetic signature results',
        validation_setting='other_domain'))
    assert a['spoofing_review_included']
    assert 'Missing physical signal validation reference' in a['gaps']
    assert 'Other-domain results require maritime validation' in a['gaps']
    assert not a['spoofing_protection_established']


def test_receipt_alone_does_not_clear_sensor_and_state_link_gaps():
    a=review_ledger(proposal(anchoring_receipt_reference='Synthetic receipt'))
    assert a['anchoring_review_included']
    assert 'Missing sensor independence reference' in a['gaps']
    assert 'Missing disagreement handling reference' in a['gaps']
    assert 'Missing validation to anchor reference' in a['gaps']
    assert not a['state_validation_established'] and not a['ledger_receipt_verified']


def test_complete_anchoring_references_are_supplied_not_verified():
    a=review_ledger(proposal(sensor_independence_reference='Synthetic calibration review',
        disagreement_handling_reference='Rejected-state test',
        validation_to_anchor_reference='State/version link',anchoring_receipt_reference='Receipt'))
    assert a['anchoring_review_included']
    assert not any('sensor independence' in g or 'validation to anchor' in g for g in a['gaps'])
    assert not a['state_validation_established'] and not a['ledger_receipt_verified']
    assert not review_ledger(proposal())['anchoring_review_included']


def test_complete_maritime_references_do_not_certify_spoofing_protection():
    a=review_ledger(proposal(spoofing_threat_scope='Synthetic combined test',
        message_authentication_reference='Message evidence',replay_protection_reference='Freshness evidence',
        physical_signal_validation_reference='Physical evidence',validation_setting='maritime_field',
        vessel_applicability_reference='Scope review'))
    assert not any('physical signal' in g or 'validation setting' in g for g in a['gaps'])
    assert not a['spoofing_protection_established']
    assert not review_ledger(proposal())['spoofing_review_included']
    with pytest.raises(ValidationError):proposal(validation_setting='certified')
