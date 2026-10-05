"""Deterministic review of supplied decision data; never invent missing evidence."""


def decision_review(decision):
    assumptions = list(dict.fromkeys([
        *decision.assumptions,
        *[e.statement for e in decision.evidence if e.kind.value == "assumption"],
        *[a for option in decision.options for a in option.assumptions],
    ]))
    gaps = []
    for label, value in [
        ("Evidence sources", [e for e in decision.evidence if e.source]),
        ("Stakeholders", decision.stakeholders), ("Alternatives", decision.options),
        ("Human values", decision.values), ("Explicit assumptions", assumptions),
        ("Expected benefits", decision.expected_benefits),
        ("Known uncertainties", decision.uncertainties),
    ]:
        if not value:
            gaps.append(label + " not supplied")
    return {
        "expected_benefits": decision.expected_benefits,
        "critical_assumptions": assumptions,
        "known_uncertainties": decision.uncertainties,
        "reversibility": decision.reversibility,
        "missing_information": gaps,
        "epistemic_counts": {kind: sum(e.kind.value == kind for e in decision.evidence)
                             for kind in ("fact", "inference", "assumption", "prediction", "human_judgment", "hypothesis", "value")},
        "coverage_prompt": "What important variable might our model be missing?",
        "human_judgment_required": True,
        "scientific_review_prompts": [
            "What is your own assessment before considering the system's advice?",
            "Which observations support the proposal, and which contradict it?",
            "What alternative explanation or missing variable could change the conclusion?",
            "Does this model fit the present context, including affected people's values?",
            "What small, reversible test could distinguish the alternatives?",
            "What observable result would make you reconsider, and when will you review it?",
        ],
        "scope": "Completeness checks on supplied inputs; not independent verification or a recommendation.",
    }
