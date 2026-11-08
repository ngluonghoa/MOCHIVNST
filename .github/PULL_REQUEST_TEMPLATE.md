<!-- MOCHIVNST PR-001 — Atomic Pull Request & Independent Rollback. -->
<!-- Each PR covers ONE independently testable and revertible work item. -->

## PR-001 — One purpose / Một mục tiêu

**Work item / milestone ID:** `...`

**One-sentence objective:** ...

**Why this is one independently reviewable and testable unit:** ...

## Scope and dependencies

**In-scope paths / behavior:** ...

**Explicitly out of scope:** ...

**Dependencies on other PRs (number + required merge order; or None):** ...

**Compatibility or migration impact (including API, data, DB schema and cache; or None):** ...

## Acceptance and QA evidence

**Acceptance criteria (including negative/failure cases):**
- [ ] ...

**Test evidence:**
- [ ] Tests run locally or synthetic (commands + results)
- [ ] Python 3.11 / 3.12 GitHub Actions checks (run URLs + exact head SHA)
- [ ] Negative, boundary and regression cases appropriate to this change
- [ ] Source / dependency / rights or security checks as applicable
- [ ] Independent reviewer checked whether scope is truly atomic

**Before merge:**
- [ ] Branch is current with protected `main`, no base SHA drift
- [ ] All required checks PASS; no CI or branch-protection bypass
- [ ] Owner and scoped writer lease were verified under the canonical gate
- [ ] Reviewer evaluated the actual diff, not just this checklist

## Independent rollback

**Squash commit / PR link (fill after merge):** ...

**Exact revert steps / rollback trigger:** ...

**If data/schema/cache/remote rights changed, independent recovery or migration plan:** ...

**How rollback and restore will be validated:** ...

## Traceability and handoff

**Master Spec / Charter / ADR IDs:** ...

**QA / acceptance receipt / CI links:** ...

**Master Handoff section / revision:** ...

**Main SHA before and after merge (record after merge):** ...

## Exceptional non-atomic scope (normally leave blank)

**Owner-approved exception receipt and rationale:** None

**Why it cannot be split into smaller PRs:** N/A

**Documented extra blast-radius and rollback controls:** N/A

---

**Required policy:** One Pull Request = one clear objective that can be independently reviewed, tested, accepted, deployed and reverted. Do not combine unrelated features or changes. Split large work into ordered PRs with explicit dependencies. Merge to `main` using **Squash only**. An exception requires explicit project-owner approval and a recorded reason.

**Safety note:** Git revert cannot undo external data migration, irreversible broker side effects, or already-consumed events. Describe a separate restore strategy whenever those apply. CI checks can verify the presence of fields, not whether a PR is semantically atomic or remotely authorized; that requires independent review and enforced credentials.
