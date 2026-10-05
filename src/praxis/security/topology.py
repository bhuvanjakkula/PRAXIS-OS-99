"""Deterministic capacity-aware failover planning; no network execution."""
from collections import deque
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, model_validator

Name=Annotated[str,Field(min_length=1,max_length=200)]

class Link(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True,allow_inf_nan=False)
    source:Name
    target:Name
    capacity:float=Field(gt=0,le=1e12)
    load:float=Field(default=0,ge=0,le=1e12)

    @model_validator(mode='after')
    def consistent(self):
        if self.source==self.target or self.load>self.capacity:
            raise ValueError('Links must connect distinct nodes and fit capacity')
        return self

class Demand(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True,allow_inf_nan=False)
    id:Name
    source:Name
    target:Name
    amount:float=Field(gt=0,le=1e12)

def plan_failover(nodes,links,demands,isolated=()):
    """Directed links, greedy admission in caller priority order, private snapshot.

    Existing load stays reserved. Demands must be additional or previously removed
    traffic, so callers never double-count rerouted loads. No splitting/preemption.
    """
    if len(nodes)>1000 or len(links)>10000 or len(demands)>1000:
        raise ValueError('Topology exceeds prototype planning limits')
    if any(not isinstance(n,str) or not n or len(n)>200 for n in nodes) or len(set(nodes))!=len(nodes):
        raise ValueError('Unique bounded node identifiers required')
    nodes=set(nodes);blocked=set(isolated)
    if not blocked<=nodes:raise ValueError('Unknown isolated node')
    links=[Link.model_validate(x.model_dump() if isinstance(x,Link) else x) for x in links]
    demands=[Demand.model_validate(x.model_dump() if isinstance(x,Demand) else x) for x in demands]
    if len({d.id for d in demands})!=len(demands):raise ValueError('Duplicate demand identifier')
    residual={};adj={n:[] for n in nodes};pruned=[]
    for edge in links:
        key=(edge.source,edge.target)
        if edge.source not in nodes or edge.target not in nodes:raise ValueError('Unknown link endpoint')
        if key in residual:raise ValueError('Duplicate directed link')
        residual[key]=edge.capacity-edge.load
        if edge.source in blocked or edge.target in blocked:pruned.append(key)
        else:adj[edge.source].append(edge.target)
    results=[]
    for demand in demands:
        if demand.source not in nodes or demand.target not in nodes:raise ValueError('Unknown demand endpoint')
        if demand.source==demand.target:raise ValueError('Demand endpoints must differ')
        path=None
        if demand.source not in blocked and demand.target not in blocked:
            queue=deque([demand.source]);parent={demand.source:None}
            while queue:
                current=queue.popleft()
                if current==demand.target:
                    path=[]
                    while current is not None:path.append(current);current=parent[current]
                    path.reverse();break
                for neighbor in sorted(adj[current]):
                    if neighbor not in parent and residual[(current,neighbor)]>=demand.amount:
                        parent[neighbor]=current;queue.append(neighbor)
        if path:
            for a,b in zip(path,path[1:]):residual[(a,b)]-=demand.amount
        results.append(dict(id=demand.id,admitted=bool(path),path=path or [],amount=demand.amount,
                            reason='capacity_reserved' if path else 'no_safe_capacity_path'))
    return dict(demands=results,pruned_edges=[list(x) for x in sorted(pruned)],
        remaining_capacity=[dict(source=a,target=b,available=value) for (a,b),value in sorted(residual.items())
                            if a not in blocked and b not in blocked],
        isolated_nodes=sorted(blocked),execution_authorized=False,transport_changed=False)
