"""PRAXIS APEX Engine: Game Theory (Nash/Maximin/Minimax Regret),
Bayesian Value of Information (EVPI/EVSI), Fat-Tail CVaR Stress Testing,
and Tamper-Evident SHA-256 Merkle Decision Seals.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ApexRequest(BaseModel):
    base_version: int = Field(default=1, ge=1)
    scenario_name: str = Field(default="Strategic Market Entry", min_length=1, max_length=200)
    player_strategies: list[str] = Field(..., min_length=2, max_length=6)
    adversary_strategies: list[str] = Field(..., min_length=2, max_length=6)
    # Row = player strategy, Col = adversary strategy
    player_payoffs: list[list[float]]
    adversary_payoffs: list[list[float]]
    # Prior probabilities over adversary/world states (must match len(adversary_strategies))
    state_priors: list[float] | None = None
    signal_accuracy: float = Field(default=0.80, ge=0.5, le=0.99)
    information_cost: float = Field(default=15.0, ge=0.0)
    shock_volatility: float = Field(default=0.25, ge=0.01, le=2.0)
    tail_jump_probability: float = Field(default=0.08, ge=0.0, le=0.5)
    tail_jump_severity: float = Field(default=0.45, ge=0.05, le=0.95)
    ruin_threshold: float = Field(default=0.0)
    samples: int = Field(default=2000, ge=200, le=10000)
    seed: int = Field(default=42)


def _normalize_priors(priors: list[float] | None, n: int) -> list[float]:
    if not priors or len(priors) != n:
        return [1.0 / n] * n
    cleaned = [max(0.0, float(p)) for p in priors]
    total = sum(cleaned)
    if total <= 0:
        return [1.0 / n] * n
    return [p / total for p in cleaned]


def _solve_game_theory(
    p_names: list[str],
    a_names: list[str],
    A: list[list[float]],
    B: list[list[float]],
) -> dict[str, Any]:
    m, n = len(p_names), len(a_names)

    # 1. Pure-Strategy Nash Equilibria
    col_best_for_p = [max(A[i][j] for i in range(m)) for j in range(n)]
    row_best_for_a = [max(B[i][j] for j in range(n)) for i in range(m)]
    pure_nash = []
    for i in range(m):
        for j in range(n):
            if math.isclose(A[i][j], col_best_for_p[j], rel_tol=1e-9, abs_tol=1e-9) and math.isclose(
                B[i][j], row_best_for_a[i], rel_tol=1e-9, abs_tol=1e-9
            ):
                pure_nash.append(
                    {
                        "player_strategy": p_names[i],
                        "adversary_strategy": a_names[j],
                        "player_payoff": round(A[i][j], 4),
                        "adversary_payoff": round(B[i][j], 4),
                    }
                )

    # 2. Mixed-Strategy Equilibrium (exact 2x2 closed-form, else fictitious play)
    mixed_p = [1.0 / m] * m
    mixed_a = [1.0 / n] * n
    mixed_method = "fictitious_play_3000"
    if m == 2 and n == 2:
        denom_q = (A[0][0] - A[1][0] - A[0][1] + A[1][1])
        denom_p = (B[0][0] - B[0][1] - B[1][0] + B[1][1])
        if abs(denom_q) > 1e-9 and abs(denom_p) > 1e-9:
            q0 = (A[1][1] - A[0][1]) / denom_q
            p0 = (B[1][1] - B[1][0]) / denom_p
            if 0.0 <= q0 <= 1.0 and 0.0 <= p0 <= 1.0:
                mixed_p = [p0, 1.0 - p0]
                mixed_a = [q0, 1.0 - q0]
                mixed_method = "exact_2x2_indifference"
    if mixed_method != "exact_2x2_indifference":
        counts_p = [1.0] * m
        counts_a = [1.0] * n
        for _ in range(3000):
            tot_a = sum(counts_a)
            qa = [c / tot_a for c in counts_a]
            best_i = max(range(m), key=lambda i: sum(A[i][j] * qa[j] for j in range(n)))
            counts_p[best_i] += 1.0
            tot_p = sum(counts_p)
            pp = [c / tot_p for c in counts_p]
            best_j = max(range(n), key=lambda j: sum(B[i][j] * pp[i] for i in range(m)))
            counts_a[best_j] += 1.0
        tot_p, tot_a = sum(counts_p), sum(counts_a)
        mixed_p = [c / tot_p for c in counts_p]
        mixed_a = [c / tot_a for c in counts_a]

    expected_mixed_payoff = sum(
        mixed_p[i] * mixed_a[j] * A[i][j] for i in range(m) for j in range(n)
    )

    # 3. Maximin (Wald) & Minimax Regret (Savage)
    row_mins = [min(A[i]) for i in range(m)]
    maximin_idx = max(range(m), key=lambda i: row_mins[i])

    regret_matrix = [[col_best_for_p[j] - A[i][j] for j in range(n)] for i in range(m)]
    max_regrets = [max(regret_matrix[i]) for i in range(m)]
    minimax_regret_idx = min(range(m), key=lambda i: max_regrets[i])

    # 4. Strictly dominated strategies
    dominated = []
    for i in range(m):
        for k in range(m):
            if i != k and all(A[k][j] > A[i][j] for j in range(n)):
                dominated.append({"strategy": p_names[i], "dominated_by": p_names[k]})
                break

    return {
        "pure_nash_equilibria": pure_nash,
        "mixed_strategy_equilibrium": {
            "method": mixed_method,
            "player_weights": {p_names[i]: round(mixed_p[i], 4) for i in range(m)},
            "adversary_weights": {a_names[j]: round(mixed_a[j], 4) for j in range(n)},
            "expected_player_payoff": round(expected_mixed_payoff, 4),
        },
        "maximin_robust": {
            "strategy": p_names[maximin_idx],
            "worst_case_payoff": round(row_mins[maximin_idx], 4),
        },
        "minimax_regret": {
            "strategy": p_names[minimax_regret_idx],
            "maximum_regret": round(max_regrets[minimax_regret_idx], 4),
            "regret_matrix": [[round(v, 4) for v in row] for row in regret_matrix],
        },
        "strictly_dominated": dominated,
    }


def _solve_bayesian_voi(
    p_names: list[str],
    a_names: list[str],
    A: list[list[float]],
    priors: list[float],
    signal_accuracy: float,
    info_cost: float,
) -> dict[str, Any]:
    m, n = len(p_names), len(a_names)
    ev_by_option = [sum(priors[j] * A[i][j] for j in range(n)) for i in range(m)]
    best_prior_idx = max(range(m), key=lambda i: ev_by_option[i])
    ev_without_info = ev_by_option[best_prior_idx]

    # EVPI: Expected Value with Perfect Information
    ev_perfect = sum(priors[j] * max(A[i][j] for i in range(m)) for j in range(n))
    evpi = max(0.0, ev_perfect - ev_without_info)

    # EVSI: Symmetric noisy signal P(signal=s | state=j) = acc if s==j else (1-acc)/(n-1)
    off_diag = (1.0 - signal_accuracy) / max(1, n - 1)
    ev_with_sample = 0.0
    for s in range(n):
        joint = [priors[j] * (signal_accuracy if s == j else off_diag) for j in range(n)]
        p_signal = sum(joint)
        if p_signal <= 0:
            continue
        post = [x / p_signal for x in joint]
        best_post_ev = max(sum(post[j] * A[i][j] for j in range(n)) for i in range(m))
        ev_with_sample += p_signal * best_post_ev

    evsi = max(0.0, ev_with_sample - ev_without_info)
    net_voi = evsi - info_cost

    if net_voi > 0:
        recommendation = "INVEST_IN_EVIDENCE_FIRST"
        rationale = f"Expected Value of Sample Information ({round(evsi, 2)}) exceeds acquisition cost ({round(info_cost, 2)}) by +{round(net_voi, 2)}."
    else:
        recommendation = "ACT_ON_CURRENT_PRIORS"
        rationale = f"Information cost ({round(info_cost, 2)}) exceeds EVSI ({round(evsi, 2)}); execute '{p_names[best_prior_idx]}' directly."

    return {
        "best_prior_strategy": p_names[best_prior_idx],
        "expected_values": {p_names[i]: round(ev_by_option[i], 4) for i in range(m)},
        "ev_without_info": round(ev_without_info, 4),
        "ev_with_perfect_info": round(ev_perfect, 4),
        "evpi": round(evpi, 4),
        "evsi": round(evsi, 4),
        "information_cost": round(info_cost, 4),
        "net_value_of_information": round(net_voi, 4),
        "recommendation": recommendation,
        "rationale": rationale,
    }


def _solve_tail_risk_cvar(
    p_names: list[str],
    A: list[list[float]],
    priors: list[float],
    volatility: float,
    jump_prob: float,
    jump_severity: float,
    ruin_threshold: float,
    samples: int,
    seed: int,
) -> dict[str, Any]:
    rng = random.Random(seed)
    n = len(priors)
    cdf = []
    acc = 0.0
    for p in priors:
        acc += p
        cdf.append(acc)

    def sample_state() -> int:
        u = rng.random()
        for idx, cut in enumerate(cdf):
            if u <= cut:
                return idx
        return n - 1

    profiles = []
    for i, name in enumerate(p_names):
        outcomes = []
        ruin_count = 0
        for _ in range(samples):
            st = sample_state()
            base = A[i][st]
            scale = max(abs(base), 10.0)
            shock = rng.gauss(0.0, volatility * scale)
            jump = -abs(jump_severity * scale) if rng.random() < jump_prob else 0.0
            val = base + shock + jump
            outcomes.append(val)
            if val < ruin_threshold:
                ruin_count += 1
        outcomes.sort()
        mean_val = sum(outcomes) / samples
        var_idx = max(0, int(0.05 * samples) - 1)
        var_95 = outcomes[var_idx]
        tail_slice = outcomes[: max(1, var_idx + 1)]
        cvar_95 = sum(tail_slice) / len(tail_slice)
        p50 = outcomes[samples // 2]
        p95 = outcomes[min(samples - 1, int(0.95 * samples))]
        ruin_prob = ruin_count / samples
        # Fragility score 0 (antifragile) to 100 (extreme fragility)
        downside_spread = max(0.0, mean_val - cvar_95)
        fragility = min(100.0, max(0.0, ruin_prob * 65.0 + (downside_spread / max(abs(mean_val), 10.0)) * 25.0))
        profiles.append(
            {
                "strategy": name,
                "mean": round(mean_val, 3),
                "median": round(p50, 3),
                "p95_upside": round(p95, 3),
                "var_95": round(var_95, 3),
                "cvar_95": round(cvar_95, 3),
                "ruin_probability_pct": round(ruin_prob * 100.0, 2),
                "fragility_score": round(fragility, 1),
            }
        )

    safest = max(profiles, key=lambda x: x["cvar_95"])
    return {
        "samples": samples,
        "seed": seed,
        "ruin_threshold": ruin_threshold,
        "safest_tail_strategy": safest["strategy"],
        "profiles": profiles,
    }


def _build_merkle_seal(payload: dict[str, Any]) -> dict[str, Any]:
    leaves = []
    for key in sorted(payload.keys()):
        raw = json.dumps({key: payload[key]}, sort_keys=True, separators=(",", ":")).encode("utf-8")
        leaves.append(hashlib.sha256(raw).hexdigest())
    level = list(leaves)
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else left
            nxt.append(hashlib.sha256((left + right).encode("utf-8")).hexdigest())
        level = nxt
    merkle_root = level[0] if level else hashlib.sha256(b"").hexdigest()
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    return {
        "algorithm": "SHA-256-MERKLE-V1",
        "merkle_root": merkle_root,
        "payload_sha256": digest,
        "leaf_count": len(leaves),
        "sealed_at": datetime.now(timezone.utc).isoformat(),
    }


def run_apex_analysis(studio: Any, decision_id: UUID, body: ApexRequest) -> dict[str, Any]:
    revision = studio.loop.latest(decision_id)
    m = len(body.player_strategies)
    n = len(body.adversary_strategies)
    if len(body.player_payoffs) != m or any(len(row) != n for row in body.player_payoffs):
        raise ValueError(f"player_payoffs must be a {m}x{n} matrix matching strategies.")
    if len(body.adversary_payoffs) != m or any(len(row) != n for row in body.adversary_payoffs):
        raise ValueError(f"adversary_payoffs must be a {m}x{n} matrix matching strategies.")

    priors = _normalize_priors(body.state_priors, n)
    game_theory = _solve_game_theory(
        body.player_strategies,
        body.adversary_strategies,
        body.player_payoffs,
        body.adversary_payoffs,
    )
    voi = _solve_bayesian_voi(
        body.player_strategies,
        body.adversary_strategies,
        body.player_payoffs,
        priors,
        body.signal_accuracy,
        body.information_cost,
    )
    tail_risk = _solve_tail_risk_cvar(
        body.player_strategies,
        body.player_payoffs,
        priors,
        body.shock_volatility,
        body.tail_jump_probability,
        body.tail_jump_severity,
        body.ruin_threshold,
        body.samples,
        body.seed,
    )

    core_output = {
        "decision_id": str(decision_id),
        "decision_version": revision.version,
        "scenario_name": body.scenario_name,
        "priors": [round(p, 4) for p in priors],
        "game_theory": game_theory,
        "bayesian_voi": voi,
        "tail_risk_cvar": tail_risk,
    }
    seal = _build_merkle_seal(core_output)

    return studio._record(
        decision_id,
        revision.version,
        "apex_analysis",
        {
            "inputs": body.model_dump(mode="json"),
            "analysis": {
                **core_output,
                "cryptographic_seal": seal,
            },
        },
    )
