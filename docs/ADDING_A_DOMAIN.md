# Adding a domain

A new engineering domain is a policy file and a folder of documents. No Python.

```
domains/<your-domain>/domain_pack.yaml     # what the domain is
/wherever/your/documents/*.json            # what it knows
```

```bash
python3 scripts/run_domain.py --list
python3 scripts/run_domain.py --domain thermal \
    --corpus /local/thermal-reports \
    --query "what caused the junction temperature excursion?"
```

`domains/thermal/` is a worked example carrying no code at all. It exists to
keep this claim honest: `tests/test_generic_domain_pack.py` fails if a `.py`
file ever appears under a domain directory.

## The documents

One JSON file per document, or a JSON array in one file. Five required fields:

```json
{
  "document_id": "DOC-TH-004",
  "revision_id": "REV-A",
  "title": "DUT-7 Thermal Excursion Failure Analysis",
  "doc_type": "bench_measurement_log",
  "text": "DUT-7 exceeded its junction rating during a 30 W burst ..."
}
```

`document_id` and `revision_id` together must be unique. Evidence without a
stable identifier is a quotation, not a citation, so a corpus with a duplicate
pair is refused rather than loaded — as is one missing any required field. A
partially-loaded corpus changes every retrieval metric measured against it, and
the change looks like a model regression rather than a missing file.

Documents stay wherever you keep them. `OPEN_DECISIONS` D-08 settled that this
repository is public, so real engineering documents must never be committed to
it. Every run records the corpus origin and a content digest, because a result
measured against an out-of-tree corpus is not re-derivable from the commit SHA
alone and that gap should be visible rather than assumed away.

## The policy

Copy `domains/thermal/domain_pack.yaml` and change four things. The rest of the
schema is optional metadata.

**1 — Identity**

```yaml
domain_id: THERMAL
version: 0.1.0
name: Thermal Design
```

**2 — Generic vocabulary.** The words so common in your field that they never
tell you *which* document is relevant. RE has `radiated`, `emission`, `test`;
thermal has `thermal`, `temperature`, `heat`. This is the one piece of real
domain knowledge the kernel cannot guess, and leaving it out costs precision.

```yaml
terminology:
  generic_terms: [thermal, temperature, heat, cooling, measured, test]
```

Ordinary English function words (`the`, `is`, `which`) come from the kernel —
don't retype them. If you *do* declare `stopwords`, your list replaces the
default entirely rather than adding to it: a domain that lists them has made a
measured choice, and silently merging a default into it moves every threshold
calibrated under that vocabulary.

**3 — What the domain measures.** Engineering text is numbers with units, and a
plain word tokenizer shatters them: `5.8 GHz` becomes `['5','8','ghz']`, which
is indistinguishable from `8.5 GHz`.

```yaml
measurement_policy:
  canonical_unit: w            # scale everything to this
  unit_multipliers: {uw: 0.000001, mw: 0.001, w: 1, kw: 1000}
  level_units: [degc, c/w, k/w, m/s]   # kept attached, not scaled
  identifier_prefixes: [rev, dut, brd, hs, tim]   # DUT-7 survives whole
  quantity_metadata_key: power_dissipation
```

With this, `500 mW` and `0.5 W` reach the same token, and a question naming a
measurement the corpus has never seen is refused rather than answered from the
nearest paragraph.

A domain of pure prose can omit the whole block and gets ordinary word
tokenization — correct, not degraded.

**4 — Thresholds.** Start by copying these, then *measure them*:

```yaml
retrieval_policy:
  allowed_modes: [bm25, trigram, hybrid]
  default_mode: hybrid
  tuning:
    coverage_floor: 0.12
    unseen_term_ceiling: 0.35
    lexical_weight: 0.6
verification_policy:
  claim_grounding_floor: 0.25
```

## Read your accuracy number against a floor

```bash
python3 scripts/re_demo.py     # reports the random-retrieval baseline with every figure
```

A hit rate has a floor and it is not zero. Drawing ten fragments at random from
the 108 in the RE corpus reaches a fifth of its documents, which scores 0.356
before retrieval does anything — so 0.906 is 85% of the distance available, not
91% of the way from nothing. Measure the floor for your corpus before quoting a
number against it, and check how many gold documents each benchmark case has:
with exactly one, "recall" is a hit rate and moves in steps of 1/n.

## Then calibrate, before trusting any number

Every one of those four values is **corpus-fitted**. The defaults are fitted to
30 synthetic radiated-emission documents and carry no authority over your
corpus.

```bash
python3 scripts/calibrate_retrieval.py --corpus /your/docs --benchmark /your/cases.json
```

It changes nothing and prints what each candidate value would buy. It exits
non-zero on two different outcomes, and they mean different things:

- **STALE** — the sweep measured the constant and a different value fits your
  corpus better. Re-derive before quoting any number.
- **UNVERIFIED** — the sweep could not measure the constant at all, because
  your benchmark lacks the cases it needs. The shipped value is neither
  confirmed nor refuted, so it carries exactly the authority it had before you
  ran anything: none, over your corpus.

`UNVERIFIED` is the one to watch, because it is the one that used to read as
success. Both `_UNSEEN_TERM_CEILING` and `RETRIEVAL_MODES` can land there, and
a benchmark written without reading the next section will put the first one
there every time.

It also refuses to run against a benchmark naming documents your corpus lacks —
pointing a tool at real documents while it still holds someone else's benchmark
would otherwise report a catastrophic recall that reads as a model regression.
`scripts/re_demo.py --corpus ... --benchmark ...` refuses the same mismatch,
through the same check in `src/corpus_source.py`.

## Write the benchmark

A benchmark is a JSON file of cases. Seven fields, of which two are optional:

```json
{
  "benchmark_id": "YOURDOMAIN-BENCH",
  "version": "0.1",
  "cases": [
    {
      "case_id": "YD-001",
      "query": "What is the minimum margin required against the Class B limit?",
      "query_type": "definition_factual",
      "expected_document_ids": ["SPEC-007"],
      "expect_abstain": false,
      "min_recall": 1.0
    },
    {
      "case_id": "YD-002",
      "query": "What is the shear modulus of the potting compound?",
      "query_type": "evidence_sufficiency_abstention",
      "expected_document_ids": [],
      "expect_abstain": true,
      "abstention_band": "entity_absent_from_corpus",
      "min_recall": 0.0
    }
  ],
  "acceptance_targets": {"evidence_recall_at_10": 0.90}
}
```

Write the questions as a person would ask them, not by paraphrasing a sentence
from the answer — a benchmark whose queries are lifted from their own documents
measures the person who wrote it. The RE benchmark reports its own figure both
ways for exactly this reason.

### Every abstention case needs a band

`abstention_band` is required on any case with `expect_abstain: true`, and it
is the field most easily missed: nothing rejects a benchmark without it, but
`calibrate_retrieval.py` then cannot check `_UNSEEN_TERM_CEILING` and reports
`UNVERIFIED` for it. Three bands, and the distinction is not cosmetic — two of
them are decidable from corpus statistics and one is not:

| band | the question asks about | decidable |
| --- | --- | --- |
| `subject_outside_domain` | something this domain does not cover at all | yes |
| `entity_absent_from_corpus` | a named thing your documents have never seen | yes |
| `near_miss_domain_subject` | your subject, but a fact the corpus does not carry | **no** |

The first two are what the ceiling is derived from: the tool picks the largest
ceiling at which both stay perfect. Write several of each or the derivation
rests on one case.

The third is a known open limitation (`OPEN_DECISIONS` D-11) — no lexical
statistic separates "we have this document but not this fact" from "we can
answer this", and eight retrieval-side and five verification-side candidates
were measured and rejected. Label those cases honestly anyway. They are
excluded from the pass/fail gate and reported separately, so they tell you the
size of the gap rather than hiding it.

### Then score it

```bash
python3 scripts/re_demo.py --corpus /your/docs --benchmark /your/cases.json
```

`query_type` is free text and is used only to group the report, so use whatever
taxonomy your domain thinks in. `docs/RE_POC.md` lists the nine categories the
RE work uses if you want a starting point.

## More than one domain at a time

Omit `--domain` and the question is routed across every loaded domain:

```bash
python3 scripts/run_domain.py --examples --query "what caused the cell to vent?"
```

Three answers are possible and only one of them is a domain. It can refuse —
"no loaded domain covers this question", exit code 3 — and it can refer, when
two domains are too close to separate, which prints a REVIEW line and answers
from the leading domain anyway so a person can check the choice.

Routing compares how strongly each corpus is *about* the question's terms, not
how many of them it has seen. That distinction is not cosmetic: on the term
count, the largest corpus wins questions it has no documents for, and the pack
that tokenizes an identifier *correctly* loses to one that shatters it into
pieces its corpus happens to contain. Both were measured, and OPEN_DECISIONS
D-13 records them.

```bash
python3 scripts/routing_benchmark.py     # 30/32 over the six example domains
```

The two routing thresholds are corpus-fitted like the other four. If you load
corpora of very different sizes together, re-derive them.

## What you get, and what you should not expect

Retrieval, claim-evidence verification and the CER gate all run, so a query
returns a gated answer: the evidence it rests on, the part of the question the
evidence never mentions, and an explicit refusal when the corpus cannot answer.

Two limits are measured rather than assumed, and both are recorded in
`docs/governance/OPEN_DECISIONS_2026-08-25.md`:

- **D-11** — a lexical retriever cannot reliably refuse a *near-miss*: a
  question about real subject matter in your field that your corpus happens not
  to cover. Questions about other fields, and about equipment your corpus does
  not contain, are refused reliably. Near-misses are refused about half the
  time. The verifier names the unsupported part of the question so a reviewer
  can see the gap, which is a person catching it, not the system.
- **D-14** — nothing decides which *revision* of a document applies. If your
  corpus holds a report and its retest, both are indexed and both can be
  retrieved; the answer says so — `DOC-X is in evidence at REV-A and REV-B` —
  and stops there. `revision_id` carries no supersession, and the one rule that
  could be built from a citation list was measured referring the questions that
  were *asking* about the difference between revisions. Semantic contradiction
  between two documents is not detected at all.
- **D-13** — routing picks the corpus and says nothing about whether the
  answer from it is right. A question routed correctly to a domain that cannot
  answer it still reaches the claim verifier and the CER gate and is still
  refused there; the two mechanisms are independent and neither covers the
  other.
- **D-12** — there is no semantic retrieval and no reranker. A hosted model API
  is permanently excluded, because a run that calls one cannot be re-derived
  from the commit it names, which is what the audit evidence contract is built
  on. A local model remains open and is not blocked by anything here.
