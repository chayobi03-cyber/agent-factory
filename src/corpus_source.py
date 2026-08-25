"""Where a Domain Pack's documents come from, and how a run says which ones it used.

A kernel capability. ARCHITECTURE_REFACTOR_PLAN puts "Engineering document
ingestion" in the shared sequence, and nothing about a document's identity --
an id, a revision, a title, a type, some text -- is specific to radiated
emission. Any Domain Pack loads a corpus the same way.

**Why this exists at all.** OPEN_DECISIONS D-08 settled that this repository
stays public. Real RE test reports and purchased standards text therefore
cannot be committed to it, so the PoC's "20+ representative legacy documents"
can only ever be synthetic in-tree. Reaching real documents means reading them
from somewhere outside the tree.

**The tension that creates, stated rather than skirted.**
`AUDIT_EVIDENCE_CHAIN_CI_CONTRACT_V1` is built on a run being re-derivable from
the commit it names. A corpus outside the tree is not in that commit, so a
benchmark measured against one cannot be reproduced from the SHA alone -- which
is the property the whole evidence chain rests on. Three things keep that from
becoming a silent hole:

1. The in-tree synthetic corpus stays the default, and is what CI measures.
   An out-of-tree source is opt-in and never implicit.
2. Every `CorpusSource` carries a `digest` over its own content and an
   `origin`. A run records both, so "which corpus produced this number" is
   answerable after the fact even when the corpus itself is not in the commit.
3. A digest mismatch is detectable: re-loading the same directory and getting a
   different digest tells you the corpus moved under you, which is exactly the
   failure a SHA would otherwise have caught.

This does not make an out-of-tree run as reproducible as an in-tree one. It
makes the difference visible instead of invisible.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

#: Every document needs these, whatever domain it belongs to. A corpus missing
#: one of them cannot be cited: evidence without a stable document and revision
#: identifier is not evidence, it is a quotation.
REQUIRED_FIELDS = ("document_id", "revision_id", "title", "doc_type", "text")

IN_TREE_ORIGIN = "in-tree:src/re_corpus.CORPUS"


class CorpusError(ValueError):
    """A corpus that cannot be loaded, rather than one that loads wrongly.

    Fail-closed on purpose. A partially-loaded corpus silently changes every
    retrieval metric measured against it, and the change looks like a model
    regression rather than a missing file.
    """


@dataclass(frozen=True)
class CorpusSource:
    documents: tuple[Mapping[str, Any], ...]
    origin: str
    digest: str

    @property
    def document_count(self) -> int:
        return len(self.documents)

    @property
    def distinct_document_ids(self) -> int:
        return len({d["document_id"] for d in self.documents})

    def identity(self) -> dict[str, Any]:
        """What a run records so its numbers stay attributable to a corpus."""
        return {
            "origin": self.origin,
            "digest": self.digest,
            "documents": self.document_count,
            "distinct_document_ids": self.distinct_document_ids,
        }


def _digest(documents: Sequence[Mapping[str, Any]]) -> str:
    """A content digest that does not depend on file order or key order.

    Sorted by (document_id, revision_id) so two directories holding the same
    documents produce the same digest regardless of filenames, and so the
    in-tree corpus and an exported copy of it can be compared directly.
    """
    canonical = json.dumps(
        sorted(
            ({k: doc[k] for k in REQUIRED_FIELDS} for doc in documents),
            key=lambda d: (d["document_id"], d["revision_id"]),
        ),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate(documents: Iterable[Mapping[str, Any]], origin: str) -> tuple[Mapping[str, Any], ...]:
    checked: list[Mapping[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for index, doc in enumerate(documents):
        if not isinstance(doc, Mapping):
            raise CorpusError(f"{origin}: entry {index} is {type(doc).__name__}, expected a mapping")
        missing = [f for f in REQUIRED_FIELDS if not str(doc.get(f, "")).strip()]
        if missing:
            raise CorpusError(
                f"{origin}: entry {index} ({doc.get('document_id', '?')}) "
                f"is missing or empty: {', '.join(missing)}"
            )
        key = (str(doc["document_id"]), str(doc["revision_id"]))
        if key in seen:
            # Two documents claiming one identity make citations ambiguous and
            # quietly double a document's weight in every df-based statistic.
            raise CorpusError(f"{origin}: duplicate document/revision {key[0]}/{key[1]}")
        seen.add(key)
        checked.append(dict(doc))
    if not checked:
        raise CorpusError(f"{origin}: no documents found")
    return tuple(checked)


def from_documents(documents: Iterable[Mapping[str, Any]], *, origin: str = IN_TREE_ORIGIN) -> CorpusSource:
    """Wrap an already-loaded document sequence, validating and digesting it."""
    checked = _validate(documents, origin)
    return CorpusSource(documents=checked, origin=origin, digest=_digest(checked))


def from_directory(path: str | Path) -> CorpusSource:
    """Load every `*.json` file under `path`, each holding one document or a list.

    Deliberately plain. The point is to reach documents that cannot live in a
    public repository, not to invent a corpus format -- a directory of JSON is
    something an export script, a scrape, or a person can produce without
    reading a specification first.
    """
    root = Path(path).expanduser()
    if not root.is_dir():
        raise CorpusError(f"{root}: not a directory")

    documents: list[Mapping[str, Any]] = []
    files = sorted(root.rglob("*.json"))
    if not files:
        raise CorpusError(f"{root}: contains no .json files")
    for file in files:
        try:
            payload = json.loads(file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CorpusError(f"{file}: invalid JSON: {exc}") from exc
        if isinstance(payload, list):
            documents.extend(payload)
        else:
            documents.append(payload)

    # The origin is the resolved path, not what the caller typed: a relative
    # path recorded in evidence is not an identity.
    return from_documents(documents, origin=f"directory:{root.resolve()}")
