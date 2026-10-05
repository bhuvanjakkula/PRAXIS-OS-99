from praxis.core.models import Decision, InquiryReport
from praxis.engines.foundational import NewtonEngine, GeometerEngine, BlakeEngine, DeweyEngine
from praxis.domains.engines import DOMAIN_ENGINES

class PraxisOrchestrator:
    def __init__(self):
        self.foundation=[NewtonEngine(),GeometerEngine(),BlakeEngine(),DeweyEngine()]

    def inquire(self,d:Decision)->InquiryReport:
        domains=list(dict.fromkeys(d.domains))
        domain_inputs=[DOMAIN_ENGINES[x].analyze(d) for x in domains
                       if x in {"business", "finance", "technology", "law"}]
        human_inputs=[DOMAIN_ENGINES[x].analyze(d) for x in domains if x in {"human", "society"}]
        human_inputs.append(BlakeEngine().analyze(d))
        geometer=GeometerEngine().synthesize(d, [*domain_inputs, *human_inputs])
        insights=[NewtonEngine().analyze(d), *domain_inputs, *human_inputs,
                  geometer, DeweyEngine().analyze(d)]
        assumptions=[e.statement for e in d.evidence if e.kind.value=="assumption"]
        hypotheses=[f"Test whether: {x}" for x in assumptions] or ["Form at least one falsifiable causal hypothesis."]
        experiments=["Choose a reversible, bounded experiment targeting the highest-impact uncertainty.",
                     "Define expected observation, failure threshold and learning criterion before acting."]
        uncertainties=[q for i in insights for q in i.questions][:10]
        actions=["Strengthen weak evidence.","Map cross-domain dependencies.","Run a bounded experiment.","Compare predicted vs actual consequences and reconstruct the model."]
        return InquiryReport(decision_id=d.id,
            framing=[d.problem, f"Objective: {d.objective}", "Separate facts, assumptions, values and predictions."],
            insights=insights,hypotheses=hypotheses,experiments=experiments,uncertainties=uncertainties,next_actions=actions)
