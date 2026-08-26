"""A new engineering domain must be data, not code.

AF-004's acceptance criterion is "kernel loads Domain Pack without code fork",
and `scripts/domain_matrix_demo.py` has been reporting it satisfied. It could
not have detected otherwise: it is fixture-only by construction, refusing any
spec not marked `fixture_only: true` and returning a canned candidate from
`retrieve`. It proves the protocol *shape* is domain-agnostic and nothing about
retrieval, so standing up a second domain still meant copying 783 lines of RE.

These tests are the version that could fail. `domains/thermal/` is a real
domain with a real policy and no Python at all, and what is asserted is that it
retrieves, abstains, tokenizes its own units, and shares one engine with RE.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from corpus_source import from_documents  # noqa: E402
from generic_domain_pack import GenericDomainPack  # noqa: E402
from re_domain_pack import REDomainPack  # noqa: E402

DOMAINS = ROOT / "domains"

THERMAL_DOCS = [
    {"document_id": "DOC-TH-001", "revision_id": "REV-A",
     "title": "DUT-4 Junction Temperature Bench Measurement",
     "doc_type": "bench_measurement_log",
     "text": "Board BRD-12 carrying DUT-4 was run at 18 W dissipation in a 25 degC ambient "
             "with 1.2 m/s forced airflow. Junction temperature reached 108 degC against a "
             "125 degC rating. Junction-to-case resistance implied is 0.9 c/w."},
    {"document_id": "DOC-TH-002", "revision_id": "REV-A",
     "title": "Heatsink HS-9 Characterisation", "doc_type": "thermal_simulation_report",
     "text": "Heatsink HS-9 measured 4.1 k/w at 0.5 m/s, 2.8 k/w at 1.2 m/s and 2.2 k/w at "
             "2.0 m/s. HS-9 is not suitable above 25 W without increasing airflow."},
    {"document_id": "DOC-TH-003", "revision_id": "REV-A",
     "title": "Thermal Interface Material Selection Guide",
     "doc_type": "internal_engineering_wiki",
     "text": "TIM-2 silicone pad tolerates 0.25 mm gap variation. TIM-5 phase-change material "
             "gives lower resistance but needs a controlled bond line."},
]


@pytest.fixture(scope="module")
def thermal() -> GenericDomainPack:
    pack = GenericDomainPack.from_directory(DOMAINS / "thermal")
    pack.load(from_documents(THERMAL_DOCS, origin="test:thermal"))
    return pack


# --- the criterion itself ----------------------------------------------------

def test_a_second_domain_exists_and_ships_no_python():
    """The whole claim, asserted directly: `domains/thermal/` is a policy file
    and nothing else. A `thermal_domain_pack.py` appearing anywhere would mean
    the extraction failed and the fork came back."""
    thermal_dir = DOMAINS / "thermal"
    assert (thermal_dir / "domain_pack.yaml").exists()
    assert not list(thermal_dir.rglob("*.py")), "a domain must not need code"
    assert not list((ROOT / "src").glob("thermal*")), "no per-domain module in the kernel"


def test_both_domains_run_on_the_same_engine(thermal):
    """RE is a binding over the generic pack, not a parallel implementation."""
    assert isinstance(REDomainPack(), GenericDomainPack)
    assert isinstance(thermal, GenericDomainPack)
    assert type(thermal) is GenericDomainPack, "thermal needs no subclass at all"


def test_the_new_domain_actually_retrieves(thermal):
    """Not a canned fixture candidate -- the right document, by content."""
    found = thermal.retrieve("What thermal resistance does HS-9 give at 1.2 m/s?", top_k=3)
    assert "DOC-TH-002" in {e.document_id for e in found}


def test_the_new_domain_abstains_on_another_domains_question(thermal):
    """A thermal corpus asked about radiated emission must refuse, not return
    its nearest paragraph."""
    assert thermal.retrieve("What is the CISPR 32 Class B radiated emission limit?") == []


# --- what the policy actually buys ------------------------------------------

def test_the_tokenizer_is_built_from_the_domains_own_units(thermal):
    """RE normalizes frequencies; thermal normalizes power. Same mechanism,
    different table -- which is the point of moving the table into YAML."""
    tokens = thermal.tokenize("a 30 W burst at 138 degC on DUT-7")
    assert "q:30w" in tokens, tokens          # scaled to the canonical unit
    assert "138degc" in tokens, tokens        # level unit stays attached
    assert "dut-7" in tokens, tokens          # identifier survives whole

    # And milliwatts land on the same token as their watt equivalent, which is
    # the property a bare word tokenizer destroys.
    assert thermal.tokenize("500 mW") == thermal.tokenize("0.5 W")


def test_each_domain_names_its_own_quantity_metadata(thermal):
    """An RE fragment carries `frequencies`. A thermal fragment has none, and
    calling its watts "frequencies" would be the kernel imposing one domain's
    vocabulary on every other."""
    re_pack = REDomainPack()
    re_pack.load()
    re_keys = set().union(*(f.metadata.keys() for f in re_pack._fragments))
    thermal_keys = set().union(*(f.metadata.keys() for f in thermal._fragments))
    assert "frequencies" in re_keys
    assert "frequencies" not in thermal_keys
    assert "power_dissipation" in thermal_keys


def test_a_domain_declaring_no_measurements_still_works():
    """A domain of pure prose has no measurements to preserve, and must get
    ordinary word tokenization rather than a crash or someone else's units."""
    pack = GenericDomainPack({"domain_id": "PROSE", "version": "0.1.0"})
    pack.load(from_documents([
        {"document_id": "D-1", "revision_id": "REV-A", "title": "A Note",
         "doc_type": "wiki", "text": "The commissioning checklist is kept by the site lead."}
    ], origin="test:prose"))
    assert pack.retrieve("who keeps the commissioning checklist?", top_k=1)
    assert pack.tokenize("30 W") == ["30", "w"]


def test_the_thresholds_come_from_the_policy():
    """They were hardcoded in Python beside a policy file that already claimed
    to describe the domain. Now the file is what decides."""
    import yaml

    declared = yaml.safe_load((DOMAINS / "re" / "domain_pack.yaml").read_text(encoding="utf-8"))
    tuning = declared["retrieval_policy"]["tuning"]
    pack = REDomainPack()
    assert pack.thresholds.coverage_floor == tuning["coverage_floor"]
    assert pack.thresholds.unseen_term_ceiling == tuning["unseen_term_ceiling"]
    assert pack.modes["hybrid"] == tuning["lexical_weight"]


def test_every_shipped_domain_policy_loads_and_declares_its_identity():
    """A policy that cannot be loaded is a domain that cannot be used, and the
    failure should be a test rather than a stack trace at query time."""
    found = [d for d in DOMAINS.iterdir() if (d / "domain_pack.yaml").exists()]
    assert len(found) >= 2, "the second domain is what proves the criterion"
    for directory in found:
        pack = GenericDomainPack.from_directory(directory)
        assert pack.domain_id and pack.domain_id != "GENERIC", directory.name
        assert pack.version != "0.0.0", directory.name


# --- the CLI is the surface a person without Python actually touches ---------

def test_the_cli_lists_the_domains_it_can_run():
    from scripts import run_domain

    assert {"re", "thermal"} <= set(run_domain.available_domains())


def test_a_domain_with_no_in_tree_corpus_refuses_rather_than_answering_from_nothing():
    from scripts import run_domain

    with pytest.raises(ValueError, match="no in-tree corpus"):
        run_domain.build_pack("thermal", None)


def test_an_unknown_domain_names_the_ones_that_exist():
    from scripts import run_domain

    with pytest.raises(FileNotFoundError, match="available:"):
        run_domain.build_pack("nonexistent", None)
