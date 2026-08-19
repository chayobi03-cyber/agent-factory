import pathlib
import yaml

SCHEMA_PATH = pathlib.Path("schemas/engineering_evidence.schema.yaml")
CONTRACT_PATH = pathlib.Path("docs/governance/GENERIC_ENGINEERING_EVIDENCE_CONTRACT_V1.md")


def test_generic_evidence_schema_has_required_sections():
    schema = yaml.safe_load(SCHEMA_PATH.read_text())
    assert set(schema) >= {
        "contract_version",
        "evidence",
        "execution_identity",
        "provenance",
        "runtime",
        "result",
        "validation",
        "artifact",
        "manifest",
        "quality",
        "hotl",
        "created_at",
    }
    assert schema["execution_identity"]["target_sha"] == "string"
    assert schema["execution_identity"]["runtime_sha"] == "string"
    assert schema["artifact"]["digest_algorithm"] == ["sha256"]
    assert "download_verified" in schema["artifact"]


def test_schema_remains_domain_neutral():
    text = SCHEMA_PATH.read_text()
    for forbidden_domain_field in ("re_frequency", "emi_limit", "cst_solver", "esd_voltage"):
        assert forbidden_domain_field not in text


def test_contract_declares_kernel_domain_pack_boundary():
    text = CONTRACT_PATH.read_text()
    assert "Domain Pack-owned evidence" in text
    assert "Kernel-owned evidence" in text
    assert "Domain-specific payloads MUST be referenced" in text
    assert "target_sha == runtime_sha" in text
