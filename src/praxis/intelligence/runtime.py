from __future__ import annotations
from dataclasses import dataclass, field
from math import prod

class CausalError(ValueError): pass
@dataclass
class CausalDAG:
    edges:list[tuple[str,str,float]]=field(default_factory=list)
    def add(self,a,b,effect=1.0):
        self.edges.append((a,b,float(effect)))
        if self._cycle(): self.edges.pop(); raise CausalError('causal DAG cannot contain cycles')
    def _cycle(self):
        g={}
        for a,b,_ in self.edges:g.setdefault(a,[]).append(b)
        seen=set(); active=set()
        def visit(n):
            if n in active:return True
            if n in seen:return False
            seen.add(n); active.add(n)
            if any(visit(x) for x in g.get(n,[])):return True
            active.remove(n); return False
        return any(visit(n) for n in list(g))
    def intervention_effect(self,source,target,delta):
        total=0.0
        def walk(n,w,visited):
            nonlocal total
            if n==target: total+=w; return
            for a,b,e in self.edges:
                if a==n and b not in visited: walk(b,w*e,visited|{b})
        walk(source,float(delta),{source}); return total

def bayes(prior,likelihood_if_true,likelihood_if_false):
    n=prior*likelihood_if_true; d=n+(1-prior)*likelihood_if_false
    return n/d if d else prior

def evidence_strength(items):
    # items: (direction +/-1, credibility 0..1, relevance 0..1)
    score=sum(d*c*r for d,c,r in items); return max(-1.0,min(1.0,score))

@dataclass
class Hypothesis:
    statement:str; prior:float=.5; status:str='proposed'; falsifiers:list[str]=field(default_factory=list)
    def update(self,lt,lf): self.prior=bayes(self.prior,lt,lf); self.status='supported' if self.prior>=.7 else 'weakened' if self.prior<=.3 else 'under_test'; return self.prior

def ensemble(estimates):
    # [(value, weight)]
    w=sum(x[1] for x in estimates); mean=sum(v*wt for v,wt in estimates)/w
    disagreement=(sum(wt*(v-mean)**2 for v,wt in estimates)/w)**.5
    return {'estimate':mean,'disagreement':disagreement}

def counterfactual(baseline,interventions,dag:CausalDAG,target):
    change=sum(dag.intervention_effect(k,target,v) for k,v in interventions.items())
    return {'baseline':baseline,'counterfactual':baseline+change,'delta':change}

def debate(proposal,criticisms,evidence_notes):
    return {'proposal':proposal,'criticisms':list(criticisms),'evidence_checks':list(evidence_notes),'unresolved':list(dict.fromkeys(criticisms))}

def inquiry(question,evidence,hypotheses,dag=None):
    ranked=sorted(hypotheses,key=lambda h:h.prior,reverse=True)
    return {'question':question,'newton':{'evidence':evidence},'geometer':{'causal_edges':dag.edges if dag else []},'blake':{'hypotheses':[h.statement for h in ranked]},'dewey':{'next_test': ranked[0].falsifiers[0] if ranked and ranked[0].falsifiers else 'collect discriminating evidence'},'conclusion':ranked[0].statement if ranked else None,'confidence':ranked[0].prior if ranked else 0.0,'human_judgment_required':True}
