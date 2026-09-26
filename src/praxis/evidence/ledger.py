from uuid import UUID
from praxis.core.ledger_models import Claim, EvidenceStatus
from praxis.infra.sqlite import SQLiteStore
class EvidenceLedger:
    def __init__(self,store:SQLiteStore): self.store=store
    def record(self,claim:Claim): return self.store.add_claim(claim)
    def claims(self,decision_id:UUID): return self.store.list_claims(decision_id)
    def verify(self,claim_id:UUID,note:str=""): return self.store.transition_claim(claim_id,EvidenceStatus.SUPPORTED,note)
    def dispute(self,claim_id:UUID,note:str=""): return self.store.transition_claim(claim_id,EvidenceStatus.DISPUTED,note)
    def refute(self,claim_id:UUID,note:str=""): return self.store.transition_claim(claim_id,EvidenceStatus.REFUTED,note)
    def history(self,claim_id:UUID): return self.store.history(claim_id)
