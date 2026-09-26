from datetime import datetime,timezone,timedelta
import pytest
from praxis.intelligence.runtime import *
from praxis.grounding.runtime import *
from praxis.action.runtime import *
from praxis.institution.runtime import *

def test_causal_dag_and_bayes():
 d=CausalDAG(); d.add('price','demand',-.5); d.add('demand','cash',.8); assert d.intervention_effect('price','cash',10)==-4
 with pytest.raises(CausalError): d.add('cash','price',1)
 assert bayes(.5,.8,.2)==.8

def test_hypothesis_ensemble_counterfactual():
 h=Hypothesis('H',.5,falsifiers=['measure x']); assert h.update(.9,.1)>.8
 e=ensemble([(10,1),(14,1)]); assert e['estimate']==12 and e['disagreement']==2
 d=CausalDAG(); d.add('x','y',2); assert counterfactual(5,{'x':3},d,'y')['counterfactual']==11

def test_grounding_temporal_contradictions_and_graph():
 g=GroundingStore(); s=g.register('filing','finance',.9); now=datetime.now(timezone.utc); d1=g.ingest(s.id,'Revenue = 100',valid_from=now-timedelta(days=2)); c1=g.promote(ClaimCandidate('Revenue = 100',s.id,d1.id,valid_from=now-timedelta(days=2)))
 d2=g.ingest(s.id,'Revenue = 90',valid_from=now); g.promote(ClaimCandidate('Revenue = 90',s.id,d2.id,valid_from=now))
 assert g.retrieve('Revenue') and len(g.contradictions())==1
 assert extract_graph('Company A -> OWNS -> Asset B')[0]['relation']=='OWNS'

def test_adapters():
 assert FinanceAdapter().normalize({'x':1})['domain']=='finance'; assert LegalAdapter().normalize({'x':1})['record']['x']==1

def test_governed_action_approval_budget_idempotency_and_compensation():
 state=[]; rt=ActionRuntime(budget=10); rt.register(Capability('write',lambda x:state.append(x) or x,{'write'},'high',2,lambda v,a:v==a['x']))
 actor=Actor('u',{'manager'},{'write'}); req=ActionRequest('write',{'x':3}); assert rt.execute(actor,req)['status']=='require_approval'; req.approved=True
 assert rt.execute(actor,req)['status']=='succeeded'; assert rt.execute(actor,req)['status']=='succeeded'; assert state==[3]
 bad=ActionRuntime(); undone=[]; bad.register(Capability('bad',lambda :1,set(),'low',0,lambda v,a:False,lambda :undone.append(True)))
 assert bad.execute(Actor('u',set(),set()),ActionRequest('bad',{}))['status']=='compensated'; assert undone

def build_twin():
 t=InstitutionalTwin('Praxis Co'); board=t.add_entity('team','Board'); finance=t.add_entity('team','Finance',board.id); cash=t.add_entity('money','Cash',finance.id,balance=1000); role=t.add_entity('role','CFO',finance.id); t.add_objective('Runway',finance.id,'cash_balance',2000,1); return t,board,finance,cash,role

def test_institution_ownership_agents_views_events():
 t,board,finance,cash,role=build_twin(); a=t.register_agent('Finance Agent','finance',{role.id},{'money','team','role','spend'}); v=t.view_for(a.id); assert any(x['name']=='Cash' for x in v['entities']); before=len(t.events); t.update(cash.id,a.id,{'balance':900}); assert len(t.events)==before+1 and t.entities[cash.id].attributes['balance']==900

def test_institution_simulation_is_non_mutating_and_objective_conflict():
 t,board,finance,cash,role=build_twin(); t.add_objective('Conserve',finance.id,'cash_balance',5000); sim=t.simulate({cash.id:{'balance':-100}}); assert sim['entities'][cash.id]['attributes']['balance']==900; assert t.entities[cash.id].attributes['balance']==1000; assert t.competing_objectives()

def test_multi_agent_governed_coordination():
 t,board,finance,cash,role=build_twin(); a=t.register_agent('Finance Agent','finance',{role.id},{'money','spend'}); rt=ActionRuntime(); rt.register(Capability('spend',lambda amount:{'spent':amount},{'spend'},'low',0)); coord=InstitutionCoordinator(t,rt); p=coord.propose(a.id,'buy data','spend',{'amount':25}); assert p['status']=='proposed'; res=coord.execute(p,Actor('cfo',{'cfo'},{'spend'}),ActionRequest); assert res['status']=='succeeded'; assert t.events[-1].type=='governed_action'

def test_agent_cannot_exceed_authority():
 t,board,finance,cash,role=build_twin(); a=t.register_agent('Finance Agent','finance',{role.id},{'money'}); c=InstitutionCoordinator(t,ActionRuntime()); assert c.propose(a.id,'deploy','cloud.deploy',{})['status']=='outside_authority'

def test_persistent_institution_events_and_snapshot(tmp_path):
 t,board,finance,cash,role=build_twin(); store=SQLiteInstitutionStore(tmp_path/'institution.db')
 for e in t.events: store.append(e)
 sid=store.save_snapshot(t); assert len(store.events())==len(t.events); assert store.load_snapshot(sid)['organization']['name']=='Praxis Co'
