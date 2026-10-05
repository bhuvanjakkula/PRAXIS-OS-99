# CEO, CFO and CTO professional workspaces

All three workspaces run locally, save their inputs and outputs with the decision
revision and accept arbitrary industry names. Sources, assumptions, monetary
unit, period and applicable industry/internal requirements are explicit inputs.
Defaults in forms are examples; they must be replaced with measured inputs.

CEO support computes normal/adverse revenue, operating costs, contribution,
operating result and net result after the declared investment. Break-even and
investment-recovery customer counts round up and are unavailable for nonpositive
contribution. These period economics do not model multi-year returns or discounting.

CFO support accepts 1–36 monthly cash-flow pairs. It computes normal/adverse
cash trajectories, their minima including opening cash, first adverse reserve
breach (month 0 means opening cash) and funding gap. Adverse inflows/outflows use
declared proportional changes. Financing, tax and interest are not invented.

CTO support computes observed time-based availability, permitted downtime,
remaining downtime budget, request failure rate, cost per capacity unit and
normal/adverse load-to-capacity ratios. Failed requests cannot exceed requests;
downtime cannot exceed the measurement period. Request rates and time availability
remain separate. Utilization is not a latency or queueing forecast.

Sector review prompts cover manufacturing, technology, retail, healthcare,
financial services, energy, construction, logistics, agriculture, education,
hospitality, professional services and the public sector. Other industry names
remain accepted, with a prompt to define relevant metrics and obligations.
These prompts do not establish regulatory compliance or specialist expertise.

Each professional workspace now has an explicit sector selector with 14 built-in
sectors including finance/financial services and real estate, plus Other/custom.
The shared packaged sector catalog provides different CEO, CFO and CTO focus
areas, evidence needs and planning questions. Selection fills the industry field
and updates the context without replacing entered financial or technical values.
Custom names remain supported. Saved analyses preserve the role/sector profile
and can be filtered by sector. Sector selection does not invent measurements or
alter numerical formulas. Finance aliases resolve to Financial services in
backend profiles; earlier plans without profiles remain readable.

The sector catalog now includes 46 specific professional areas, each with separate
CEO, CFO and CTO focus, measurement and evidence prompts. Examples include banking,
insurance, payments and investment management; software, cybersecurity, cloud and
hardware; automotive, electronics, textiles and food processing; and residential,
commercial, industrial and development property. Other sectors have their own
area lists. Users can also explicitly enter a custom area.

An optional professional_area and custom_area flag are saved with plans. Backend
validation rejects predefined areas outside the selected sector. Saved reports
retain the area-specific role profile; old plans without area fields still work.
These planning prompts supplement the existing numerical tools. They do not add
specialist numerical models, inferred measurements or regulatory determinations.
Tests cover role-specific area guidance, mismatches, custom areas and browser
selection, saving, reload persistence and mobile layout.

Saved role-specific plans show conditional warnings, numerical tables/charts,
evidence, information gaps and suggested next steps. They can be exported as JSON.
A handoff button loads professional criteria into Decision compute, where users
supply option scores and constraints for simulation, exact interval optimization,
scenario comparisons and observed-score feedback. No external action is executed.

Access controls and revision checks match the existing authenticated API. Tests
cover arithmetic, invalid observations, roles, tenants, revision conflicts and
saved history. Browser checks cover every role, persistence after reload,
role-specific compute criteria and mobile layout.
