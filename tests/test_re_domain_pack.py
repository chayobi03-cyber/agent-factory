from pathlib import Path

import yaml


PACK = Path("domains/re/domain_pack.yaml")


def load_pack():
    return yaml.safe_load(PACK.read_text(encoding="utf-8"))


def test_re_pack_identity_and_ontology():
    pack = load_pack()
    assert pack["domain_id"] == "RE"
    assert pack["version"] == "0.1.0"
    assert "radiated emission" in pack["terminology"]["canonical_terms"]
    assert "DUT" in pack["ontology"]["entities"]
    assert "measurement" in pack["ontology"]["entities"]
    assert "exceeds" in pack["ontology"]["relations"]


def test_re_pack_is_evidence_first():
    pack = load_pack()
    verification = pack["verification_policy"]
    assert verification["require_evidence_for_claims"] is True
    assert verification["require_stable_locator"] is True
    assert verification["require_revision_validity"] is True
    assert verification["abstain_when_evidence_insufficient"] is True


def test_re_pack_keeps_kernel_boundary_clean():
    pack_text = PACK.read_text(encoding="utf-8")
    forbidden_kernel_terms = [
        "FactoryRuntime",
        "CER Snapshot",
        "WorkflowRun",
        "HOTL controller implementation",
        "financial",
    ]
    assert not any(term in pack_text for term in forbidden_kernel_terms)


def test_re_pack_query_classes_match_poc():
    pack = load_pack()
    classes = set(pack["benchmark_catalog"]["query_classes"])
    expected = {
        "definition",
        "document_location",
        "revision_comparison",
        "condition_cause_analysis",
        "re_failure_diagnosis",
        "supporting_or_contradicting_evidence",
        "recommended_additional_test",
        "engineering_report",
        "evidence_sufficiency",
    }
    assert expected <= classes
