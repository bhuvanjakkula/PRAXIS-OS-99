"""Evidence retrieval and human-directed SRK decision memos; no autonomous execution."""
from math import isclose
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, model_validator
from praxis.grounding.documents import retrieve_documents, tokens
from praxis.grounding.public_search import public_search
from praxis.services.srk_lenses import LENSES
from praxis.services.decision_loop import RevisionConflict


class Inputs(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, allow_inf_nan=False)


class SearchRequest(Inputs):
    query: str = Field(min_length=1, max_length=500)
    scope: Literal['local', 'web', 'both'] = 'local'
    provider: Literal['wikipedia', 'brave'] = 'wikipedia'
    limit: int = Field(default=8, ge=1, le=20)
    jurisdiction: str | None = Field(default=None, max_length=100)
    as_of: AwareDatetime | None = None
    known_at: AwareDatetime | None = None


def search(sources, documents, request):
    local = []
    if request.scope in {'local', 'both'}:
        local = retrieve_documents(sources, documents, request.query, limit=request.limit,
                    jurisdiction=request.jurisdiction, as_of=request.as_of, known_at=request.known_at, ranking='bm25')
        for hit in local:
            hit['citation_id'] = f"doc:{hit['document_id']}:{hit['excerpt_start']}:{hit['excerpt_end']}"
    web = public_search(request.query, request.provider, request.limit) if request.scope in {'web', 'both'} else {
        'status': 'not_requested', 'provider': request.provider, 'hits': [], 'message': 'No external request made.'}
    return {'query': request.query, 'scope': request.scope, 'local': local, 'web': web,
            'limitations': 'Lexical document search and public snippets are research leads, not verified facts. '
                            'Date and jurisdiction filters apply only to local documents. Public results use provider ranking; scores are not combined.'}


class Scenario(Inputs):
    name: str = Field(min_length=1, max_length=100)
    probability: float = Field(ge=0, le=1)
    payoff: float = Field(ge=-1e12, le=1e12)


class Forecast(Inputs):
    option: str = Field(min_length=1, max_length=500)
    scenarios: list[Scenario] = Field(min_length=1, max_length=20)
    constraints: dict[str, Literal['pass','fail','unknown']] = Field(default_factory=dict, max_length=100)
    @model_validator(mode='after')
    def probabilities(self):
        if not isclose(sum(x.probability for x in self.scenarios), 1, abs_tol=1e-8):
            raise ValueError('Scenario probabilities must sum to 1; they are never silently normalized')
        if len({s.name for s in self.scenarios}) != len(self.scenarios):
            raise ValueError('Scenario names must be unique')
        return self


class ResearchRequest(SearchRequest):
    base_version: int = Field(ge=1)
    forecasts: list[Forecast] = Field(default_factory=list, max_length=20)
    payoff_unit: str = Field(default='', max_length=80)
    maximum_loss: float | None = Field(default=None, ge=0, le=1e12)


def research(studio, identifier, request, sources, documents, actor='local-user'):
    revision = studio.loop.latest(identifier)
    if revision.version != request.base_version:
        raise RevisionConflict('Reload the decision before researching this revision')
    decision = revision.decision
    names = [o.name for o in decision.options]
    if request.forecasts:
        if not request.payoff_unit:
            raise ValueError('Supply a common payoff unit for option forecasts')
        if len(set(names)) != len(names) or sorted(f.option for f in request.forecasts) != sorted(names):
            raise ValueError('Provide exactly one forecast for every current option')
        if any(set(f.constraints) != set(decision.constraints) for f in request.forecasts):
            raise ValueError('Explicitly assess every decision constraint for every forecast: pass, fail or unknown')
    # Validate all local inputs before disclosing a query to a public provider.
    results = search(sources, documents, request)
    text = tokens(' '.join([decision.problem, decision.objective, *decision.domains]))
    keywords = {'technology': {'technology','software','system','data','ai','code','latency'},
                'business': {'business','customer','market','revenue','strategy'},
                'finance': {'finance','cash','risk','capital','debt','price'},
                'law': {'law','legal','regulation','compliance','contract'},
                'humanerror': {'human','mistake','bias','team','process','accident'}}
    domains = [name for name, words in keywords.items() if text & words] or ['technology','business','finance','law','humanerror']
    lenses = [{'domain': name, **LENSES[name]} for name in domains]
    cues = []
    lowered = decision.problem.casefold()
    for phrase, question in [('already spent','Would you choose this option without the sunk cost?'),
                             ('everyone agrees','Who has independently challenged the proposal?'),
                             ('guaranteed','What observation would disprove the claimed certainty?')]:
        if phrase in lowered:
            cues.append({'matched_phrase': phrase, 'question': question, 'status': 'language_cue_not_bias_diagnosis'})
    evaluations = []
    for forecast in request.forecasts:
        possible = [s for s in forecast.scenarios if s.probability > 0]
        worst = min(s.payoff for s in possible)
        reasons = [f'Constraint {k}: {v}' for k,v in forecast.constraints.items() if v != 'pass']
        if request.maximum_loss is not None and worst < -request.maximum_loss:
            reasons.append('Supplied scenario loss exceeds the specified limit')
        evaluations.append({'option': forecast.option, 'expected_value': sum(s.probability*s.payoff for s in possible),
                            'worst_supplied_outcome': worst, 'loss_probability': sum(s.probability for s in possible if s.payoff<0),
                            'eligible_under_supplied_inputs': not reasons, 'blocking_reasons': reasons})
    eligible = [row for row in evaluations if row['eligible_under_supplied_inputs']]
    best = max((row['expected_value'] for row in eligible), default=None)
    leaders = [row['option'] for row in eligible if isclose(row['expected_value'], best, abs_tol=1e-8)]
    gaps = list(decision.uncertainties)
    if not results['local'] and not results['web']['hits']:
        gaps.append('No matching sources were retrieved; gather evidence before drawing conclusions.')
    if not request.forecasts:
        gaps.append('Option probabilities, payoffs and constraint assessments were not supplied; no numerical winner is claimed.')
    if results['web']['status'] in {'unavailable','unconfigured'}:
        gaps.append(results['web']['message'])
    memo = {
        'method': 'SRK-inspired first-principles inquiry, source retrieval, scenario evaluation and adversarial review',
        'first_principles': {'problem': decision.problem, 'goal': decision.objective,
                             'constraints_to_verify': decision.constraints, 'assumptions': decision.assumptions,
                             'unknowns': decision.uncertainties, 'stakeholders': [s.name for s in decision.stakeholders]},
        'domain_lenses': lenses, 'language_cues': cues, 'search': results,
        'option_evaluations': evaluations, 'leaders_under_supplied_inputs': leaders,
        'payoff_unit': request.payoff_unit, 'evidence_gaps': gaps,
        'adversarial_questions': ['What evidence contradicts the preferred option?',
                                 'What happens if the largest assumption fails?',
                                 'Which rare losses are absent from the supplied scenarios?',
                                 'Who could be harmed, and who can stop the plan?'],
        'next_steps': ['Verify cited sources and record contradictory evidence.',
                       'Specify a reversible experiment, measurable outcome and stop conditions.',
                       'Compare actual results with predictions and record a new human review.'],
        'alternatives': names or ['Frame multiple options, including waiting for better evidence.'],
        'confidence': None, 'execution_status': 'not_executed',
        'limitations': 'Deterministic decision support adapted from supplied code. No calibrated confidence, optimality, '
                      'bias elimination or loss protection is established. Scenario probabilities and constraint checks '
                      'are human inputs, not verified findings. Sources are not automatically promoted to evidence.'}
    return studio._record(identifier, revision.version, 'research_memo',
                          {'inputs': request.model_dump(mode='json'), 'analysis': memo, 'author': actor})
