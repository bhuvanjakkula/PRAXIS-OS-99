# Maritime technology adaptation — 2026-10-01

Integrated the supplied maritime prototype as Ship captain support -> Maritime
simulation lab. It runs locally and stores revision-bound simulation inputs and
outputs independently of cockpit replay and aviation incidents.

Capabilities: configurable telemetry rules for steering, hull, stability, weather,
navigation and security; timestamp/unit/data-validity checks; signed TCPA,
unbounded DCPA and minimum separation inside a supplied time horizon; under-keel
clearance from chart depth plus tide minus draft, squat, motion and uncertainty;
and hypothetical refuge-port screening with declared permissions and services.

Corrections to the supplied prototype:
- Bow-relative bearings are converted to true bearings using heading before vector
  geometry. Velocity uses true course over ground, not heading or a mislabeled
  course_over_ground_kts field. Distances are NM, speeds knots and time minutes.
- Zero relative velocity yields undefined TCPA rather than a magic 999 value.
  Past CPA and a horizon-limited future minimum are reported separately.
- Missing AIS does not classify a craft as hostile. Geometric encounters do not
  establish COLREG right of way. No helm, whistle, throttle, counter-flooding,
  security-evasion or other operational commands are generated.
- Wave height is not used to invent wave period or diagnose rolling resonance.
  GM alone is not treated as proof of intact or damage stability.
- Fixed global ports, depths and service availability are replaced by explicit
  scenario inputs; unknown entry permission and service availability remain gaps.
  Great-circle proximity does not establish a navigable passage or safe refuge.

No NMEA/AIS/ARPA hardware feed, certified stability model, navigation integration,
COLREG/SOLAS/ISPS compliance claim or operational control is provided. The lab is
for offline training and preparation. Thresholds and depth allowances are supplied
assumptions; the master must use approved procedures and all available information.

References:
- IMO COLREG: https://www.imo.org/en/about/conventions/pages/colreg.aspx
- IMO places of refuge: https://www.imo.org/en/ourwork/safety/pages/placesofrefuge.aspx

Verification: six maritime/shared-cockpit tests passed, including bearing-frame
math, parallel/past/future geometry, finite horizon, depth allowance math, stale
traffic, unknown port services and API authorization/scope/revision checks.
Browser checks passed replay, three telemetry event categories, six-minute CPA,
persistence, absence of control commands and mobile layout.

## Sensor uncertainty strengthening

Optional sensor-error inputs now support 100–1,000 reproducible perturbations per
valid target. Bearing, range, course and speed errors are explicit. Reports show
P05/median/P95 future minimum separation, closest-time ranges, sampled minimum,
inside-threshold fraction and classification instability. Nominal-only snapshots
are labeled. Review summaries highlight missing traffic/depth and clearance gaps.
Sampling uses independent uniform errors, nonnegative range/speed clipping and
angular wraparound. These are model assumptions, not sensor calibration or
collision probabilities; sampled minima are not rigorous worst-case bounds.
Four maritime tests and the browser replay/mobile/persistence check passed.
