import pytest
from pydantic import ValidationError
from praxis.services.innovation_network import InnovationNetwork, analyze_network
from praxis.services.cross_functional import IntegrationReview, analyze_integration
from praxis.services.aviation_coordination import AviationCoordination, AVIATION_AREAS, analyze_aviation_coordination


def network_payload():
    def link(a,b,status='observed'):
        return dict(source=a,target=b,status=status,recorded_on='2026-10-01',evidence='Synthetic workshop',owner='Team owner',outcome='Test transfer')
    return dict(as_of='2026-10-03',max_age_days=10,scope='Synthetic three-unit chain',
                units=[dict(name=n,function=n,kind='external' if n=='C' else 'internal') for n in 'ABC'],
                links=[link('A','B'),link('B','C'),link('A','C','proposed')])


def integration_payload():
    return dict(as_of='2026-10-03',shared_objective='Evaluate a reported issue',escalation_owner='Review lead',handoffs=[
        dict(title='Knowledge trial',sending_team='Research',receiving_team='Operations',owner='Ops lead',due_on='2026-10-02',
             stage='reviewed',source='Report',interpretation='Testable observation',acceptance='Meeting note',
             experiment='Bounded exercise',result='Inconclusive',reviewer='Safety lead',result_reference='Review log')])


def aviation_payload():
    return dict(as_of='2026-10-03',checks=[dict(area=a,status='pass',owner='Responsible role',reference='Approved process reference',review_on='2026-10-10') for a in AVIATION_AREAS],integration=integration_payload())


def test_chain_betweenness_removal_and_hypothetical_triangle():
    a=analyze_network(InnovationNetwork(**network_payload()))
    middle=a['current']['units'][1]
    assert middle['degree']==2 and middle['betweenness']==1
    assert middle['newly_disconnected_pairs_if_removed']==1
    assert a['current']['density']==pytest.approx(2/3)
    assert a['with_proposals']['density']==1
    assert all(u['betweenness']==0 and u['clustering']==1 and u['newly_disconnected_pairs_if_removed']==0 for u in a['with_proposals']['units'])
    assert a['current']['internal_external_links']==1


def test_missing_stale_and_isolated_units_do_not_become_observed_connections():
    p=network_payload();p['links'][0]['evidence']='';p['links'][1]['recorded_on']='2026-01-01'
    a=analyze_network(InnovationNetwork(**p))
    assert a['current']['component_count']==3 and a['current']['link_count']==0
    assert len(a['excluded_links'])==2 and a['with_proposals']['link_count']==1
    assert all(u['degree_centrality']==0 and u['betweenness']==0 for u in a['current']['units'])


def test_disconnected_graph_removal_counts_only_newly_disconnected_pairs():
    p=network_payload();p['links']=p['links'][:2]
    p['units'].append(dict(name='D',function='Other',kind='internal'))
    a=analyze_network(InnovationNetwork(**p))['current']
    assert a['component_count']==2
    assert a['units'][1]['betweenness']==pytest.approx(1/3)
    assert a['units'][1]['newly_disconnected_pairs_if_removed']==1
    assert a['units'][3]['newly_disconnected_pairs_if_removed']==0


def test_network_rejects_duplicates_unknown_names_and_future_evidence():
    for change in ('duplicate','unknown','future','self'):
        p=network_payload()
        if change=='duplicate':p['links'].append(p['links'][0]|{'source':'B','target':'A'})
        if change=='unknown':p['links'][0]['source']='Unknown'
        if change=='future':p['links'][0]['recorded_on']='2026-10-04'
        if change=='self':p['links'][0]['target']='A'
        with pytest.raises(ValidationError):InnovationNetwork(**p)


def test_reviewed_handoff_needs_result_evidence_and_negative_results_are_retained():
    p=integration_payload();a=analyze_integration(IntegrationReview(**p))
    assert a['documented_reviews']==1 and a['overdue_count']==0
    p['handoffs'][0]['result_reference']=''
    a=analyze_integration(IntegrationReview(**p))
    assert a['documented_reviews']==0 and a['overdue_count']==1
    assert a['handoffs'][0]['escalation_owner']=='Review lead'
    assert 'result_reference' in a['handoffs'][0]['missing']


def test_aviation_all_passes_do_not_imply_fitness_or_clearance():
    p=aviation_payload();a=analyze_aviation_coordination(AviationCoordination(**p))
    assert a['actions']==[] and a['flight_clearance'] is False and a['fitness_assessment'] is False
    p['checks'][0]['reference']='';p['checks'][1]['review_on']='2026-10-02'
    assert len(analyze_aviation_coordination(AviationCoordination(**p))['actions'])==2
    p['integration']['as_of']='2026-10-01'
    with pytest.raises(ValidationError):AviationCoordination(**p)


def test_cto_network_date_consistency_and_integration():
    from test_leadership_execution import technology_payload
    from praxis.services.cto_strategy import CTOStrategy,analyze_cto_strategy
    p=technology_payload();p['network']=network_payload();p['network']['integration']=integration_payload()
    a=analyze_cto_strategy(CTOStrategy(**p))
    assert a['network_review']['integration']['documented_reviews']==1
    p['network']['as_of']='2026-10-04'
    with pytest.raises(ValidationError):CTOStrategy(**p)


def test_aviation_coordination_authenticated_persistence(sql_store):
    from fastapi.testclient import TestClient
    from praxis.product.api import create_app
    from praxis.product.security import Credentials
    credentials=Credentials('network-review-test-key-only-not-real-credentials')
    def auth(role='admin',tenant='alpha'):
        return {'Authorization':'Bearer '+credentials.issue('reviewer',tenant,[role])}
    with TestClient(create_app(sql_store,credentials)) as client:
        identifier=client.post('/v1/decision-models',headers=auth(),json=dict(title='Review',problem='Prepare',objective='Document')).json()['decision_id']
        path=f'/v2/decisions/{identifier}/operations-incidents'
        payload=dict(base_version=1,domain='aviation',platform_type='Training',identifier='Test',phase='Preparation',
                     situation='Coordination exercise',observations='Synthetic',coordination=aviation_payload())
        assert client.post(path,headers=auth('reader'),json=payload).status_code==403
        assert client.post(path,headers=auth(tenant='other'),json=payload).status_code==404
        assert client.post(path,headers=auth(),json=payload|{'base_version':2}).status_code==409
        assert client.post(path,headers=auth(),json=payload|{'domain':'maritime'}).status_code==400
        result=client.post(path,headers=auth(),json=payload)
        assert result.status_code==201,result.text
        records=client.get(f'/v1/decision-models/{identifier}/workspace',headers=auth()).json()['records']
        saved=next(r for r in records if r['id']==result.json()['id'])
        assert saved['inputs']['coordination']['as_of']=='2026-10-03'
        assert saved['analysis']['coordination']['flight_clearance'] is False
