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

## Then calibrate, before trusting any number

Every one of those four values is **corpus-fitted**. The defaults are fitted to
30 synthetic radiated-emission documents and carry no authority over your
corpus.

```bash
python3 scripts/calibrate_retrieval.py --corpus /your/docs --benchmark /your/cases.json
```

It changes nothing, prints what each candidate value would buy, and exits
non-zero when a shipped constant is no longer the right choice for the corpus
it just measured. It refuses to run against a benchmark naming documents your
corpus lacks — pointing it at real documents while still holding someone else's
benchmark would otherwise report a catastrophic recall that reads as a model
regression.

You need a benchmark of your own for this: questions with the document ids that
should answer them. Write the questions as a person would ask them, not by
paraphrasing a sentence from the answer — a benchmark whose queries are lifted
from their own documents measures the person who wrote it. The RE benchmark
reports its own figure both ways for exactly this reason.

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
- **D-12** — there is no semantic retrieval and no reranker. A hosted model API
  is permanently excluded, because a run that calls one cannot be re-derived
  from the commit it names, which is what the audit evidence contract is built
  on. A local model remains open and is not blocked by anything here.
