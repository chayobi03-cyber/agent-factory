"""OPEN_DECISIONS D-12 option C is excluded. This is what makes that true.

The owner ruled out reaching a hosted model API on 2026-08-26. The reason is
not cost or preference: `AUDIT_EVIDENCE_CHAIN_CI_CONTRACT_V1` is built on a run
being re-derivable from the commit it names, and a hosted model breaks that
whatever the corpus contains. A GREEN decision citing a SHA would stop being
reproducible from that SHA -- the exact failure the contract exists to prevent.

A decision recorded only in a document is the pattern this register has now
caught three times: D-09 found a contract enforced by nothing, D-12 itself
found three retrieval modes declared and absent, and the 2026-08-26 audit found
a gating mechanism described in a docstring after its deletion. So the
exclusion is asserted here rather than merely written down.

The property is currently *true*, not aspirational: nothing under `src/` or
`scripts/` performs any network access at all. `verify_artifact_sha256.py`
takes a local path -- the CI runner downloads the artifact, the script only
hashes it. This test exists so that changing that becomes a deliberate act with
a visible failure, instead of arriving as an incidental import.

It does not forbid networking in the abstract. Option B -- a *local* embedding
model -- stays open, and would add a heavyweight dependency without touching
reproducibility, which is why it survives this guard and C does not.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

#: Clients for model services that run somewhere else. A run that calls one of
#: these cannot be re-derived from its commit.
#:
#: `google` was missing while `vertexai` -- Google's *other* hosted entry point
#: -- was listed, so the single most likely way to reach a hosted model from
#: this repository went unguarded: `import google.generativeai` and
#: `from google import genai` both resolve to the top-level name `google`, and
#: neither was caught. Found by probe, not by reading: a file importing both
#: passed all 35 tests. A namespace rather than one package, deliberately --
#: nothing under `src/` or `scripts/` has any use for `google.*`, which is the
#: same reasoning `NETWORK_TRANSPORTS` already runs on.
#:
#: `litellm` is the same omission one step removed: a router whose entire
#: purpose is to call whichever hosted provider you configure.
#:
#: Adding to this set enforces an owner ruling that is already final (D-12
#: option C, excluded 2026-08-26). It cannot permit anything, only refuse more,
#: so it does not need the decision reopened -- unlike a removal, which would.
HOSTED_MODEL_SDKS = {
    "openai", "anthropic", "cohere", "mistralai", "replicate",
    "together", "groq", "vertexai", "boto3", "google", "litellm",
}

#: Deliberately absent, and the reason matters: OPEN_DECISIONS D-12 option B --
#: a model running locally -- is open, and the state file's exclusion covers a
#: hosted API only. `transformers`, `sentence_transformers`, `torch`,
#: `llama_cpp` and `ollama` all reach a local model and none of them break the
#: property this guard protects, so blocking them here would quietly close an
#: option the owner left open. `huggingface_hub` is the awkward one: it is how
#: option B would fetch weights, and also carries an inference client for
#: hosted calls. Left permitted, because refusing it would block the download
#: that option B needs.
LOCAL_MODEL_PATHS_STAY_OPEN = {
    "transformers", "sentence_transformers", "torch", "llama_cpp", "ollama",
    "huggingface_hub",
}

#: Generic transports. Forbidden in these trees not because HTTP is wrong, but
#: because there is no legitimate use for it here and its arrival is how a
#: hosted-model call would actually enter -- rarely as `import openai`.
NETWORK_TRANSPORTS = {
    "urllib", "requests", "httpx", "aiohttp", "http", "socket",
    "ftplib", "telnetlib", "xmlrpc",
}

FORBIDDEN = HOSTED_MODEL_SDKS | NETWORK_TRANSPORTS

GUARDED_TREES = ("src", "scripts")


def _modules_imported_by(path: Path) -> set[str]:
    """Top-level module names imported by a file, via AST.

    Parsed rather than grepped so a mention in a comment, a docstring, or a
    string literal cannot trip it, and so an import cannot hide from it by
    being formatted unusually.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            # `from . import x` has no module; relative imports are local.
            if node.module and not node.level:
                modules.add(node.module.split(".")[0])
    return modules


def _guarded_files() -> list[Path]:
    files = [p for tree in GUARDED_TREES for p in (ROOT / tree).rglob("*.py")
             if "__pycache__" not in p.parts]
    assert files, "found no files to guard -- the tree layout changed"
    return files


@pytest.mark.parametrize("path", _guarded_files(), ids=lambda p: str(p.relative_to(ROOT)))
def test_no_module_reaches_a_hosted_model_or_the_network(path: Path) -> None:
    offending = sorted(_modules_imported_by(path) & FORBIDDEN)
    assert not offending, (
        f"{path.relative_to(ROOT)} imports {offending}.\n"
        "OPEN_DECISIONS D-12 option C (a hosted model API) is excluded, because a "
        "run that calls one cannot be re-derived from the commit it names -- which "
        "is what AUDIT_EVIDENCE_CHAIN_CI_CONTRACT_V1 requires.\n"
        "If this is deliberate, reopen D-12 and record the decision there first. "
        "Option B (a local model) does not need this import and is not blocked by "
        "this test."
    )


def test_the_guard_can_actually_fail(tmp_path: Path) -> None:
    """A guard that cannot fail is decoration. Proven against a synthetic file
    rather than by breaking a real one."""
    offender = tmp_path / "reaches_out.py"
    offender.write_text("import json\nimport httpx\n", encoding="utf-8")
    assert _modules_imported_by(offender) & FORBIDDEN == {"httpx"}

    disguised = tmp_path / "disguised.py"
    disguised.write_text("from openai.types import Thing\n", encoding="utf-8")
    assert _modules_imported_by(disguised) & FORBIDDEN == {"openai"}


def test_the_gemini_sdk_is_caught(tmp_path: Path) -> None:
    """The hole this set was widened to close.

    `vertexai` was listed and `google` was not, so both import spellings of the
    Gemini SDK reached the kernel untouched. Written as its own test because
    the omission was invisible in the list -- it reads as covering Google.
    """
    for source in ("import google.generativeai as genai\n",
                   "from google import genai\n",
                   "from google.genai import Client\n"):
        probe = tmp_path / "gemini.py"
        probe.write_text(source, encoding="utf-8")
        assert _modules_imported_by(probe) & FORBIDDEN == {"google"}, source


def test_a_local_model_is_still_reachable(tmp_path: Path) -> None:
    """Widening the set must not close OPEN_DECISIONS D-12 option B.

    The exclusion is of a *hosted* API, because that is what breaks
    re-derivation from a commit. A local model does not, so every import that
    reaches one has to keep passing -- otherwise this guard would have quietly
    decided a question the owner left open.
    """
    probe = tmp_path / "local_model.py"
    probe.write_text(
        "".join(f"import {name}\n" for name in sorted(LOCAL_MODEL_PATHS_STAY_OPEN)),
        encoding="utf-8",
    )
    assert not _modules_imported_by(probe) & FORBIDDEN


def test_a_mention_in_prose_is_not_an_import(tmp_path: Path) -> None:
    """The reason this parses rather than greps: these very files discuss the
    forbidden names at length."""
    prose = tmp_path / "talks_about_it.py"
    prose.write_text(
        '"""We deliberately do not import requests or openai here."""\n'
        "NOTE = 'httpx would break reproducibility'\n"
        "import json  # noqa\n",
        encoding="utf-8",
    )
    assert not _modules_imported_by(prose) & FORBIDDEN


def test_the_decision_is_recorded_where_a_reader_would_look() -> None:
    """The test and the register have to agree, or one of them is stale."""
    state = (ROOT / "docs" / "governance" / "CURRENT_SESSION_STATE.yaml").read_text(encoding="utf-8")
    assert "hosted_model_api_dependency" in state, (
        "the exclusion is enforced by this test but absent from the state file's "
        "forbidden list"
    )
    register = (ROOT / "docs" / "governance" / "OPEN_DECISIONS_2026-08-25.md").read_text(
        encoding="utf-8"
    ).lower()
    assert "option c is excluded" in register, (
        "the exclusion is enforced by this test but D-12 does not record it"
    )
