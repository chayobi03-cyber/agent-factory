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
# AgentFactory Next Session Handoff — 2026-08-30

Supersedes `NEXT_SESSION_HANDOFF_2026-08-29.md`, which is retained as history.
`CURRENT_SESSION_STATE.yaml.handoff` names this file, and every validator
follows that pointer rather than a path of its own.

**The position in one paragraph.** The kernel is GREEN and M1 meets the targets
it gates. The handover-blocking tooling defects are fixed: a foreign corpus now
scores against its own benchmark or is refused, and calibration says
`unverified` instead of green when it cannot measure. What remains is waiting
on the real RE documents and on three decisions that are stated, costed, and
deliberately not taken. **Do not start retrieval accuracy work.**

## Start here — any CLI, cold

This repository is read by Claude Code (`CLAUDE.md`) and Gemini CLI
(`GEMINI.md`). Both files are three lines that `@`-import
**`docs/AGENT_CONTEXT.md`**, which is the only copy of the operating
instructions. Read that first; this document is the *state*, that one is the
*rules*.

Setup is now two commands, and only the second is ever needed twice:

```bash
python3 -m pip install pytest          # NOT --upgrade -- see AGENT_CONTEXT
export AGENTFACTORY_TARGET_BRANCH=main # only the three validators need it
```

`PYTHONPATH` is **no longer required**. Every script in `scripts/` puts `src/`
on `sys.path` itself as of 2026-08-30, so all thirteen run on a bare clone.
`tests/test_scripts_run_standalone.py` scrubs the variable and fails if one
goes back to needing it. If you find instructions telling you to export it,
they are older than this document.

In a Claude Code **web** session `.claude/hooks/session-start.sh` does both
lines for you. Claude Code local and Gemini CLI have no such hook — run them by
hand. Nothing else differs between the two clients.

Then verify, and run every line rather than a sample:

```bash
python3 -m pytest tests/ -q                    # 386 passing
python3 scripts/validate_project_context.py    # CONTEXT_GUARD=PASS
python3 scripts/validate_session_resume.py     # RESUME_ALLOWED
python3 scripts/validate_session_state.py      # resume_checks=PASS
python3 scripts/re_demo.py                     # acceptance targets MET
python3 scripts/routing_benchmark.py           # 30/32
python3 scripts/calibrate_retrieval.py         # exit 0, ~28s
```

## Canonical identity
- project_id: `agent-factory`
- repository: `chayobi03-cyber/agent-factory`
- branch: `main`
- governance_namespace: `AgentFactory`
- audited baseline SHA: `20a54b92aad0857f75c6200d984b13098c6f4927` — unchanged

## Where the work stands

M0 Foundation and M0.5 Factory Kernel Verification are closed and GREEN. M1 RE
Hybrid RAG meets the targets it gates, against a synthetic corpus. A new
engineering domain is a YAML file plus a folder of documents, with no Python.

Measured on this tree, not copied forward:

```
Evidence Recall@10   0.914 headline / 0.906 earned   target 0.90
                     random-retrieval floor 0.356 -> 85.4% of available headroom
Recall@1 / @3        0.827 / 0.906        MRR@10 0.868
Per-case             142/159              nine query categories, all covered
Abstention           outside 5/5   absent 7/7   near-miss held 3/8 (reported, not gated)
Cross-domain routing 30/32 (0.938)   out_of_scope 6/6
Tests                386
```

Six domains ship ready for documents: `re`, `thermal`, `structural`,
`battery`, `manufacturing`, `firmware`.

```bash
python3 scripts/run_domain.py --list
python3 scripts/run_domain.py --domain thermal --corpus /local/docs --query "..."
python3 scripts/run_domain.py --query "..."          # routes across every loaded domain
python3 scripts/re_demo.py --corpus DIR --benchmark PATH
python3 scripts/calibrate_retrieval.py --corpus DIR --benchmark PATH
```

## What changed on 2026-08-30, and why it matters to you

A rehearsal on six out-of-tree documents — pretending to be the day the real
corpus lands — found three ways the first day reported the wrong thing. All
three are fixed, and they are the reason the commands above can be trusted
against documents this repository has never seen.

| | was | now |
| --- | --- | --- |
| `re_demo.py` on a foreign corpus | scored it against the in-tree `DOC-RE-*` answer key: `Recall@10 0.000`, "targets NOT MET" | takes `--benchmark`; refuses a mismatch with exit 2 |
| `calibrate_retrieval.py` | claimed `FITS` for constants it could not measure, exit 0 | third verdict `UNVERIFIED`, exit 1 |
| benchmark schema | `abstention_band` existed only inside the RE benchmark's JSON | documented in `docs/ADDING_A_DOMAIN.md`, pinned to the kernel by test |

Also closed: the hosted-model guard listed `vertexai` but not `google`, so both
Gemini SDK import spellings reached the kernel untouched while `import openai`
failed. Widened, with a test proving local-model imports still pass — D-12
option B was not closed by accident.

## Do these now, in this order, when you resume

Nothing here needs the real corpus. Everything else does.

1. **Nothing is required.** The tree is green and consistent. If you are
   resuming only to check state, run the verification block and stop.
2. If the real documents have arrived, go to *The day the documents land*.
3. If they have not, and you want to move something, the only work that is both
   useful and safe is **D-15 branch 2** — see below. Everything else in the
   deferred queue is deliberately deferred, not merely unstarted.

## Decisions: what is settled and what is not

`docs/governance/OPEN_DECISIONS_2026-08-25.md` holds D-01..D-16. Current shape:

**Closed.** D-01..D-10, D-13, D-14, D-16.

**D-16** closed 2026-08-30: `2 model providers minimum` struck from the RE PoC
target and moved to M5, because a hosted API is permanently excluded and the
kernel has no network, so it was unreachable by the route anyone would take.

**D-15 is four separate questions, not one.** Measuring the five "unmeasured"
acceptance targets split them:

| branch | state | what it needs |
| --- | --- | --- |
| 1 Citation Accuracy | **open** | a definition. Three defensible readings measure 0.969, 0.567, 0.864 against a 0.95 target, so the definition decides the verdict. Recommendation in the register: adopt the 0.969 reading, the only one the benchmark can label |
| 2 Unsupported Rate | **open, cheap** | aggregation only — the data is already in every run's output. Measured 0.086 over answerable cases. Report it; do **not** gate on 0.02, which is unreachable without refusing 46.8% of answerable questions |
| 3 Trace completeness | **open** | not a metric gap. `re_demo.py` drives `CERGateRuntime` and never constructs a `FactoryRuntime`, so this path emits no trace at all. Belongs in M0.5↔M1 integration, against the real corpus |
| 4 Abstention target | **applied** | `RE_POC.md` now states it per band, matching what the gate always checked. A test pins which bands gate |
| 5 Revision correctness | **blocked** | D-14's question, and an input to the internal handover |

**D-11 and D-12 remain open and deferred** behind the real corpus.

`meets_acceptance_targets` and `re_demo`'s output are deliberately untouched:
changing what the gate checks is branch 1 and 2's implementation and should
follow the definition decision, not anticipate it.

## The one thing blocking progress

**Accuracy work waits for the real RE corpus, by owner decision.** Every
acceptance number above is measured against documents this repository wrote
about itself. D-08 keeps the repository public, so real reports cannot be
committed; `corpus_source.py` loads an out-of-tree folder and every run records
the corpus origin and a content digest so the gap is visible rather than
assumed away.

Tuning further against the synthetic corpus would be fitting to our own prose.
That is the single reason the four retrieval-quality defects below are recorded
and not fixed.

## The day the documents land

1. `python3 scripts/calibrate_retrieval.py --corpus <DIR> --benchmark <CASES>` —
   re-derives all four corpus-fitted constants. **Before trusting any number.**
   Read the verdict carefully: `STALE` means a different value fits better;
   `UNVERIFIED` means the sweep could not measure at all, usually because the
   benchmark carries no banded abstention cases.
2. Author a benchmark for the real corpus first — the schema is in
   `docs/ADDING_A_DOMAIN.md` under *Write the benchmark*. Include several cases
   in each of `subject_outside_domain` and `entity_absent_from_corpus`, or
   step 1 reports `UNVERIFIED` for the ceiling. Write queries as a person would
   ask them; a benchmark paraphrased from its own answers measures the person
   who wrote it.
3. `python3 scripts/re_demo.py --corpus <DIR> --benchmark <CASES>`. It refuses a
   benchmark naming documents your corpus lacks, which is the guard rather than
   an obstacle.
4. Measure the random baseline for that corpus before quoting a figure, and
   check the gold-set size per case. With one gold document, "recall" is a hit
   rate.
5. Re-derive `MINIMUM_SCORE` and `DECISIVE_MARGIN` if two real corpora of very
   different sizes are loaded together (`scripts/routing_benchmark.py`).
6. Then revisit D-11 with real vocabulary breadth, and D-12 with whatever D-11
   turns out to cost.

## What the handover meeting must produce

These cannot be derived here; they come from the people who manage the
documents.

1. **The revision rule (D-14) — put this first on the agenda.** Which revision
   applies when a retest and the original are both in evidence? Newest wins,
   both returned, or refer to a person when the question carries no time scope?
   It may add a field to the corpus, so settling it *before* documents are
   exported avoids exporting them twice. Open the discussion with the warning
   the system actually prints, not with an abstraction:
   *"DOC-X is in evidence at REV-A and REV-B; these may not agree, and nothing
   here records which supersedes which."*
2. **The documents.** Four fields per JSON file: `document_id`, `revision_id`,
   `title`, `doc_type`, `text`. 20–30 to start, and **include at least one
   report at two revisions** so D-14 is exercised rather than theorised.
3. **The benchmark**, written by an engineer who asks these questions, not by
   whoever wrote the documents.
4. **EMI/RFI documents** — deferred. One real domain carried end to end beats
   two started. M6 is not urgent; generalisation is already demonstrated across
   six domains.

## Deferred queue — do not start these before the corpus

| | why it waits |
| --- | --- |
| four retrieval defects: hybrid fusion 6.5:1 and near a no-op; chunking 0% overlap splitting mid-sentence on `;`; no de-duplication; no alias table | fitting them to synthetic documents measures our own prose |
| D-11 near-miss abstention (3/8) | eight retrieval-side and five verification-side statistics already measured and rejected; needs real vocabulary breadth |
| D-12 options A, B, D | comparative trial belongs on the real corpus |
| D-15 branches 1 and 3 | branch 1 wants a definition decision; branch 3 is integration work better done against real traces |
| M2 diagnosis, M3 reporting | the benchmark's weakest categories (0.79, 0.86) sit exactly here — they are unstarted milestones, not retrieval failures |
| M0.5 `replay` | declared in the milestone, no implementation and no test. Recorded, not urgent |

## What this codebase keeps teaching

Something declared that was not what it said: an evidence contract enforced by
nothing; three retrieval modes and a reranker that did not exist; a gating
mechanism still described in a docstring after its deletion; a `RouteDecision`
constructed by nothing; a `CONTRADICTORY_EVIDENCE` rule unreachable since it
was written; `FactoryRuntime.evaluate_gate` dropping the argument that made
verification reachable; a `meets_acceptance_targets` flag checking two of seven
targets; a calibration tool declaring constants correct that it had not
measured.

Its companion is one definition living in two places — the D-02 override missed
in a third validator, claim construction in three copies, a handoff filename
hardcoded in one validator while another read it from state, the
benchmark-mismatch guard present in one of the two tools that needed it, the
abstention band tuple written out in three places across two scripts.

Both are found the same way, and it is the one habit this repository asks:

> **Run the thing and measure it, rather than reading what it says about
> itself.**

Three examples from the 2026-08-30 session, all of which were caught only by
running something:

- A test asserting `state["working_branch"] in document` passed after the trunk
  was renamed to `master`, because "main" still occurred in `push: [main]`
  further down. A substring check against a whole document proves nothing about
  a common word.
- De-duplicating the abstention band tuple into the kernel left every test
  green when a script was reverted to its own literal copy — the
  de-duplication was a claim with no mechanism until a source scan was added,
  which then found two more copies that had been missed.
- The unsupported-claim rate first came out at 0.170, which counted twenty
  *correct* abstentions as failures. Over answerable cases it is 0.086 — and
  that agrees with a figure D-14 had already recorded, which is what confirmed
  the correction rather than the first number.

## Primary evidence rule

Documentation and state are not execution evidence. A GREEN claim requires:
`target SHA -> workflow run -> job -> logs -> artifact -> GitHub digest -> independent verification`

Absence of a returned run is `EVIDENCE_UNAVAILABLE`, not inferred success.

Neither workflow triggers on a `claude/**` push — both are `push: [main]` and
`pull_request: [main]`. Work on a session branch carries no primary evidence
until a pull request is opened against `main`.

## Governance
- Open decisions: `docs/governance/OPEN_DECISIONS_2026-08-25.md` (D-01..D-16)
- Session state: `docs/governance/CURRENT_SESSION_STATE.yaml`
- Agent operating rules: `docs/AGENT_CONTEXT.md` — imported by `CLAUDE.md` and `GEMINI.md`
- Adding a domain, and the benchmark schema: `docs/ADDING_A_DOMAIN.md`
- Context guard: `scripts/validate_project_context.py`
- Startup hook (Claude Code web only): `.claude/hooks/session-start.sh`
