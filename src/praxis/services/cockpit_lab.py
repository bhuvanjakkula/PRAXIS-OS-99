"""Offline cockpit telemetry replay and hypothetical airport screening."""
from math import radians,sin,cos,asin,sqrt
from typing import Literal
from pydantic import Field,AwareDatetime,model_validator
from praxis.services.research import Inputs
from praxis.services.decision_loop import RevisionConflict


class Reading(Inputs):
    value: float = Field(ge=-1e12,le=1e12)
    unit: str = Field(min_length=1,max_length=80)
    valid: bool = True


class Frame(Inputs):
    timestamp: AwareDatetime
    readings: dict[str,Reading] = Field(min_length=1,max_length=100)


class Rule(Inputs):
    metric: str = Field(min_length=1,max_length=150)
    unit: str = Field(min_length=1,max_length=80)
    operator: Literal['above','below']
    threshold: float = Field(ge=-1e12,le=1e12)
    category: Literal['propulsion','weather','navigation','cabin','hydraulics','steering','hull','stability','security','shallow_water','other']
    priority: Literal['review','elevated'] = 'review'
    reference: str = Field(min_length=1,max_length=2000)


class Airport(Inputs):
    identifier: str = Field(min_length=1,max_length=100)
    latitude: float = Field(ge=-90,le=90)
    longitude: float = Field(ge=-180,le=180)
    landing_distance_available_ft: float = Field(gt=0,le=100000)
    availability: Literal['unknown','reported_open','reported_closed'] = 'unknown'
    conditions_reference: str = Field(default='',max_length=2000)


class Planning(Inputs):
    latitude: float = Field(ge=-90,le=90)
    longitude: float = Field(ge=-180,le=180)
    fuel_lbs: float = Field(ge=0,le=1e9)
    reserve_lbs: float = Field(ge=0,le=1e9)
    burn_low_lbs_per_nm: float = Field(gt=0,le=1e6)
    burn_high_lbs_per_nm: float = Field(gt=0,le=1e6)
    route_factor: float = Field(default=1,ge=1,le=10)
    required_landing_distance_ft: float = Field(gt=0,le=100000)
    performance_reference: str = Field(min_length=1,max_length=2000)
    airports: list[Airport] = Field(min_length=1,max_length=50)
    @model_validator(mode='after')
    def consistent(self):
        if self.burn_low_lbs_per_nm>self.burn_high_lbs_per_nm:raise ValueError('Burn range must be ordered')
        if len({a.identifier for a in self.airports})!=len(self.airports):raise ValueError('Airport identifiers must be unique')
        return self


class CockpitRequest(Inputs):
    base_version: int = Field(ge=1)
    mode: Literal['simulation'] = 'simulation'
    platform_type: str = Field(min_length=1,max_length=300)
    source: str = Field(min_length=1,max_length=2000)
    reference_time: AwareDatetime
    maximum_age_seconds: int = Field(default=30,ge=1,le=86400)
    frames: list[Frame] = Field(min_length=1,max_length=120)
    rules: list[Rule] = Field(min_length=1,max_length=50)
    planning: Planning | None = None
    @model_validator(mode='after')
    def ordered(self):
        if any(b.timestamp<=a.timestamp for a,b in zip(self.frames,self.frames[1:])):raise ValueError('Frames must have strictly increasing timestamps')
        keys=[r.metric for r in self.rules]
        if len(set(keys))!=len(keys):raise ValueError('Use one rule per metric')
        return self


def distance_nm(lat1,lon1,lat2,lon2):
    dlat=radians(lat2-lat1);dlon=radians(lon2-lon1)
    a=sin(dlat/2)**2+cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return 3440.065*2*asin(sqrt(max(0,min(1,a))))


def screen_airports(planning):
    rows=[]
    for airport in planning.airports:
        direct=distance_nm(planning.latitude,planning.longitude,airport.latitude,airport.longitude)
        route=direct*planning.route_factor
        low=route*planning.burn_low_lbs_per_nm+planning.reserve_lbs
        high=route*planning.burn_high_lbs_per_nm+planning.reserve_lbs
        reasons=[]
        if high>planning.fuel_lbs:reasons.append('High-burn fuel scenario exceeds supplied fuel')
        if airport.landing_distance_available_ft<planning.required_landing_distance_ft:reasons.append('Supplied landing distance is insufficient')
        if airport.availability!='reported_open':reasons.append('Airport reported closed or availability unknown')
        if not airport.conditions_reference:reasons.append('No current conditions reference supplied')
        rows.append({'airport':airport.identifier,'direct_distance_nm':direct,'modeled_route_nm':route,
                     'fuel_required_low_lbs':low,'fuel_required_high_lbs':high,'high_burn_margin_lbs':planning.fuel_lbs-high,
                     'landing_distance_margin_ft':airport.landing_distance_available_ft-planning.required_landing_distance_ft,
                     'screen':'supplied_checks_pass_operational_suitability_unknown' if not reasons else 'screening_gaps',
                     'gaps':reasons,'conditions_reference':airport.conditions_reference})
    return sorted(rows,key=lambda r:r['direct_distance_nm'])


def evaluate_cockpit(request):
    timeline=[];previous={}
    for frame in request.frames:
        age=(request.reference_time-frame.timestamp).total_seconds()
        quality=[];events=[]
        if age<0:quality.append('Frame timestamp is after the replay reference time')
        if age>request.maximum_age_seconds:quality.append('Frame is stale at the replay reference time')
        for rule in request.rules:
            reading=frame.readings.get(rule.metric)
            reason=('Missing reading' if reading is None else 'Reading marked invalid' if not reading.valid else
                    'Unit does not match rule' if reading.unit!=rule.unit else None)
            if reason:quality.append(f'{rule.metric}: {reason}');continue
            if age<0 or age>request.maximum_age_seconds:continue
            crossed=reading.value>rule.threshold if rule.operator=='above' else reading.value<rule.threshold
            if crossed:events.append({'metric':rule.metric,'category':rule.category,'priority':rule.priority,
                                      'value':reading.value,'unit':rule.unit,'threshold':rule.threshold,
                                      'reference':rule.reference,'label':'Supplied simulation threshold crossed'})
        trends=[]
        for key,reading in frame.readings.items():
            prior=previous.get(key)
            if age>=0 and age<=request.maximum_age_seconds and reading.valid and prior and prior[1].unit==reading.unit:
                dt=(frame.timestamp-prior[0]).total_seconds()
                trends.append({'metric':key,'change_per_second':(reading.value-prior[1].value)/dt,'unit':reading.unit+'/s'})
            if age>=0 and age<=request.maximum_age_seconds and reading.valid:previous[key]=(frame.timestamp,reading)
            else:previous.pop(key,None)
        events.sort(key=lambda e:(0 if e['priority']=='elevated' else 1,e['category'],e['metric']))
        timeline.append({'timestamp':frame.timestamp.isoformat(),'age_seconds':age,'data_quality':quality,'events':events,'trends':trends,
                         'status':'data_incomplete' if quality else 'thresholds_crossed' if events else 'no_supplied_threshold_crossing'})
    latest=timeline[-1]
    return {'mode':'simulation','platform_type':request.platform_type,'timeline':timeline,'latest':latest,
            'airport_screening':screen_airports(request.planning) if request.planning else [],
            'live_connected':False,'control_commands':[],'certification_status':'not_certified',
            'limitations':'Offline training replay only. Thresholds and performance inputs are supplied assumptions, not universal aircraft limits. No threshold crossing does not establish safety. This is not TCAS/TAWS, a flight director, an emergency checklist or a diversion recommendation. Airport screening omits terrain, actual routes, changing weather, aircraft configuration, approach minima and operational clearance.',
            'execution_status':'not_executed'}


def cockpit_replay(studio,identifier,request,actor='local-user'):
    revision=studio.loop.latest(identifier)
    if revision.version!=request.base_version:raise RevisionConflict('Decision changed; reload before replay')
    return studio._record(identifier,revision.version,'cockpit_replay',{'inputs':request.model_dump(mode='json'),'analysis':evaluate_cockpit(request),'author':actor})
