from __future__ import annotations
from .models import DecisionRequest, DecisionAnalysis, OptionResult


def _normalized_weights(weights):
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()}


def analyze(req: DecisionRequest) -> DecisionAnalysis:
    weights = _normalized_weights(req.weights)
    results = []
    for option in req.options:
        by_dim = {c.dimension: c for c in option.criteria}
        base = 0.0
        confidence_gap = 0.0
        evidence_count = 0
        contributions = {}
        for dim, weight in weights.items():
            c = by_dim.get(dim)
            if not c:
                confidence_gap += weight
                contributions[dim] = 0.0
                continue
            contribution = weight * c.score
            base += contribution
            confidence_gap += weight * (1 - c.confidence)
            evidence_count += len(c.evidence)
            contributions[dim] = contribution

        risk_adjusted = base - abs(base) * req.uncertainty_penalty * confidence_gap
        scenario_scores = {}
        for scenario in req.scenarios:
            s = base
            for dim, shock in scenario.dimension_shocks.items():
                s += weights.get(dim, 0.0) * shock
            scenario_scores[scenario.name] = round(s, 3)

        weakest = [k for k, _ in sorted(contributions.items(), key=lambda x: x[1])[:3]]
        results.append(OptionResult(
            option_id=option.id,
            option_name=option.name,
            base_score=round(base, 3),
            risk_adjusted_score=round(risk_adjusted, 3),
            scenario_scores=scenario_scores,
            weakest_dimensions=weakest,
            evidence_count=evidence_count,
        ))

    # Sorting is analytical convenience, not a political endorsement.
    results.sort(key=lambda x: x.risk_adjusted_score, reverse=True)
    return DecisionAnalysis(
        question=req.question,
        country_code=req.context.country_code.upper(),
        results=results,
        caveats=[
            "Scores reflect user-supplied objectives, weights, inputs, and assumptions; they are not objective political truth.",
            "A higher analytical score is not an instruction to adopt a policy; accountable officials must review legality, rights, distributional effects, evidence quality, and dissent.",
            "Missing criteria are treated conservatively as zero contribution with low confidence.",
            "Production use requires independent validation, security review, audit logging, access controls, and jurisdiction-specific legal/constitutional review.",
        ],
        method="Weighted multi-criteria analysis with confidence penalty and scenario shocks",
    )
