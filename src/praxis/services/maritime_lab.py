"""Offline maritime geometry and explicit depth assumptions; no bridge orders."""
from math import radians,sin,cos,hypot
from random import Random
from typing import Literal
from pydantic import Field,AwareDatetime,model_validator
from praxis.services.research import Inputs
from praxis.services.cockpit_lab import Frame,Rule,CockpitRequest,evaluate_cockpit,distance_nm
from praxis.services.decision_loop import RevisionConflict


class Target(Inputs):
    identifier: str = Field(min_length=1,max_length=100)
    bearing_deg: float = Field(ge=0,lt=360)
    bearing_reference: Literal['relative_to_heading','true']
    distance_nm: float = Field(ge=0,le=500)
    speed_over_ground_kts: float = Field(ge=0,le=150)
    course_over_ground_deg: float = Field(ge=0,lt=360)
    ais_status: Literal['matched','not_seen','unknown'] = 'unknown'
    valid: bool = True


class SensorUncertainty(Inputs):
    bearing_error_deg: float = Field(ge=0,le=30)
    distance_error_nm: float = Field(ge=0,le=10)
    course_error_deg: float = Field(ge=0,le=30)
    speed_error_kts: float = Field(ge=0,le=20)
    samples: int = Field(default=500,ge=100,le=1000)
    seed: int = Field(default=42,ge=0,le=2147483647)
    reference: str = Field(min_length=1,max_length=2000)


class Traffic(Inputs):
    timestamp: AwareDatetime
    own_heading_deg: float = Field(ge=0,lt=360)
    own_course_over_ground_deg: float = Field(ge=0,lt=360)
    own_speed_over_ground_kts: float = Field(ge=0,le=150)
    closest_distance_threshold_nm: float = Field(gt=0,le=100)
    horizon_minutes: float = Field(gt=0,le=120)
    reference: str = Field(min_length=1,max_length=2000)
    targets: list[Target] = Field(default_factory=list,max_length=100)
    uncertainty: SensorUncertainty | None = None
    @model_validator(mode='after')
    def distinct(self):
        if len({t.identifier for t in self.targets})!=len(self.targets):raise ValueError('Target identifiers must be unique')
        return self


class Depth(Inputs):
    charted_depth_m: float = Field(ge=0,le=15000)
    tide_height_m: float = Field(ge=-30,le=30)
    draft_m: float = Field(ge=0,le=50)
    squat_allowance_m: float = Field(ge=0,le=20)
    motion_allowance_m: float = Field(ge=0,le=20)
    depth_uncertainty_m: float = Field(ge=0,le=20)
    required_clearance_m: float = Field(ge=0,le=30)
    reference: str = Field(min_length=1,max_length=2000)


class RefugePort(Inputs):
    identifier: str = Field(min_length=1,max_length=100)
    latitude: float = Field(ge=-90,le=90)
    longitude: float = Field(ge=-180,le=180)
    depth: Depth
    entry_permission: Literal['unknown','reported_granted','reported_denied'] = 'unknown'
    tug_support: Literal['unknown','reported_available','reported_unavailable'] = 'unknown'
    medical_support: Literal['unknown','reported_available','reported_unavailable'] = 'unknown'
    conditions_reference: str = Field(default='',max_length=2000)


class RefugePlanning(Inputs):
    latitude: float = Field(ge=-90,le=90)
    longitude: float = Field(ge=-180,le=180)
    require_tug: bool = True
    require_medical: bool = True
    ports: list[RefugePort] = Field(min_length=1,max_length=50)
    @model_validator(mode='after')
    def distinct(self):
        if len({p.identifier for p in self.ports})!=len(self.ports):raise ValueError('Port identifiers must be unique')
        return self


class MaritimeRequest(Inputs):
    base_version: int = Field(ge=1)
    mode: Literal['simulation'] = 'simulation'
    vessel_type: str = Field(min_length=1,max_length=300)
    source: str = Field(min_length=1,max_length=2000)
    reference_time: AwareDatetime
    maximum_age_seconds: int = Field(default=30,ge=1,le=86400)
    frames: list[Frame] = Field(min_length=1,max_length=120)
    rules: list[Rule] = Field(min_length=1,max_length=50)
    traffic: Traffic | None = None
    depth: Depth | None = None
    refuge: RefugePlanning | None = None


def closest_approach(traffic,target):
    bearing=(target.bearing_deg+traffic.own_heading_deg)%360 if target.bearing_reference=='relative_to_heading' else target.bearing_deg
    angle=radians(bearing);rx=target.distance_nm*sin(angle);ry=target.distance_nm*cos(angle)
    own=radians(traffic.own_course_over_ground_deg);other=radians(target.course_over_ground_deg)
    vx=target.speed_over_ground_kts*sin(other)-traffic.own_speed_over_ground_kts*sin(own)
    vy=target.speed_over_ground_kts*cos(other)-traffic.own_speed_over_ground_kts*cos(own)
    square=vx*vx+vy*vy
    if square<1e-12:
        signed=None;future=0.0;infinite=target.distance_nm;geometry='no_relative_motion'
    else:
        hours=-(rx*vx+ry*vy)/square;signed=hours*60
        future=max(0,min(hours,traffic.horizon_minutes/60))
        infinite=hypot(rx+vx*hours,ry+vy*hours)
        geometry='past_closest_approach' if hours<0 else 'future_closest_approach'
    minimum=hypot(rx+vx*future,ry+vy*future)
    return {'target':target.identifier,'true_bearing_deg':bearing,'signed_tcpa_minutes':signed,
            'unbounded_dcpa_nm':infinite,'horizon_minimum_distance_nm':minimum,'horizon_minimum_time_minutes':future*60,
            'relative_speed_kts':sqrt_value(square),'geometry':geometry,
            'within_supplied_distance_threshold':minimum<traffic.closest_distance_threshold_nm,
            'ais_status':target.ais_status,'identity_assessment':'Not inferred from AIS availability',
            'right_of_way_assessment':'Not determined','control_commands':[]}


def sqrt_value(value):return value**.5


def uncertainty_screen(traffic,target):
    u=traffic.uncertainty
    if u is None:return None
    rng=Random(u.seed);distances=[];times=[];inside=0
    # Independent uniform perturbations are declared assumptions, not sensor calibration.
    def angle(value,error):return (value+rng.uniform(-error,error))%360
    def speed(value):return max(0,min(150,value+rng.uniform(-u.speed_error_kts,u.speed_error_kts)))
    for _ in range(u.samples):
        own=traffic.model_copy(update={'own_heading_deg':angle(traffic.own_heading_deg,u.bearing_error_deg),
            'own_course_over_ground_deg':angle(traffic.own_course_over_ground_deg,u.course_error_deg),
            'own_speed_over_ground_kts':speed(traffic.own_speed_over_ground_kts)})
        other=target.model_copy(update={'bearing_deg':angle(target.bearing_deg,u.bearing_error_deg),
            'distance_nm':max(0,target.distance_nm+rng.uniform(-u.distance_error_nm,u.distance_error_nm)),
            'course_over_ground_deg':angle(target.course_over_ground_deg,u.course_error_deg),
            'speed_over_ground_kts':speed(target.speed_over_ground_kts)})
        result=closest_approach(own,other)
        distances.append(result['horizon_minimum_distance_nm']);times.append(result['horizon_minimum_time_minutes'])
        inside+=result['within_supplied_distance_threshold']
    distances.sort();times.sort()
    def percentile(values,p):
        at=(len(values)-1)*p;i=int(at)
        return values[i]+(values[min(i+1,len(values)-1)]-values[i])*(at-i)
    return {'samples':u.samples,'seed':u.seed,'separation_p05_nm':percentile(distances,.05),
            'separation_p50_nm':percentile(distances,.5),'separation_p95_nm':percentile(distances,.95),
            'minimum_sampled_separation_nm':distances[0],'time_p05_minutes':percentile(times,.05),'time_p95_minutes':percentile(times,.95),
            'inside_threshold_share':inside/u.samples,'threshold_classification_changes':0<inside<u.samples,
            'reference':u.reference,'limitations':'Independent uniform error assumptions with clipped nonnegative distance/speed. Sampled minima are not guaranteed bounds. Shares are not calibrated collision probabilities; turns, correlations and sensor biases are not modeled.'}


def depth_screen(depth):
    available=depth.charted_depth_m+depth.tide_height_m
    static=available-depth.draft_m
    adjusted=static-depth.squat_allowance_m-depth.motion_allowance_m-depth.depth_uncertainty_m
    return {'water_depth_m':available,'static_clearance_m':static,'allowance_adjusted_clearance_m':adjusted,
            'required_clearance_m':depth.required_clearance_m,'clearance_margin_m':adjusted-depth.required_clearance_m,
            'supplied_clearance_check_pass':adjusted>=depth.required_clearance_m,'reference':depth.reference,
            'operational_suitability':'unknown'}


def evaluate_maritime(request):
    replay= evaluate_cockpit(CockpitRequest(base_version=request.base_version,platform_type=request.vessel_type,
                source=request.source,reference_time=request.reference_time,maximum_age_seconds=request.maximum_age_seconds,
                frames=request.frames,rules=request.rules))
    traffic_rows=[];quality=[]
    if request.traffic:
        age=(request.reference_time-request.traffic.timestamp).total_seconds()
        if age<0 or age>request.maximum_age_seconds:quality.append('Traffic snapshot is future-dated or stale; CPA calculations withheld')
        else:
            for target in request.traffic.targets:
                if target.valid:
                    traffic_rows.append({**closest_approach(request.traffic,target),'uncertainty':uncertainty_screen(request.traffic,target)})
                else:quality.append(f'{target.identifier}: target invalid; CPA calculation withheld')
    if request.traffic and request.traffic.uncertainty is None:quality.append('Sensor uncertainty was not supplied; nominal geometry only')
    summary=[]
    if not request.traffic:summary.append('No traffic snapshot supplied')
    if not request.depth:summary.append('No under-keel-clearance scenario supplied')
    for row in traffic_rows:
        if row['within_supplied_distance_threshold']:summary.append(f"{row['target']}: nominal separation enters the supplied threshold")
        if row['uncertainty'] and row['uncertainty']['threshold_classification_changes']:summary.append(f"{row['target']}: threshold classification changes under supplied sensor errors")
    if request.depth and not depth_screen(request.depth)['supplied_clearance_check_pass']:summary.append('Supplied depth allowances leave inadequate clearance margin')
    ports=[]
    if request.refuge:
        for port in request.refuge.ports:
            depth=depth_screen(port.depth);gaps=[]
            if not depth['supplied_clearance_check_pass']:gaps.append('Supplied clearance requirement not met')
            if port.entry_permission!='reported_granted':gaps.append('Entry permission denied or unknown')
            if request.refuge.require_tug and port.tug_support!='reported_available':gaps.append('Required tug support unavailable or unknown')
            if request.refuge.require_medical and port.medical_support!='reported_available':gaps.append('Required medical support unavailable or unknown')
            if not port.conditions_reference:gaps.append('Current port conditions reference missing')
            ports.append({'port':port.identifier,'distance_nm':distance_nm(request.refuge.latitude,request.refuge.longitude,port.latitude,port.longitude),
                          'depth_screen':depth,'gaps':gaps,'screen':'supplied_checks_pass_operational_suitability_unknown' if not gaps else 'screening_gaps'})
    return {'mode':'simulation','vessel_type':request.vessel_type,'timeline':replay['timeline'],'latest':replay['latest'],
            'traffic':traffic_rows,'traffic_data_quality':quality,'depth_screen':depth_screen(request.depth) if request.depth else None,
            'review_summary':summary,
            'refuge_screening':sorted(ports,key=lambda p:p['distance_nm']),
            'live_connected':False,'control_commands':[],'certification_status':'not_certified','execution_status':'not_executed',
            'limitations':'Offline training only. CPA assumes constant straight-line ground velocities in a local tangent plane; bearing frames must be explicit. No COLREG right-of-way or maneuver is inferred. AIS absence does not imply hostile intent. Depth allowances and thresholds are supplied assumptions; GM and wave-height readings do not establish intact/damage stability or rolling resonance. Port screening is not entry permission, a navigable route or a safe refuge recommendation.'}


def maritime_replay(studio,identifier,request,actor='local-user'):
    revision=studio.loop.latest(identifier)
    if revision.version!=request.base_version:raise RevisionConflict('Decision changed; reload before maritime replay')
    return studio._record(identifier,revision.version,'maritime_replay',{'inputs':request.model_dump(mode='json'),'analysis':evaluate_maritime(request),'author':actor})
