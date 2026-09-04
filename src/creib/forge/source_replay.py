"""Exact, fail-closed replay of translation source spans.

The replay performed here is deliberately narrower than semantic review.  It
can establish that bound bytes, locators, literal snapshots, and (where the
record makes the relation executable) verbatim claim text agree.  It cannot
establish that the selected words mean what a translation says they mean.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
import hashlib
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any, Mapping
import unicodedata
import xml.etree.ElementTree as ET

from creib.canonical import bytes_digest, canonical_bytes
from creib.errors import RecordError

from .translation import (
    TranslationValidationResult,
    validate_translation_record,
    validate_translation_snapshot,
)


UTF8_RANGE_ALGORITHM = "creib.semantic-forge.utf8-byte-range.v1"
UTF8_RANGE_TOOL = "creib"
UTF8_RANGE_TOOL_VERSION = "1"
UTF8_RANGE_SELECTION_RULE = (
    "exact bytes [start_byte,end_byte_exclusive); items are bytes; "
    "strict UTF-8 decode without normalization"
)
UTF8_RANGE_DIGEST_DOMAIN = UTF8_RANGE_ALGORITHM

PDF_WORD_ALGORITHM = "CR-EIB/pdftotext-word-snapshot/v1"
PDF_WORD_TOOL = "pdftotext"
PDF_WORD_SELECTION_RULE = (
    "word center inside tight_bbox_millipoints; ordered by pdftotext output"
)
PDF_WORD_DIGEST_DOMAIN = PDF_WORD_ALGORITHM


class SourceReplayMismatch(RecordError):
    """A replayed fact disagrees with an immutable source record."""


class SourceReplayUnavailable(Exception):
    """The current runtime cannot execute a declared replay profile exactly."""


@dataclass(frozen=True)
class SourceReplayResult:
    """Narrow outcome of source replay, with no semantic verdict."""

    verified_document_ids: tuple[str, ...]
    verified_span_ids: tuple[str, ...]
    unresolved_span_ids: tuple[str, ...]
    mechanically_grounded_claim_ids: tuple[str, ...]
    unresolved_claim_ids: tuple[str, ...]
    limitations: tuple[tuple[str, str], ...]

    @property
    def complete(self) -> bool:
        return not self.unresolved_span_ids and not self.unresolved_claim_ids

    def details(self) -> dict[str, Any]:
        return {
            "verified_document_ids": list(self.verified_document_ids),
            "verified_span_ids": list(self.verified_span_ids),
            "unresolved_span_ids": list(self.unresolved_span_ids),
            "mechanically_grounded_claim_ids": list(
                self.mechanically_grounded_claim_ids
            ),
            "unresolved_claim_ids": list(self.unresolved_claim_ids),
            "limitations": [
                {"subject_id": subject_id, "reason": reason}
                for subject_id, reason in self.limitations
            ],
            "semantic_verdict": None,
        }


@dataclass(frozen=True)
class _SegmentReplay:
    exact_text: str | None
    claim_text_available: bool
    limitation: str | None = None


_DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z")
_PDFTO_TEXT_VERSION = re.compile(r"pdftotext version ([0-9.]+)")
_PDF_PAGES = re.compile(r"^Pages:\s+(\d+)\s*$", re.MULTILINE)


def _plain_decimal(token: str, where: str) -> Decimal:
    if not _DECIMAL.fullmatch(token):
        raise SourceReplayMismatch(f"{where} is not a plain finite decimal")
    try:
        value = Decimal(token)
    except InvalidOperation as exc:
        raise SourceReplayMismatch(f"{where} is not a valid decimal") from exc
    if not value.is_finite():
        raise SourceReplayMismatch(f"{where} is not finite")
    return value


def _exact_millipoints(token: str, where: str) -> int:
    scaled = _plain_decimal(token, where) * 1000
    if scaled != scaled.to_integral_value():
        raise SourceReplayMismatch(f"{where} is not an exact millipoint value")
    return int(scaled)


def _rounded_millipoints(token: str, where: str) -> int:
    scaled = _plain_decimal(token, where) * 1000
    return int(scaled.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))


def _run(command: list[str]) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
        )
    except FileNotFoundError as exc:
        raise SourceReplayUnavailable(
            f"required replay tool is unavailable: {command[0]}"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise SourceReplayUnavailable(
            f"source replay tool timed out: {command[0]}"
        ) from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout).decode(
            "utf-8", errors="replace"
        ).strip()
        raise SourceReplayMismatch(
            f"source replay tool failed: {command[0]}: {detail}"
        ) from exc


def _framed_bytes_digest(domain: str, payload: bytes) -> str:
    try:
        prefix = domain.encode("ascii")
    except UnicodeEncodeError as exc:
        raise SourceReplayMismatch("literal snapshot digest_domain is not ASCII") from exc
    return hashlib.sha256(prefix + b"\0" + payload).hexdigest()


def _require_profile(
    literal: Mapping[str, Any],
    *,
    algorithm: str,
    tool: str,
    tool_version: str | None,
    selection_rule: str,
    digest_domain: str,
) -> None:
    expected: dict[str, str] = {
        "algorithm": algorithm,
        "tool": tool,
        "selection_rule": selection_rule,
        "digest_domain": digest_domain,
    }
    if tool_version is not None:
        expected["tool_version"] = tool_version
    differences = [
        name for name, expected_value in expected.items()
        if literal.get(name) != expected_value
    ]
    if differences:
        raise SourceReplayUnavailable(
            "unsupported literal snapshot profile fields: " + ", ".join(differences)
        )


def _replay_utf8_segment(
    raw: bytes,
    locator: Mapping[str, Any],
    literal: Mapping[str, Any],
) -> _SegmentReplay:
    _require_profile(
        literal,
        algorithm=UTF8_RANGE_ALGORITHM,
        tool=UTF8_RANGE_TOOL,
        tool_version=UTF8_RANGE_TOOL_VERSION,
        selection_rule=UTF8_RANGE_SELECTION_RULE,
        digest_domain=UTF8_RANGE_DIGEST_DOMAIN,
    )
    start = int(locator["start_byte"])
    end = int(locator["end_byte_exclusive"])
    if end > len(raw):
        raise SourceReplayMismatch("UTF-8 byte-range locator exceeds the source artifact")
    selected = raw[start:end]
    try:
        text = selected.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SourceReplayMismatch(
            "UTF-8 byte-range locator splits or contains an invalid UTF-8 sequence"
        ) from exc
    if len(selected) != literal["item_count"]:
        raise SourceReplayMismatch("literal snapshot item_count does not replay")
    actual = _framed_bytes_digest(UTF8_RANGE_DIGEST_DOMAIN, selected)
    if actual != literal["sha256"]:
        raise SourceReplayMismatch("literal snapshot digest does not replay")
    return _SegmentReplay(exact_text=text, claim_text_available=True)


def _pdf_page_info(path: Path, physical_page: int) -> tuple[int, list[int], int]:
    output = _run(
        [
            "pdfinfo",
            "-f",
            str(physical_page),
            "-l",
            str(physical_page),
            "-box",
            str(path),
        ]
    ).stdout.decode("utf-8", errors="strict")
    pages_match = _PDF_PAGES.search(output)
    size_match = re.search(
        rf"^Page\s+{physical_page}\s+size:\s+"
        r"([0-9]+(?:\.[0-9]+)?)\s+x\s+([0-9]+(?:\.[0-9]+)?)\s+pts",
        output,
        re.MULTILINE,
    )
    rotation_match = re.search(
        rf"^Page\s+{physical_page}\s+rot:\s+(\d+)\s*$",
        output,
        re.MULTILINE,
    )
    if not pages_match or not size_match or not rotation_match:
        raise SourceReplayMismatch("PDF page metadata is incomplete or unparseable")
    return (
        int(pages_match.group(1)),
        [
            _exact_millipoints(size_match.group(1), "PDF page width"),
            _exact_millipoints(size_match.group(2), "PDF page height"),
        ],
        int(rotation_match.group(1)),
    )


def _pdf_words(path: Path, physical_page: int, page_size: list[int]) -> list[list[Any]]:
    xml = _run(
        [
            "pdftotext",
            "-f",
            str(physical_page),
            "-l",
            str(physical_page),
            "-bbox",
            str(path),
            "-",
        ]
    ).stdout
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise SourceReplayMismatch(
            f"pdftotext returned malformed bbox XML: {exc}"
        ) from exc
    pages = [
        element for element in root.iter()
        if element.tag.rsplit("}", 1)[-1] == "page"
    ]
    if len(pages) != 1:
        raise SourceReplayMismatch("pdftotext did not return exactly one selected page")
    page = pages[0]
    try:
        actual_size = [
            _exact_millipoints(page.attrib["width"], "pdftotext page width"),
            _exact_millipoints(page.attrib["height"], "pdftotext page height"),
        ]
    except KeyError as exc:
        raise SourceReplayMismatch("pdftotext page lacks dimensions") from exc
    if actual_size != page_size:
        raise SourceReplayMismatch("pdftotext page geometry does not match the locator")
    words: list[list[Any]] = []
    for element in page.iter():
        if element.tag.rsplit("}", 1)[-1] != "word":
            continue
        try:
            exact = [
                _plain_decimal(element.attrib[name], f"pdftotext word {name}")
                for name in ("xMin", "yMin", "xMax", "yMax")
            ]
            rounded = [
                _rounded_millipoints(element.attrib[name], f"pdftotext word {name}")
                for name in ("xMin", "yMin", "xMax", "yMax")
            ]
        except KeyError as exc:
            raise SourceReplayMismatch("pdftotext word lacks coordinates") from exc
        x_min, y_min, x_max, y_max = exact
        if not (
            Decimal(0) <= x_min <= x_max <= Decimal(page_size[0]) / 1000
            and Decimal(0) <= y_min <= y_max <= Decimal(page_size[1]) / 1000
        ):
            raise SourceReplayMismatch("pdftotext word coordinates are outside the page")
        words.append([element.text or "", *rounded])
    return words


def _replay_pdf_segment_path(
    path: Path,
    document: Mapping[str, Any],
    locator: Mapping[str, Any],
    literal: Mapping[str, Any],
) -> _SegmentReplay:
    _require_profile(
        literal,
        algorithm=PDF_WORD_ALGORITHM,
        tool=PDF_WORD_TOOL,
        tool_version=None,
        selection_rule=PDF_WORD_SELECTION_RULE,
        digest_domain=PDF_WORD_DIGEST_DOMAIN,
    )
    version_result = _run(["pdftotext", "-v"])
    version_text = (version_result.stderr + version_result.stdout).decode(
        "utf-8", errors="replace"
    )
    match = _PDFTO_TEXT_VERSION.search(version_text)
    if not match:
        raise SourceReplayUnavailable("cannot determine the pdftotext version")
    if match.group(1) != literal["tool_version"]:
        raise SourceReplayUnavailable(
            "pdftotext version differs from the literal snapshot profile"
        )

    page = int(locator["physical_page"])
    page_count, page_size, rotation = _pdf_page_info(path, page)
    if page_count != document["structure"]["page_count"]:
        raise SourceReplayMismatch("PDF page count does not match the source record")
    if page > page_count:
        raise SourceReplayMismatch("PDF region names a page outside the source artifact")
    if page_size != locator["page_size_millipoints"]:
        raise SourceReplayMismatch("PDF page size does not match the region locator")
    if rotation != locator["page_rotation_degrees"]:
        raise SourceReplayMismatch("PDF page rotation does not match the region locator")
    if rotation != 0:
        raise SourceReplayUnavailable(
            "non-zero PDF rotation has no declared coordinate transform in this profile"
        )

    words = _pdf_words(path, page, page_size)
    left, top, right, bottom = locator["bbox_millipoints"]
    selected: list[list[Any]] = []
    for word in words:
        x_min, y_min, x_max, y_max = word[1:]
        center_x = (x_min + x_max) // 2
        center_y = (y_min + y_max) // 2
        if left <= center_x <= right and top <= center_y <= bottom:
            selected.append(word)
    if len(selected) != literal["item_count"]:
        raise SourceReplayMismatch("literal snapshot item_count does not replay")
    digest = hashlib.sha256(
        PDF_WORD_DIGEST_DOMAIN.encode("ascii") + b"\0" + canonical_bytes(selected)
    ).hexdigest()
    if digest != literal["sha256"]:
        raise SourceReplayMismatch("literal snapshot digest does not replay")
    metadata_limit = ""
    if locator["printed_label"] is not None or locator["section_raw"] is not None:
        metadata_limit = (
            "; printed_label and section_raw are descriptive metadata without "
            "an executable replay rule"
        )
    return _SegmentReplay(
        exact_text=None,
        claim_text_available=False,
        limitation=(
            "PDF word replay proves the ordered word snapshot, not an exact "
            "character-and-whitespace transcription" + metadata_limit
        ),
    )


def _replay_pdf_segment(
    raw: bytes,
    document: Mapping[str, Any],
    locator: Mapping[str, Any],
    literal: Mapping[str, Any],
) -> _SegmentReplay:
    """Run both PDF tools against one private copy of already-verified bytes."""

    with tempfile.TemporaryDirectory(prefix="smf-source-replay-") as directory:
        private_path = Path(directory) / "verified-source.pdf"
        private_path.write_bytes(raw)
        return _replay_pdf_segment_path(
            private_path,
            document,
            locator,
            literal,
        )


def _reviewed_path(root: Path, declared: str) -> Path:
    candidate = Path(declared)
    if candidate.is_absolute():
        raise SourceReplayMismatch("reviewed transcription path must be relative")
    base = root.resolve()
    resolved = (base / candidate).resolve()
    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise SourceReplayMismatch(
            "reviewed transcription path escapes the replay root"
        ) from exc
    return resolved


def _replay_reviewed_transcription(
    reviewed: Mapping[str, Any],
    *,
    transcription_root: Path | None,
    selected: _SegmentReplay,
) -> _SegmentReplay:
    if transcription_root is None:
        raise SourceReplayUnavailable(
            "a reviewed transcription was declared but no replay root was supplied"
        )
    path = _reviewed_path(transcription_root, str(reviewed["path"]))
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise SourceReplayUnavailable(
            f"cannot read reviewed transcription: {reviewed['path']}"
        ) from exc
    if bytes_digest(raw) != reviewed["sha256"]:
        raise SourceReplayMismatch("reviewed transcription digest does not replay")
    if b"\r" in raw:
        raise SourceReplayMismatch("reviewed transcription is not LF-only")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SourceReplayMismatch("reviewed transcription is not UTF-8") from exc
    if unicodedata.normalize("NFC", text) != text:
        raise SourceReplayMismatch("reviewed transcription is not NFC")
    if raw.endswith(b"\n") != reviewed["final_newline"]:
        raise SourceReplayMismatch(
            "reviewed transcription final_newline declaration does not replay"
        )
    transformations = reviewed["declared_transformations"]
    if transformations:
        return _SegmentReplay(
            exact_text=None,
            claim_text_available=False,
            limitation=(
                "declared transcription transformations have no executable "
                "replay semantics in v1"
            ),
        )
    if not selected.claim_text_available:
        return _SegmentReplay(
            exact_text=None,
            claim_text_available=False,
            limitation=(
                "the transcription artifact replays, but its character-level "
                "relation to the PDF word snapshot is not executable in v1"
            ),
        )
    if text != selected.exact_text:
        raise SourceReplayMismatch(
            "zero-transformation reviewed transcription differs from the exact selection"
        )
    return _SegmentReplay(exact_text=text, claim_text_available=True)


def replay_translation_sources(
    *,
    snapshot: Mapping[str, Any],
    validation: TranslationValidationResult,
    records: Mapping[str, Mapping[str, Any]],
    source_documents: Mapping[str, Path],
    transcription_root: Path | None,
) -> SourceReplayResult:
    """Replay all selected source records and exact verbatim claim bindings.

    This is a context-bound replay step, not a standalone record validator.
    Its mandatory ``validation`` argument must be the successful result of
    ``validate_translation_snapshot(snapshot, records)`` for this exact
    snapshot. Unsupported profiles and unavailable tools are returned as
    explicit limitations. Any disagreement with a profile that *can* be
    executed raises :class:`SourceReplayMismatch` and must invalidate source
    identity.
    """

    if not isinstance(validation, TranslationValidationResult):
        raise TypeError("validation must be a TranslationValidationResult")
    current_validation = validate_translation_snapshot(dict(snapshot), records)
    if current_validation != validation:
        raise RecordError(
            "source replay validation does not bind this exact snapshot inventory"
        )

    verified_documents: list[str] = []
    document_bytes: dict[str, bytes] = {}
    for document_id in snapshot["document_ids"]:
        document = records[document_id]
        validate_translation_record(document)
        path = source_documents[document_id]
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise SourceReplayMismatch(f"cannot read source document: {exc}") from exc
        artifact = document["artifact"]
        if len(raw) != artifact["byte_length"] or bytes_digest(raw) != artifact["sha256"]:
            raise SourceReplayMismatch(
                "source document bytes do not match the bound artifact"
            )
        if document["structure"]["kind"] == "UTF8_TEXT":
            try:
                raw.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise SourceReplayMismatch(
                    "bound UTF8_TEXT artifact is not valid UTF-8"
                ) from exc
        document_bytes[document_id] = raw
        verified_documents.append(document_id)

    verified_spans: list[str] = []
    unresolved_spans: list[str] = []
    limitations: dict[str, str] = {}
    span_text: dict[str, str | None] = {}
    for span_id in snapshot["span_ids"]:
        span = records[span_id]
        validate_translation_record(span)
        document_id = span["document_id"]
        document = records[document_id]
        segments: list[_SegmentReplay] = []
        span_limitations: list[str] = []
        for segment in span["segments"]:
            locator = segment["locator"]
            literal = segment["literal_snapshot"]
            try:
                if locator["kind"] == "UTF8_BYTE_RANGE":
                    if document["structure"]["kind"] != "UTF8_TEXT":
                        raise SourceReplayMismatch(
                            "UTF-8 byte-range locator is bound to a non-text document"
                        )
                    replay = _replay_utf8_segment(
                        document_bytes[document_id], locator, literal
                    )
                elif locator["kind"] == "PDF_REGION":
                    if document["structure"]["kind"] != "PDF":
                        raise SourceReplayMismatch(
                            "PDF region locator is bound to a non-PDF document"
                        )
                    replay = _replay_pdf_segment(
                        document_bytes[document_id], document, locator, literal
                    )
                else:  # Intrinsic validation should already make this unreachable.
                    raise SourceReplayUnavailable("unsupported source locator kind")
                if segment["reviewed_transcription"] is not None:
                    replay = _replay_reviewed_transcription(
                        segment["reviewed_transcription"],
                        transcription_root=transcription_root,
                        selected=replay,
                    )
                if replay.limitation is not None:
                    span_limitations.append(replay.limitation)
                segments.append(replay)
            except SourceReplayUnavailable as exc:
                span_limitations.append(str(exc))
                segments.append(
                    _SegmentReplay(
                        exact_text=None,
                        claim_text_available=False,
                        limitation=str(exc),
                    )
                )
        if span_limitations:
            unresolved_spans.append(span_id)
            limitations[span_id] = "; ".join(dict.fromkeys(span_limitations))
        else:
            verified_spans.append(span_id)
        if segments and all(
            segment.claim_text_available and segment.exact_text is not None
            for segment in segments
        ):
            span_text[span_id] = "".join(
                segment.exact_text for segment in segments
                if segment.exact_text is not None
            )
        else:
            span_text[span_id] = None

    grounded_claims: list[str] = []
    unresolved_claims: list[str] = []
    graph = records[snapshot["graph_id"]]
    for obligation in graph["obligations"]:
        claim = obligation["source_claim"]
        claim_id = claim["claim_id"]
        cited = claim["source_span_ids"]
        if (
            claim.get("claim_kind") != "SOURCE_AUTHORITY"
            or claim.get("expression_mode") != "VERBATIM_TRANSCRIPTION"
        ):
            raise SourceReplayMismatch(
                f"source claim {claim_id} is not a declared verbatim SOURCE_AUTHORITY claim"
            )
        if claim.get("source_marks_raw"):
            unresolved_claims.append(claim_id)
            limitations[claim_id] = (
                "source_marks_raw has no executable locator relation in v1"
            )
            continue
        if len(cited) != 1 or span_text.get(cited[0]) is None:
            unresolved_claims.append(claim_id)
            limitations[claim_id] = (
                "verbatim claim grounding requires one source span whose "
                "ordered character-level segments all replay exactly in v1"
            )
            continue
        if claim["statement"] != span_text[cited[0]]:
            raise SourceReplayMismatch(
                f"SOURCE_AUTHORITY claim {claim_id} is not the exact replayed transcription"
            )
        grounded_claims.append(claim_id)

    return SourceReplayResult(
        verified_document_ids=tuple(sorted(verified_documents)),
        verified_span_ids=tuple(sorted(verified_spans)),
        unresolved_span_ids=tuple(sorted(unresolved_spans)),
        mechanically_grounded_claim_ids=tuple(sorted(grounded_claims)),
        unresolved_claim_ids=tuple(sorted(unresolved_claims)),
        limitations=tuple(sorted(limitations.items())),
    )


__all__ = [
    "PDF_WORD_ALGORITHM",
    "PDF_WORD_DIGEST_DOMAIN",
    "PDF_WORD_SELECTION_RULE",
    "PDF_WORD_TOOL",
    "SourceReplayMismatch",
    "SourceReplayResult",
    "SourceReplayUnavailable",
    "UTF8_RANGE_ALGORITHM",
    "UTF8_RANGE_DIGEST_DOMAIN",
    "UTF8_RANGE_SELECTION_RULE",
    "UTF8_RANGE_TOOL",
    "UTF8_RANGE_TOOL_VERSION",
    "replay_translation_sources",
]
