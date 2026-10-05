"""Reproducible multi-criteria decision analysis under supplied uncertainty."""
from math import isclose, sqrt
from random import Random
from statistics import mean, stdev
from hashlib import sha256
import json
from typing import Literal
from datetime import date
from pydantic import Field, model_validator
from praxis.services.research import Inputs
from praxis.services.decision_loop import RevisionConflict


class Weight(Inputs):
    name: str = Field(min_length=1,max_length=80)
    weight: float = Field(gt=0,le=100)


class ScoreRange(Inputs):
    low: float = Field(ge=0,le=10)
    likely: float = Field(ge=0,le=10)
    high: float = Field(ge=0,le=10)
    @model_validator(mode='after')
    def ordered(self):
        if not self.low<=self.likely<=self.high:raise ValueError('Require low ≤ likely ≤ high')
        return self


class ComputeOption(Inputs):
    option: str = Field(min_length=1,max_length=500)
    scores: dict[str,ScoreRange] = Field(min_length=1,max_length=10)
    constraint_checks: dict[str,Literal['pass','fail','unknown']] = Field(default_factory=dict,max_length=100)
    source: str = Field(min_length=1,max_length=2000)
    evidence_date: date | None = None
    evidence_status: Literal['assumption','measured','reviewed'] = 'assumption'


class ComputeRequest(Inputs):
    base_version: int = Field(ge=1)
    criteria: list[Weight] = Field(min_length=1,max_length=10)
    options: list[ComputeOption] = Field(min_length=2,max_length=20)
    weight_uncertainty: float = Field(default=.2,ge=0,le=.9)
    samples: int = Field(default=2000,ge=200,le=50000)
    seed: int = Field(default=42,ge=0,le=2147483647)
    dependence: Literal['independent','shared_shock'] = 'independent'
    scenario: Literal['normal','adverse','severe','custom'] = 'normal'
    scenario_note: str = Field(default='',max_length=2000)
    @model_validator(mode='after')
    def complete(self):
        names=[c.name for c in self.criteria]
        if len({n.casefold() for n in names})!=len(names):raise ValueError('Use distinct criteria')
        if len({o.option for o in self.options})!=len(self.options):raise ValueError('Use distinct options')
        if any(set(o.scores)!=set(names) for o in self.options):raise ValueError('Every option must supply every criterion range')
        if self.samples*len(self.options)*(len(names)+len(self.options))>10000000:
            raise ValueError('Simulation workload exceeds the local budget; reduce samples, criteria or options')
        return self


def triangular_quantile(score,u):
    if score.low==score.high:return score.low
    span=score.high-score.low; split=(score.likely-score.low)/span
    return (score.low+sqrt(u*span*(score.likely-score.low)) if u<=split else
            score.high-sqrt((1-u)*span*(score.high-score.likely)))


def quantile(ordered,p):
    index=(len(ordered)-1)*p;i=int(index)
    return ordered[i]+(ordered[min(i+1,len(ordered)-1)]-ordered[i])*(index-i)


def interval_extreme(values, weights, uncertainty, maximize=False):
    """Exact normalized weighted extreme in O(n log n), with a witness.

    The derivative's sign is values[k] minus the current weighted mean.
    Thus an optimum puts high weights on one side of a sorted threshold
    and low weights on the other. Evaluate all n+1 thresholds.
    """
    ordered=sorted(values,key=values.get,reverse=maximize)
    witness={k:weights[k]*(1-uncertainty) for k in values}
    numerator=sum(witness[k]*values[k] for k in values)
    denominator=sum(witness.values())
    best=numerator/denominator;best_weights=dict(witness)
    for k in ordered:
        delta=2*uncertainty*weights[k]
        witness[k]+=delta;numerator+=delta*values[k];denominator+=delta
        candidate=numerator/denominator
        if (candidate>best if maximize else candidate<best):
            best=candidate;best_weights=dict(witness)
    return {'score':best,'weights':best_weights}


def interval_analysis(eligible,weights,uncertainty):
    rows=[];margins={}
    for option in eligible:
        lower=interval_extreme({k:option.scores[k].low for k in weights},weights,uncertainty)
        upper=interval_extreme({k:option.scores[k].high for k in weights},weights,uncertainty,True)
        comparisons={other.option:interval_extreme(
            {k:option.scores[k].low-other.scores[k].high for k in weights},weights,uncertainty)
            for other in eligible if other.option!=option.option}
        margins[option.option]=comparisons
        worst=max([0.0]+[-result['score'] for result in comparisons.values()])
        rows.append({'option':option.option,'lower_bound':lower,'upper_bound':upper,
                     'worst_case_regret':worst})
    best=min((r['worst_case_regret'] for r in rows),default=None)
    return {'options':rows,'worst_pairwise_margins':margins,
            'minimax_regret_leaders':[r['option'] for r in rows if isclose(r['worst_case_regret'],best,abs_tol=1e-9,rel_tol=0)],
            'range_stable_leaders':[n for n,results in margins.items() if len(eligible)>1 and all(r['score']>=-1e-9 for r in results.values())],
            'method':'Exact bounds over independent supplied score and relative weight intervals. Witness weights attain each bound. Worst-case regret compares different options under the same weights. Shared-shock dependencies are relaxed, so these bounds can be conservative.'}


def evaluate_compute(request):
    eligible=[o for o in request.options if all(v=='pass' for v in o.constraint_checks.values())]
    blocked=[{'option':o.option,'reasons':[f'{k}: {v}' for k,v in o.constraint_checks.items() if v!='pass']} for o in request.options if o not in eligible]
    names=[o.option for o in eligible]; weights={c.name:c.weight for c in request.criteria};total=sum(weights.values())
    normalized={k:v/total for k,v in weights.items()}
    modal={o.option:sum(normalized[k]*o.scores[k].likely for k in weights) for o in eligible}
    def leaders(values,minimize=False):
        if not values:return []
        best=(min if minimize else max)(values.values())
        return [n for n,v in values.items() if isclose(v,best,rel_tol=0,abs_tol=1e-9)]
    draws={n:[] for n in names};regrets={n:[] for n in names};wins={n:0.0 for n in names};pairwise={n:{m:0.0 for m in names if m!=n} for n in names}
    rng=Random(request.seed)
    for _ in range(request.samples if eligible else 0):
        sampled={k:v*rng.uniform(1-request.weight_uncertainty,1+request.weight_uncertainty) for k,v in weights.items()};denominator=sum(sampled.values())
        shared=rng.random() if request.dependence=='shared_shock' else None
        scores={o.option:sum(sampled[k]*triangular_quantile(o.scores[k],shared if shared is not None else rng.random())/denominator for k in weights) for o in eligible}
        top=leaders(scores);best=max(scores.values())
        for n in names:
            draws[n].append(scores[n]);regrets[n].append(best-scores[n]);wins[n]+=(1/len(top) if n in top else 0)
        # One comparison per unordered pair instead of comparing both directions.
        for i,n in enumerate(names):
            for m in names[i+1:]:
                share=1 if scores[n]>scores[m]+1e-9 else .5 if isclose(scores[n],scores[m],rel_tol=0,abs_tol=1e-9) else 0
                pairwise[n][m]+=share;pairwise[m][n]+=1-share
    rows=[]
    for o in eligible:
        ordered=sorted(draws[o.option]);regret=sorted(regrets[o.option]);tail=max(1,int(request.samples*.05))
        dominated=[other.option for other in eligible if other!=o and all(other.scores[k].low>=o.scores[k].high for k in weights) and any(other.scores[k].low>o.scores[k].high for k in weights)]
        rows.append({'option':o.option,'modal_score':modal[o.option],'mean_score':mean(ordered),
                     'p05':quantile(ordered,.05),'p50':quantile(ordered,.5),'p95':quantile(ordered,.95),
                     'lower_tail_mean':mean(ordered[:tail]),'best_share':wins[o.option]/request.samples,
                     'mean_regret':mean(regret),'p95_regret':quantile(regret,.95),
                     'mean_score_standard_error':stdev(ordered)/sqrt(request.samples),
                     'robustly_dominated_by':dominated,'source':o.source})
    switches=[]
    for i,a in enumerate(eligible):
        for b in eligible[i+1:]:
            for k in weights:
                difference=a.scores[k].likely-b.scores[k].likely
                if abs(difference)<1e-12:continue
                other=sum(weights[j]*(a.scores[j].likely-b.scores[j].likely) for j in weights if j!=k)
                boundary=-other/difference
                if boundary>0:
                    switches.append({'criterion':k,'options':[a.option,b.option],'weight_at_tie':boundary,
                                     'relative_change':boundary/weights[k]-1,
                                     'within_weight_range':weights[k]*(1-request.weight_uncertainty)<=boundary<=weights[k]*(1+request.weight_uncertainty)})
    modal_leaders=leaders(modal);average=leaders({r['option']:r['mean_score'] for r in rows});downside=leaders({r['option']:r['lower_tail_mean'] for r in rows});regret_leaders=leaders({r['option']:r['mean_regret'] for r in rows},True)
    disagreements=len({tuple(sorted(x)) for x in [modal_leaders,average,downside,regret_leaders]})>1
    # Expected perfect-information improvement equals best fixed expected regret.
    information=min((r['mean_regret'] for r in rows),default=None)
    warnings=[]
    if not eligible:warnings.append('No eligible options: resolve failed or unknown constraints first.')
    if len(eligible)==1:warnings.append('Only one eligible option; compare another feasible alternative.')
    if disagreements:warnings.append('Average performance and downside protection favor different options; choose the risk preference explicitly.')
    if any(s['within_weight_range'] for s in switches):warnings.append('At least one pair changes order within the supplied one-at-a-time weight range.')
    if request.dependence=='independent':warnings.append('Score uncertainties are sampled independently. Use shared shock to stress a common movement across all scores.')
    if request.dependence=='shared_shock':warnings.append('Shared shock uses one common percentile for every score; it does not model arbitrary correlations.')
    next_steps=([f"Compare {', '.join(average)} for average performance with {', '.join(downside)} for downside protection."] if eligible else ['Resolve constraint gaps before selecting an option.'])
    if information is not None:next_steps.append(f'Perfect-information improvement under the supplied model: {information:.4f} desirability points; identify evidence that could distinguish close alternatives.')
    next_steps+=['Test the assumptions and run both dependence settings before committing.','Validate the candidate using a measured practical inquiry and record prediction error.']
    return {'options':sorted(rows,key=lambda r:(-r['mean_score'],r['option'])),'blocked':blocked,
            'interval_analysis':interval_analysis(eligible,weights,request.weight_uncertainty),
            'normalized_weights':normalized,'modal_leaders':modal_leaders,'mean_leaders':average,'downside_leaders':downside,
            'regret_leaders':regret_leaders,'risk_preference_disagreement':disagreements,
            'pairwise_win_share':{n:{m:v/request.samples for m,v in comparisons.items()} for n,comparisons in pairwise.items()},
            'weight_switches':switches,'perfect_information_upper_bound':information,
            'samples':request.samples,'seed':request.seed,'dependence':request.dependence,'warnings':warnings,'next_steps':next_steps,
            'computation':{'engine':'classical-local-monte-carlo-v2','quantum_backend':False,
                           'input_sha256':sha256(json.dumps(request.model_dump(mode='json'),sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest(),
                           'pair_comparisons':request.samples*len(eligible)*(len(eligible)-1)//2,
                           'precision_note':'Standard error measures Monte Carlo noise in the mean, not uncertainty in evidence or the real world. SHA-256 identifies inputs; it is not encryption or an authenticity signature.'},
            'method':'Seeded triangular score sampling and uniform relative weight perturbations. Scores are weighted desirability (0–10). Lower-tail mean uses the worst 5% of sampled outcomes.',
            'limitations':'Simulation shares are conditional on supplied ranges and dependence, not calibrated real-world success probabilities. Additive scores assume compensating criteria; hard constraints are checked separately. Unlisted outcomes, unreliable evidence and incorrect preferences can change the result. Information value is in score points, not money.',
            'execution_status':'not_executed'}


def compute_decision(studio,identifier,request,actor='local-user'):
    revision=studio.loop.latest(identifier)
    if revision.version!=request.base_version:raise RevisionConflict('Decision changed; reload before computing')
    if set(o.option for o in request.options)!=set(o.name for o in revision.decision.options):raise ValueError('Include every current decision option exactly once')
    if any(set(o.constraint_checks)!=set(revision.decision.constraints) for o in request.options):raise ValueError('Assess every stored constraint for each option')
    return studio._record(identifier,revision.version,'decision_compute',{'inputs':request.model_dump(mode='json'),'analysis':evaluate_compute(request),'author':actor})


class ComputeObservation(Inputs):
    base_version: int = Field(ge=1)
    compute_id: str = Field(min_length=1,max_length=150)
    option: str = Field(min_length=1,max_length=500)
    actual_scores: dict[str,float] = Field(min_length=1,max_length=10)
    observed_on: date
    source: str = Field(min_length=1,max_length=2000)
    lesson: str = Field(min_length=1,max_length=4000)
    @model_validator(mode='after')
    def valid_scores(self):
        if any(not 0<=score<=10 for score in self.actual_scores.values()):
            raise ValueError('Observed desirability scores must be finite and between 0 and 10')
        return self


def observe_compute(studio,identifier,request,actor='local-user'):
    revision=studio.loop.latest(identifier)
    if revision.version!=request.base_version:raise RevisionConflict('Decision changed; reload before recording outcomes')
    run=next((r for r in studio.records(identifier) if r['id']==request.compute_id and r['kind']=='decision_compute' and r['version']==revision.version),None)
    if not run:raise ValueError('Select an analysis from this decision and current revision')
    inputs=run['inputs'];option=next((o for o in inputs['options'] if o['option']==request.option),None)
    if not option:raise ValueError('Observed option must belong to the saved analysis')
    if set(request.actual_scores)!=set(option['scores']):raise ValueError('Observe every saved criterion exactly once')
    weights=run['analysis']['normalized_weights']
    errors={k:request.actual_scores[k]-score['likely'] for k,score in option['scores'].items()}
    observed=sum(weights[k]*request.actual_scores[k] for k in weights)
    predicted=sum(weights[k]*option['scores'][k]['likely'] for k in weights)
    inside={k:score['low']<=request.actual_scores[k]<=score['high'] for k,score in option['scores'].items()}
    return studio._record(identifier,revision.version,'compute_observation',{
        **request.model_dump(mode='json'),'author':actor,'predicted_score':predicted,'observed_score':observed,
        'score_error':observed-predicted,'criterion_errors':errors,'inside_supplied_ranges':inside,
        'mean_absolute_error':sum(abs(v) for v in errors.values())/len(errors),
        'limitations':'Observed desirability scores are self-reported on the original rubric. Repeated tests and independent measurements are needed to assess real-world accuracy.'})
