# Stage-aware retry and DLQ review

Integrated 5 October 2026 from supplied research leads. Existing checkpoint, idempotency and recovery reviews cover most themes. Added notes review retry budgets and DLQ replay. Either note enables both checks plus links to checkpoint atomicity, key conflicts/expiry and authoritative settlement evidence.

Retry review records one accountable retry layer, fault classification, stage evidence, attempt/deadline limits, jitter/backoff and downstream load budgets. DLQ review records quarantine reason, retention, schema/version repair, key expiry, unknown outcomes, ordering, replay rate and verified closure. Neither a queue move nor a repaired message proves the original side effect did not occur.

A DLQ isolates failures; it does not guarantee completion. Replaying after deduplication retention expires can repeat external effects. Checkpoint recovery must consider the crash between a remote effect and local state persistence. A universal 24–48 hour deduplication period is not assumed: provider retention and maximum recovery horizon need explicit alignment. Nested retries can amplify load, so bounded retry ownership requires testing.

The supplied performance percentages and universal exactly-once claims remain unverified research leads and are not product guarantees. This release saves evidence and flags gaps; it adds no retry executor, DLQ, redrive operation or payment integration. Replay authorization and exactly-once verification remain false. Original narrative and figures are not reproduced.
Primary references: AWS SQS DLQ guidance (https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) and SDK retry behavior (https://docs.aws.amazon.com/sdkref/latest/guide/feature-retry-behavior.html) document queue retention/redrive and bounded backoff/jitter behavior. These are design references, not an AWS integration.
