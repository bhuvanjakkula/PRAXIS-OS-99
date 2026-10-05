"""Descriptive collaboration structure; no causal innovation or employee scores."""
from collections import deque
from datetime import date
from typing import Literal
from pydantic import Field, model_validator
from praxis.services.research import Inputs
from praxis.services.cross_functional import IntegrationReview, analyze_integration


class NetworkUnit(Inputs):
    name: str = Field(min_length=1,max_length=100)
    function: str = Field(min_length=1,max_length=100)
    kind: Literal['internal','external']


class KnowledgeLink(Inputs):
    source: str = Field(min_length=1,max_length=100)
    target: str = Field(min_length=1,max_length=100)
    status: Literal['observed','proposed']
    recorded_on: date
    evidence: str = Field(default='',max_length=2000)
    owner: str = Field(default='',max_length=200)
    outcome: str = Field(default='',max_length=2000)


class InnovationNetwork(Inputs):
    integration: IntegrationReview | None = None
    as_of: date
    max_age_days: int = Field(ge=0,le=3650)
    units: list[NetworkUnit] = Field(min_length=2,max_length=40)
    links: list[KnowledgeLink] = Field(default_factory=list,max_length=200)
    scope: str = Field(min_length=1,max_length=2000)

    @model_validator(mode='after')
    def consistent(self):
        if self.integration and self.integration.as_of!=self.as_of:raise ValueError('Network and integration dates must match')
        names={u.name for u in self.units}
        if len({u.name.casefold() for u in self.units})!=len(self.units):raise ValueError('Use distinct team and partner names')
        pairs=set()
        for link in self.links:
            if link.source not in names or link.target not in names:raise ValueError('Links must name supplied units exactly')
            if link.source==link.target:raise ValueError('Self-links are not supported')
            pair=frozenset((link.source,link.target))
            if pair in pairs:raise ValueError('List each undirected relationship once')
            pairs.add(pair)
            if link.recorded_on>self.as_of:raise ValueError('Evidence dates cannot be after the snapshot date')
        return self


def components(adj):
    unseen=set(adj);result=[]
    while unseen:
        stack=[min(unseen)];part=set()
        while stack:
            node=stack.pop()
            if node in part:continue
            part.add(node);unseen.discard(node);stack.extend(adj[node]-part)
        result.append(sorted(part))
    return result


def network_metrics(units,links):
    adj={u.name:set() for u in units};n=len(adj)
    for link in links:adj[link.source].add(link.target);adj[link.target].add(link.source)
    groups=components(adj);between={v:0.0 for v in adj}
    # Brandes' unweighted shortest-path accumulation, normalized over all units.
    for source in adj:
        stack=[];parents={v:[] for v in adj};paths={v:0 for v in adj};paths[source]=1
        distance={v:-1 for v in adj};distance[source]=0;queue=deque([source])
        while queue:
            v=queue.popleft();stack.append(v)
            for w in sorted(adj[v]):
                if distance[w]<0:queue.append(w);distance[w]=distance[v]+1
                if distance[w]==distance[v]+1:paths[w]+=paths[v];parents[w].append(v)
        dependency={v:0.0 for v in adj}
        while stack:
            w=stack.pop()
            for v in parents[w]:dependency[v]+=paths[v]/paths[w]*(1+dependency[w])
            if w!=source:between[w]+=dependency[w]
    rows=[]
    for unit in units:
        name=unit.name;neighbors=adj[name];degree=len(neighbors)
        removed={v:neighbors-{name} for v,neighbors in adj.items() if v!=name}
        baseline=sum((len(g)-(name in g))*(len(g)-(name in g)-1)//2 for g in groups)
        remaining=sum(len(g)*(len(g)-1)//2 for g in components(removed))
        triangles=sum(w in adj[v] for v in neighbors for w in neighbors if v!=w)//2
        rows.append(dict(name=name,function=unit.function,kind=unit.kind,degree=degree,
                         degree_centrality=degree/(n-1),betweenness=between[name]/((n-1)*(n-2)) if n>2 else 0,
                         clustering=2*triangles/(degree*(degree-1)) if degree>1 else 0,
                         newly_disconnected_pairs_if_removed=baseline-remaining))
    return dict(unit_count=n,link_count=len(links),component_count=len(groups),components=groups,
                density=2*len(links)/(n*(n-1)),units=rows,
                cross_function_links=sum(a.function.casefold()!=b.function.casefold() for link in links
                                         for a in units if a.name==link.source for b in units if b.name==link.target),
                internal_external_links=sum(a.kind!=b.kind for link in links
                                            for a in units if a.name==link.source for b in units if b.name==link.target))


def analyze_network(p):
    observed=[];proposed=[];excluded=[];actions=[]
    for link in p.links:
        label=link.source+' ↔ '+link.target
        if link.status=='proposed':
            proposed.append(link)
            actions.append(dict(subject=label,reason='Hypothetical connection',owner=link.owner or None,
                                action='Review partner consent, information-sharing permissions, available time and the learning outcome before testing this connection.'))
        elif not link.evidence or (p.as_of-link.recorded_on).days>p.max_age_days:
            excluded.append(dict(link=label,reason='Missing evidence' if not link.evidence else 'Evidence exceeds supplied age limit'))
        else:observed.append(link)
        if not link.owner or not link.outcome:
            actions.append(dict(subject=label,reason='Missing handoff owner or measurable learning outcome',owner=link.owner or None,
                                action='Assign an integration owner and define how shared knowledge will be translated into a testable product or process change.'))
    current=network_metrics(p.units,observed)
    hypothetical=network_metrics(p.units,observed+proposed) if proposed else None
    for unit in current['units']:
        if unit['degree']==0:
            actions.append(dict(subject=unit['name'],reason='No current evidenced connection in supplied scope',owner=None,
                                action='Confirm whether connections are missing from the records; if isolation is real, propose a relevant cross-functional learning session.'))
        if unit['newly_disconnected_pairs_if_removed']:
            actions.append(dict(subject=unit['name'],reason=f"Removing this unit disconnects {unit['newly_disconnected_pairs_if_removed']} additional pairs of remaining units",
                                owner=None,action='Review handoff coverage, documented knowledge and alternate collaboration paths; do not equate brokerage with spare capacity.'))
    return dict(integration=analyze_integration(p.integration) if p.integration else None,
                current=current,with_proposals=hypothetical,actions=actions,excluded_links=excluded,
                observed_links=[r.model_dump(mode='json') for r in observed],proposed_links=[r.model_dump(mode='json') for r in proposed],
                snapshot=p.as_of.isoformat(),scope=p.scope,
                method='Simple undirected, unweighted graph of supplied teams and partners. Current links require evidence within the supplied age limit. Degree centrality divides degree by N−1. Betweenness is the normalized share of shortest paths through a unit, excluding endpoints, using all N units. Clustering measures links between neighbors; it is zero for degree below two. Removal counts only newly disconnected pairs among remaining units. Proposals are included only in a separate hypothetical graph.',
                limitations='Descriptive structure within the recorded scope, not verified collaboration quality, trust, executive authority, absorptive capacity, individual influence or innovation performance. Missing links can change every measure. More centrality or density is not inherently better. No optimal network, causal effect, patent increase or financial return is inferred. Proposed links are unverified assumptions, not approved partnerships; no outreach or organizational change is executed.')
