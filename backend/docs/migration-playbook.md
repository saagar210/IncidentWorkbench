# Expand/Contract Playbook

1. Expand
Add nullable/new columns, add new indexes, and deploy dual-write code paths.

2. Backfill
Use bounded batch jobs with checkpoints, retries, and metrics.

3. Switch reads
Flip read path behind a feature flag after backfill verification.

4. Contract
Drop deprecated columns only after at least one full release cycle and rollback window.

5. Reversibility
Every migration must include a rollback/fallback strategy unless explicitly approved.
