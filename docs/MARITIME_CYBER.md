# Autonomous bridge cyber-control evidence

Use Maritime > Enable maritime coordination review > Add system review. Select
**Cyber response**, open **Cyber control evidence (optional)**, and add a control.
Seven optional areas cover navigation integrity, ship–shore authentication,
access/key lifecycle, network segmentation, monitoring, software/chart/model
integrity and recovery testing. Review each area at most once per system record.

Each control records asset/interface scope, supplied status, owner, approved
control and revision, applicability assessment, authorized validation evidence,
limitations and next review date. Missing references, reported gaps and overdue
reviews propagate into the system review. Complete documentation remains
unverified; it does not establish effectiveness or compliance. Controls can only
be attached to cyber-response reviews. Existing records without controls remain
supported. Inputs and analysis persist in the revision-bound incident record and
handover export.

The supplied summary, attachment `49dc4de7-33a9-4de5-aa68-be4a153ce79d`, informed
the review categories. Its protocol mappings and standards applicability were
not independently verified or adopted as requirements. No GNSS/AIS authentication,
SECOM implementation, PKI, firewall changes, network scanning, anomaly detector,
blockchain service or live monitoring is implemented by this update. Applicable
standards and control suitability must be recorded by the responsible reviewer
for the specific interface and vessel. Keep keys and sensitive vulnerability
details in authorized systems and store references here.

Validation: 231 backend tests passed, one PostgreSQL-only skip; browser scenario
passed persistence, export and mobile layout. JavaScript syntax passed. Existing
Starlette/httpx deprecation warning remains.
