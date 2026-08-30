"""The calibration tool has to be able to say "these constants are wrong".

Four numbers decide how retrieval behaves and every one is corpus-fitted. The
tool exists so that re-deriving them against a new corpus is a command rather
than an archaeology exercise -- which matters because the real RE documents
arrive from outside the tree (OPEN_DECISIONS D-08), and on the day they land
every one of those four values is unfounded until re-measured.

A calibration tool that only ever prints "all good" would be worse than none,
so what is tested here is that it fails: on stale constants, on a corpus it
cannot load, and on a benchmark that does not match the corpus.

The full sweep takes ~40s, so these tests drive the sweep functions directly
rather than the CLI where they can.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import re_domain_pack as rdp  # noqa: E402
from re_corpus import CORPUS  # noqa: E402
from re_domain_pack import REDomainPack  # noqa: E402
from scripts import calibrate_retrieval as cal  # noqa: E402

BENCHMARK = json.loads(
    (ROOT / "templates" / "benchmark" / "re_hybrid_rag_v0.1.json").read_text(encoding="utf-8")
)
CASES = BENCHMARK["cases"]


@pytest.fixture(scope="module")
def pack() -> REDomainPack:
    p = REDomainPack()
    p.load()
    return p


def test_the_shipped_unseen_ceiling_is_the_one_the_rule_selects(pack, capsys):
    """Not "a reasonable value" -- the value the documented selection rule
    picks: the largest ceiling at which the decidable abstention bands stay
    perfect."""
    assert cal.sweep_unseen_ceiling(pack, CASES, rdp._UNSEEN_TERM_CEILING) == cal.FITS
    assert "matches" in capsys.readouterr().out


def test_a_stale_unseen_ceiling_is_reported_stale(pack, capsys):
    assert cal.sweep_unseen_ceiling(pack, CASES, 0.50) == cal.STALE
    assert "DOES NOT match" in capsys.readouterr().out


def test_the_shipped_grounding_floor_rejects_no_answerable_case(pack, capsys):
    policy = (pack.policy or {}).get("verification_policy", {}) or {}
    shipped = float(policy["claim_grounding_floor"])
    assert cal.sweep_grounding_floor(pack, CASES, shipped) == cal.FITS
    assert "is safe" in capsys.readouterr().out


def test_a_grounding_floor_that_rejects_real_claims_is_reported(pack, capsys):
    assert cal.sweep_grounding_floor(pack, CASES, 0.40) == cal.STALE
    assert "REJECTS answerable cases" in capsys.readouterr().out


def test_a_benchmark_naming_documents_the_corpus_lacks_is_caught():
    """The check that runs before any sweep. Without it, pointing the tool at a
    real corpus while still holding the synthetic benchmark would report a
    catastrophic recall that reads as a model regression.

    It now lives in the kernel, because `re_demo.py` needed the same rule and
    did not have it. This test reaches it through the calibration tool's own
    import so that the tool losing the guard fails here."""
    missing = cal.missing_benchmark_documents(CASES, [
        {"document_id": "SOMETHING-ELSE", "revision_id": "REV-A"}
    ])
    assert "DOC-RE-001" in missing
    assert not cal.missing_benchmark_documents(CASES, CORPUS)


def test_stability_shapes_are_not_faked_for_a_real_corpus():
    """The adversarial generators are written against the synthetic corpus. Run
    against real documents they would inject fabricated ones, so the tool
    degrades to the corpus as provided and says so rather than reporting a
    stability result it did not measure."""
    synthetic = cal.build_shapes(CORPUS, synthetic=True)
    real = cal.build_shapes(CORPUS, synthetic=False)
    assert len(synthetic) == 15
    assert list(real) == ["as-provided"]


@pytest.mark.parametrize("args,expected", [
    (["--corpus", "/nonexistent-corpus-path"], 2),
])
def test_the_cli_fails_closed(tmp_path, args, expected):
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "calibrate_retrieval.py"), *args],
        capture_output=True, text=True,
        env={"PATH": "/usr/bin:/bin", "PYTHONPATH": f"{ROOT}:{SRC}"},
    )
    assert result.returncode == expected, result.stderr
