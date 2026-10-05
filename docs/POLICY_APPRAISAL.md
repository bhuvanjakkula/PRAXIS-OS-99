# National policy computation engine

Optional appraisal adds six neutral review lenses: economic efficiency,
distributional consequences, rights/lawful authority, institutional feasibility,
international obligation compatibility, and uncertainty/reversibility. Website
labels contain no thinkers' or advisers' names. This is a selected set of
operational frameworks, not an exhaustive encoding of political, legal or
economic scholarship.

Every existing decision alternative supplies upfront cost, annual benefit/cost
low/likely/high ranges, economic/review references, distributional impacts and
six review gates. The horizon is 1–30 years, discount rate 0–50%, adverse benefit
reduction 0–100% and adverse cost increase 0–100%. Annual cash flows are constant
and occur at year end. All inputs share the plan's monetary unit.

The engine computes discounted net present value, exact independent interval
bounds, benefit/cost ratio, adverse NPV and worst-case regret. Zero-cost ratios
are undefined rather than infinite. Ties are retained. Gate failures or unknowns
and failed/unknown stored decision constraints exclude implementation candidates
from ranking; their economics remain inspectable. Worst-case regret excludes
self-comparison. Range-stable leaders require at least two eligible alternatives.

Group benefits, burdens, mixed impacts and unknowns retain their evidence and
are reviewed separately. No invented welfare weights cancel rights or burden
assessments. A supplied pass is not certification. Monetary benefit is not GDP
growth. No legal system, treaty interpretation or macroeconomic behavior is
inferred from a country name.

General method references: [regulatory impact assessment principles](https://www.oecd.org/en/publications/regulatory-impact-assessment_7a9638cb-en.html)
support alternatives, benefit/cost analysis and monitoring. [Economic analysis
handbook](https://ppp.worldbank.org/public-private-partnership/sites/ppp.worldbank.org/files/2022-05/Handbook-Economic-Analysis-Investment-Operations.pdf)
discusses uncertainty, sensitivity and switching values. These references inform
the design; they do not validate this software or its user-supplied evidence.

Tests verify analytic discounting, endpoint bounds, adverse arithmetic, regret,
ties, zero-cost ratios, gate/constraint exclusions, distribution flags, current
option matching, input immutability and saved browser results. No external
policy action is executed.
