"""Tests for the M1 RE Hybrid RAG Domain Pack (src/re_domain_pack.py)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from interfaces import Claim  # noqa: E402
from cer_runtime import CERGateRuntime  # noqa: E402
from re_corpus import CORPUS  # noqa: E402
from re_domain_pack import REDomainPack, Document  # noqa: E402

BENCHMARK_PATH = ROOT / "templates" / "benchmark" / "re_hybrid_rag_v0.1.json"
SNAPSHOT_KWARGS = dict(
    policy_id="CER", policy_version="1.0.0", snapshot_id="TEST-SNAP",
    snapshot_hash="test-hash", source_commit="test", required_checks=("EVIDENCE",),
)


@pytest.fixture
def pack() -> REDomainPack:
    p = REDomainPack()
    p.load()
    return p


def test_domain_pack_identity(pack: REDomainPack) -> None:
    assert pack.domain_id == "RE"
    assert pack.version


def test_domain_pack_policy_loaded_and_identity_matches_code(pack: REDomainPack) -> None:
    """Phase 1 (structural refactor): domains/re/domain_pack.yaml, conforming
    to schemas/domain_pack.schema.yaml, was cherry-picked from the unmerged
    p0/re-domain-pack-v0.1 branch (11_Audit/LSN-0001) rather than re-authored.
    This test pins the two artifacts together so they cannot silently drift:
    if someone bumps DOMAIN_VERSION in code without updating the YAML (or
    vice versa), this fails loudly instead of the two quietly diverging."""
    assert pack.policy, "domains/re/domain_pack.yaml did not load"
    assert pack.policy["domain_id"] == pack.domain_id
    assert pack.policy["version"] == pack.version
    assert "equipment" in pack._ontology_entities
    assert "chamber" in pack._ontology_entities


def test_ontology_entities_are_tagged_on_matching_fragments(pack: REDomainPack) -> None:
    tagged = [f for f in pack._fragments if f.metadata.get("ontology_entities")]
    assert tagged, "expected at least one fragment tagged with an ontology entity"
    assert any("chamber" in f.metadata["ontology_entities"] for f in tagged)


def test_load_without_kernel_modification(pack: REDomainPack) -> None:
    """RE_POC.md acceptance target: 'Domain Pack load without kernel
    modification = PASS'. This Domain Pack only imports from interfaces.py
    (the protocol) and standalone stdlib -- it does not import or require
    changes to cer_runtime.py or factory_runtime.py."""
    import inspect
    import re_domain_pack as mod

    source = inspect.getsource(mod)
    import_lines = [ln for ln in source.splitlines() if ln.strip().startswith(("import ", "from "))]
    imports = "\n".join(import_lines)
    assert "cer_runtime" not in imports
    assert "factory_runtime" not in imports


def test_ingest_returns_documents() -> None:
    pack = REDomainPack()
    docs = pack.ingest()
    assert len(docs) == len(CORPUS)
    assert all(isinstance(d, Document) for d in docs)


def test_parse_splits_into_multiple_fragments() -> None:
    pack = REDomainPack()
    doc = pack.ingest()[0]
    chunks = pack.parse(doc)
    assert len(chunks) >= 2
    assert all(isinstance(c, str) and c for c in chunks)


def test_normalize_extracts_frequency_and_level_metadata() -> None:
    pack = REDomainPack()
    doc = next(d for d in pack.ingest() if d.document_id == "DOC-RE-001" and d.revision_id == "REV-A")
    fragments = pack.normalize(doc)
    freq_hits = [f for f in fragments if "frequencies" in f.metadata]
    level_hits = [f for f in fragments if "levels" in f.metadata]
    assert freq_hits, "expected at least one fragment with extracted frequency metadata"
    assert level_hits, "expected at least one fragment with extracted dBuV/m level metadata"


def test_retrieve_finds_relevant_document(pack: REDomainPack) -> None:
    results = pack.retrieve("What is the CISPR 32 Class B limit at 3 meters for 30 to 230 MHz?", top_k=5)
    assert results
    assert results[0].document_id == "DOC-RE-002"
    assert results[0].score > 0


def test_retrieve_abstains_on_out_of_corpus_query(pack: REDomainPack) -> None:
    """The core M1 abstention requirement (RE_POC.md 'evidence sufficiency
    / abstention'): an out-of-corpus question must return no evidence, not
    a deceptively-scored 'closest' fragment."""
    results = pack.retrieve("What is the recommended lunar regolith shielding thickness?", top_k=5)
    assert results == []


def test_retrieve_ranks_multiple_revisions_of_same_document(pack: REDomainPack) -> None:
    results = pack.retrieve("EUT-7 132 MHz peak ferrite choke mitigation retest", top_k=5)
    doc_ids = {e.document_id for e in results}
    assert "DOC-RE-001" in doc_ids
    revisions = {e.revision_id for e in results if e.document_id == "DOC-RE-001"}
    assert "REV-A" in revisions or "REV-B" in revisions


def test_verify_grounded_claim(pack: REDomainPack) -> None:
    evidence = pack.retrieve("CISPR 32 Class B limit 30 to 230 MHz", top_k=1)
    claim = Claim("C-1", "The CISPR 32 Class B limit for 30-230 MHz", "answer", [evidence[0].evidence_id], 0.9)
    result = pack.verify([claim], evidence)
    assert result["claims"]["C-1"]["grounded"] is True
    assert result["all_grounded"] is True


def test_verify_ungrounded_claim_when_evidence_missing(pack: REDomainPack) -> None:
    claim = Claim("C-2", "Completely unrelated statement about spacecraft propulsion", "answer", ["E-MISSING"], 0.9)
    result = pack.verify([claim], [])
    assert result["claims"]["C-2"]["grounded"] is False
    assert result["all_grounded"] is False


def test_evaluate_recall_and_abstention() -> None:
    pack = REDomainPack()
    case = {"case_id": "X", "expected_document_ids": ["DOC-RE-002"], "min_recall": 1.0, "expect_abstain": False}
    good_result = {"evidence": pack.retrieve("CISPR 32 Class B 30 to 230 MHz"), "cer_result": "PASS"}
    score = pack.evaluate(case, good_result)
    assert score["evidence_recall"] == 1.0
    assert score["passed"] is True

    abstain_case = {"case_id": "Y", "expected_document_ids": [], "expect_abstain": True}
    abstain_result = {"evidence": [], "cer_result": "BLOCK"}
    abstain_score = pack.evaluate(abstain_case, abstain_result)
    assert abstain_score["abstained"] is True
    assert abstain_score["passed"] is True


def test_render_report_contains_query_and_evidence(pack: REDomainPack) -> None:
    evidence = pack.retrieve("CISPR 32 Class B limit", top_k=1)
    report = pack.render_report({"query": "test query", "evidence": evidence, "claims": [], "cer_result": "PASS"})
    assert "test query" in report
    assert evidence[0].evidence_id in report


def test_cer_gate_blocks_unsupported_re_claim(pack: REDomainPack) -> None:
    """End-to-end: a claim citing evidence that doesn't exist in the
    retrieved pool must BLOCK through the *existing, unmodified* CER gate
    -- this is the RE_POC.md acceptance target in practice."""
    gate = CERGateRuntime()
    from interfaces import CERSnapshot
    snapshot = CERSnapshot(**SNAPSHOT_KWARGS)
    claim = Claim("C-BAD", "Unsupported RE claim", "answer", ["E-DOES-NOT-EXIST"], 0.9)
    decision = gate.evaluate(snapshot=snapshot, run_id="R1", gate_id="RE-QA", claims=[claim], evidence=[])
    assert decision.result == "BLOCK"


def test_cer_gate_passes_grounded_re_claim(pack: REDomainPack) -> None:
    gate = CERGateRuntime()
    from interfaces import CERSnapshot
    snapshot = CERSnapshot(**SNAPSHOT_KWARGS)
    evidence = pack.retrieve("CISPR 32 Class B limit 30 to 230 MHz", top_k=1)
    claim = Claim("C-GOOD", "Grounded RE claim", "answer", [evidence[0].evidence_id], 0.9)
    decision = gate.evaluate(snapshot=snapshot, run_id="R2", gate_id="RE-QA", claims=[claim], evidence=evidence)
    assert decision.result == "PASS"


# -- Benchmark-driven regression (templates/benchmark/re_hybrid_rag_v0.1.json) --

def _load_benchmark_cases() -> list[dict]:
    return json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))["cases"]


def _load_benchmark() -> dict:
    return json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))


# The 15 cases of the original first slice. These stay pinned per-case: they
# are the regression set, and any one of them breaking is a defect regardless
# of what the aggregate metrics say.
_PINNED_REGRESSION_CASES = [f"RE-BC-{n:03d}" for n in range(1, 16)]


@pytest.mark.parametrize(
    "case",
    [c for c in _load_benchmark_cases() if c["case_id"] in _PINNED_REGRESSION_CASES],
    ids=lambda c: c["case_id"],
)
def test_pinned_regression_case_still_behaves(pack: REDomainPack, case: dict) -> None:
    evidence = pack.retrieve(case["query"], top_k=10)
    if case.get("expect_abstain"):
        assert evidence == [], f"{case['case_id']} expected abstention (no evidence) but got results"
        return
    retrieved_docs = {e.document_id for e in evidence}
    expected_docs = set(case["expected_document_ids"])
    recall = len(retrieved_docs & expected_docs) / len(expected_docs) if expected_docs else 1.0
    assert recall >= case.get("min_recall", 1.0), (
        f"{case['case_id']} ({case['query_type']}): recall {recall}; "
        f"retrieved={retrieved_docs} expected={expected_docs}"
    )


# Beyond the pinned set the benchmark is judged the way docs/RE_POC.md judges
# it -- on aggregate acceptance targets. Requiring all 159 cases to pass would
# not be a stricter test, it would be a weaker benchmark: the only way to keep
# such a gate green is to write cases the retriever already handles, which is
# how a benchmark ends up measuring nothing. The targets live in the benchmark
# file so the bar and the cases move together.

# Scored by running the demo, not by reimplementing it here.
#
# This used to recompute recall and abstention from pack.retrieve() alone, and
# the two drifted the moment claim verification landed: the demo gates on
# retrieve -> verify -> CER, so a claim whose evidence does not support it now
# BLOCKs, while a test looking only at retrieval could not see that and
# reported the old number. Two places encoding one definition is the same
# defect this codebase has already hit at the D-02 override and at the
# evidence gate's benchmark rule. There is one definition, and it is the one
# that ships.

def _acceptance() -> dict:
    from scripts import re_demo

    return re_demo.run()["acceptance"]


def _bands() -> dict[str, dict[str, int]]:
    return _acceptance()["abstention_by_band"]


def test_evidence_recall_meets_the_acceptance_target() -> None:
    """Scored on what the retriever earns, not on the headline.

    11 of the 139 answerable cases have queries whose every informative term
    already appears in the document the benchmark expects back. They cannot
    really fail, they pass at 100%, and they lift the headline by 0.008.
    Gating on the headline would let a regression hide behind them.
    """
    acceptance = _acceptance()
    target = acceptance["evidence_recall_target"]
    earned = acceptance["evidence_recall_excluding_verbatim"]
    assert acceptance["evidence_recall_gated_on"] == "evidence_recall_excluding_verbatim"
    assert earned >= target, f"earned Evidence Recall@10 {earned:.3f} < target {target}"
    # And the margin is thin. Recorded so nobody reads 0.914 as comfortable.
    assert earned < acceptance["evidence_recall_at_10"], (
        "the verbatim split stopped separating anything -- either the benchmark "
        "changed or query_is_verbatim_in_its_answer regressed"
    )


def test_self_answering_cases_are_detected_rather_than_hand_labelled(pack: REDomainPack) -> None:
    """A hand-labelled 'this one is easy' flag drifts the moment a document is
    edited and nobody re-checks, so it is computed from the corpus instead."""
    cases = {c["case_id"]: c for c in _load_benchmark_cases()}
    # RE-BC-009 abstains; an abstention case has no expected document and can
    # never be verbatim-contained.
    assert not pack.query_is_verbatim_in_its_answer(cases["RE-BC-009"])
    flagged = [cid for cid, c in cases.items() if pack.query_is_verbatim_in_its_answer(c)]
    assert len(flagged) == _acceptance()["verbatim_case_count"] == 11, flagged


def test_abstention_is_perfect_on_the_bands_that_are_decidable() -> None:
    """Two of the three abstention bands must never be missed.

    A question about a subject outside the domain, or about an equipment or
    chamber identifier the corpus does not contain, is decidable from corpus
    statistics alone -- the terms that carry the question are simply absent.
    Missing one of these is a defect, not a limitation.
    """
    bands = _bands()
    for band in ("subject_outside_domain", "entity_absent_from_corpus"):
        assert bands[band]["held"] == bands[band]["total"], f"{band}: {bands[band]}"


def test_near_miss_abstention_limitation_is_still_what_the_record_says() -> None:
    """The third band is a measured open limitation (OPEN_DECISIONS D-11), and
    this test exists so it cannot drift quietly in either direction.

    A near-miss query names real RE subject matter this corpus happens not to
    cover -- conducted emission, immunity, ESD, another standard. No threshold
    on lexical statistics separates it from an answerable question; that was
    measured for eight retrieval-side statistics and again for five
    verification-side ones.

    4/8 rather than 3/8 because claim verification catches one more as a side
    effect: where the cited evidence supplies too little of what the question
    asks, the gate BLOCKs. That is not a fix for the band -- it is a partial
    catch, and the register says which is which. If this number moves again,
    update D-11 and this test together.
    """
    band = _bands()["near_miss_domain_subject"]
    assert band == {"held": 4, "total": 8}, (
        f"near-miss abstention is now {band}, recorded as 4/8. "
        "Update OPEN_DECISIONS D-11 and this test together."
    )


def test_benchmark_covers_the_whole_query_taxonomy() -> None:
    """docs/RE_POC.md lists 9 categories. The first slice covered 7 of them and
    said so; at 159 cases there is no excuse for a gap."""
    query_types = {c["query_type"] for c in _load_benchmark_cases()}
    assert len(query_types) == 9, sorted(query_types)


def test_benchmark_meets_the_poc_case_count() -> None:
    assert len(_load_benchmark_cases()) >= 150


# --- M1-1: measurement-aware tokenization ------------------------------------
#
# The RE domain's content *is* numbers with units -- frequencies, limit levels,
# separation distances, revision ids. Before 2026-08-25 the tokenizer was
# `[a-z0-9]+` over lowercased text, which shattered every one of them:
# "5.8 GHz" became ['5','8','ghz'] and "REV-A"/"REV-B" became ['rev','a'] /
# ['rev','b']. normalize() already extracted frequencies and levels into
# fragment metadata, so the pack knew they mattered -- the retriever just could
# not see them.

from re_domain_pack import _tokenize  # noqa: E402


def test_decimal_measurements_survive_tokenization() -> None:
    """A decimal must not be split into two meaningless integers."""
    tokens = _tokenize("peak of 38.2 dBuV/m")
    # The requirement is that the measurement is not shattered -- not that a
    # bare "38.2" appears. Keeping the value attached to its unit is stronger:
    # "38.2 dBuV/m" and "38.2 MHz" are different facts.
    assert "38" not in tokens and "2" not in tokens, tokens
    assert any("38.2" in t for t in tokens), tokens


def _numeric(tokens):
    """Tokens carrying a digit -- the measurement-bearing ones."""
    return {t for t in tokens if any(ch.isdigit() for ch in t)}


def test_frequency_is_a_single_token_and_normalized_across_units() -> None:
    """5.8 GHz and 5800 MHz are the same frequency. A retriever that cannot see
    that cannot answer an RE question about a band. Compares only the
    measurement-bearing tokens, so shared prose words cannot fake a pass."""
    ghz = _numeric(_tokenize("interference at 5.8 GHz"))
    mhz = _numeric(_tokenize("interference at 5800 MHz"))
    assert ghz & mhz, f"no shared frequency token: {sorted(ghz)} vs {sorted(mhz)}"


def test_distinct_measurements_do_not_collide() -> None:
    """'38.2 dBuV/m at 132 MHz' and '32.8 dBuV/m at 138 MHz' are different
    findings. Under bare-digit tokenization they shared every numeric token."""
    # Digit-reversal is the sharpest case: under bare-digit tokenization
    # "5.8 GHz" and "8.5 GHz" produce the identical token set {5, 8, ghz}.
    a = _numeric(_tokenize("emission at 5.8 GHz"))
    b = _numeric(_tokenize("emission at 8.5 GHz"))
    assert a != b, f"5.8 GHz and 8.5 GHz tokenize identically: {sorted(a)}"
    c = _numeric(_tokenize("peak 38.2 dBuV/m at 132 MHz"))
    d = _numeric(_tokenize("peak 13.2 dBuV/m at 238 MHz"))
    assert not (c & d), f"different findings collide on {sorted(c & d)}"


def test_revision_identifiers_are_distinguishable() -> None:
    """RC/benchmark revision_comparison depends on telling REV-A from REV-B."""
    a = set(_tokenize("as recorded in REV-A"))
    b = set(_tokenize("as recorded in REV-B"))
    assert a != b
    assert ("rev-a" in a) or ("reva" in a), sorted(a)


def test_equipment_identifiers_are_distinguishable() -> None:
    """EUT-7 and EUT-99 are different devices; the abstention benchmark case
    turns on exactly this."""
    a = set(_tokenize("device EUT-7 under test"))
    assert ("eut-7" in a) or ("eut7" in a), sorted(a)
    # EUT-7 must not read as the bare number 7, which collides with every
    # unrelated "7" in the corpus -- distances, counts, channel numbers.
    assert "7" not in a, sorted(a)


def test_unit_spelling_variants_normalize_together() -> None:
    """Legacy documents spell the field-strength unit inconsistently."""
    variants = ["38.2 dBuV/m", "38.2 dBuV/M", "38.2 dbuv/m"]
    token_sets = [set(_tokenize(v)) for v in variants]
    assert token_sets[0] == token_sets[1] == token_sets[2], [sorted(s) for s in token_sets]
    # And the level must be one token, not a number sitting next to a unit
    # fragment -- "38.2 dBuV/m" and "38.2 dBuV" are different assertions.
    assert any(("dbuv" in t and "38.2" in t) for t in token_sets[0]), sorted(token_sets[0])


def test_plain_words_still_tokenize() -> None:
    """The measurement handling must not break ordinary lexical retrieval.

    The requirement is that an ordinary word is *matchable*, not that its
    surface form survives -- the tokenizer stems, so asserting `"shielded" in
    tokens` was asserting that stemming does not happen. What retrieval needs
    is that the same word in a query and in a document lands on one token,
    including across inflection.
    """
    tokens = _tokenize("the shielded enclosure and connector")
    assert len(tokens) == 5, tokens
    for word in ("shielded", "enclosure", "connector"):
        assert _tokenize(word)[0] in tokens, (word, tokens)
    # Inflected forms must meet, or a query term looks absent from a document
    # that plainly discusses it.
    for a, b in (("shielded", "shielding"), ("route", "routed"), ("harness", "harnesses")):
        assert _tokenize(a) == _tokenize(b), (a, b, _tokenize(a), _tokenize(b))


def test_measurement_policy_matches_the_code_that_implements_it() -> None:
    """Same code<->YAML consistency guarantee the ontology has: the declarative
    Domain Pack policy and the tokenizer must not drift apart, or the policy
    becomes documentation of something that is not happening."""
    import yaml
    from decimal import Decimal
    from re_domain_pack import _FREQ_TO_MHZ, _LEVEL_UNITS, _ID_PREFIXES, POLICY_PATH

    policy = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))["measurement_policy"]
    assert policy["canonical_frequency_unit"].lower() == "mhz"
    assert {k: Decimal(str(v)) for k, v in policy["frequency_units"].items()} == _FREQ_TO_MHZ
    assert tuple(policy["level_units"]) == _LEVEL_UNITS
    assert tuple(policy["identifier_prefixes"]) == _ID_PREFIXES


# --- claim verification: the Domain Pack's half of a kernel mechanism --------

def test_claim_grounding_floor_comes_from_the_policy_not_the_code() -> None:
    """Same code<->YAML guarantee the ontology and measurement policy have.

    The threshold is corpus-fitted and belongs to the domain; the kernel owns
    only the mechanism. If these drift, the policy file becomes documentation
    of something that is not happening -- which is exactly the state
    `require_evidence_for_claims` was in before the verifier existed.
    """
    import yaml

    policy = yaml.safe_load(
        (Path(__file__).resolve().parents[1] / "domains" / "re" / "domain_pack.yaml")
        .read_text(encoding="utf-8")
    )
    declared = policy["verification_policy"]["claim_grounding_floor"]
    assert REDomainPack().claim_verifier.grounding_floor == declared


def test_a_pack_with_no_policy_file_still_verifies() -> None:
    """load_domain_policy supports a code-only minimal mode. The verifier has
    to work there too, or the fallback mode silently stops enforcing grounding
    rather than failing loudly."""
    minimal = REDomainPack(policy={})
    assert minimal.claim_verifier.grounding_floor > 0


def test_verification_names_what_the_evidence_did_not_supply(pack: REDomainPack) -> None:
    """The reviewer-facing half of OPEN_DECISIONS D-11's mitigation: where the
    threshold cannot decide a near-miss, the report still says which part of
    the question went unanswered."""
    query = "What field strength is applied during a radiated immunity test?"
    evidence = pack.retrieve(query, top_k=3)
    assert evidence, "expected this near-miss query to retrieve something"
    claim = Claim("C-NM", query, "answer", [evidence[0].evidence_id], 0.5)
    report = pack.verify([claim], evidence)
    assert "immunity" in report["claims"]["C-NM"]["unsupported_terms"]


# --- retrieval methods (docs/RE_POC.md: "3 retrieval methods minimum") -------

def test_the_three_declared_modes_are_all_selectable(pack: REDomainPack) -> None:
    from re_domain_pack import RETRIEVAL_MODES

    assert set(RETRIEVAL_MODES) == {"bm25", "trigram", "hybrid"}
    for mode in RETRIEVAL_MODES:
        assert pack.retrieve("What caused the 375 MHz exceedance on EUT-31?",
                             top_k=3, mode=mode)


def test_the_modes_actually_rank_differently(pack: REDomainPack) -> None:
    """Three names over one behaviour would satisfy the letter of the PoC
    requirement and none of its point."""
    query = "What caused the 375 MHz exceedance on EUT-31?"
    ordering = {m: [e.fragment_id for e in pack.retrieve(query, top_k=5, mode=m)]
                for m in ("bm25", "trigram", "hybrid")}
    assert ordering["bm25"] != ordering["trigram"], ordering


def test_an_unimplemented_mode_raises_on_every_call(pack: REDomainPack) -> None:
    """`retrieval_policy.allowed_modes` also lists vector, graph and agentic,
    and none exists (OPEN_DECISIONS D-12). Selecting one must raise -- including
    for a query that abstains early, where returning [] would read as "vector
    retrieval found nothing" rather than "there is no vector retrieval"."""
    for query in ("What caused the EUT-31 exceedance?",          # answerable
                  "What quarterly revenue did the lab report?"):  # abstains early
        with pytest.raises(ValueError, match="unknown retrieval mode"):
            pack.retrieve(query, mode="vector")


def test_recall_at_10_cannot_separate_the_methods_and_the_rank_metrics_can() -> None:
    """The measurement finding that forced R@1 and MRR into the demo.

    Every blend from pure trigram to pure BM25 scores the same Recall@10,
    because the coverage floor and the abstention rules decide the result set
    rather than the ranking. Reported as an assertion so that if a future
    change makes Recall@10 discriminating again, someone notices and revisits
    which metric the PoC target should be stated against.
    """
    from scripts import re_demo

    scores = {}
    for mode in ("bm25", "trigram", "hybrid"):
        summary = re_demo.run(mode=mode)["acceptance"]
        scores[mode] = (summary["evidence_recall_at_10"], summary["mean_reciprocal_rank"])

    recalls = {v[0] for v in scores.values()}
    assert len(recalls) == 1, f"Recall@10 now separates the methods: {scores}"
    assert scores["trigram"][1] < scores["bm25"][1], scores
