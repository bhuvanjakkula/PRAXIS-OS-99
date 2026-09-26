from praxis.core.models import Decision, Evidence, EpistemicType
from praxis.services.orchestrator import PraxisOrchestrator

def test_cross_domain_inquiry():
    d=Decision(title="AI launch",problem="Should we launch an AI lending pilot?",objective="Learn demand safely",domains=["business","finance","technology","law","human","society"],evidence=[Evidence(statement="Customers will pay",kind=EpistemicType.ASSUMPTION)])
    r=PraxisOrchestrator().inquire(d)
    names={x.engine for x in r.insights}
    assert {"newton","geometer","blake","dewey","business","finance","technology","law","human","society"} <= names
    assert r.experiments
