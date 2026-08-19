# Human-over-the-Loop Failure Analysis Loop V1

**Status:** Permanent workflow rule
**Scope:** AgentFactory governance, CI, data, evidence, and agentic workflow failures

## 1. Purpose

When a material problem occurs, the agent must not immediately patch the visible symptom. The workflow must establish a repeatable human-over-the-loop (HOTL) correction cycle.

## 2. Three-cycle rule

For each material failure or unexpected result:

```text
Problem observed
  ↓
Cause analysis
  ↓
Countermeasure proposed
  ↓
Countermeasure implemented
  ↓
Regression / execution result
  ↓
Human review
  ↓
Solved?
  ├─ YES → rule-gap review
  └─ NO  → next RCA cycle
```

Run up to **3 RCA/remediation cycles** before escalating to a broader architectural review.

A cycle is complete only when the proposed countermeasure has been tested against the failure case.

## 3. What each cycle must record

- observed problem;
- failed invariant or expected condition;
- root-cause classification;
- proposed countermeasure;
- implementation/change;
- regression or execution evidence;
- human review result;
- remaining risk;
- next action.

## 4. Human review boundary

The agent may diagnose, propose, implement, and run regression tests within its authorized scope.

The human reviewer decides whether:

- the problem is actually solved;
- the evidence is sufficient;
- the residual risk is acceptable;
- a governance rule should change;
- the change is safe to promote.

The agent must not infer human approval from a passing local test or from absence of an error.

## 5. Rule-update review after resolution

When a problem is solved, perform a separate rule-gap review:

```text
Solved
  ↓
Could this happen again?
  ↓
  YES → propose permanent rule / regression seed / automation
  NO  → record lesson only
```

A permanent rule is promoted only when there is:

```text
lesson
→ proposed rule
→ regression witness
→ execution evidence
→ human review
→ governance update
```

## 6. Escalation after three cycles

If three cycles do not solve the problem, do not continue blind retries.

Classify the issue as one or more of:

- specification problem;
- architecture problem;
- implementation problem;
- data/provenance problem;
- evidence/execution problem;
- environment/tooling problem;
- human decision required.

Then stop the downstream gate and request targeted human review.

## 7. Fail-closed rule

No failure-analysis cycle may convert missing evidence into PASS/GREEN.

`REVIEW_REQUIRED` and `BLOCKED` remain valid outcomes.

## 8. Relationship to existing workflow

This rule extends the existing:

`VERIFY → DIAGNOSE → REPAIR → REGRESS → EVIDENCE → PROMOTE`

workflow by adding explicit human review and a three-cycle escalation boundary.

It does not authorize OPRO promotion, GEPA implementation, domain implementation, OOS, optimization, stress, or Monte Carlo before their independent gates are satisfied.
