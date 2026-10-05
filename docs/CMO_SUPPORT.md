# CMO decision support

Open **CMO support**, or launch the studio with `/#cmo`, and select a decision.
Enter any company name and sector, from solo businesses to enterprises. The
workspace supports business, consumer, government and mixed buyer models.

Define the offer, target customer, value proposition, differentiation, measurement
window, currency and attribution cohort. Supply distinct channel cohorts with
leads, qualified leads, opportunities, acquired customers and allocated spend.
The illustrative example is fictional and must be replaced before reliance.

Saved plans show funnel conversion, channel and blended acquisition cost,
break-even customers and finite-horizon contribution after acquisition. Recurring
offers use monthly price less monthly delivery cost with geometric retention;
one-time offers use one sale. Onboarding is deducted once. The adverse case reduces
customer wins with acquisition spend held fixed. Missing denominators display
“Not available”; this model does not estimate causal attribution or market benchmarks.

Strategy prompts cover positioning, bounded channel experiments, sales enablement,
small-company focus and enterprise coordination. Intelligence subscriptions,
reports, data APIs and analytics software receive additional paid-pilot guidance
and checks for data provenance, rights, coverage, security, licensing and renewal.
These prompts require evidence and human review. No campaigns or purchases execute.

Export an individual plan as JSON or select **Compare marketing options** to load
CMO criteria into Decision compute. Saved plans remain tied to their decision
revision. Authenticated deployments require editor permission and enforce tenant
isolation. The endpoint is `POST /v2/decisions/{identifier}/marketing-support`.

No OpenAI call is required for this feature. The existing explicitly invoked AI
analysis remains available when the operator configures its provider.

## Alignment, shared metrics and continuity

Enable the optional execution review to add owned actions, KPI freshness checks,
leadership continuity and budget/capacity-constrained initiative comparisons.
See [Leadership execution](LEADERSHIP_EXECUTION.md).
