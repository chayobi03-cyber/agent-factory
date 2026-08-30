"""What a benchmark has to carry, and what happens when it does not.

The real RE documents arrive from outside the tree (OPEN_DECISIONS D-08), so
the first thing anyone does with this repository's tooling is point it at a
corpus it has never seen. Three defects made that first day report the wrong
thing, and each is pinned here by the case that used to pass:

1. `scripts/re_demo.py` took `--corpus` but not `--benchmark`, so a foreign
   corpus was scored against the in-tree answer key and reported
   `Evidence Recall@10 : 0.000 ... acceptance targets NOT MET`. The reader
   concludes their documents are bad. `calibrate_retrieval.py` had always
   refused exactly this mismatch; the rule simply was not in both places.

2. `calibrate_retrieval.py` had two verdicts where it needed three. A sweep
   that could not measure its constant had to claim `FITS`, and two did: the
   ceiling sweep whenever the benchmark carried no banded abstention case, and
   the mode sweep unconditionally. Measured on a six-document corpus, the tool
   printed a table showing the shipped ceiling costing a third of the recall
   and then declared every constant correct, exit 0.

3. `abstention_band` decides whether (2) can measure anything at all, and was
   documented nowhere -- it existed only inside the RE benchmark's own JSON. A
   benchmark authored from `docs/ADDING_A_DOMAIN.md` could not have carried it.
   It is documented now, and the documentation is pinned to the code here so
   the two cannot drift.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (str(SRC), str(ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

import corpus_source  # noqa: E402
import re_domain_pack as rdp  # noqa: E402
from corpus_source import (  # noqa: E402
    ABSTENTION_BANDS,
    DECIDABLE_ABSTENTION_BANDS,
    UNDECIDABLE_ABSTENTION_BANDS,
    from_documents,
    missing_benchmark_documents,
)
from re_domain_pack import REDomainPack  # noqa: E402
from scripts import calibrate_retrieval as cal  # noqa: E402
from scripts import re_demo  # noqa: E402

GUIDE = ROOT / "docs/ADDING_A_DOMAIN.md"

#: A corpus that shares no document identifier with the in-tree synthetic one.
FOREIGN_DOCS = [
    {"document_id": "EMC-SPEC-007", "revision_id": "REV-A",
     "title": "Internal EMC Acceptance Specification", "doc_type": "specification",
     "text": "All units shall meet the Class B radiated emission limits with a minimum "
             "margin of 3 dB across 30 to 1000 MHz, measured at 3 meters in a semi "
             "anechoic chamber with the unit in its worst case operating mode."},
    {"document_id": "EMC-FMEA-015", "revision_id": "REV-A",
     "title": "Switching Regulator Emission Failure Modes", "doc_type": "failure_analysis",
     "text": "Known emission failure modes for the DC DC stage include insufficient input "
             "filtering, a floating heatsink acting as a patch radiator, and harness "
             "common mode coupling. The heatsink shall be bonded to chassis where a "
             "floating conductor is suspected."},
]


def _case(case_id, query, expected, *, abstain=False, band=None):
    case = {"case_id": case_id, "query": query, "query_type": "definition_factual",
            "expected_document_ids": expected, "expect_abstain": abstain,
            "min_recall": 0.0 if abstain else 1.0}
    if band:
        case["abstention_band"] = band
    return case


FOREIGN_CASES = [
    _case("FC-001", "What is the minimum margin required against the Class B limit?",
          ["EMC-SPEC-007"]),
    _case("FC-002", "What should be done when a floating heatsink is suspected?",
          ["EMC-FMEA-015"]),
]


def _write_benchmark(tmp_path: Path, cases, benchmark_id="FOREIGN-BENCH") -> Path:
    path = tmp_path / "benchmark.json"
    path.write_text(json.dumps({
        "benchmark_id": benchmark_id, "version": "0.1", "cases": cases,
        "acceptance_targets": {"evidence_recall_at_10": 0.90},
    }), encoding="utf-8")
    return path


def _write_corpus(tmp_path: Path) -> Path:
    d = tmp_path / "corpus"
    d.mkdir()
    for i, doc in enumerate(FOREIGN_DOCS):
        (d / f"doc-{i:03d}.json").write_text(json.dumps(doc), encoding="utf-8")
    return d


# --- 1. one mismatch rule, reachable from both tools -------------------------

def test_the_mismatch_rule_lives_in_the_kernel():
    """Both tools import it from here. Two copies is how one of them lost it."""
    assert missing_benchmark_documents is corpus_source.missing_benchmark_documents
    assert cal.missing_benchmark_documents is missing_benchmark_documents
    assert re_demo.missing_benchmark_documents is missing_benchmark_documents


def test_no_tool_writes_the_band_names_out_for_itself():
    """The tuple was literal in both scripts before this; the kernel copy only
    helps while nothing drifts back to a literal.

    Found by sabotage: reverting `re_demo.py` to its own `("subject_outside_
    domain",)` left every other test in this file green, which made the
    de-duplication a claim with no mechanism behind it -- the exact shape of
    defect the de-duplication was for.
    """
    for script in (ROOT / "scripts/re_demo.py", ROOT / "scripts/calibrate_retrieval.py"):
        body = script.read_text(encoding="utf-8")
        for band in ABSTENTION_BANDS:
            assert f'"{band}"' not in body, (
                f"{script.name} spells out {band!r}. Import the vocabulary from "
                f"corpus_source instead; two copies is how they drifted."
            )
        assert "DECIDABLE_ABSTENTION_BANDS" in body


def test_both_tools_share_the_kernel_band_vocabulary():
    assert cal.DECIDABLE_ABSTENTION_BANDS is DECIDABLE_ABSTENTION_BANDS
    assert re_demo.DECIDABLE_ABSTENTION_BANDS is DECIDABLE_ABSTENTION_BANDS


def test_a_benchmark_naming_absent_documents_is_reported():
    missing = missing_benchmark_documents(
        [{"expected_document_ids": ["DOC-RE-001", "EMC-SPEC-007"]}], FOREIGN_DOCS
    )
    assert missing == ["DOC-RE-001"]


def test_an_abstention_case_names_no_document_and_so_cannot_mismatch():
    """`expected_document_ids: []` is the normal shape of an abstention case."""
    assert missing_benchmark_documents([{"expected_document_ids": []}], FOREIGN_DOCS) == []


def test_re_demo_refuses_a_foreign_corpus_against_the_in_tree_benchmark(tmp_path):
    """The defect, reproduced: this used to score 0.000 and report NOT MET."""
    with pytest.raises(re_demo.BenchmarkError) as exc:
        re_demo.run(corpus=str(_write_corpus(tmp_path)))
    assert "DOC-RE-001" in str(exc.value)
    assert "--benchmark" in str(exc.value)


def test_re_demo_scores_a_benchmark_written_for_the_corpus(tmp_path):
    summary = re_demo.run(corpus=str(_write_corpus(tmp_path)),
                          benchmark_path=str(_write_benchmark(tmp_path, FOREIGN_CASES)))
    assert summary["benchmark_id"] == "FOREIGN-BENCH"
    assert summary["cases_total"] == len(FOREIGN_CASES)
    assert summary["corpus"]["documents"] == len(FOREIGN_DOCS)


def test_re_demo_exposes_benchmark_on_the_command_line(tmp_path):
    """Driven through the CLI, not `run()`.

    Every other test here calls `run(benchmark_path=...)`, which stayed green
    when the `--benchmark` argument was deleted from the parser -- so the tests
    covered the capability and not the way anyone reaches it. A person with
    their own corpus meets the command line first.
    """
    help_text = subprocess.run(
        [sys.executable, str(ROOT / "scripts/re_demo.py"), "--help"],
        capture_output=True, text=True, cwd=ROOT, check=True,
    ).stdout
    assert "--benchmark" in help_text

    done = subprocess.run(
        [sys.executable, str(ROOT / "scripts/re_demo.py"),
         "--corpus", str(_write_corpus(tmp_path))],
        capture_output=True, text=True, cwd=ROOT,
    )
    assert done.returncode == 2, "a mismatched benchmark is a usage error, not a bad score"
    assert "benchmark error" in done.stderr


def test_re_demo_still_defaults_to_the_in_tree_benchmark():
    """`--benchmark` is opt-in; omitting it must not change what CI measures."""
    assert re_demo.load_benchmark()["benchmark_id"] == re_demo.load_benchmark(None)["benchmark_id"]


# --- 2. a sweep that cannot measure says so ----------------------------------

@pytest.fixture(scope="module")
def foreign_pack() -> REDomainPack:
    pack = REDomainPack()
    pack.load(from_documents(FOREIGN_DOCS, origin="test:foreign"))
    return pack


def test_the_three_verdicts_are_distinct():
    assert len({cal.FITS, cal.STALE, cal.UNVERIFIED}) == 3


def test_an_unbanded_benchmark_leaves_the_ceiling_unverified(foreign_pack, capsys):
    """The defect, reproduced. These cases carry no `abstention_band`, so the
    selection rule has nothing to select on -- which used to return FITS."""
    verdict = cal.sweep_unseen_ceiling(foreign_pack, FOREIGN_CASES, rdp._UNSEEN_TERM_CEILING)
    assert verdict == cal.UNVERIFIED
    out = capsys.readouterr().out
    assert "UNVERIFIED" in out
    assert "abstention_band" in out


def test_a_banded_benchmark_lets_the_ceiling_be_judged(foreign_pack):
    """With bands present the sweep reaches a real verdict -- either one."""
    banded = FOREIGN_CASES + [
        _case("FC-003", "What is the shear modulus of the potting compound?", [],
              abstain=True, band="entity_absent_from_corpus"),
        _case("FC-004", "What were the gearbox mounting bolt torques?", [],
              abstain=True, band="subject_outside_domain"),
    ]
    verdict = cal.sweep_unseen_ceiling(foreign_pack, banded, rdp._UNSEEN_TERM_CEILING)
    assert verdict in (cal.FITS, cal.STALE)


def test_modes_tied_on_every_metric_are_unverified(foreign_pack, capsys):
    verdict = cal.sweep_modes(foreign_pack, FOREIGN_CASES)
    assert verdict == cal.UNVERIFIED
    assert "UNVERIFIED" in capsys.readouterr().out


def test_modes_separated_by_r1_are_not_unverified(pack_in_tree, capsys):
    """Recall@10 ties across all three modes on the in-tree corpus while R@1 and
    MRR separate trigram from the rest. That is the D-14 finding about Recall@10
    being blind, not an inability to compare -- and a first version of the tie
    rule keyed off Recall@10 alone and turned the in-tree run non-zero."""
    assert cal.sweep_modes(pack_in_tree, IN_TREE_CASES) == cal.FITS
    assert "Judge on R@1/MRR" in capsys.readouterr().out


IN_TREE_CASES = json.loads(
    (ROOT / "templates/benchmark/re_hybrid_rag_v0.1.json").read_text(encoding="utf-8")
)["cases"]


@pytest.fixture(scope="module")
def pack_in_tree() -> REDomainPack:
    pack = REDomainPack()
    pack.load()
    return pack


# --- 3. the guide and the code agree on the bands ----------------------------

def _bands_documented_in_the_guide() -> set[str]:
    """Band names from the guide's band table, as backticked cells."""
    text = GUIDE.read_text(encoding="utf-8")
    start = text.index("### Every abstention case needs a band")
    end = text.index("\n### ", start + 1)
    return set(re.findall(r"^\| `([a-z_]+)` \|", text[start:end], re.MULTILINE))


def test_the_guide_documents_exactly_the_bands_the_kernel_defines():
    assert _bands_documented_in_the_guide() == set(ABSTENTION_BANDS)


def test_the_guide_marks_the_undecidable_band_as_undecidable():
    """The distinction is the point of the table: two bands derive the ceiling
    and one cannot, and a reader who labels every abstention case
    `near_miss_domain_subject` gets UNVERIFIED without being told why."""
    text = GUIDE.read_text(encoding="utf-8")
    start = text.index("### Every abstention case needs a band")
    end = text.index("\n### ", start + 1)
    rows = {
        band: rest
        for band, rest in re.findall(r"^\| `([a-z_]+)` \|([^\n]*)\|", text[start:end], re.MULTILINE)
    }
    for band in DECIDABLE_ABSTENTION_BANDS:
        assert rows[band].rstrip().endswith("yes"), f"{band} is decidable and the table should say so"
    for band in UNDECIDABLE_ABSTENTION_BANDS:
        assert "no" in rows[band].rsplit("|", 1)[-1]


def test_the_guides_example_benchmark_is_a_benchmark_this_code_can_read():
    """Extracted from the guide and run through the same reader the tools use.
    A documented example that does not parse is worse than no example."""
    text = GUIDE.read_text(encoding="utf-8")
    # Scoped to the benchmark section: the guide's first JSON block is a
    # document, not a benchmark, and an unscoped search finds that one.
    start = text.index("## Write the benchmark")
    end = text.index("\n## ", start + 1)
    block = re.search(r"```json\n(\{.*?\})\n```", text[start:end], re.DOTALL)
    assert block, "the benchmark section should carry a JSON example"
    example = json.loads(block.group(1))
    assert example["cases"], "the example should carry at least one case"
    for case in example["cases"]:
        assert {"case_id", "query", "query_type", "expected_document_ids",
                "expect_abstain"} <= set(case)
        if case["expect_abstain"]:
            assert case["abstention_band"] in ABSTENTION_BANDS
    # The mismatch guard reads it the same way it reads a real one.
    assert missing_benchmark_documents(example["cases"], []) == ["SPEC-007"]


def test_the_guide_tells_the_reader_how_to_score_with_their_own_benchmark():
    text = GUIDE.read_text(encoding="utf-8")
    assert "--benchmark" in text
    assert "UNVERIFIED" in text


# --- 4. RE_POC's abstention target says what the gate actually does ----------

RE_POC = ROOT / "docs/RE_POC.md"


def _abstention_targets_stated_in_re_poc() -> dict[str, bool]:
    """{band: is it gated} as `docs/RE_POC.md` states it.

    A gated band carries a numeric target; the undecidable one is marked
    "reported, not gated". Parsed rather than eyeballed because this exact
    statement is what drifted: the document said `>= 0.90` over all abstention
    cases while the gate required the two decidable bands to be perfect and
    reported the third separately. The run scored 0.75 against a target the
    gate had never checked, and both readings looked correct in isolation.
    """
    text = RE_POC.read_text(encoding="utf-8")
    start = text.index("Negative-case Abstention — stated per band")
    end = text.index("This replaces", start)
    stated: dict[str, bool] = {}
    for band, rest in re.findall(r"- `([a-z_]+)`([^\n]*)", text[start:end]):
        stated[band] = "not gated" not in rest
    return stated


def test_re_poc_states_a_target_for_every_band():
    assert set(_abstention_targets_stated_in_re_poc()) == set(ABSTENTION_BANDS)


def test_re_poc_gates_exactly_the_bands_the_kernel_calls_decidable():
    """The document and the gate have to name the same rule.

    Not the measured figures -- those move legitimately and pinning them would
    make the document brittle. What must not drift is *which* bands are gated,
    because a document describing a different rule than the code is the defect
    this entry was opened for (OPEN_DECISIONS D-15, branch 4).
    """
    stated = _abstention_targets_stated_in_re_poc()
    gated = {band for band, is_gated in stated.items() if is_gated}
    assert gated == set(DECIDABLE_ABSTENTION_BANDS), (
        f"RE_POC.md gates {sorted(gated)} while the kernel calls "
        f"{sorted(DECIDABLE_ABSTENTION_BANDS)} decidable"
    )
    ungated = {band for band, is_gated in stated.items() if not is_gated}
    assert ungated == set(UNDECIDABLE_ABSTENTION_BANDS)


def test_re_poc_no_longer_states_the_single_abstention_figure():
    """The superseded target, kept out of the list rather than left beside it."""
    text = RE_POC.read_text(encoding="utf-8")
    listed = re.findall(r"^- Negative-case Abstention >= 0\.90\s*$", text, re.MULTILINE)
    assert listed == [], "the single-figure target is still stated as a live target"
