from praxis.core.models import Decision, InquiryReport
from praxis.engines.foundational import NewtonEngine, GeometerEngine, BlakeEngine, DeweyEngine
from praxis.domains.engines import DOMAIN_ENGINES

class PraxisOrchestrator:
    def __init__(self):
        self.foundation=[NewtonEngine(),GeometerEngine(),BlakeEngine(),DeweyEngine()]

    def inquire(self,d:Decision)->InquiryReport:
        domain_engines=[DOMAIN_ENGINES[x] for x in d.domains if x in DOMAIN_ENGINES]
        insights=[e.analyze(d) for e in [*self.foundation,*domain_engines]]
        assumptions=[e.statement for e in d.evidence if e.kind.value=="assumption"]
        hypotheses=[f"Test whether: {x}" for x in assumptions] or ["Form at least one falsifiable causal hypothesis."]
        experiments=["Choose a reversible, bounded experiment targeting the highest-impact uncertainty.",
                     "Define expected observation, failure threshold and learning criterion before acting."]
        uncertainties=[q for i in insights for q in i.questions][:10]
        actions=["Strengthen weak evidence.","Map cross-domain dependencies.","Run a bounded experiment.","Compare predicted vs actual consequences and reconstruct the model."]
        return InquiryReport(decision_id=d.id,
            framing=[d.problem, f"Objective: {d.objective}", "Separate facts, assumptions, values and predictions."],
            insights=insights,hypotheses=hypotheses,experiments=experiments,uncertainties=uncertainties,next_actions=actions)
