"""Explainable review signals and human-supplied option tradeoffs."""
from datetime import datetime, timezone
from math import isclose
from uuid import UUID
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict, Field, model_validator
from praxis.services.decision_loop import RevisionConflict


class Criterion(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False, str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=80)
    weight: float = Field(gt=0, le=100)


class OptionScores(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False, str_strip_whitespace=True)
    option: str = Field(min_length=1, max_length=500)
    scores: dict[str, float] = Field(min_length=1, max_length=10)
    rationale: str = Field(min_length=1, max_length=4000)

    @model_validator(mode='after')
    def bounded(self):
        if any(not 0 <= value <= 10 for value in self.scores.values()):
            raise ValueError('Scores must be between 0 and 10; higher always means more desirable')
        return self


class ComparisonRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    base_version: int = Field(ge=1)
    criteria: list[Criterion] = Field(min_length=1, max_length=10)
    options: list[OptionScores] = Field(min_length=2, max_length=20)

    @model_validator(mode='after')
    def complete_matrix(self):
        criteria = [item.name for item in self.criteria]
        options = [item.option for item in self.options]
        if len({name.casefold() for name in criteria}) != len(criteria):
            raise ValueError('Criterion names must be unique')
        if len(set(options)) != len(options):
            raise ValueError('Option names must be unique')
        if any(set(option.scores) != set(criteria) for option in self.options):
            raise ValueError('Every option must score every criterion exactly once')
        return self


def evaluate(request):
    weights = {item.name:item.weight for item in request.criteria}
    def totals(current):
        total = sum(current.values())
        return {option.option:sum(option.scores[key]*weight/total for key,weight in current.items())
                for option in request.options}
    def leaders(scores):
        best = max(scores.values())
        return sorted(name for name,score in scores.items() if isclose(score,best,rel_tol=0,abs_tol=1e-9))
    base = totals(weights)
    scenarios = []
    for criterion in weights:
        for factor in (.8, 1.2):
            altered = {**weights, criterion:weights[criterion]*factor}
            scenarios.append({'criterion':criterion, 'weight_change_percent':round((factor-1)*100),
                              'leaders':leaders(totals(altered))})
    ranking = []
    for option in request.options:
        dominated = [other.option for other in request.options
                     if all(other.scores[key] >= option.scores[key] for key in weights)
                     and any(other.scores[key] > option.scores[key] for key in weights)]
        ranking.append({'option':option.option, 'score':round(base[option.option],6),
                        'rank':1+sum(score>base[option.option]+1e-9 for score in base.values()),
                        'dominated_by':dominated})
    return {'ranking':sorted(ranking,key=lambda row:(row['rank'],row['option'])),
            'normalized_weights':{key:value/sum(weights.values()) for key,value in weights.items()},
            'leaders':leaders(base), 'sensitivity':scenarios,
            'leader_changes':sum(row['leaders']!=leaders(base) for row in scenarios),
            'method':'Weighted mean of user-supplied desirability scores (0–10). Each weight is varied ±20% separately and weights are renormalized.',
            'limitations':'Subjective inputs, not probabilities or verified facts. Weight checks do not test all combinations or enforce constraints. Human judgment remains required.',
            'execution_status':'not_executed'}


def comparison(studio, decision_id: UUID, request: ComparisonRequest, *, save=False, actor='local-user'):
    revision = studio.loop.latest(decision_id)
    if revision.version != request.base_version:
        raise RevisionConflict('The decision changed; reload before comparing options')
    names = [option.name for option in revision.decision.options]
    if len(names)!=len(set(names)) or set(names)!={item.option for item in request.options}:
        raise ValueError('Compare every current decision option exactly once; option names must be unique')
    result = {'inputs':request.model_dump(mode='json'), 'analysis':evaluate(request), 'author':actor}
    if save:
        return studio._record(decision_id,revision.version,'option_comparison',result)
    return {'decision_id':str(decision_id), 'version':revision.version, **result}


def review_radar(revisions, claims, records, impacts):
    rows = []
    for revision in revisions:
        identifier = str(revision['decision_id']); version = revision['version']; decision = revision['decision']
        evidence = [claim for claim in claims if str(claim['decision_id'])==identifier]
        judgments = [record for record in records if str(record['decision_id'])==identifier and record['kind']=='judgment']
        pending = [impact for impact in impacts if str(impact['decision_id'])==identifier and impact['status']=='review_required']
        flags = []
        def flag(code, count, message, urgency='gap'):
            if count: flags.append({'code':code,'count':count,'message':message,'urgency':urgency})
        flag('source_changes',len(pending),'Review imported source changes','review')
        flag('challenged_claims',sum(c['status'] in {'disputed','refuted','stale'} for c in evidence),'Revisit disputed, refuted or stale claims','review')
        flag('unverified_claims',sum(c['status']=='unverified' for c in evidence),'Verify ledger claims')
        flag('missing_evidence',not evidence and not decision.get('evidence'),'Add evidence and its provenance')
        flag('few_options',len(decision.get('options',[]))<2,'Frame at least two alternatives')
        flag('missing_stakeholders',not decision.get('stakeholders'),'Identify affected stakeholders')
        flag('missing_judgment',not any(record['version']==version for record in judgments),
             'Review the current revision; older judgments do not apply' if judgments else 'Record human judgment for this revision')
        rows.append({'decision_id':identifier,'title':decision['title'],'version':version,'flags':flags,
                     'attention':'review' if any(f['urgency']=='review' for f in flags) else 'gaps' if flags else 'no_flags',
                     'flag_count':len(flags)})
    rows.sort(key=lambda row:({'review':0,'gaps':1,'no_flags':2}[row['attention']],-row['flag_count'],row['title']))
    return {'decisions':rows,'total':len(rows),'needs_review':sum(row['attention']=='review' for row in rows),
            'with_gaps':sum(row['attention']=='gaps' for row in rows),
            'note':'Rule-based review prompts from stored records. No flags does not establish readiness, safety or correctness.'}


def decision_brief(studio, decision_id, impacts):
    workspace = jsonable_encoder(studio.workspace(decision_id))
    version = workspace['revision']['version']
    return {'format':'praxis.decision-brief.v1','generated_at':datetime.now(timezone.utc).isoformat(),
            'decision_id':str(decision_id),'decision_version':version,
            'revision':workspace['revision'],'claims':workspace['claims'],'review':workspace['review'],
            'human_control':workspace['human_control'],
            'conflicts':workspace['conflicts'],
            'records':[{**record,'applies_to_current_revision':record['version']==version} for record in workspace['records']],
            'source_impacts':[impact for impact in impacts if impact['decision_id']==str(decision_id)],
            'notice':'Contains user-supplied workspace information; review before sharing. Historical analyses and judgments apply only to their recorded revision. No external action is authorized.'}
