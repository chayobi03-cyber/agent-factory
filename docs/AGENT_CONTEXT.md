# Agent context

Operating instructions for an AI coding agent working in this repository —
Claude Code, Gemini CLI, or any other.

This file is the only copy. `CLAUDE.md` and `GEMINI.md` at the repository root
each inline it with an `@` import and hold no content of their own, because one
definition living in two places is the defect this repository has caught most
often. `tests/test_agent_context.py` fails if either importer grows a body.

## What this is

A domain-agnostic factory for engineering knowledge: retrieval, evidence-backed
answers, a gate that refuses an unsupported claim, and a human in the loop when
risk requires one. A domain is a YAML policy file and a folder of documents,
with no Python — see `docs/ADDING_A_DOMAIN.md`.

The kernel performs no network access at all. Nothing under `src/` or
`scripts/` imports an HTTP client or a hosted-model SDK, and
`tests/test_no_hosted_model_dependency.py` fails if that changes.

## Identity

| | |
| --- | --- |
| project_id | `agent-factory` |
| repository | `chayobi03-cyber/agent-factory` |
| trunk | `main` |
| governance namespace | `AgentFactory` |
| audited baseline SHA | `20a54b92aad0857f75c6200d984b13098c6f4927` |

These are pinned against `docs/governance/CURRENT_SESSION_STATE.yaml` by
`tests/test_agent_context.py`. If you change one there, the test tells you this
file disagrees.

## Before you trust anything, run it

```bash
export AGENTFACTORY_TARGET_BRANCH=main      # the branch your work targets
export PYTHONPATH="$PWD:$PWD/src"           # opro_baseline + domain_matrix need it
python3 -m pip install pytest               # NOT --upgrade: see below

python3 -m pytest tests/ -q
python3 scripts/validate_project_context.py
python3 scripts/validate_session_resume.py
python3 scripts/validate_session_state.py
python3 scripts/re_demo.py
python3 scripts/routing_benchmark.py
```

In a Claude Code web session `.claude/hooks/session-start.sh` does the first
three lines for you. Gemini CLI has no equivalent hook, so run them by hand.

Two traps, both measured rather than assumed:

- **`pip install --upgrade pytest pyyaml`** is what CI runs and it is correct on
  a clean `actions/setup-python` runner. On a container carrying a
  distribution-managed PyYAML, pip cannot uninstall it (`RECORD file not
  found`) and the aborted install takes pytest down with it. Install only what
  is missing.
- **`PYTHONPATH` is no longer required, only harmless.** Every script in
  `scripts/` puts `src/` on `sys.path` itself, so all of them run on a bare
  clone. Two of them did not until 2026-08-30 and failed for anyone outside CI
  — and CI *sets* `PYTHONPATH`, so no workflow could ever have caught it.
  `tests/test_scripts_run_standalone.py` runs each script with the variable
  scrubbed and fails if one goes back to needing it.

Verifying a change to tooling means running every step above, not a sample.

## Constraints that are not yours to relax

The complete and authoritative list is `forbidden:` in
`docs/governance/CURRENT_SESSION_STATE.yaml`. Read it. The entries below are
the ones that most often come up, and this summary is deliberately not
complete:

- `hosted_model_api_dependency` — permanently excluded by owner decision
  (OPEN_DECISIONS D-12 option C). Not cost or preference: a run that calls a
  hosted model cannot be re-derived from the commit it names, which is what the
  evidence contract exists to guarantee. A *local* model is a different
  question and stays open.
- `GEPA_implementation`, `OPRO_promotion` — optimization work is gated.
- `audited_baseline_redefinition` — the baseline SHA above does not move.
- `PASS_without_primary_execution_evidence` — see below.

Every constraint named here is asserted to exist in `state.forbidden` by
`tests/test_agent_context.py`, so this list cannot keep a retired entry or
invent one. It can still be incomplete, which is why you read the state file.

## What counts as evidence

Documentation and state are not execution evidence. A GREEN claim requires the
whole chain:

```
target SHA -> workflow run -> job -> logs -> artifact -> GitHub digest -> independent verification
```

Absence of a returned run is `EVIDENCE_UNAVAILABLE`, not inferred success.

Neither workflow triggers on a `claude/**` or feature-branch push — both are
`push: [main]` and `pull_request: [main]`. Work sitting on a session branch
carries no primary evidence until a pull request is opened against `main`.

## How to work here

This codebase's recurring failure is **something declared that was not what it
said**: an evidence contract enforced by nothing; three retrieval modes and a
reranker that did not exist; a gating mechanism still described in a docstring
after its deletion; a `RouteDecision` that no code ever constructed; a
`CONTRADICTORY_EVIDENCE` rule that tested plurality and had been unreachable
since it was written; a wrapper silently dropping the argument that made
verification reachable.

Its companion is **one definition living in two places** — an override missed in
a third validator, claim construction in three copies with the third already
drifted, a handoff filename hardcoded in one validator while another read it
from state.

Both are found the same way, and it is the one habit this repository asks of
you:

> **Run the thing and measure it, rather than reading what it says about
> itself.**

Practically:

- Reproduce a defect before fixing it, and show the fix turning it green.
- When you add a rule, verify it *fails* on the case it exists to catch. A gate
  that cannot fail is not a gate.
- Prefer deriving a value over restating it. If you must restate it, add the
  test that pins the two together.
- Record a measurement that came out against your hypothesis. Several entries
  in the open-decisions register exist because a proposed fix was built,
  measured, and rejected — that is a result, not a failure.
- Do not tune retrieval against the synthetic corpus. Every accuracy number in
  this repository is measured on documents it wrote about itself; further
  fitting measures our own prose. Accuracy work waits for the real corpus by
  owner decision.

## Where things are

| | |
| --- | --- |
| session state | `docs/governance/CURRENT_SESSION_STATE.yaml` |
| current handoff | named by `state.handoff` — follow the pointer, never a filename you remember |
| open decisions | `docs/governance/OPEN_DECISIONS_2026-08-25.md` (D-01..D-16) |
| scope | `docs/governance/AGENT_FACTORY_SCOPE_V1.md` |
| context guard | `scripts/validate_project_context.py` |
| adding a domain | `docs/ADDING_A_DOMAIN.md` |
| source of truth | `SOURCE_OF_TRUTH_MANIFEST.md` |

The live Git repository is the canonical baseline. Historical archives are
evidence of prior design state only, and model memory never overrides a
versioned artifact.
