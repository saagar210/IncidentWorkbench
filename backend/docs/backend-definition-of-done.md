# Backend Definition Of Done

## API DoD
- [ ] OpenAPI updated and lint clean.
- [ ] Request and response validation enforced at boundary.
- [ ] Non-2xx responses use `application/problem+json`.
- [ ] Versioning/deprecation policy documented for changed endpoints.
- [ ] Idempotency requirements defined for unsafe writes.

## Database DoD
- [ ] Migration follows expand/contract or has approved exception.
- [ ] Index and constraint changes reviewed for lock/runtime risk.
- [ ] Rollback/fallback strategy documented.
- [ ] Transaction boundaries explicit for multi-step writes.
- [ ] Data retention and PII handling documented for changed data.

## Auth DoD
- [ ] Auth model selected with threat-model rationale.
- [ ] Session/token lifecycle includes revocation behavior.
- [ ] Permission checks deny by default and are test covered.
- [ ] Sensitive cookies/tokens use secure storage + transport settings.
- [ ] Auth failure paths do not leak sensitive detail.

## Integration DoD
- [ ] Outbound calls have timeout, bounded retry, and jitter policy.
- [ ] Webhooks verify signature and dedupe by delivery ID.
- [ ] Queue/DLQ behavior defined for failed processing.
- [ ] Secrets sourced from secret manager or secure env injection.
- [ ] External dependency contracts are stubbed/mocked in tests.

## Reliability DoD
- [ ] Liveness/readiness endpoints implemented.
- [ ] Graceful shutdown drains in-flight work safely.
- [ ] Backpressure or queue limits defined.
- [ ] Connection pool limits defined and load-tested.
- [ ] Retry policy avoids amplification during dependency outages.

## Observability DoD
- [ ] Structured logs include request and trace correlation fields.
- [ ] Traces cover request path and critical background jobs.
- [ ] Core SLI metrics emitted (latency, error rate, saturation).
- [ ] Alerts include runbook links and noise controls.
- [ ] Incident triage can link logs, traces, and request IDs quickly.
