# Free ChatGPT Collaboration Protocol V0.1

**Purpose:** Run the AgentFactory future-collaboration method with a free ChatGPT account before building API-level orchestration.

## 1. Operating model

Use three clean roles:

1. **Producer** — solves the task from evidence.
2. **Critic** — independently attacks the producer's result.
3. **Integrator** — reconciles only from the Goal Contract + evidence + critique.

Use a fresh chat for the Critic when possible. The point is not that a fresh chat makes the model independent in a formal statistical sense; it reduces conversational anchoring.

## 2. Goal Contract prompt

Copy the following at the beginning of a task:

~~~text
You are operating under a Goal Contract.

OBJECTIVE:
[one sentence]

SUCCESS CRITERIA:
1. [...]
2. [...]

NON-GOALS:
1. [...]
2. [...]

CONSTRAINTS:
- time scope: [...]
- evidence scope: [...]
- tools allowed: [...]
- prohibited actions: [...]

AUTHORITY:
- analyze: yes
- propose: yes
- execute: no
- mutate: no
- approve: no

EVIDENCE RULE:
Use authoritative evidence where available.
Do not turn uncertainty into confidence.
Distinguish evidence, inference, and assumption.

STOP CONDITIONS:
- success criteria are met
- evidence is insufficient
- evidence conflicts and cannot be resolved
- human decision is required

Before solving, restate the objective, non-goals, and success criteria in a compact form.
If they are internally inconsistent, return REVIEW rather than silently changing them.
~~~

## 3. Producer prompt

~~~text
ROLE: Producer / Researcher

Using ONLY the Goal Contract and supplied evidence:

1. solve the task;
2. map important claims to evidence;
3. state assumptions explicitly;
4. identify uncertainty;
5. identify unresolved questions.

Return:

GOAL_STATUS:
SUPPORTED_CLAIMS:
EVIDENCE:
ASSUMPTIONS:
UNCERTAINTIES:
UNRESOLVED:
PROPOSED_RESULT:

Do not request additional agents.
Do not claim verification you did not perform.
~~~

## 4. Critic prompt

~~~text
ROLE: Independent Critic / Red Team

You are not the author of the result.
Your job is to find reasons the result may be wrong.

Given:
- Goal Contract
- source evidence
- Producer artifact

Check:

1. goal drift;
2. constraint violations;
3. unsupported claims;
4. evidence mismatch;
5. contradictory evidence;
6. hidden assumptions;
7. calculation or logical errors;
8. omitted counterexamples;
9. premature closure;
10. unauthorized action recommendations.

For every defect return:

DEFECT_ID:
SEVERITY: LOW / MEDIUM / HIGH / CRITICAL
CLAIM:
PROBLEM:
EVIDENCE:
REPAIR_REQUIRED:

If no defect is found, say:
NO_DEFECT_FOUND

Do not rewrite the entire answer.
~~~

## 5. Integrator prompt

~~~text
ROLE: Integrator / Verifier

You receive:
- Goal Contract
- Producer artifact
- Critic artifact
- authoritative evidence

Your task is NOT to average opinions.

For every disputed claim:
1. separate the claims;
2. map each claim to evidence;
3. check whether evidence is independent;
4. check scope, time, revision, and assumptions;
5. resolve only what the evidence resolves;
6. preserve uncertainty where it remains.

Return exactly:

GOAL_STATUS: PASS / REVIEW / BLOCK

SUPPORTED_CLAIMS:
- claim
- evidence_ref

DISPUTED_OR_UNRESOLVED:
- issue
- reason

EVIDENCE_GAPS:
- [...]

FINAL_RESULT:
[...]

HUMAN_DECISION_REQUIRED: YES / NO

AUTHORITY_CHECK:
- no unauthorized execution or mutation

REPRODUCTION_NOTES:
- sources
- inputs
- important assumptions
~~~

## 6. Adaptive trigger

Do not automatically run all three roles.

Start with a single producer.

Trigger Critic when any of the following is true:

- task is high consequence;
- evidence is conflicting;
- uncertainty is material;
- the answer depends on a non-trivial calculation;
- the producer identifies a major unresolved issue;
- the task contains an adversarial or misleading context.

Trigger a second independent specialist only when the problem requires genuinely different expertise or information sources.

## 7. Manual handoff discipline

Never paste the entire previous conversation into the next role.

Pass:

~~~text
Goal Contract
+
Required evidence
+
Producer artifact
+
Unresolved items
~~~

This intentionally tests selective context transfer.

## 8. Minimal experiment log

For each run, record:

~~~yaml
run_id: ...
goal_id: ...
task_id: ...
configuration: C0 | C1 | C2
producer_result: ...
critic_result: ...
integrator_result: ...
goal_drift: PASS | FAIL
evidence_grounding: PASS | FAIL
task_success: PASS | FAIL
human_intervention: 0 | 1 | N
turns_observed: ...
notes: ...
~~~

## 9. First benchmark

Do not use an artificial question that is too easy.

Use 10-20 real engineering questions for which a human can define the expected evidence and acceptance condition.

Include:

- straightforward cases;
- evidence-conflict cases;
- missing-evidence cases;
- near-miss cases;
- misleading-context cases;
- calculation cases.

The benchmark must be frozen before comparing C0/C1/C2.

## 10. Decision rule

The question is not:

> Which configuration sounds better?

The question is:

> Does adding collaboration measurably improve the frozen benchmark while preserving goal adherence and evidence grounding at an acceptable cost?

Only measured evidence can move a collaboration pattern from research to implementation.

## 11. Free-tier practical constraints

The protocol intentionally avoids:

- autonomous sub-agent APIs;
- persistent model memory as a dependency;
- provider-specific orchestration;
- parallel API calls;
- paid model assumptions.

If the free account has a session or usage limitation, the same protocol can be continued by storing the Goal Contract and artifacts externally and resuming with those objects.

The method therefore tests the **protocol**, not the product tier.

## 12. Transition to AgentFactory

After manual experiments:

~~~text
Free ChatGPT roles
   ↓
Goal Contract
   ↓
Typed WorkItem
   ↓
Artifact schema
   ↓
Evidence binding
   ↓
Verifier
   ↓
CER
   ↓
HOTL
   ↓
Factory Runtime
~~~

Only the orchestration mechanism changes. The governance contract should remain stable.

