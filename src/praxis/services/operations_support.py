"""General incident preparation and handover; no operational control instructions."""
from typing import Literal
from pydantic import Field
from praxis.services.research import Inputs
from praxis.services.decision_loop import RevisionConflict
from praxis.services.maritime_coordination import MaritimeCoordination, analyze_maritime_coordination
from praxis.services.aviation_coordination import AviationCoordination, analyze_aviation_coordination


class IncidentRequest(Inputs):
    coordination: AviationCoordination | None = None
    maritime: MaritimeCoordination | None = None
    base_version: int = Field(ge=1)
    domain: Literal['aviation','maritime']
    platform_type: str = Field(min_length=1,max_length=300)
    identifier: str = Field(min_length=1,max_length=200)
    phase: str = Field(min_length=1,max_length=200)
    situation: str = Field(min_length=1,max_length=4000)
    observations: str = Field(min_length=1,max_length=4000)
    people_status: str = Field(default='',max_length=2000)
    position_and_time: str = Field(default='',max_length=2000)
    environmental_conditions: str = Field(default='',max_length=2000)
    crew_roles: str = Field(default='',max_length=2000)
    communications_status: str = Field(default='',max_length=2000)
    procedure_reference: str = Field(default='',max_length=2000)
    procedure_applicability: Literal['not_checked','confirmed_by_crew','not_applicable'] = 'not_checked'
    unresolved_questions: str = Field(default='',max_length=4000)
    urgency: Literal['training','uncertain','urgent'] = 'training'


def incident_support(studio,decision_id,request,actor='local-user'):
    revision=studio.loop.latest(decision_id)
    if revision.version!=request.base_version:raise RevisionConflict('Decision changed; reload before saving incident')
    aviation=request.domain=='aviation'
    if request.coordination and not aviation:raise ValueError('Aviation coordination applies to aviation records only')
    if request.maritime and aviation:raise ValueError('Maritime coordination applies to maritime records only')
    authority='pilot in command' if aviation else 'master and bridge team'
    procedure='current aircraft flight manual / POH, approved emergency checklist and operator procedures' if aviation else 'vessel safety management system, approved shipboard emergency plans and operator procedures'
    gaps=[label for key,label in [('people_status','Passenger and crew status'),('position_and_time','Position and observation time'),
                                  ('environmental_conditions','Environmental conditions'),('crew_roles','Crew responsibilities'),
                                  ('communications_status','Communication status'),('procedure_reference','Exact approved procedure reference')]
          if not getattr(request,key)]
    if request.procedure_applicability!='confirmed_by_crew':gaps.append('Procedure applicability has not been confirmed by crew')
    if request.procedure_applicability=='confirmed_by_crew' and not request.procedure_reference:
        raise ValueError('Provide the exact procedure reference before confirming applicability')
    status='preparation_only_missing_context' if gaps else 'crew_report_complete_unverified'
    priorities=[f'The {authority} retains operational authority; use {procedure}.',
                'Use this record for preparation and handover without interrupting essential crew duties.',
                'Separate observed indications from suspected causes; note when each observation was made.',
                'Check passenger and crew welfare using the applicable approved procedures.',
                'Record unresolved questions and communication needs for the responsible crew and relevant support services.']
    if request.urgency!='training':priorities.insert(0,'For an actual or suspected emergency, rely on the responsible crew, approved procedures and the relevant emergency support service. Do not wait for this form or software output.')
    handover={k:getattr(request,k) for k in ['domain','platform_type','identifier','phase','urgency','situation','observations',
                                           'people_status','position_and_time','environmental_conditions','crew_roles','communications_status',
                                           'procedure_reference','procedure_applicability','unresolved_questions']}
    return studio._record(decision_id,revision.version,'operations_incident',{
        'author':actor,'inputs':request.model_dump(mode='json'),'analysis':{'domain':request.domain,'status':status,'missing_information':gaps,
            'maritime':analyze_maritime_coordination(request.maritime) if request.maritime else None,
            'coordination':analyze_aviation_coordination(request.coordination) if request.coordination else None,
            'handover':handover,'coordination_prompts':priorities,
            'questions':['Which indications were directly observed, and which are interpretations?',
                         'Does the referenced procedure match the exact model, configuration, operating phase and revision?',
                         'Who owns each communication and passenger/crew welfare task?',
                         'What has changed since the last report, and which facts remain uncertain?'],
            'operational_guidance_available':False,'live_telemetry_connected':False,'execution_status':'not_executed',
            'limitations':'Training, preparation and incident documentation only. No certified operational guidance, navigation, control commands, diagnosis or passenger-safety guarantee. Procedure confirmation is a crew declaration, not software verification.',
            'references':([{'title':'FAA emergency responsibility and authority','url':'https://www.faa.gov/air_traffic/publications/atpubs/aim_html/chap6_section_1.html'}] if aviation else
                          [{'title':'IMO International Safety Management Code','url':'https://www.imo.org/en/ourwork/humanelement/pages/ismcode.aspx'}])}})
