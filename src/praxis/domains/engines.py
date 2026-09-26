from praxis.core.models import Decision, Insight

class BusinessEngine:
    name="business"
    def analyze(self,d): return Insight(engine=self.name, findings=["Model customer, value proposition, pricing, distribution, competition and unit economics."], questions=["Where is value created, captured or lost?"], risks=["Demand and competitive-response assumptions may dominate the outcome."])
class FinanceEngine:
    name="finance"
    def analyze(self,d): return Insight(engine=self.name, findings=["Model cash flow, capital needs, downside, liquidity and scenario sensitivity."], questions=["What can cause permanent capital loss?"], risks=["Narrative confidence must not substitute for cash-flow evidence."])
class TechnologyEngine:
    name="technology"
    def analyze(self,d): return Insight(engine=self.name, findings=["Map architecture, data, security, reliability, dependencies, cost and technical debt."], questions=["What is the cheapest architecture that tests the critical assumption?"], risks=["Complexity can be committed before product uncertainty is resolved."])
class LawEngine:
    name="law"
    def analyze(self,d): return Insight(engine=self.name, findings=["Map jurisdiction, authority, obligations, evidence, rights, duties and remedies."], questions=["Which conclusions require current authoritative sources or professional review?"], risks=["Legal conclusions can become stale or jurisdictionally invalid; preserve provenance and effective dates."])
class HumanEngine:
    name="human"
    def analyze(self,d): return Insight(engine=self.name, findings=["Map incentives, trust, autonomy, behavior, dignity, culture and stakeholder experience."], questions=["Who bears costs that the primary metric does not capture?"], risks=["Locally optimal decisions can create human resistance and second-order harm."])
class SocietyEngine:
    name="society"
    def analyze(self,d): return Insight(engine=self.name, findings=["Map institutions, externalities, distributional effects, norms and long-run feedback."], questions=["What happens if this behavior scales across society?"], risks=["Private benefit may create public externalities."])

DOMAIN_ENGINES={e.name:e for e in [BusinessEngine(),FinanceEngine(),TechnologyEngine(),LawEngine(),HumanEngine(),SocietyEngine()]}
