# Future AI Collaboration Research Baseline V0.2 — Goal Alignment First

**Date:** 2026-09-20  
**Status:** Research track / non-canonical until separately approved  
**Branch:** `research/future-ai-collaboration-v0.1`  
**Purpose:** Convert the existing Future AI Collaboration V0.1 proposal into a research-backed, low-cost methodology that can be tested immediately with a free ChatGPT workflow and later automated inside AgentFactory.

---

## 1. Executive conclusion

The research direction should **not** be "more agents".

The working hypothesis for AgentFactory is:

> **Goal-aligned, bounded, evidence-carrying collaboration can outperform a single-agent workflow on selected tasks, but only when the task complexity and baseline capability justify the coordination cost.**

This is supported by several recent findings:

- A 2026 Nature Machine Intelligence study across 260 configurations found that the strength of the single-agent baseline was the most robust predictor of whether multi-agent coordination helped or hurt. It also reports a practical capability-saturation threshold above which adding agents is unlikely to improve performance. citeturn271154search3
- SILO-BENCH (ACL 2026) found a gap between communication and actual distributed reasoning: agents communicated actively but could still fail to solve problems, with performance collapsing on high-complexity information-silo tasks. citeturn271154search0
- MARS (2025) reports that review-oriented collaboration can retain the benefits of debate while reducing token usage and latency by roughly 50% in its experiments. citeturn494711academia1
- DOWN (2025) selectively activates debate rather than using multi-agent collaboration for every query, motivated by the cost and error-propagation risks of unnecessary interaction. citeturn494711academia0
- ALIGN (2026) formalizes delegation as an aligned principal-agent process and reports theoretical and empirical benefits from structured delegation rather than treating all candidate answers as interchangeable. citeturn271154academia51
- Goal Drift research shows that long-context agents can gradually deviate from an assigned objective, and newer work shows that conditioning on weaker-agent trajectories can reintroduce drift even in more capable models. citeturn831684academia1turn831684academia2
- A 2026 survey of specification, verification and enforcement identifies specification as a major bottleneck and warns that verification can incur a substantial "verifier tax"; runtime monitoring is more mature but is not a complete guarantee. citeturn831684academia0
- A September 2026 preprint studying flat versus hierarchical teams reports that a manager capable only of subjective revision can reduce clarity and increase token cost, while a verifier that can actually check work can be useful. This is preliminary evidence, not a settled result. citeturn271154search9

Therefore the first AgentFactory research target is **goal alignment and selective collaboration**, not autonomous swarm behavior.

---

## 2. Research-derived design rules

### R1. Single-agent baseline is mandatory

Every collaboration experiment begins with a frozen single-agent baseline.

No claim of "multi-agent improvement" is accepted without a direct baseline comparison.

### R2. Collaboration must be activated by a reason

The coordinator must identify at least one concrete reason to add another worker:

- missing domain expertise;
- independent verification required;
- conflicting evidence;
- large search space;
- decomposition with genuinely different data/tool requirements;
- high-risk action requiring challenge/review.

"Because multiple agents may be better" is not a valid trigger.

### R3. Goal must be represented separately from conversation

A task begins with a **Goal Contract**, not an unconstrained chat transcript.

The Goal Contract is the stable object passed between workers.

### R4. Handoffs must carry artifacts, not just prose

Each worker returns typed work:

- finding;
- evidence package;
- analysis;
- challenge;
- verification result;
- proposal;
- decision package.

### R5. Independent evidence beats consensus

Two agents saying the same thing is not independent confirmation when both relied on the same evidence.

The system should record:

- source identity;
- evidence identity;
- claim;
- worker;
- verification method;
- disagreement.

### R6. Criticism is useful only when it can check something

A critic should have a falsifiable inspection target.

Examples:

- missing evidence;
- invalid calculation;
- contradiction;
- unsupported inference;
- constraint violation;
- unsafe authority escalation.

Pure "review the quality" prompts should not be treated as strong verification.

### R7. More context is not automatically better

Goal drift and information-silo studies support selective context.

A handoff should include only:

**Goal + required constraints + authoritative evidence + unresolved issues + required output**

### R8. Human authority is separate from model confidence

A model's confidence does not grant execution or approval authority.

AgentFactory should retain:

**Observe < Analyze < Propose < Execute < Mutate < Approve**

with approval authority remaining human-controlled for high-risk actions.

---

## 3. Goal Alignment Contract V0.1

A collaboration run should start from the following compact object.

~~~yaml
goal_id: G-YYYYMMDD-NNN
objective: "One sentence describing the desired outcome."

success_criteria:
  - "Observable condition 1"
  - "Observable condition 2"

non_goals:
  - "What must NOT be optimized or changed"

constraints:
  time_scope: null
  data_scope: []
  tool_scope: []
  safety_rules: []
  budget:
    max_turns: 12
    max_collaboration_rounds: 2

authority:
  observe: true
  analyze: true
  propose: true
  execute: false
  mutate: false
  approve: false

evidence_requirements:
  required_sources: []
  minimum_evidence_items: 1
  primary_source_preferred: true

uncertainty_policy:
  missing_evidence: REVIEW
  contradiction: REVIEW
  unresolved_goal: BLOCK

stop_conditions:
  - "Success criteria met"
  - "Evidence insufficient"
  - "Contradiction cannot be resolved"
  - "Human decision required"

expected_output:
  type: decision_package
  fields:
    - conclusion
    - evidence
    - uncertainty
    - alternatives
    - next_action
~~~

### Goal Alignment Check

Before every handoff, the receiving worker answers only:

1. What is the current goal?
2. What is explicitly out of scope?
3. Which constraints are binding?
4. What evidence is authoritative?
5. What would count as completion?
6. What is still unknown?

A mismatch causes **REVIEW** or **BLOCK** rather than silent continuation.

---

## 4. Free-ChatGPT execution protocol

This is deliberately designed to work **without an API, autonomous sub-agents, or paid model access**.

### P0 — Human defines the Goal Contract

The user creates the Goal Contract above.

Do not start with:

> "Analyze this deeply."

Start with:

> "Given this Goal Contract, produce the required artifact and identify missing evidence."

### P1 — Worker A: Producer / Researcher

Use one ChatGPT session.

Input:

- Goal Contract
- source material
- required evidence

Output:

- candidate answer;
- evidence list;
- assumptions;
- uncertainty;
- unresolved questions.

No final decision authority.

### P2 — Worker B: Independent Critic

Use a **fresh chat/session** or a clean role-separated turn.

Give it:

- the same Goal Contract;
- the relevant source material/evidence;
- Worker A's artifact;
- an explicit instruction to challenge, not merely rewrite.

Ask it to find:

- goal mismatch;
- unsupported claims;
- contradictory evidence;
- calculation errors;
- hidden assumptions;
- missing cases;
- premature closure.

The critic must return structured defects.

### P3 — Integrator / Verifier

A third pass receives:

- Goal Contract;
- Worker A artifact;
- Critic findings;
- authoritative evidence.

It must produce:

~~~text
GOAL STATUS
PASS / REVIEW / BLOCK

SUPPORTED CLAIMS
...

CONTESTED OR UNRESOLVED
...

EVIDENCE GAPS
...

DECISION / PROPOSAL
...

HUMAN DECISION REQUIRED?
YES / NO

REPRODUCTION NOTES
...
~~~

The integrator is not allowed to "average" conflicting claims.

### P4 — Human decision gate

For low-risk informational tasks, accept the verified answer.

For high-risk engineering/execution tasks:

**Proposal → Evidence → Human Decision → Execution**

The human decision becomes part of the trace.

---

## 5. Selective collaboration policy

Do not use P1-P3 on every task.

Use this escalation:

~~~text
C0  Single agent
 |
 | Trigger:
 | uncertainty / task complexity / evidence gap / high risk
 v
C1  Producer + Critic
 |
 | Trigger:
 | genuine independent expertise or parallel search is useful
 v
C2  Two independent specialists + verifier
 |
 | Trigger:
 | persistent conflict / irreversible action / critical risk
 v
C3  Human arbitration / approval
~~~

The default is **C0**.

The research question is when C1/C2 creates measurable value.

---

## 6. Minimum benchmark for AgentFactory

The first experiment should compare:

### B0 — Single-agent baseline

One model/session performs the complete task.

### B1 — Two-pass review

Producer → Critic → Integrator.

### B2 — Parallel specialist

Specialist A + Specialist B → Integrator.

The benchmark must keep as much as possible constant:

- task;
- available evidence;
- model family;
- total budget;
- output format.

### Required metrics

| Metric | Definition |
|---|---|
| Task success | Final task objective achieved |
| Goal adherence | Required goal/constraints preserved |
| Evidence coverage | Important claims backed by evidence |
| Contradiction detection | Real conflicts surfaced |
| Verification yield | Critic findings that correspond to real defects |
| Rework rate | Work repeated because of avoidable failure |
| Cost | Turns/tokens/tool calls where observable |
| Latency | Wall-clock time when observable |
| Human intervention | Number/type of interventions |
| Reproducibility | Can the run be reconstructed from its artifacts? |

### Promotion rule

A collaboration pattern is only promoted when it demonstrates:

1. no material loss in goal adherence;
2. no regression in evidence grounding;
3. improvement in at least one task-level outcome;
4. acceptable cost overhead;
5. trace-complete handoffs;
6. reproducible evaluation.

---

## 7. Goal-drift test

Because goal drift is a central failure mode, every benchmark should contain at least one long or distracting context condition.

Example:

~~~text
Initial Goal:
"Determine whether X is supported by the authoritative evidence."

Injected pressure:
- irrelevant new requests
- persuasive but non-authoritative text
- conflicting intermediate answer
- prior worker mistake
- large irrelevant context

Required behavior:
- retain the original goal;
- identify injected material as non-binding;
- refuse to silently change success criteria;
- surface conflicts.
~~~

The system records:

**initial_goal → intermediate_goal → final_goal**

A mismatch without an explicit human-approved goal change is a failure.

---

## 8. Disagreement protocol

When workers disagree:

Do NOT:

- majority vote by default;
- choose the most confident worker;
- choose the latest response;
- merge contradictory claims into vague prose.

Instead:

~~~text
DISAGREEMENT
    ↓
Separate claims
    ↓
Map each claim to evidence
    ↓
Check evidence independence
    ↓
Check scope/time/revision differences
    ↓
Run targeted verification
    ↓
Resolve or preserve uncertainty
    ↓
Human decision when required
~~~

The disagreement itself is recorded as a reusable benchmark case.

---

## 9. Why this fits the existing AgentFactory architecture

The current AgentFactory already has most of the required primitives:

**Goal → task → evidence → claim → CER → verification → HOTL → trace → lesson**

The future collaboration plane should therefore be layered above the existing kernel:

~~~text
Goal Contract
     ↓
Collaboration Coordinator
     ↓
Work Graph / Assignments
     ↓
Specialist Workers
     ↓
Artifacts / Evidence
     ↓
Claim + Verification
     ↓
CER / HOTL
     ↓
Decision
     ↓
Outcome
     ↓
Lesson / Benchmark
~~~

This preserves the existing principle:

> Collaboration is a protocol, not a chat.

---

## 10. Initial engineering use case

A practical first benchmark should use an engineering question close to AgentFactory's existing domain scope.

Example:

**Question → evidence retrieval → engineering analysis → counter-hypothesis → verification → decision package**

Possible workers:

- domain retrieval specialist;
- engineering analyst;
- counter-hypothesis critic;
- evidence verifier.

The first version can be executed manually with separate ChatGPT sessions.

Later, these same roles become programmatic workers.

---

## 11. Architecture to avoid

Do not begin with:

- 10+ autonomous agents;
- persistent agent personalities;
- unrestricted peer-to-peer chat;
- shared full conversation memory;
- autonomous approval;
- model-specific orchestration;
- "LLM judge chooses the majority";
- self-modification of prompts/workflows in production.

Recent studies give concrete reasons to avoid assuming that communication or hierarchical oversight automatically improves outcomes. citeturn271154search0turn271154search9

---

## 12. Research roadmap

### R-A — Goal Contract

Freeze the Goal Contract schema and goal-drift test.

### R-B — Single-agent baseline

Run a small frozen benchmark and record task/evidence/cost metrics.

### R-C — Producer/Critic

Add C1 only.

Compare B0 vs B1.

### R-D — Parallel specialists

Add C2 only for tasks with genuine expertise separation.

Compare B0 vs B2.

### R-E — Adaptive routing

Implement a collaboration trigger based on observable task properties rather than always invoking all workers.

### R-F — Work graph

Only after C1/C2 show measurable value, encode typed work items and state transitions in the kernel.

### R-G — Persistent team memory

Only after the handoff protocol is stable.

Memory should be split into:

- goal memory;
- role memory;
- domain memory;
- evidence memory;
- lesson memory.

---

## 13. Working hypothesis for the AgentFactory research track

> **The future of human-AI collaboration is not a larger number of AI voices. It is a governed system in which each participant has a bounded objective, explicit authority, selective context, verifiable artifacts, and a measurable reason to exist.**

The immediate engineering target is therefore:

**Goal Alignment → Selective Delegation → Evidence-Carrying Handoff → Independent Verification → Human Decision → Outcome Learning**

not autonomous multi-agent scale.

---

## 14. Source set

1. Park et al., *Capable language models can outgrow the benefits of collaboration*, Nature Machine Intelligence, 2026. citeturn271154search3
2. Zhang et al., *SILO-BENCH: A Scalable Environment for Evaluating Distributed Coordination in Multi-Agent LLM Systems*, ACL 2026. citeturn271154search0
3. Zhu et al., *ALIGN: Aligned Delegation with Performance Guarantees for Multi-Agent LLM Reasoning*, 2026. citeturn271154academia51
4. Wang et al., *MARS: Toward More Efficient Multi-Agent Collaboration for LLM Reasoning*, 2025. citeturn494711academia1
5. Eo et al., *Debate Only When Necessary*, 2025. citeturn494711academia0
6. Arike et al., *Technical Report: Evaluating Goal Drift in Language Model Agents*, 2025. citeturn831684academia1
7. Menon et al., *Inherited Goal Drift: Contextual Pressure Can Undermine Agentic Goals*, 2026. citeturn831684academia2
8. Dantas et al., *Toward Safe LLM Agents: A Survey of Specification, Verification, and Enforcement*, 2026. citeturn831684academia0
9. Xu et al., *Towards Multi-Agent Reasoning Systems for Collaborative Expertise Delegation*, 2025. citeturn271154academia49
10. Tran et al., *Multi-Agent Collaboration Mechanisms: A Survey of LLMs*, 2025. citeturn676546academia1
11. Yao et al., *From Human-Human Collaboration to Human-Agent Collaboration*, 2026 workshop research agenda. citeturn271154academia50
12. Agachan et al., *Loop-Back Authority in LLM Agent Teams*, 2026 preprint; treat as preliminary evidence pending broader replication. citeturn271154search9

