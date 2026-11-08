# P0 — MOCHIVNST control-ref / Google Drive trust boundary

Status: **DESIGN + REFERENCE TESTS ONLY / NOT DEPLOYED / REMOTE_ENFORCED=BLOCKED**.
This document is a scoped engineering contract, **not** an authorization credential.

## Current remote facts (2026-11-08)

- Canonical code repository: `ngluonghoa/MOCHIVNST`; `main` is protected by Ruleset **26791176**, with two required GitHub Actions checks.
- Control ref: `refs/heads/control/mochivnst-writer-gate`, at bootstrap SHA `90f74f5f182b6fd3ab3083a8235f100c833df8cd` at drafting; **not protected**. Its JSON record has `FROZEN`, `NOT_ACTIVE`, `permit_write=false`.
- Official owner: persistent generation 1, selected administratively by the user. The ChatGPT connector does **not** supply a verifiable per-conversation identity.
- Google Docs canonical lease uses revision-guarded CAS, but owner OAuth credentials remain shared between ChatGPT conversations; Drive owner-only sharing alone does not stop those chats from making direct edits.
- The tests in `tests/test_reference_authorizer.py` are synthetics; they do not prove that an uncooperative writer is actually denied by GitHub or Drive.

## Non-negotiable design

1. **Credential boundary:** a distinct, purpose-built GitHub App installation with the minimum repository permissions needed for the control ref; install ONLY on MOCHIVNST. GitHub App Contents write is repository-scoped, not inherently branch-scoped: therefore restrictions must be enforced in GitHub Rulesets, not inferred from token naming. The App private key and installation tokens must never be exposed to a ChatGPT conversation, GitHub repository file, PR runner or Google Doc.
2. **Separate trusted gateway:** Only an independently controlled service obtains App installation tokens and restricted Google Drive credentials, reads fresh GitHub and Google state, verifies authenticated operator authorization, issues/validates bounded signed intent, and performs expected-head Git CAS and revision-guarded Docs writes. Users/chats may submit requests but do not receive raw write tokens.
3. **Control branch Ruleset, only AFTER dedicated App works:** exact target `control/mochivnst-writer-gate` (NOT the default branch); Restrict updates, Restrict deletions, Block force pushes, and linear history. Add **only the dedicated GitHub App** as an Always-allow bypass actor for its direct atomic updates; no admin/shared ChatGPT app bypass. Do NOT require PR merges or CI on the control ref because the control path needs immediate compare-and-swap ref updates. Confirm an App bypass permits direct updates with `force=false` and expected SHA and that an ordinary actor receives a clear server-side denial before marking ready.
4. **Avoid self-deadlock:** never activate Restrict updates while the authorized App is absent or its token/CAS update unproven. If a rule blocks valid traffic, freeze, reconcile HEAD, repair under owner-approved incident procedure, re-test. Do not temporarily grant a bypass to shared owner/chat credentials just to make tests pass.
5. **Drive boundary:** project gate/Handoff must cease being directly editable by a shared ChatGPT OAuth owner credential. Use separately administered Workspace/shared-drive roles or an equivalent auditable owner-mediated writer with read-only user-facing connector and a separate write service. Consumer My Drive cannot be assumed to provide per-chat ACLs. Move/copy/transfer only with explicit owner approval, verified ownership and backup; never cut over based on a copied document ID alone.
6. **Authenticated requests:** project, owner generation, session, lease epoch, work item, short expiry, unique nonce, target ref, Docs revision, Git main/control SHA and action must be bound to a valid signature issued by the trusted gateway. The signing key is kept only in a secret manager. Replay consumption requires **durable atomic** storage (no in-memory set). Any missing, stale or conflicting evidence => deny.
7. **Trust boundary:** `governance/reference_authorizer.py` is a pure predicate for testing the contract, not a production HTTP endpoint. Passing its Python tests does not install any credential isolation. A caller could fabricate its snapshots unless they are fetched by the trusted gateway; a chat holding direct GitHub/Drive write credentials could bypass it.
8. **CI threat model:** Python 3.11/3.12 smoke jobs currently run from PR content. A PR author can potentially edit those jobs and tests; their success is not proof of independent trusted-governance validation. Before claiming hardened main, use a trusted, independently controlled check issuer, protected workflow/reusable workflow outside untrusted PR content, and server-enforced required status source. Verify negative forged-check attempts.

## Staged remote acceptance

- **Phase A — present:** main protection verified; Git control ref created but unprotected/frozen; synthetic reference verifier PR and negative-unit-tests only. Gate must remain frozen.
- **Phase B — manual security prerequisites:** register independent GitHub App and credential vault, isolate Docs write identity, create dedicated control ref Ruleset with exact branch match, verify role and App identity independently. Do not accidentally create the Ruleset inside MOCHIFX.
- **Phase C — actual writer gateway:** deploy gateway with verified actor identity, server-side signed-intent validation, fresh GitHub/Docs reads, atomic durable nonce storage, CAS updates, append-only receipts, revocation.
- **Phase D — negative acceptance:** run disposable independently credentialed tests for GOV-01..GOV-10/T01..T18; verify forbidden actors are actually refused on both GitHub and Google Docs with HTTP/log evidence, including old chat, discussion-only chat, cross-project identity and forged PR check. Main/control HEADs and production docs must be unchanged by every rejected attempt.
- **Phase E — owner signoff:** only after real negative tests and protected ACLs may control record switch to `ACTIVE` and `permit_write=true` via a guarded, audited transition.

No source-code import, market-data access, trading authority or release is authorized by this milestone.
