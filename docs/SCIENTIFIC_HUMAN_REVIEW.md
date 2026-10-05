# Scientific inquiry with human authority

The user-supplied “Scientific Decision-Making in Minds and Algorithms” text
informed this workflow. Its bibliography and empirical claims have not been
independently verified by this implementation. The generated research digest is
not reproduced in the release.

## Use Human review

Choose a decision, open **Human review**, write your independent assessment and
select a specific advisory result. Inspect the advice, then explicitly choose
**Accept**, **Reject**, **Request changes**, or **Defer**. No response is selected
by default. Record your reason, evidence checked, uncertainty and circumstances
that would change your mind. The optional preferred option can differ from the
comparison's highest-scoring option.

A later response changes the displayed latest response while preserving earlier
records. Reviews belong to one decision revision and the exact inquiry or saved
comparison reviewed. Updated decisions need new reviews. A request for changes
records the person's response; it does not automatically rewrite the model.

In the local workspace the reviewer name is self-reported. In the authenticated
workspace an approver or administrator role is required and the signed identity
overrides the supplied name. Reader/editor roles cannot record acceptance or
rejection. Acceptance does not execute actions, grant permissions, establish
truth, or override the separate action-governance system.

## Ideas mapped to the architecture

| Idea | Implementation | Boundary |
|---|---|---|
| Human qualitative judgment plus calculation | Independent assessment alongside preserved comparison inputs/results | Scores are supplied assessments, not calibrated probabilities |
| Scientific inquiry under uncertainty | Evidence/contradiction, alternative-explanation and falsification prompts | Prompts do not discover unknown variables automatically |
| Test and learn | Existing Labs hypotheses, experiments, actual outcomes and prediction errors; review conditions recorded here | Review dates/conditions are text, not scheduled notifications |
| Context and human values | Existing stakeholder/value model plus explicit uncertainty/context review | No guarantee that affected people are represented |
| Avoid uncritical acceptance or rejection of algorithms | Independent-assessment field precedes advice; explicit choice and rationale | No empirical claim that this interface removes cognitive bias |
| Final human authority | Advice-specific acceptance/rejection/defer/change requests, signed attribution and preserved history | No real-world execution enabled |
| Bayesian learning and constrained calculation | Existing intelligence and simulation kernels remain available | No new cognitive model, reinforcement-learning agent or clinical validation |

Implementation: `services/human_review.py`, `services/studio.py`,
`services/review.py`, `web/human-review.js`. Both local and authenticated APIs
reuse the judgments endpoint; workspace and decision-brief exports include the
human-control projection and review history.

Remaining research work includes calibrated trust/outcome studies, live provider
evaluation, learning from sufficient behavioral data and domain-specific external
validation. Unresolved questions remain explicit rather than being marked solved.

## Mental models — completed 2026-09-30

Human review now includes optional expectations, failure boundaries, comparable
examples, observed outcomes with source notes, and changes in understanding.
These fields are persisted with each review and included in review history and
JSON decision briefs. Earlier records remain readable with missing fields.
Advice snapshots include plain-language behavior notes and illustrative failure
cases for inquiry prompts and weighted comparisons. Examples are hypothetical,
not retrieved evidence. Later reviews let people document learning without
rewriting earlier judgments. All existing revision, tenant and role checks apply.

The user-supplied Mental Models digest informed these workflow choices. Its
research claims and references were not independently verified or reproduced.
This implementation does not infer a person's cognition, measure calibrated
trust, learn a cognitive model, or establish improved team performance. Outcome
notes are self-reported; use the existing experiment workflow for measured data.
