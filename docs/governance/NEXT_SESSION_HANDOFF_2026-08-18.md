# AgentFactory Next Session Handoff — 2026-08-18

## Objective

Resume governed work without relying on prior chat history as canonical state. First repair and verify continuity identity/evidence, then continue the financial-information M1-B gate.

## Canonical state

Read first, in order:

1. `docs/governance/CURRENT_SESSION_STATE.yaml`
2. `docs/governance/CER_SESSION_CONTINUITY_CONTRACT_V1.md`
3. `schemas/session_state.schema.yaml`
4. `docs/governance/NEXT_SESSION_HANDOFF_2026-08-18.md`
5. `docs/governance/CER_SESSION_CLOSURE_2026-08-18_SESSION_CONTINUITY.md` only if needed
6. `docs/governance/CER_OPRO_GEPA_LESSONS_2026-08-18.md` when performing lesson-based workflow improvement

## Repository

- repository: `chayobi03-cyber/agent-factory`
- branch: `p0/opro-baseline`
- audited OPRO baseline SHA: `20a54b92aad0857f75c6200d984b13098c6f4927`
- latest durable checkpoint anchor: `16972e2fa29496731319f088907170d93961ae48`

## Resume Contract

A new session MUST NOT execute `next_action` until RC-01..RC-08 are verified.

```text
state → Git identity/ancestry → handoff → audited baseline → gate/constraints → required context/evidence
```

### Mandatory resume checks

1. state `working_branch` == actual Git branch/ref;
2. actual HEAD satisfies state checkpoint ancestry/relation;
3. state audited baseline == immutable audited baseline;
4. state checkpoint and handoff checkpoint are consistent;
5. handoff repository/branch agree with Git;
6. handoff audited baseline agrees with immutable baseline;
7. gate and forbidden actions are consistent;
8. required CER/schema/evidence context exists and is version-compatible.

Any identity contradiction is `RESUME_BLOCKED`. Missing runtime evidence or environment ambiguity is `INCONCLUSIVE`, not PASS.

## Immediate next-session workflow

### Phase A — Continuity remediation

1. Read canonical state and handoff.
2. Confirm state/handoff checkpoint identity and ancestry.
3. Confirm actual branch/ref and HEAD through primary Git evidence.
4. Locate the current push-triggered GitHub Actions run for the current branch.
5. Capture:
   - run ID;
   - workflow name;
   - event;
   - branch/ref;
   - commit SHA;
   - RC-01..RC-08 results;
   - overall resume result;
   - pytest result;
   - machine evidence artifact ID/name;
   - failure/inconclusive details.
6. Verify the evidence belongs to the same commit/ref being resumed.
7. Only if all RC-01..RC-08 are PASS and evidence is primary/executable: set `RESUME_ALLOWED`.

### Phase B — M1-B source decision

Only after `RESUME_ALLOWED`:

1. Discover a bounded candidate set of financial data sources.
2. Score candidates on authority, historical depth, corporate actions, PIT capability, API stability, licensing, reproducibility, cost, and operational burden.
3. Apply hard gates first; optimize only among hard-gate-valid candidates.
4. Select the minimum sufficient source stack; avoid unnecessary provider proliferation.
5. Record rationale and rejected alternatives.

### Phase C — M1-B evidence build

1. Select five real historical series.
2. Preserve raw responses/data.
3. Record source, endpoint/query, retrieval time, parameters, version/identifier, and provenance.
4. Compute content hashes.
5. Re-ingest/replay where practical to test reproducibility.
6. Cross-source reconcile with explicit tolerances and discrepancy classification.
7. Establish PIT evidence and identify survivorship/look-ahead risks.
8. Emit machine-verifiable evidence.
9. Run M1-B gate and classify `GREEN` / `NOT_GREEN` / `INCONCLUSIVE`.

## OPRO/GEPA methodological guardrails

Do NOT implement GEPA or promote OPRO in this phase. Use their methodological lessons only:

- OPRO: optimize verified useful progress subject to hard governance constraints.
- GEPA: diagnose failure, preserve the case as a regression seed, propose a targeted improvement, and promote only after evidence.
- Never optimize an aggregate score across a hard-gate failure.
- Keep workflow alternatives explicit when multiple designs are viable.
- Prefer small, reversible governance changes with deterministic witnesses.

Reference: `docs/governance/CER_OPRO_GEPA_LESSONS_2026-08-18.md`.

## CHECKPOINT trigger

Checkpoint immediately after any of these:

- state/handoff identity is repaired;
- CI evidence is captured;
- a gate changes status;
- source-stack decision is made;
- an evidence schema/provenance contract changes;
- a material regression case is added.

Checkpoint sequence:

`Execute → Capture → Verify → Classify → CER CHECK → Update State/Handoff → Git Commit`

## CLOSE trigger

At session end:

`Execute → Capture → Verify → Classify → CER CHECK → Update State/Handoff → Git Commit`

The closure must record lessons, distinguish permanent rules from task-level guidance, and preserve unresolved issues as explicit next actions.

## Absolute constraints

- GEPA implementation forbidden.
- RE Domain implementation forbidden.
- OPRO promotion forbidden.
- Audited baseline SHA must not change.
- PASS without primary execution evidence forbidden.
- Backtest forbidden before M1-B GREEN.
- OOS forbidden before M1-B GREEN.
- Optimization forbidden before M1-B GREEN.
- Monte Carlo forbidden before M1-B GREEN.

## Context minimization

Use progressive disclosure:

`state → resume checks → relevant handoff → relevant evidence → targeted Git history`

Do not replay the entire prior conversation.

## Definition of success for next session

The session succeeds only if it produces either:

1. `RESUME_ALLOWED` backed by primary CI/Git evidence and then advances M1-B; or
2. a precise, machine-verifiable remediation package explaining why resume remains blocked.

Never convert an unavailable or stale execution result into PASS merely to maintain workflow momentum.
