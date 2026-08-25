"""Loading a corpus from outside the repository, and saying which one it was.

OPEN_DECISIONS D-08 settled that this repository stays public, so real RE test
reports and purchased standards text can never be committed to it. Reaching
real documents means reading them from outside the tree -- and that collides
with AUDIT_EVIDENCE_CHAIN_CI_CONTRACT_V1, which is built on a run being
re-derivable from the commit it names.

These tests pin the three things that keep the collision visible rather than
silent: the in-tree corpus stays the default, every source carries a content
digest, and a corpus that cannot be loaded cleanly fails closed instead of
loading partially.
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

from corpus_source import (  # noqa: E402
    IN_TREE_ORIGIN,
    CorpusError,
    from_directory,
    from_documents,
)
from re_corpus import CORPUS  # noqa: E402
from re_domain_pack import REDomainPack  # noqa: E402


def doc(document_id: str = "DOC-1", revision_id: str = "REV-A", **over) -> dict:
    return {
        "document_id": document_id,
        "revision_id": revision_id,
        "title": "A Title",
        "doc_type": "test_report",
        "text": "Some measured content.",
        **over,
    }


def write(directory: Path, documents, *, name_from=lambda i, d: f"doc-{i:03d}.json") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    for i, d in enumerate(documents):
        (directory / name_from(i, d)).write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return directory


# --- identity ---------------------------------------------------------------

def test_the_in_tree_corpus_is_the_default_and_names_itself():
    identity = from_documents(CORPUS).identity()
    assert identity["origin"] == IN_TREE_ORIGIN
    assert identity["digest"].startswith("sha256:")
    assert identity["documents"] == len(CORPUS)


def test_the_same_documents_digest_the_same_from_disk_as_from_the_tree(tmp_path):
    """The property that makes the digest an identity rather than a checksum of
    a directory listing: exporting the in-tree corpus to files and reading it
    back must produce the same digest, whatever the files are called or what
    order they are read in."""
    exported = from_directory(write(tmp_path / "a", CORPUS))
    assert exported.digest == from_documents(CORPUS).digest
    assert exported.origin.startswith("directory:")


def test_filenames_and_order_do_not_change_the_digest(tmp_path):
    forward = from_directory(write(tmp_path / "f", CORPUS))
    reversed_names = write(
        tmp_path / "r", list(reversed(CORPUS)),
        name_from=lambda i, d: f"{d['document_id']}-{d['revision_id']}-{i}.json",
    )
    assert from_directory(reversed_names).digest == forward.digest


def test_changing_one_character_changes_the_digest(tmp_path):
    before = from_directory(write(tmp_path / "b", [doc()])).digest
    after = from_directory(write(tmp_path / "a", [doc(text="Some measured content!")])).digest
    assert before != after


def test_a_document_list_in_one_file_loads_the_same_as_one_file_each(tmp_path):
    single = tmp_path / "single"
    single.mkdir()
    (single / "all.json").write_text(json.dumps(list(CORPUS), ensure_ascii=False), encoding="utf-8")
    assert from_directory(single).digest == from_directory(write(tmp_path / "many", CORPUS)).digest


# --- failing closed ---------------------------------------------------------

@pytest.mark.parametrize("field", ["document_id", "revision_id", "title", "doc_type", "text"])
def test_a_document_missing_a_required_field_is_refused(tmp_path, field):
    """Evidence without a stable document and revision identifier is not
    evidence, it is a quotation."""
    with pytest.raises(CorpusError, match=field):
        from_directory(write(tmp_path, [doc(**{field: ""})]))


def test_two_documents_claiming_one_identity_are_refused(tmp_path):
    """Ambiguous citations, and a silently doubled weight in every
    document-frequency statistic the retriever computes."""
    with pytest.raises(CorpusError, match="duplicate"):
        from_directory(write(tmp_path, [doc(), doc(title="A Different Title")]))


def test_a_directory_with_no_json_is_refused(tmp_path):
    (tmp_path / "notes.txt").write_text("not a corpus", encoding="utf-8")
    with pytest.raises(CorpusError, match="no .json files"):
        from_directory(tmp_path)


def test_invalid_json_names_the_file_that_broke(tmp_path):
    tmp_path.joinpath("broken.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(CorpusError, match="broken.json"):
        from_directory(tmp_path)


def test_a_path_that_is_not_a_directory_is_refused(tmp_path):
    with pytest.raises(CorpusError, match="not a directory"):
        from_directory(tmp_path / "does-not-exist")


def test_partial_loading_never_happens(tmp_path):
    """One bad document rejects the corpus rather than yielding the rest.

    A partially-loaded corpus changes every retrieval metric measured against
    it, and the change looks like a model regression rather than a missing
    file."""
    write(tmp_path, [doc("DOC-1"), doc("DOC-2"), doc("DOC-3", title="")])
    with pytest.raises(CorpusError):
        from_directory(tmp_path)


# --- equivalence: the claim that makes the out-of-tree path trustworthy ------

def test_a_pack_loaded_from_disk_behaves_identically_to_the_in_tree_one(tmp_path):
    """Out-of-tree is a different *source*, not different *behaviour*. If these
    diverged, no benchmark number measured against a real corpus could be
    compared to one measured against the synthetic one."""
    in_tree = REDomainPack()
    in_tree.load()
    from_disk = REDomainPack()
    from_disk.load(from_directory(write(tmp_path, CORPUS)))

    assert from_disk.corpus_identity["digest"] == in_tree.corpus_identity["digest"]
    assert from_disk.corpus_identity["origin"] != in_tree.corpus_identity["origin"]

    for query in (
        "What caused the 375 MHz exceedance on EUT-31?",
        "Which document records the qualification of the fully-anechoic chamber?",
        "What quarterly revenue did the test laboratory report?",
    ):
        assert (
            [e.fragment_id for e in from_disk.retrieve(query, top_k=10)]
            == [e.fragment_id for e in in_tree.retrieve(query, top_k=10)]
        ), query
