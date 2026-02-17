# Backend Reliability Contract (Codex)

## Scope
Applies to backend changes in `/backend`: API, auth, DB schema/migrations, background jobs, external integrations, observability, and security.

## Mandatory sequence
1. Run a spec pressure test (security + data + contract + failure modes).
2. Implement the minimal safe change.
3. Run the read-only reviewer agent and collect findings.
4. Run the fixer agent on accepted findings (highest severity first).
5. Re-run reviewer + required gates in `.codex/verify.commands`.

## Blocking conditions
- Any failing required gate blocks completion.
- Any open critical/high review finding blocks completion.
- Any migration that skips expand/contract safety checks on live tables blocks completion.

## No-silent-risk policy
If verification cannot run, completion is blocked unless a temporary waiver includes owner, mitigation issue, and expiry <= 7 days.

## Worktree policy
Use a dedicated worktree for any change touching auth, migrations, queue/webhook logic, or more than 3 backend files.

## Definition of Done: Tests + Docs (Blocking)

- Any production code change must include meaningful test updates in the same PR.
- Meaningful tests must include at least:
  - one primary behavior assertion
  - two non-happy-path assertions (edge, boundary, invalid input, or failure mode)
- Trivial assertions are forbidden (`expect(true).toBe(true)`, snapshot-only without semantic assertions, render-only smoke tests without behavior checks).
- Mock only external boundaries (network, clock, randomness, third-party SDKs). Do not mock the unit under test.
- UI changes must cover state matrix: loading, empty, error, success, disabled, focus-visible.
- API/command surface changes must update generated contract artifacts and request/response examples.
- Architecture-impacting changes must include an ADR in `/docs/adr/`.
- Required checks are blocking when `fail` or `not-run`: lint, typecheck, tests, coverage, diff coverage, docs check.
- Reviewer -> fixer -> reviewer loop is required before merge.
