# RE PoC Scope

## Objective
Validate that the Agent Factory kernel, contracts, retrieval, evidence verification, reporting, HOTL and benchmark system work on a real engineering domain without domain-specific kernel forks.

## Inputs
- legacy PDF
- test reports
- specifications
- measurement logs/exports
- internal wiki/Markdown

## Functions
- ingestion and revision detection
- hybrid retrieval
- evidence extraction
- claim generation
- claim-evidence verification
- natural-language QA
- comparative QA
- diagnosis workflow
- report generation
- HOTL review
- trace
- benchmark

## Initial RE ontology
Entities: equipment, DUT, chamber, antenna, cable, connector, enclosure, frequency, limit, test_setup, measurement, peak, mitigation, failure_mode.

Relations: tested_with, connected_to, measured_at, exceeds, mitigated_by, correlates_with, reproduced_by.

## Query taxonomy
1. definition / factual
2. document location
3. revision comparison
4. condition/cause analysis
5. RE failure diagnosis
6. evidence supporting or contradicting a hypothesis
7. recommended additional test
8. engineering report
9. evidence sufficiency / abstention

## PoC target
- 20+ representative legacy documents
- 150 benchmark cases
- 3 retrieval methods minimum
- citation and evidence verification
- report output
- human correction capture

> **"2 model providers minimum" was struck 2026-08-30** (OPEN_DECISIONS D-16).
> A hosted model API is permanently excluded — a run that calls one cannot be
> re-derived from the commit it names, which is what
> `AUDIT_EVIDENCE_CHAIN_CI_CONTRACT_V1` rests on (D-12 option C) — and the
> kernel performs no network access at all. The target was therefore unreachable
> by the route anyone would take to reach it, and had been since the exclusion
> was recorded.
>
> Multi-provider comparison moves to **M5 Method Ensemble**, where method
> comparison and arbitration already live. Provider neutrality remains an
> architecture principle (`docs/MDD.md`): the PoC demonstrates that the kernel
> needs no provider, which is a stronger claim than running two — though not a
> demonstration that the adapter boundary works, which is M5's to make.

## Initial acceptance targets

These are calibration targets and must be revised after source
characterization. Revised 2026-08-30 against what is actually measured; each
entry now says whether the PoC gates on it, and where it does not, why.

**Gated — a run fails without these.**

- **Evidence Recall@10 >= 0.90.** Measured 0.914, or 0.906 excluding eleven
  cases whose query restates its own answer, against a random-retrieval floor
  of 0.356. With one gold document per case this is a hit rate, and
  `hit_rate_at_10` reports it under that name.
- **Negative-case Abstention — stated per band, not as one figure.** A single
  number over all abstention cases is not reachable by a lexical retriever, and
  averaging the three bands hides which one fails. The gate is:
  - `subject_outside_domain` = 1.00 — measured 5/5
  - `entity_absent_from_corpus` = 1.00 — measured 7/7
  - `near_miss_domain_subject` — **reported, not gated.** Measured 3/8. No
    lexical statistic separates "we hold this document but not this fact" from
    "we can answer this"; eight retrieval-side and five verification-side
    candidates were built, measured and rejected (OPEN_DECISIONS D-11). The
    run reports `silently_answered` for this band so the gap reaches a reader
    rather than passing unseen.

  This replaces `Negative-case Abstention >= 0.90`, which the run scored 0.75
  against while the gate — correctly — checked something else. The code was
  right and this document was describing a different rule.
- **Domain Pack load without kernel modification = PASS.** Asserted by
  `tests/test_generic_domain_pack.py`, which fails if a `.py` file appears
  under a domain directory.

**Stated but not gated — see OPEN_DECISIONS D-15.**

- **Citation Accuracy >= 0.95 — the definition is undecided, and it decides the
  verdict.** Three defensible readings measure 0.969 (at least one cited
  fragment comes from a gold document), 0.567 (share of cited fragments from a
  gold document) and 0.864 (mean IDF coverage of the claim's terms by its
  citations). The benchmark labels one gold *document* per case while a claim
  cites 2.35 fragments on average over the 127 cases that cite anything, so a
  fragment-level figure needs fragment-level ground truth that does not exist
  yet.
- **Critical Claim Unsupported Rate <= 0.02 — measured, not yet reported.**
  Derivable from `verification.ungrounded_claim_ids`, which every run already
  emits: 12 of 139 answerable cases, **0.086**. The threshold is not reachable
  by tightening the grounding floor — doing so to reach perfect abstention
  costs 46.8% false abstention (D-14).
- **Revision correctness >= 0.95 — not definable yet.** Which revision of a
  document applies is a document-management rule this project does not have,
  and `revision_id` carries no supersession metadata to derive one from
  (OPEN_DECISIONS D-14). The verifier names the conflict and tells the reader;
  nothing decides it.
- **Trace completeness = 100% — does not describe this path.** `re_demo.py`
  drives `CERGateRuntime` directly and never constructs a `FactoryRuntime`, and
  `src/cer_runtime.py` contains no trace machinery, so the benchmark run emits
  no trace at all. Where the target applies, and what its denominator is
  against a ten-stage lifecycle, is open.
