from praxis.core.models import Decision, Insight, EpistemicType

class NewtonEngine:
    name="newton"
    def analyze(self, d: Decision) -> Insight:
        facts=[e.statement for e in d.evidence if e.kind==EpistemicType.FACT]
        assumptions=[e.statement for e in d.evidence if e.kind==EpistemicType.ASSUMPTION]
        return Insight(engine=self.name,
            findings=[f"Verified/declared facts: {len(facts)}", f"Explicit assumptions: {len(assumptions)}"],
            questions=["Which claims need stronger evidence?", "Which variables can be measured before acting?"],
            risks=[] if facts else ["Decision currently has no explicit factual evidence."])

class GeometerEngine:
    name="geometer"
    def analyze(self, d: Decision) -> Insight:
        return Insight(engine=self.name,
            findings=[f"Domains connected: {', '.join(d.domains) or 'not yet mapped'}",
                      f"Constraints identified: {len(d.constraints)}"],
            questions=["What causes what?", "Where are the bottlenecks, feedback loops and boundary conditions?"],
            risks=["Hidden dependency risk: map cross-domain effects before irreversible action."])

class BlakeEngine:
    name="blake"
    def analyze(self, d: Decision) -> Insight:
        return Insight(engine=self.name,
            findings=[f"Human values declared: {', '.join(d.values) or 'none yet'}"],
            questions=["What possibility is excluded by the current framing?",
                       "What would stakeholders experience even if the metrics improve?"],
            risks=["Optimization may erase qualitative human consequences."])

class DeweyEngine:
    name="dewey"
    def analyze(self, d: Decision) -> Insight:
        return Insight(engine=self.name,
            findings=["Treat conclusions as hypotheses until consequences are observed."],
            questions=["What is the smallest safe experiment that resolves the largest uncertainty?",
                       "What observation would make us reconstruct the current model?"],
            risks=["Large irreversible commitments before learning can destroy option value."])
