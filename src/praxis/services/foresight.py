"""Bounded forecasting, scenario robustness and hypothesis generation for human review."""
from math import isclose, sqrt
from random import Random
from statistics import mean, pstdev
from typing import Annotated, Literal
from uuid import UUID
from pydantic import Field, model_validator
from praxis.services.research import Inputs
from praxis.services.decision_loop import RevisionConflict
from praxis.grounding.documents import tokens

Number = Annotated[float, Field(ge=-1e12, le=1e12)]
Text = Annotated[str, Field(min_length=1, max_length=1000)]


class Series(Inputs):
    metric: str = Field(min_length=1, max_length=200)
    unit: str = Field(min_length=1, max_length=80)
    interval: str = Field(min_length=1, max_length=80)
    source: str = Field(min_length=1, max_length=2000)
    values: list[Number] = Field(min_length=8, max_length=500)
    horizon: int = Field(default=6, ge=1, le=24)
    target: Number


class World(Inputs):
    name: str = Field(min_length=1, max_length=100)
    probability: float = Field(ge=0, le=1)


class Strategy(Inputs):
    option: str = Field(min_length=1, max_length=500)
    payoffs: dict[str, Number] = Field(min_length=1, max_length=12)
    constraints: dict[str, Literal['pass','fail','unknown']] = Field(default_factory=dict, max_length=100)


class ScenarioModel(Inputs):
    unit: str = Field(min_length=1, max_length=80)
    worlds: list[World] = Field(min_length=2, max_length=12)
    strategies: list[Strategy] = Field(min_length=2, max_length=20)
    maximum_loss: float | None = Field(default=None, ge=0, le=1e12)
    @model_validator(mode='after')
    def complete(self):
        names=[w.name for w in self.worlds]
        if len(set(names))!=len(names) or not isclose(sum(w.probability for w in self.worlds),1,abs_tol=1e-8):
            raise ValueError('Use unique scenario names and probabilities summing to 1')
        if len({s.option for s in self.strategies})!=len(self.strategies):
            raise ValueError('Option names must be unique')
        if any(set(s.payoffs)!=set(names) for s in self.strategies):
            raise ValueError('Every option must supply a payoff for every scenario')
        return self


class ForesightRequest(Inputs):
    base_version: int = Field(ge=1)
    new_situation: str = Field(default='', max_length=4000)
    unknowns: list[Text] = Field(default_factory=list, max_length=20)
    series: Series | None = None
    scenario_model: ScenarioModel | None = None
    seed: int = Field(default=42, ge=0, le=2147483647)


def _predict(values, model, horizon=1):
    if model=='last_value': return values[-1]
    if model=='drift': return values[-1]+(values[-1]-values[0])*horizon/(len(values)-1)
    center=(len(values)-1)/2
    average=mean(values)
    slope=sum((i-center)*(v-average) for i,v in enumerate(values))/sum((i-center)**2 for i in range(len(values)))
    return average+slope*(len(values)-1+horizon-center)


def _quantile(values, p):
    ordered=sorted(values); index=(len(ordered)-1)*p; lo=int(index)
    return ordered[lo]+(ordered[min(lo+1,len(ordered)-1)]-ordered[lo])*(index-lo)


def forecast(series, seed=42):
    values=series.values
    models=['last_value','drift','linear_trend']
    start=max(4,len(values)-20)
    errors={m:[values[i]-_predict(values[:i],m) for i in range(start,len(values))] for m in models}
    maes={m:mean(abs(e) for e in errors[m]) for m in models}
    # Prefer a simpler model for exact ties. Do not invent trained-model confidence.
    chosen=min(models,key=lambda m:maes[m])
    residuals=errors[chosen]
    rng=Random(seed)
    rows=[]
    for step in range(1,series.horizon+1):
        center=_predict(values,chosen,step)
        draws=[center+rng.choice(residuals)*sqrt(step) for _ in range(2000)]
        rows.append({'step':step,'estimate':center,'p10':_quantile(draws,.1),'p90':_quantile(draws,.9),
                     'probability_at_or_above_target':sum(x>=series.target for x in draws)/len(draws)})
    recent=values[-4:]; previous=values[-8:-4]
    shifted=abs(mean(recent)-mean(previous))>max(2*pstdev(values),1e-9)
    # An abrupt last-step surprise is another indication of a changing process.
    typical=mean(abs(values[i]-values[i-1]) for i in range(1,len(values)-1))
    shifted=shifted or abs(values[-1]-values[-2])>max(3*typical,1e-9)
    warnings=[]
    if len(values)<30:warnings.append('Fewer than 30 observations: error estimates may be unstable.')
    if series.horizon>len(values)/4:warnings.append('Long extrapolation relative to the available history.')
    if shifted:warnings.append('A recent shift is flagged; historical relationships may no longer apply.')
    if max(residuals)-min(residuals)<1e-8:warnings.append('Historical errors have little variation; narrow bands do not rule out future shocks.')
    return {'metric':series.metric,'unit':series.unit,'interval':series.interval,'source':series.source,
            'selected_model':chosen,'backtests':[{'model':m,'one_step_mae':maes[m],'test_points':len(errors[m])} for m in models],
            'forecast':rows,'target':series.target,'warnings':warnings,'regime_shift_flag':shifted,
            'method':'Rolling one-step backtests select among last value, endpoint drift and linear trend. Seeded residual resampling uses square-root-of-horizon scaling.',
            'limitations':'Conditional projections for equally spaced observations in supplied order. Bands are empirical 10th–90th residual quantiles, not calibrated confidence intervals. '
                          'Model selection uses the same backtests shown here; scores are not independent validation. No seasonality, causal effects or unseen shocks are modeled.'}


def robustness(model):
    worlds=model.worlds
    eligible=[]; blocked=[]
    for strategy in model.strategies:
        reasons=[f'{name}: {status}' for name,status in strategy.constraints.items() if status!='pass']
        # Include zero-probability worlds in robustness and loss-limit checks deliberately.
        if model.maximum_loss is not None and min(strategy.payoffs.values()) < -model.maximum_loss:
            reasons.append('Worst supplied scenario exceeds the maximum loss')
        if reasons:blocked.append({'option':strategy.option,'reasons':reasons})
        else:eligible.append(strategy)
    rows=[]
    for s in eligible:
        rows.append({'option':s.option,'expected_payoff':sum(w.probability*s.payoffs[w.name] for w in worlds),
                     'worst_case':min(s.payoffs.values()),
                     'maximum_regret':max(max(o.payoffs[w.name] for o in eligible)-s.payoffs[w.name] for w in worlds)})
    def best(key, reverse=False):
        if not rows:return []
        value=(min if reverse else max)(r[key] for r in rows)
        return [r['option'] for r in rows if isclose(r[key],value,rel_tol=0,abs_tol=1e-8)]
    sensitivity=[]
    for focus in worlds:
        for factor in (.5,1.5):
            weights={w.name:w.probability*(factor if w.name==focus.name else 1) for w in worlds}
            total=sum(weights.values())
            scores={s.option:sum(weights[w.name]*s.payoffs[w.name]/total for w in worlds) for s in eligible}
            top=max(scores.values(),default=None)
            sensitivity.append({'scenario':focus.name,'probability_multiplier':factor,
                                'leaders':[name for name,value in scores.items() if isclose(value,top,rel_tol=0,abs_tol=1e-8)]})
    perfect=sum(w.probability*max(s.payoffs[w.name] for s in eligible) for w in worlds) if eligible else None
    evpi=max(0,perfect-max(r['expected_payoff'] for r in rows)) if rows else None
    return {'unit':model.unit,'options':rows,'blocked':blocked,'expected_value_leaders':best('expected_payoff'),
            'worst_case_leaders':best('worst_case'),'minimax_regret_leaders':best('maximum_regret',True),
            'scenario_information_upper_bound':evpi,'sensitivity':sensitivity,
            'limitations':'Payoffs, probabilities and constraint checks are supplied assumptions. Zero-probability scenarios still enter worst-case and regret checks. '
                          'Information value assumes perfect knowledge of the listed scenario before choosing; it is an upper bound, not an experiment budget recommendation. '
                          'Sensitivity changes one probability at a time; unlisted outcomes and combinations are not covered.'}


def hypotheses(decision, situation, unknowns, past):
    names=[o.name for o in decision.options]
    candidates=[]
    for option in names[:3] or ['a proposed approach']:
        for strategy,description,test in [
            ('stage',f'Test a limited version of {option}, with explicit expansion gates.', 'Compare a limited trial with the current baseline before expansion.'),
            ('substitute',f'Replace the most uncertain dependency in {option} with a simpler alternative.', 'Test whether the replacement preserves the objective and constraints.'),
            ('contingency',f'Prepare a fallback for {option} when a stated assumption fails.', 'Rehearse the trigger and recovery steps under the new situation.')]:
            candidates.append({'title':description,'method':strategy,'status':'template_derived_hypothesis',
                               'goal':decision.objective,'new_situation':situation,
                               'assumptions_to_test':unknowns or decision.assumptions or ['Identify the assumption most likely to change the outcome.'],
                               'constraints_to_verify':decision.constraints,'experiment':test,
                               'falsifier':'Reject or revise if the measured outcome misses the predeclared target or any required constraint fails.',
                               'required_measurements':['Baseline and target','Observed outcome and source','Cost, harm and stop conditions']})
    query=tokens(decision.problem+' '+decision.objective+' '+situation)
    analogies=[]
    for revision in past:
        if str(revision['decision_id'])==str(decision.id):continue
        other=revision['decision'];terms=tokens(other['problem']+' '+other['objective'])
        overlap=len(query&terms)/max(1,len(query|terms))
        if overlap:
            analogies.append({'decision_id':str(revision['decision_id']),'version':revision['version'],
                             'title':other['title'],'similarity':overlap,'options':[o['name'] for o in other['options']],
                             'lesson':revision.get('feedback',{}).get('learning') if revision.get('feedback') else None,
                             'caution':'Lexical analogy only; transferability and outcomes must be independently checked.'})
    analogies.sort(key=lambda r:(-r['similarity'],r['decision_id']))
    return candidates,analogies[:3]


def foresight(studio, identifier, request, past, actor='local-user'):
    revision=studio.loop.latest(identifier)
    if revision.version!=request.base_version:raise RevisionConflict('Reload the latest decision before forecasting')
    d=revision.decision
    if request.scenario_model:
        model=request.scenario_model
        if sorted(s.option for s in model.strategies)!=sorted(o.name for o in d.options):
            raise ValueError('Assess every current decision option exactly once')
        if any(set(s.constraints)!=set(d.constraints) for s in model.strategies):
            raise ValueError('Assess every decision constraint for every option')
    unknowns=list(dict.fromkeys([*d.uncertainties,*request.unknowns]))
    candidates,analogies=hypotheses(d,request.new_situation,unknowns,past)
    analysis={'forecast':forecast(request.series,request.seed) if request.series else None,
              'robustness':robustness(request.scenario_model) if request.scenario_model else None,
              'candidate_solutions':candidates,'analogies':analogies,'uncertainties':unknowns,
              'new_situation':request.new_situation,
              'stress_questions':[f'What changes if {a} is false?' for a in d.assumptions[:10]]+[
                  'What if demand, costs or available resources change abruptly?',
                  'What if a dependency or key person becomes unavailable?',
                  'What irreversible harm could occur before feedback arrives?'],
              'next_steps':['Review forecast assumptions and data provenance.',
                            'Choose a candidate experiment, define success and stop thresholds, then record observed outcomes.',
                            'Use Human review to accept, reject, modify or defer this analysis.'],
              'execution_status':'not_executed','confidence':None,
              'limitations':'Forecasts are conditional on supplied history and scenarios. Candidate solutions are structured hypotheses, not proven inventions or autonomous reasoning. '
                            'No system can guarantee predictions for unseen situations. Human judgment and real-world testing remain required.'}
    return studio._record(identifier,revision.version,'foresight_run',{'inputs':request.model_dump(mode='json'),'analysis':analysis,'author':actor})


class ForecastObservation(Inputs):
    base_version: int = Field(ge=1)
    forecast_id: UUID
    step: int = Field(ge=1, le=24)
    actual: Number
    source: str = Field(min_length=1,max_length=2000)
    learning: str = Field(min_length=1,max_length=4000)


def observe_forecast(studio,identifier,request,actor='local-user'):
    revision=studio.loop.latest(identifier)
    if revision.version!=request.base_version:raise RevisionConflict('Reload before recording an observation')
    run=next((r for r in studio.records(identifier) if r['id']==str(request.forecast_id) and r['kind']=='foresight_run'),None)
    if not run:raise ValueError('Forecast must belong to this decision')
    result=run['analysis']['forecast']
    if not result or request.step>len(result['forecast']):raise ValueError('The forecast has no such step')
    row=result['forecast'][request.step-1]
    return studio._record(identifier,revision.version,'forecast_observation',{
        **request.model_dump(mode='json'),'author':actor,'forecast_version':run['version'],'unit':result['unit'],
        'predicted':row['estimate'],'error':request.actual-row['estimate'],'absolute_error':abs(request.actual-row['estimate']),
        'inside_empirical_band':row['p10']<=request.actual<=row['p90'],
        'note':'Self-reported observation; repeated observations/corrections remain in history. No automatic retraining or calibration claim.'})
