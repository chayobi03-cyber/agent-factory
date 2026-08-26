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


# --- every shipped domain, exercised the same way ---------------------------
#
# Six domains, one engine. These run over whatever is in `domains/`, so a
# seventh added tomorrow is covered without editing this file -- which is the
# behaviour a factory should have and a per-domain test file would not.

SHIPPED = sorted(d.name for d in DOMAINS.iterdir() if (d / "domain_pack.yaml").exists())

#: One question per domain that its own example corpus answers, and the
#: document that must come back. Not paraphrases of a sentence in the answer:
#: a benchmark whose queries are lifted from their documents measures whoever
#: wrote it.
ANSWERABLE = {
    "thermal": ("what caused the DUT-7 junction temperature excursion?", "DOC-TH-003"),
    "structural": ("why did PART-118 crack in the field?", "DOC-ST-003"),
    "battery": ("why did PACK-19 miss its cycle life requirement?", "DOC-BT-002"),
    "manufacturing": ("what caused the LOT-2291 solder defects?", "DOC-MF-002"),
    "firmware": ("why do SKU-31 units reset after a cold start?", "DOC-FW-002"),
}


def _with_examples(domain: str) -> GenericDomainPack:
    from corpus_source import from_directory

    pack = GenericDomainPack.from_directory(DOMAINS / domain)
    pack.load(from_directory(DOMAINS / domain / "examples"))
    return pack


@pytest.mark.parametrize("domain", sorted(ANSWERABLE))
def test_every_domain_answers_its_own_question_out_of_the_box(domain):
    """`--corpus domains/<d>/examples` has to work the moment someone clones
    the repository, or the examples are decoration."""
    query, expected = ANSWERABLE[domain]
    found = _with_examples(domain).retrieve(query, top_k=3)
    assert expected in {e.document_id for e in found}, [e.document_id for e in found]


@pytest.mark.parametrize("domain", sorted(ANSWERABLE))
def test_every_domain_refuses_another_domains_question(domain):
    """A pack asked about a field it does not cover must refuse rather than
    return its nearest paragraph. This is the reliable half of abstention --
    OPEN_DECISIONS D-11 records that the near-miss half is not."""
    foreign = "What is the CISPR 32 Class B radiated emission limit at 3 meters?"
    assert _with_examples(domain).retrieve(foreign) == []


@pytest.mark.parametrize("domain", SHIPPED)
def test_no_domain_ships_code(domain):
    assert not list((DOMAINS / domain).rglob("*.py")), f"{domain} must be data only"


@pytest.mark.parametrize("domain", SHIPPED)
def test_every_domain_declares_the_vocabulary_the_kernel_cannot_guess(domain):
    """`generic_terms` is the one piece of real domain knowledge required. The
    kernel supplies English function words; it cannot know that "radiated" says
    nothing in an RE archive or "thermal" nothing in a heat one."""
    pack = GenericDomainPack.from_directory(DOMAINS / domain)
    assert pack.generic_terms, f"{domain} declares no generic_terms"
    assert pack.stopwords, f"{domain} resolved to no stopwords at all"


@pytest.mark.parametrize("domain", SHIPPED)
def test_every_domain_declares_only_retrieval_modes_that_exist(domain):
    """RE's policy once listed vector, graph and agentic with nothing behind
    the names (OPEN_DECISIONS D-12). A new domain must not reintroduce that."""
    pack = GenericDomainPack.from_directory(DOMAINS / domain)
    declared = set((pack.policy.get("retrieval_policy") or {}).get("allowed_modes") or [])
    assert declared <= set(pack.modes), f"{domain} declares unimplemented modes: {declared - set(pack.modes)}"


def test_a_domain_can_declare_identifiers_without_any_units():
    """FIRMWARE ships with no unit tables at all -- prose plus build and ticket
    identifiers. Not every engineering domain measures things, and that path
    has to be exercised by something shipped rather than only by a fixture."""
    pack = GenericDomainPack.from_directory(DOMAINS / "firmware")
    assert not pack.tokenize.unit_multipliers
    assert not pack.tokenize.level_units
    assert pack.tokenize.identifier_prefixes
    tokens = pack.tokenize("FW-4.2.0 supersedes FW-4.1.3 under TKT-4471")
    assert "fw-4.2.0" in tokens and "tkt-4471" in tokens, tokens


def test_domains_do_not_share_a_unit_vocabulary():
    """Each domain's tokenizer is built from its own table. If these collided,
    the tables would be decorative and the kernel would be carrying one
    domain's units for everyone."""
    units = {d: set(GenericDomainPack.from_directory(DOMAINS / d).tokenize.unit_multipliers)
             for d in ("re", "thermal", "structural", "battery", "manufacturing")}
    assert units["re"] & units["thermal"] == set(), units
    assert units["structural"] != units["battery"]
    # And a quantity tokenizes to its own domain's canonical unit.
    thermal = GenericDomainPack.from_directory(DOMAINS / "thermal")
    structural = GenericDomainPack.from_directory(DOMAINS / "structural")
    assert "q:30w" in thermal.tokenize("a 30 W burst")
    assert "q:214mpa" in structural.tokenize("214 MPa at the fillet")
