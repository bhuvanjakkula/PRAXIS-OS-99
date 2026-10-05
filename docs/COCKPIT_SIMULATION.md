# Cockpit technology adaptation — 2026-10-01

Adapted the supplied ACDS-TMS prototype into an offline cockpit simulation lab
within Aircrew support. All computation remains local. The integration supports
up to 120 chronological telemetry frames, 50 explicit rules and 50 hypothetical
airports. Arbitrary metric names allow engine, weather, navigation-integrity,
cabin and hydraulic simulations without assuming a particular aircraft model.

The API validates timezone-aware timestamps, finite readings, matching units,
ordered replay frames and explicit source/threshold references. Missing, invalid,
stale and future readings produce data-quality findings rather than normal-system
claims. Threshold events are prioritized as simulation findings and show the
supplied rule reference. Change rates retain physical units per second.

Airport screening uses great-circle distances with clamping for numerical stability,
an explicit route factor, low/high fuel burn and reserve, declared landing distance
available and a supplied landing requirement. Availability and current-condition
references remain visible. Passing supplied checks leaves operational suitability
unknown. No live airport/weather data or navigation route is inferred.

The sample's universal aircraft limits, fixed 60 lb/NM burn, fixed runway lengths,
engine-fire memory items, windshear pitch commands, inferred collision-resolution
advisories and emergency-descent instructions were not adopted. They are not
validated across aircraft types. This module makes no ICAO, FAA or DO-178C
compliance or certification claim, provides no aircraft control interface and
returns an empty control-command list. It is training software, not TCAS/TAWS,
a flight director, QRH replacement or operational diversion solver.

Sources used to frame limitations:
- FAA landing-performance guidance: https://www.faa.gov/airports/resources/advisory_circulars/index.cfm/go/document.information/documentID/1042093
- FAA TALPA: https://www.faa.gov/about/initiatives/talpa

Verification: three tests passed covering threshold/trend logic, missing/stale/unit
checks, prohibited live mode, distance/fuel/reserve math, airport gaps and API
role/tenant/revision boundaries. Browser passed synthetic replay in five categories,
persistence after reload, absence of control commands and mobile layout.
