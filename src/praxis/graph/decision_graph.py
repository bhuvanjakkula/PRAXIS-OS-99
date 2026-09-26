from collections import defaultdict, deque
from uuid import UUID
from praxis.core.graph_models import GraphNode,GraphEdge,ImpactPath
from praxis.infra.sqlite import SQLiteStore
class DecisionGraph:
    def __init__(self,store:SQLiteStore): self.store=store
    def add_node(self,node:GraphNode): return self.store.add_node(node)
    def connect(self,edge:GraphEdge): return self.store.add_edge(edge)
    def snapshot(self,decision_id:UUID): return {"nodes":self.store.list_nodes(decision_id),"edges":self.store.list_edges(decision_id)}
    def impact_paths(self,decision_id:UUID,start_id:UUID,max_depth:int=4)->list[ImpactPath]:
        edges=self.store.list_edges(decision_id); adj=defaultdict(list)
        for e in edges: adj[e.source_id].append(e)
        out=[]; q=deque([(start_id,[start_id],[],1.0)])
        while q:
            current,nodes,rels,weight=q.popleft()
            if len(rels)>=max_depth: continue
            for e in adj[current]:
                if e.target_id in nodes: continue
                nn=nodes+[e.target_id]; nr=rels+[e.relation]; nw=weight*e.weight
                out.append(ImpactPath(node_ids=nn,relations=nr,cumulative_weight=nw)); q.append((e.target_id,nn,nr,nw))
        return out
