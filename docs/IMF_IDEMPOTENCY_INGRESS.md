# Idempotency ingress and legitimate repetition

Integrated 5 October 2026. Most supplied themes overlap existing retry, checkpoint and conflict reviews. New evidence areas are webhook-event review and legitimate business-repeat review. Either note enables both reviews plus links to idempotency conflicts, cross-channel traces and settlement status.

Review webhook signature/raw-body validation, timestamp policy, secret rotation, duplicate event identifiers, ordering and authoritative state confirmation. Separately identify technical retries versus new purchases and document intent-key ownership, scope, downstream propagation and tests. A valid signature is not proof that an event is unique, newest or financially settled. Similar payloads may represent legitimate repeated purchases; automatic payload-only deduplication can suppress them.

The supplied percentages and universal exactly-once/elimination claims are not adopted as product guarantees. A provider's published API behavior does not establish its internal gateway/database architecture. Byzantine payment protocols rely on explicit fault models and are not substitutes for validating a bank integration. Original summary prose and figures are not reproduced.

This implementation saves evidence and flags gaps. It introduces no webhook endpoint, signature verifier, business-intent deduplication or payment integration. Webhook authenticity and exactly-once execution remain unverified.
Primary implementation references: Stripe webhook guidance (https://docs.stripe.com/webhooks) and idempotent requests (https://docs.stripe.com/api/idempotent_requests). Verify current provider semantics before implementing any live adapter.
