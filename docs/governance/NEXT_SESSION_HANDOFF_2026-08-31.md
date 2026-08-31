---
project_id: agent-factory
repository: chayobi03-cyber/agent-factory
branch: main
governance_namespace: AgentFactory
audited_baseline_sha: 20a54b92aad0857f75c6200d984b13098c6f4927
forbidden:
  - hosted_model_api_dependency
  - GEPA_implementation
  - OPRO_promotion
  # Time-bounded and discharged 2026-08-25: the Factory Kernel gate this was
  # waiting on is GREEN. Retained as the record of the bound, not a live ban.
  - RE_domain_implementation_until_kernel_gate
  - audited_baseline_redefinition
  - PASS_without_primary_execution_evidence
---
# AgentFactory Next Session Handoff — 2026-08-31

Supersedes `NEXT_SESSION_HANDOFF_2026-08-29.md`, which is retained as history.
`CURRENT_SESSION_STATE.yaml.handoff` names this file, and every validator
follows that pointer rather than a path of its own.

## Canonical identity
- project_id: `agent-factory`
- repository: `chayobi03-cyber/agent-factory`
- branch: `main`
- governance_namespace: `AgentFactory`

## Read this first: the 2026-08-31 work has no CI evidence

PR #39 **merged** — the SessionStart hook is on the trunk, so the verification
block at the bottom runs unchanged in a web session. That question from the
last handoff is closed.

The new one: the 2026-08-31 session ran entirely on `claude/audit-sgts3o` and
**never opened a pull request**. Neither workflow triggers on `claude/**`, so
every claim from that session is local execution evidence (E2) at best.

```bash
git log --oneline main..claude/audit-sgts3o   # non-empty = still unmerged
```

**First action: open a PR from that branch against `main`** and let the Factory
Kernel workflow run. Until it does, `EVIDENCE_UNAVAILABLE` applies to all of it
— including the 332 passing tests, which were run locally. Closure record:
`CER_SESSION_CLOSURE_2026-08-31_APF_AUDIT.md` §1.

## Where the work stands

Unchanged from 2026-08-29 on capability: M0 and M0.5 are closed and GREEN, M1
RE Hybrid RAG meets every PoC acceptance target against a synthetic corpus, six
domains ship as policy plus example documents, and routing works across all six.
**The 2026-08-31 session changed no kernel behaviour and no measured number.**

What changed is what the repository knows about itself.

An external specification package (*APF Living Specification vNext 0.1*) was
audited cold and rejected — RED as a specification. It marked seven of eight
hypotheses `OPEN` against evidence already in this tree. Auditing it turned up
four things that were true here and unwritten:

| | Finding | Where it lives now |
|---|---|---|
| 1 | Nothing fixed the boundary against external *capabilities* — agent runtimes, durable execution, telemetry. The domain boundary was fixed; this one was not. | `EXTERNAL_CAPABILITY_BOUNDARY_V1.md` |
| 2 | 58 declared schema field names are named nowhere outside `schemas/`, across 9 of 12 schema files. | `schemas/INDEX.md`, `scripts/audit_schema_bindings.py` |
| 3 | Run-layer durability does not exist. RC-01..RC-08 is *session* resume; `WorkflowRunState` is an in-memory dict, so `REVIEW_REQUIRED` cannot survive a restart. | **D-17** |
| 4 | LSN-0001 was never enforced, and recurred. | `scripts/verify_plan_baseline.py`, LSN-0003 |

## The one thing blocking progress

**Unchanged: the real RE corpus.** Every acceptance number is measured against
documents this repository wrote about itself. D-08 keeps the repository public,
so real RE reports and CISPR text cannot be committed; an out-of-tree corpus can
be loaded, but a benchmark measured against one is not re-derivable from the
commit SHA. Waiting on the internal handover.

Nothing from the 2026-08-31 session changes that, and nothing in it should be
read as progress toward it.

## Decisions waiting on a person

`OPEN_DECISIONS_2026-08-25.md` now runs **D-01..D-17**. D-01..D-10 resolved.

| | Open since | What it needs |
|---|---|---|
| D-11 | M1 | Near-miss abstention is not decidable by any lexical statistic. Waits on the real corpus. |
| D-12 | M1 | Three RE_POC requirements need a model dependency the kernel does not have. Option C closed permanently. |
| D-13, D-14 | routing / citation work | Closed, retained as record. |
| **D-15** | 2026-08-31 | Does the kernel earn its place above the substrates it replaces? Recommendation: answer per capability when one is in hand, not by building a benchmark first. D-17 is the first such occasion. |
| **D-16** | 2026-08-31 | `supersedes_revision_id`, `previous_decision_id`, `parent_fragment_id` — lineage declared three times, implemented never. Recommendation: populate where the supersession is real, i.e. on the real corpus, one relation at a time. |
| **D-17** | 2026-08-31 | Run-layer durability. Recommendation: a local run journal when HOTL gets its first non-demo consumer, not before. |

**Three lessons also await human review** — all `status: candidate`. See
`11_Audit/LSN-INDEX.md`. An agent may carry a lesson to execution evidence and
no further (`HOTL_FAILURE_ANALYSIS_LOOP_V1` §4).

## Still open from 2026-08-29, not addressed

> **`scripts/` resolves imports two different ways.** Six of the eight scripts
> insert the repository root on `sys.path` themselves. **`opro_baseline.py`**
> and **`domain_matrix_demo.py`** do not, and rely on the ambient `PYTHONPATH`
> that only `factory-kernel.yml` and the startup hook set. The hook fixes the
> symptom. Which convention wins is undecided: either those two self-bootstrap
> like the other six, or the other six drop their bootstrap and the env var
> becomes the single mechanism. It should not stay both.

Two scripts were added on 2026-08-31 (`audit_schema_bindings.py`,
`verify_plan_baseline.py`). Both avoid the question — neither imports from
`src/` — so the count is unchanged and the decision is still owed.

## What this codebase keeps teaching

The 2026-08-29 handoff counted this seven times: something declared that was
not what it said. The 2026-08-31 session found four more, and then found the
pattern had reached the lesson register itself.

- **Lineage declared three times, implemented never** — `supersedes_revision_id`,
  `previous_decision_id`, `parent_fragment_id`. D-14 stopped on what it read as
  missing corpus metadata; the schema for exactly that had been sitting
  unpopulated in `schemas/` the whole time.
- **A six-boolean `verification` block** in `claim_evidence.schema.yaml` —
  `domain_rule_passed`, `cross_method_passed`, `citation_locator_valid` — none
  of which exist in code.
- **The execution-evidence contract written twice**, in the schema and in the
  gate's own `REQUIRED` tuple, agreeing by coincidence with nothing binding them.
- **LSN-0001 itself.** It prescribed the check that would have caught its own
  recurrence, recorded `regression_guard: N/A (process lesson, not a code
  regression)`, and recurred. "Process lesson" described why it was unenforced,
  not why it was unenforceable.

The counter-instance is worth as much as the failures. **LSN-0002 held.** Its
rule — a fail-closed guard must be tested under every situation it actually runs
in — caught a defect in the guard being written to enforce LSN-0001, before that
guard shipped: it reported `BLOCKED` for any unresolvable baseline, which in a
shallow clone would have failed every handoff in this repository, since
`20a54b92` lies outside the default fetch depth.

The method is unchanged and it is the whole lesson: **run the thing and measure
it, rather than reading what it says about itself.** Three registers now have a
status index for exactly that reason — `docs/governance/INDEX.md`,
`schemas/INDEX.md`, `11_Audit/LSN-INDEX.md`.

## Governance
- Open decisions: `docs/governance/OPEN_DECISIONS_2026-08-25.md` (D-01..D-17)
- Session state: `docs/governance/CURRENT_SESSION_STATE.yaml`
- Governance index: `docs/governance/INDEX.md`
- Schema index: `schemas/INDEX.md`
- Lesson index: `11_Audit/LSN-INDEX.md`
- Capability boundary: `docs/governance/EXTERNAL_CAPABILITY_BOUNDARY_V1.md`
- Adding a domain: `docs/ADDING_A_DOMAIN.md`
- Context guard: `scripts/validate_project_context.py`
- Startup hook: `.claude/hooks/session-start.sh`, registered in `.claude/settings.json`
- Audited baseline SHA: `20a54b92aad0857f75c6200d984b13098c6f4927` — unchanged

## Primary evidence rule
Documentation and state are not execution evidence. A GREEN claim requires:
`target SHA -> workflow run -> job -> logs -> artifact -> GitHub digest -> independent verification`

Absence of a returned run is `EVIDENCE_UNAVAILABLE`, not inferred success.

Neither workflow triggers on a `claude/**` push — both are `push: [main]` and
`pull_request: [main]`. Work on a session branch carries no primary evidence
until a PR is opened against `main`. **That applies in full to the 2026-08-31
session.**

## Before adopting any incoming plan

New on 2026-08-31, and the reason LSN-0001 recurred is that this did not exist:

```bash
python3 scripts/verify_plan_baseline.py <the-document.md>
```

It answers whether the document declares a baseline, whether this repository has
it, and how far the trunk has moved since. A plan that names no baseline is
`REVIEW_REQUIRED` before anyone reads its content.

## Local verification
The startup hook does the first two lines for you in a web session. Run them by
hand anywhere else.

```bash
export AGENTFACTORY_TARGET_BRANCH=main            # branch this work targets
export PYTHONPATH="$PWD:$PWD/src"                 # opro_baseline + domain_matrix need it
python3 -m pip install pytest                     # NOT --upgrade: breaks on the web container
python3 -m pytest tests/ -q
python3 scripts/validate_project_context.py
python3 scripts/validate_session_resume.py
python3 scripts/validate_session_state.py
python3 scripts/re_demo.py
python3 scripts/routing_benchmark.py
```

Verifying a change to the hook itself means running **every** CI step, not a
sample:

```bash
python3 scripts/factory_demo.py --scenario all --json
python3 scripts/run_harness.py --json
python3 scripts/opro_baseline.py --json
python3 scripts/re_demo.py --json
python3 scripts/domain_matrix_demo.py --json
python3 -m pytest -q
```

Reporting surfaces added 2026-08-31 (neither gates; both report):

```bash
python3 scripts/audit_schema_bindings.py          # declared fields nothing reads
python3 scripts/verify_plan_baseline.py --help    # baseline check for incoming plans
```
