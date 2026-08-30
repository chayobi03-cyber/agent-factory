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
# AgentFactory Next Session Handoff — 2026-08-29

Supersedes `NEXT_SESSION_HANDOFF_2026-08-27.md`, which is retained as history.
`CURRENT_SESSION_STATE.yaml.handoff` names this file, and every validator
follows that pointer rather than a path of its own.

## Canonical identity
- project_id: `agent-factory`
- repository: `chayobi03-cyber/agent-factory`
- branch: `main`
- governance_namespace: `AgentFactory`

## Read this first: check whether PR #39 merged

The 2026-08-29 session added a **SessionStart hook** so a Claude Code web
session can run the verification block at the bottom of this document. At the
time of writing it is **open and unmerged** in PR #39, green and mergeable.

```bash
git log --oneline -1 -- .claude/hooks/session-start.sh   # empty = not merged
```

**If it merged**, your session already has `pytest` installed and
`AGENTFACTORY_TARGET_BRANCH=main` exported. The verification block runs
unchanged. Nothing to do.

**If it did not merge**, you are in the situation the hook was written to fix,
and the block below will not run as written:

| | symptom | why |
| --- | --- | --- |
| `python3 -m pytest tests/ -q` | `No module named pytest` | fresh container, no dependency manifest in the repo |
| the three validators | **exit 2** each | your session is on a `claude/*` branch, not the trunk |

Recover by hand with `python3 -m pip install pytest` and
`export AGENTFACTORY_TARGET_BRANCH=main`, then decide whether to revive #39.

## Where the work stands

M0 Foundation and M0.5 Factory Kernel Verification are closed and GREEN. **M1
RE Hybrid RAG meets every PoC acceptance target** against a synthetic corpus,
and the kernel has been generalised so a new engineering domain is a YAML file
plus a folder of documents with no Python at all.

Measured on this tree, not copied forward:

```
Evidence Recall@10   0.914 headline / 0.906 earned   target 0.90
                     random-retrieval floor 0.356 -> 85.4% of available headroom
Recall@1 / @3        0.827 / 0.906        MRR@10 0.868
Per-case             142/159              acceptance targets MET
Abstention           outside 5/5   absent 7/7   near-miss held 3/8, silent 5/8
Cross-domain routing 30/32 (0.938)   clear 17/19   out_of_scope 6/6   shared_vocab 7/7
Tests                322
```

Six domains ship ready for documents: `re`, `thermal`, `structural`,
`battery`, `manufacturing`, `firmware`.

```bash
python3 scripts/run_domain.py --list
python3 scripts/run_domain.py --domain thermal --corpus /local/docs --query "..."
python3 scripts/run_domain.py --query "..."          # routes across every loaded domain
python3 scripts/routing_benchmark.py
python3 scripts/calibrate_retrieval.py --corpus DIR --benchmark CASES
```

## The one thing blocking progress

**Accuracy work waits for the real RE corpus, by owner decision.** Every
acceptance number above is measured against documents this repository wrote
about itself. D-08 keeps the repository public, so real reports cannot be
committed; `corpus_source.py` loads an out-of-tree folder and every run records
the corpus origin and a content digest so the gap is visible rather than
assumed away.

Tuning further against the synthetic corpus would be fitting to our own prose.
That is the single reason the four retrieval-quality defects below are recorded
and not fixed. **The 2026-08-29 session changed nothing here** — it touched
tooling only, no kernel, retrieval, routing or domain behaviour.

## First actions on the day the real documents land

1. `python3 scripts/calibrate_retrieval.py --corpus <DIR> --benchmark <CASES>` —
   re-derives all four corpus-fitted constants and exits non-zero if a shipped
   value no longer fits. **Do this before trusting any number.**
2. Author a benchmark for the real corpus. The synthetic one names `DOC-RE-*`
   and the calibration tool refuses a benchmark whose expected documents are
   absent — that is the intended guard, not an obstacle. Write queries as a
   person would ask them; a benchmark paraphrased from its own answers measures
   the person who wrote it, which is why the RE benchmark reports its figure
   both ways.
3. Measure the random baseline for that corpus before quoting a figure against
   it, and check the gold-set size per case. With one gold document, "recall"
   is a hit rate.
4. Re-derive `MINIMUM_SCORE` and `DECISIVE_MARGIN` if two real corpora of very
   different sizes are loaded together (`scripts/routing_benchmark.py`).
5. Then revisit D-11 with real vocabulary breadth, and D-12 with whatever D-11
   turns out to cost.

## Decisions waiting on a person

- **Document revisions (D-14).** Nothing decides which revision of a document
  applies. The verifier names the conflict and the reader is told — *"DOC-RE-001
  is in evidence at REV-A and REV-B; these may not agree"* — and stops there.
  Whether a query should prefer the newest revision, return both, or refer to a
  person when the question carries no time scope is a working rule for how RE
  documents are managed. `revision_id` carries no supersession metadata to
  decide it from, so the corpus may need to change too.
- **D-12 options A, B and D** go to comparative trial on the real corpus.
  Option C (a hosted model API) is permanently excluded and enforced by
  `tests/test_no_hosted_model_dependency.py`.
- **PR #39**, if still open. It is green and mergeable; only review stands
  between it and the trunk.

## Measured, recorded, deliberately unfixed

All four are retrieval quality and belong against the real corpus
(OPEN_DECISIONS D-14, final section):

| | finding |
| --- | --- |
| hybrid fusion | contributes **6.5 : 1** in BM25's favour at rank 1 and is close to a no-op; RRF is the dependency-free alternative |
| chunking | **0% overlap**, splits mid-sentence on `;`, producing fragments like *"use an isolated ground strap if this is suspected"* |
| de-duplication | none; near-identical fragments can fill the top-k |
| aliases | none, so adding "equipment under test" to a query changes which revision comes back |

## What this codebase keeps teaching

Seven times now, something was declared and was not what it said. The audit
evidence contract enforced by nothing (D-09); three retrieval modes and a
reranker that did not exist (D-12); a gating mechanism still described in a
docstring after its deletion; `RouteDecision` constructed by nothing (D-13); a
`CONTRADICTORY_EVIDENCE` rule that tested plurality and had been unreachable
since it was written; `FactoryRuntime.evaluate_gate` silently dropping the
`verification` argument; and a handoff path hardcoded in one validator while
another read it from state.

The companion pattern is one definition living in two places — the D-02
override missed in a third validator, claim construction in three copies with
the third already drifted, the evidence gate's harness count. Both are found
the same way: **run the thing and measure it, rather than reading what it says
about itself.**

The 2026-08-29 session added three instances of each. CI's own install line
(`pip install --upgrade pytest pyyaml`) is correct on an `actions/setup-python`
runner and *fails* on the web container — pip cannot uninstall a Debian-managed
PyYAML, and the aborted install takes pytest with it. Reading the workflow
would have reproduced the bug; running it found it. The hook reads the trunk
name from `state.working_branch` rather than writing `main` a third time next
to `EXPECTED_BRANCH` and the state field.

And a live one, still open:

> **`scripts/` resolves imports two different ways.** Six of the eight scripts
> insert the repository root on `sys.path` themselves —
> `calibrate_retrieval`, `factory_demo`, `re_demo`, `routing_benchmark`,
> `run_domain`, `run_harness`. Two do not: **`opro_baseline.py`** and
> **`domain_matrix_demo.py`** import `factory_runtime` and
> `synthetic_domain_matrix` from the ambient `PYTHONPATH`, which only
> `factory-kernel.yml` sets. They therefore raise `ModuleNotFoundError` for
> anyone running them outside CI, and the failure is invisible until you run
> exactly those two — checking the other six proves nothing about them.
>
> The hook now exports the same `PYTHONPATH` CI does, so the sequence runs.
> That fixes the symptom. The remaining question is which convention wins:
> either the two scripts self-bootstrap like the other six, or the other six
> drop their bootstrap and the env var becomes the single mechanism. It should
> not stay both. Left open deliberately rather than decided inside a tooling
> change.

## Governance
- Open decisions: `docs/governance/OPEN_DECISIONS_2026-08-25.md` (D-01..D-14)
- Session state: `docs/governance/CURRENT_SESSION_STATE.yaml`
- Adding a domain: `docs/ADDING_A_DOMAIN.md`
- Context guard: `scripts/validate_project_context.py`
- Startup hook: `.claude/hooks/session-start.sh`, registered in `.claude/settings.json`
- Audited baseline SHA: `20a54b92aad0857f75c6200d984b13098c6f4927` — unchanged

## Primary evidence rule
Documentation and state are not execution evidence. A GREEN claim requires:
`target SHA -> workflow run -> job -> logs -> artifact -> GitHub digest -> independent verification`

Absence of a returned run is `EVIDENCE_UNAVAILABLE`, not inferred success.

Note that **neither workflow triggers on a `claude/**` push** — both are
`push: [main]` and `pull_request: [main]`. Work sitting on a session branch
carries no primary evidence until a PR is opened against `main`. That is what
PR #39 is for, and it is the evidence-only-branch/PR pattern
`AUDIT_EVIDENCE_CHAIN_CI_CONTRACT_V1.md` describes.

## Local verification
The startup hook does the first two lines for you in a web session. Run them
by hand anywhere else.

```bash
export AGENTFACTORY_TARGET_BRANCH=main            # branch this work targets
export PYTHONPATH="$PWD:$PWD/src"                 # opro_baseline + domain_matrix need it
python3 -m pip install pytest                     # NOT --upgrade: see above
python3 -m pytest tests/ -q
python3 scripts/validate_project_context.py
python3 scripts/validate_session_resume.py
python3 scripts/validate_session_state.py
python3 scripts/re_demo.py
python3 scripts/routing_benchmark.py
```

Verifying a change to the hook itself means running **every** CI step, not a
sample. `re_demo` and `factory_demo` pass without `PYTHONPATH` and prove
nothing about the two scripts that need it:

```bash
python3 scripts/factory_demo.py --scenario all --json
python3 scripts/run_harness.py --json
python3 scripts/opro_baseline.py --json
python3 scripts/re_demo.py --json
python3 scripts/domain_matrix_demo.py --json
python3 -m pytest -q
```
