from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from uuid import uuid4
@dataclass(frozen=True)
class Source:
    id:str; name:str; domain:str; credibility:float=.5
@dataclass(frozen=True)
class DocumentVersion:
    id:str; source_id:str; content:str; checksum:str; valid_from:datetime|None; valid_to:datetime|None; observed_at:datetime; ingested_at:datetime
@dataclass
class ClaimCandidate:
    statement:str; source_id:str; document_id:str; valid_from:datetime|None=None; valid_to:datetime|None=None; confidence:float=.5
class GroundingStore:
    def __init__(self): self.sources={}; self.documents=[]; self.claims=[]
    def register(self,name,domain,credibility=.5):
        s=Source(str(uuid4()),name,domain,credibility); self.sources[s.id]=s; return s
    def ingest(self,source_id,content,valid_from=None,valid_to=None,observed_at=None):
        now=datetime.now(timezone.utc); d=DocumentVersion(str(uuid4()),source_id,content,sha256(content.encode()).hexdigest(),valid_from,valid_to,observed_at or now,now); self.documents.append(d); return d
    def promote(self,claim): self.claims.append(claim); return claim
    def as_of(self,when): return [c for c in self.claims if (c.valid_from is None or c.valid_from<=when) and (c.valid_to is None or when<c.valid_to)]
    def retrieve(self,query,when=None):
        q=query.lower(); claims=self.as_of(when) if when else self.claims
        return [{'claim':c.statement,'source':self.sources[c.source_id].name,'credibility':self.sources[c.source_id].credibility,'document_id':c.document_id} for c in claims if any(t in c.statement.lower() for t in q.split())]
    def contradictions(self):
        # explicit semantic-lite contradiction: same subject before '=' with differing values
        groups={}
        for c in self.claims:
            if '=' in c.statement: groups.setdefault(c.statement.split('=',1)[0].strip().lower(),[]).append(c)
        return [v for v in groups.values() if len({x.statement for x in v})>1]

def extract_graph(text):
    # deterministic compact convention: "A -> REL -> B"
    out=[]
    for line in text.splitlines():
        p=[x.strip() for x in line.split('->')]
        if len(p)==3: out.append({'source':p[0],'relation':p[1],'target':p[2]})
    return out
class Adapter:
    domain='generic'
    def normalize(self,record): return {'domain':self.domain,'record':dict(record)}
class BusinessAdapter(Adapter): domain='business'
class FinanceAdapter(Adapter): domain='finance'
class TechnologyAdapter(Adapter): domain='technology'
class LegalAdapter(Adapter): domain='legal'
