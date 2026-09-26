from __future__ import annotations
from dataclasses import dataclass,field,asdict
from datetime import datetime,timezone
from uuid import uuid4
from copy import deepcopy
@dataclass
class InstitutionalEntity:
    id:str; kind:str; name:str; owner_id:str|None=None; attributes:dict=field(default_factory=dict)
@dataclass
class Objective:
    id:str; name:str; owner_id:str; metric:str; target:float; priority:float=1.0
@dataclass(frozen=True)
class InstitutionalEvent:
    id:str; type:str; actor_id:str; entity_id:str|None; payload:dict; at:datetime
@dataclass
class InstitutionalAgent:
    id:str; name:str; specialty:str; role_ids:set[str]; authority:set[str]
class InstitutionalTwin:
    def __init__(self,organization_name):
        self.organization=InstitutionalEntity(str(uuid4()),'organization',organization_name); self.entities={self.organization.id:self.organization}; self.objectives={}; self.events=[]; self.agents={}
    def add_entity(self,kind,name,owner_id=None,**attributes):
        if owner_id and owner_id not in self.entities: raise KeyError('owner not found')
        e=InstitutionalEntity(str(uuid4()),kind,name,owner_id,attributes); self.entities[e.id]=e; self.emit('entity_created','system',e.id,{'kind':kind}); return e
    def add_objective(self,name,owner_id,metric,target,priority=1):
        if owner_id not in self.entities: raise KeyError('objective owner not found')
        o=Objective(str(uuid4()),name,owner_id,metric,float(target),float(priority)); self.objectives[o.id]=o; self.emit('objective_created','system',owner_id,asdict(o)); return o
    def register_agent(self,name,specialty,role_ids,authority):
        if not set(role_ids)<=set(self.entities): raise KeyError('role not found')
        a=InstitutionalAgent(str(uuid4()),name,specialty,set(role_ids),set(authority)); self.agents[a.id]=a; return a
    def view_for(self,agent_id):
        a=self.agents[agent_id]; visible={i:e for i,e in self.entities.items() if e.kind in a.authority or e.id in a.role_ids or e.owner_id in a.role_ids or e.kind=='organization'}
        return {'organization':self.organization.name,'entities':[asdict(x) for x in visible.values()],'objectives':[asdict(o) for o in self.objectives.values() if o.owner_id in visible],'events':[asdict(e) for e in self.events if e.entity_id is None or e.entity_id in visible]}
    def emit(self,type,actor_id,entity_id,payload):
        ev=InstitutionalEvent(str(uuid4()),type,actor_id,entity_id,deepcopy(payload),datetime.now(timezone.utc)); self.events.append(ev); return ev
    def update(self,entity_id,actor_id,changes):
        e=self.entities[entity_id]; before=deepcopy(e.attributes); e.attributes.update(changes); return self.emit('entity_updated',actor_id,entity_id,{'before':before,'after':deepcopy(e.attributes)})
    def snapshot(self): return {'organization':asdict(self.organization),'entities':{k:asdict(v) for k,v in self.entities.items()},'objectives':{k:asdict(v) for k,v in self.objectives.items()},'event_count':len(self.events)}
    def simulate(self,changes):
        snap=deepcopy(self.snapshot())
        for entity_id,delta in changes.items():
            attrs=snap['entities'][entity_id]['attributes']
            for k,v in delta.items(): attrs[k]=attrs.get(k,0)+v if isinstance(v,(int,float)) else v
        return snap
    def competing_objectives(self):
        by_metric={}
        for o in self.objectives.values(): by_metric.setdefault(o.metric,[]).append(o)
        return [v for v in by_metric.values() if len({o.target for o in v})>1]
class InstitutionCoordinator:
    def __init__(self,twin,action_runtime): self.twin=twin; self.actions=action_runtime
    def propose(self,agent_id,goal,capability,args):
        a=self.twin.agents[agent_id]
        if capability not in a.authority: return {'status':'outside_authority','goal':goal}
        return {'status':'proposed','agent_id':agent_id,'goal':goal,'capability':capability,'args':args}
    def execute(self,proposal,actor,request_cls):
        req=request_cls(capability=proposal['capability'],args=proposal['args']); result=self.actions.execute(actor,req); self.twin.emit('governed_action',proposal['agent_id'],None,{'goal':proposal['goal'],'result':result}); return result
import json, sqlite3
class SQLiteInstitutionStore:
    """Durable append-only institutional event store plus named snapshots."""
    def __init__(self,path='praxis_institution.db'):
        self.path=str(path)
        with sqlite3.connect(self.path) as c:
            c.executescript('''CREATE TABLE IF NOT EXISTS institution_events(seq INTEGER PRIMARY KEY AUTOINCREMENT,id TEXT UNIQUE,type TEXT,actor_id TEXT,entity_id TEXT,payload TEXT,at TEXT); CREATE TABLE IF NOT EXISTS institution_snapshots(id TEXT PRIMARY KEY,payload TEXT,created_at TEXT);''')
    def append(self,event:InstitutionalEvent):
        with sqlite3.connect(self.path) as c:c.execute('INSERT INTO institution_events(id,type,actor_id,entity_id,payload,at) VALUES(?,?,?,?,?,?)',(event.id,event.type,event.actor_id,event.entity_id,json.dumps(event.payload,default=str),event.at.isoformat()))
        return event
    def events(self):
        with sqlite3.connect(self.path) as c: rows=c.execute('SELECT id,type,actor_id,entity_id,payload,at FROM institution_events ORDER BY seq').fetchall()
        return [InstitutionalEvent(r[0],r[1],r[2],r[3],json.loads(r[4]),datetime.fromisoformat(r[5])) for r in rows]
    def save_snapshot(self,twin:InstitutionalTwin):
        sid=str(uuid4()); payload=twin.snapshot()
        with sqlite3.connect(self.path) as c:c.execute('INSERT INTO institution_snapshots VALUES(?,?,?)',(sid,json.dumps(payload,default=str),datetime.now(timezone.utc).isoformat()))
        return sid
    def load_snapshot(self,sid):
        with sqlite3.connect(self.path) as c:r=c.execute('SELECT payload FROM institution_snapshots WHERE id=?',(sid,)).fetchone()
        return json.loads(r[0]) if r else None
