# Space–air–ground signed manifest prototype

Extends the working PQC primitives with ML-DSA-65 signed route manifests and the
distinct signature context `PRAXIS-SAGIN-MANIFEST-v1`. Manifests bind sender,
receiver, route, tiers, sequence, validity, selected mode and policy. A verifier
uses separately pinned public keys and separately pinned sender/route policies.
The message cannot replace either trust configuration.

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[pqc]"
.\.venv\Scripts\python.exe -m praxis.security.sagin
```

The local demo creates ephemeral keys, verifies a synthetic ground/air/space route
manifest and rejects a replay. No keys or signatures are printed.

Policies: `pqc_only`, `qkd_required`, `qkd_with_pqc_fallback`. QKD-required manifests
cannot select PQC. QKD selections are always rejected because no physical QKD
capability exists in this prototype. Explicit fallback policy permits the local
PQC manifest test; it does not automatically establish a channel or execute a route.
No QBER measurement, quantum key pool, entanglement routing, teleportation or
satellite/aircraft link is simulated as a real capability.

The supplied research summary (`3e6b9ae3-2f21-4e47-a8ab-6a0261b6c090`) informed
multi-tier scope and explicit fallback policy. Its study-specific distances,
rates, fidelity and effectiveness were not independently verified or used as
product performance claims.

## Practical limits

This is a signed application-record component, not a standardized secure transport
protocol. It does not encrypt payloads, authenticate a network session, establish
forward secrecy or implement routing. Replay state is in memory, single-threaded
and lost on restart; durable atomic sequence storage and trusted time are required
before remote use. Out-of-order manifests are rejected. Keys must be enrolled and
rotated through a reviewed trust process. The manifest validity limit is a local
prototype design choice, not an aerospace standard.

The prototype does not authorize flight/space operations. Existing Praxis identity
and transport configuration remain separate. Published conformance vectors,
external protocol interoperability and target-device assurance remain pending.
# Node compromise containment

For supplied-input MTU, storage, outage-horizon and configured revocation/session
limit checks, see [Recovery resource review](RECOVERY_BUDGET.md). This advisory
planner is separate from key authorization and checkpoint verification.

## Operator-pinned signing-key lifetimes

Construct `ManifestVerifier(..., require_key_lifetimes=True)` to require a trusted
operator validity window for each sender. `set_key_lifetime(sender, not_before,
expires_at)` pins integer timestamps with an inclusive start and exclusive end.
Verification rejects a key outside this window, a manifest extending beyond it,
or a missing authorization in strict mode, without advancing replay state.
The caller supplies trusted time; this module does not obtain or synchronize it.

Key replacement removes the previous lifetime authorization. Strict mode therefore
requires a fresh window before the replacement key can accept traffic. Signed
checkpoints preserve both strict mode and lifetime windows, including quarantined
nodes. Lifetime changes are operator actions and require explicit checkpointing.
The default remains optional for compatibility with existing local callers.

These are signing-key authorization windows. They do not generate session keys,
implement self-healing group-key distribution, or establish forward secrecy.

## Signed revocation checkpoints

`save_checkpoint(verifier, path, operator_signer, generation)` writes an ML-DSA-65
signed snapshot containing public node keys, isolation reasons, route policies,
epochs and replay floors. It flushes a temporary file and atomically replaces the
destination. No node or operator private key is included. `load_checkpoint(path,
operator_verifier, receiver, minimum_generation)` verifies the signature, pinned
receiver, strict schema and generation floor before constructing a new verifier.
Unsigned, modified, wrong-receiver and older-than-floor snapshots are rejected.

The operator signing key must be independent of compromised node keys. The caller
must maintain the generation floor in a separate trusted store; a signature alone
cannot detect replacement with an older correctly signed snapshot. Explicitly save
after revocation, policy updates, key replacement and accepted traffic before relying
on restart durability. These functions do not automatically checkpoint each mutation,
coordinate multiple writers or broadcast revocation. Preserve strict mode and protect
the checkpoint directory with operating-system access controls.

Revocation modifies verifier state without rewriting stored application records.
It does not cancel existing transport sessions, rekey encrypted group traffic,
remove previously obtained plaintext, or provide forward/backward secrecy. Checkpoint
integration into a live controller remains pending.

## Capacity-aware topology planning

`ManifestVerifier.plan_failover(nodes, links, demands)` takes the verifier's current
quarantine snapshot and excludes edges touching those isolated nodes. Directed
links carry capacity and existing load; demands reserve residual capacity in caller
priority order. The planner chooses deterministic shortest feasible paths and
reports unmet demands when isolation or capacity prevents routing. It never exceeds
supplied link capacities or modifies caller data. It is a greedy advisory planner,
not a globally optimal allocator or a physical cascade simulator.

Capacity and load must use matching units and come from trusted, fresh measurements.
Only additional or already removed traffic should be submitted as demands, because
existing loads remain reserved. No split flows, preemption, node processing-capacity
model, automatic repair, malicious-behavior detection or live routing changes are
implemented. Plans need fresh validation and authenticated execution by a real
network controller. Isolation state is local and volatile. This prototype does not
guarantee network survival, consensus, uptime or prevention of cascading collapse.

## Dynamic policy switching

`switch_route_policy(sender, route_id, policy)` is a trusted local operator action.
It increments the pinned route's policy epoch and requires a new signed manifest
containing that epoch. It preserves sequence floors, rejects isolated nodes, and
does not resume traffic or generate session keys. Switching back to an earlier
policy still requires a new epoch. QKD-required requests fail closed because no
QKD provider exists. Policy updates are not accepted from peer manifests.

`max_manifest_lifetime` pins an accepted validity window from 1 to 3600 seconds.
For example, use 60 seconds for short-lived manifest authorization. This bounds
manifest validity, not the lifetime of a signing key or an established session.
An attacker with an active signing key can issue new manifests until isolated.

Manifests now include signed `policy_epoch` (initially zero). Older signatures
must be regenerated because the canonical signed content has changed. Epochs,
isolation and replay floors are volatile; durable authenticated state is required
before production deployment. This prototype does not claim session key rotation,
handover key agreement, forward secrecy or post-compromise recovery.

The local verifier supports trusted-operator `isolate(sender, reason)` and
`replace_isolated_key(sender, public_key)` controls. Isolation rejects even correctly
signed manifests. Recovery requires a different pinned ML-DSA-65 key and preserves
the sender's sequence floors. Unaffected senders retain their own route policies.
These controls are in-memory prototype state: a restart loses isolation and replay
state. Production use requires persistent authenticated revocation, coordinated
distribution, operator authorization, session termination and audit records.
No live network node or aircraft is controlled by this module.

Hybrid key exchange does not itself prevent compromise of an endpoint holding both
keys. Hardware attestation and QKD require real trusted provider integrations;
neither is simulated as successful authentication. No automatic reinforcement-learning
route execution, uptime guarantee or post-compromise recovery guarantee is claimed.
See [NIST hybrid guidance](https://csrc.nist.gov/Projects/Post-Quantum-Cryptography/faqs)
and [NSA QKD limitations](https://www.nsa.gov/Cybersecurity/Quantum-Key-Distribution-QKD-and-Quantum-Cryptography-QC/).
