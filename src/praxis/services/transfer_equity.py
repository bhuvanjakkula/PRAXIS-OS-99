"""Grouped income accounting with explicit delivery assumptions."""
from pydantic import Field,model_validator
from praxis.services.research import Inputs
class IncomeGroup(Inputs):
    name: str=Field(min_length=1,max_length=200)
    population: int=Field(ge=1,le=2000000000)
    income: float=Field(ge=0,le=1e12)
    tax: float=Field(ge=0,le=1e12)
    transfer: float=Field(ge=0,le=1e12)
    coverage: float=Field(ge=0,le=1)
    @model_validator(mode='after')
    def tax_valid(self):
        if self.tax>self.income:raise ValueError('Tax cannot exceed supplied income')
        return self
class TransferEquity(Inputs):
    groups: list[IncomeGroup]=Field(min_length=2,max_length=40)
    leakage: float=Field(ge=0,le=1)
    poverty_line: float=Field(ge=0,le=1e12)
    evidence: str=Field(min_length=1,max_length=2000)
    @model_validator(mode='after')
    def distinct(self):
        if len({g.name.casefold() for g in self.groups})!=len(self.groups):raise ValueError('Use distinct income groups')
        return self

def income_metrics(points,line):
    count=sum(n for x,n in points);total=sum(x*n for x,n in points)
    cumulative=0;area=0
    for income,n in sorted(points):
        area+=n*(2*cumulative+income*n);cumulative+=income*n
    return {'mean_income':total/count,'grouped_gini':1-area/(count*total) if total else None,
        'poverty_headcount_share':sum(n for x,n in points if x<line)/count}

def analyze_transfers(request):
    before=[(g.income,g.population) for g in request.groups];after=[];rows=[]
    for g in request.groups:
        received=g.transfer*(1-request.leakage);base=g.income-g.tax
        after.extend([(base,g.population*(1-g.coverage)),(base+received,g.population*g.coverage)])
        rows.append({'group':g.name,'income_after_tax':base,'recipient_income':base+received,
            'expected_recipients':g.population*g.coverage,'delivered_transfer_total':received*g.population*g.coverage,
            'allocated_transfer_total':g.transfer*g.population*g.coverage})
    return {'before':income_metrics(before,request.poverty_line),'after':income_metrics(after,request.poverty_line),
        'groups':rows,'tax_total':sum(g.tax*g.population for g in request.groups),
        'allocated_transfers':sum(r['allocated_transfer_total'] for r in rows),
        'delivered_transfers':sum(r['delivered_transfer_total'] for r in rows),'evidence':request.evidence,
        'limitations':'Grouped synthetic accounting, not a national Gini estimate or causal forecast. All members of each group share the supplied starting income and tax. Coverage divides each group into recipients and nonrecipients; fractions are expected counts. Leakage reduces delivery but its recipients and administrative costs are not modeled. No behavioral, price or public-service effects. Inputs must use one per-person monetary unit and period; transfer financing is assessed separately.'}
