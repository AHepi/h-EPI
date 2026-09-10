"""Evidence: cut into blocks, tagged with a tier, shown as a legend, and every
citation byte-checked (R12).

A supplied source is cut at blank lines into paragraph-level blocks. Each block
carries the byte offsets of its span in the source and the digest of its text,
and its identity is a digest over that content, so cutting the same bytes twice
gives the same ids.

What is deliberately absent is DeepReason's wiring. A citation check here is a
measure written to the record and read by nothing that decides anything: it
reaches no routing decision, no permission decision, and no status. This
prototype mints no status at all.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .common import BLOCK_DOMAIN, MiniError, content_id, digest_bytes

TIER_EVIDENCE = "evidence"
TIER_GENERATED = "generated"
BUILTIN_TIERS: tuple[str, ...] = (TIER_EVIDENCE, TIER_GENERATED)

CITATION_VERIFIED = "MINI_CITATION_VERIFIED"
CITATION_UNKNOWN_BLOCK = "MINI_CITATION_UNKNOWN_BLOCK"
CITATION_AMBIGUOUS = "MINI_CITATION_AMBIGUOUS"
CITATION_WITHHELD = "MINI_CITATION_WITHHELD"
CITATION_QUOTE_MISMATCH = "MINI_CITATION_QUOTE_MISMATCH"
CITATION_CODES: tuple[str, ...] = (
    CITATION_VERIFIED,
    CITATION_UNKNOWN_BLOCK,
    CITATION_AMBIGUOUS,
    CITATION_WITHHELD,
    CITATION_QUOTE_MISMATCH,
)

_PARAGRAPH_BREAK = re.compile(rb"(?:[ \t]*\r?\n){2,}")
_TRAILING = b" \t\r\n"
_WHITESPACE = re.compile(r"\s+")
_LEGEND_EXCERPT = 160
_REF_PREFIX = 16


@dataclass(frozen=True)
class Block:
    """One content-addressed span of one source, tagged with a tier."""

    block_id: str
    source_id: str
    source_sha256: str
    tier: str
    span_start: int
    span_end: int
    text_sha256: str
    text: str

    def to_dict(self) -> dict[str, object]:
        return {
            "block_id": self.block_id,
            "source_id": self.source_id,
            "source_sha256": self.source_sha256,
            "tier": self.tier,
            "span_start": self.span_start,
            "span_end": self.span_end,
            "text_sha256": self.text_sha256,
        }


@dataclass(frozen=True)
class CitationMeasure:
    """The typed outcome of checking one citation. It changes no standing."""

    code: str
    block_ref: str
    block_id: str | None
    quoted: bool
    detail: str
    recovered: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "block_ref": self.block_ref,
            "block_id": self.block_id,
            "quoted": self.quoted,
            "detail": self.detail,
            "recovered": self.recovered,
        }


def folded(value: str) -> str:
    """Collapse every run of whitespace to one space, and strip.

    Folding never inserts whitespace where the source had none, so a quote that
    joins words the source separated still fails.
    """

    return _WHITESPACE.sub(" ", value).strip()


def cut_source(source_id: str, raw: bytes, tier: str) -> tuple[Block, ...]:
    """Cut one source into paragraph-level blocks. Deterministic in the bytes."""

    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise MiniError("MINI_SOURCE_INVALID", f"source {source_id!r} is not UTF-8") from error
    source_sha256 = digest_bytes(raw)
    blocks: list[Block] = []
    offset = 0
    spans: list[tuple[int, int]] = []
    for match in _PARAGRAPH_BREAK.finditer(raw):
        spans.append((offset, match.start()))
        offset = match.end()
    spans.append((offset, len(raw)))
    for start, end in spans:
        while start < end and raw[start : start + 1] in (b" ", b"\t", b"\r", b"\n"):
            start += 1
        while end > start and raw[end - 1 : end] in (b" ", b"\t", b"\r", b"\n"):
            end -= 1
        if start >= end:
            continue
        window = raw[start:end]
        text_sha256 = digest_bytes(window)
        block_id = content_id(
            BLOCK_DOMAIN,
            {
                "source_id": source_id,
                "source_sha256": source_sha256,
                "span_start": start,
                "span_end": end,
                "text_sha256": text_sha256,
            },
        )
        blocks.append(
            Block(
                block_id=block_id,
                source_id=source_id,
                source_sha256=source_sha256,
                tier=tier,
                span_start=start,
                span_end=end,
                text_sha256=text_sha256,
                text=window.decode("utf-8"),
            )
        )
    return tuple(blocks)


def render_legend(blocks: Iterable[Block], header: str) -> str:
    """Render blocks as a legend of ids plus excerpts, one line per block."""

    lines = [header]
    listed = list(blocks)
    if not listed:
        lines.append("(nothing admitted)")
        return "\n".join(lines)
    lines.append(
        "To ground a claim in one of these, name its id in this artifact's citations; "
        "a quote must reproduce the block's own words."
    )
    for block in listed:
        excerpt = folded(block.text)
        if len(excerpt) > _LEGEND_EXCERPT:
            excerpt = excerpt[:_LEGEND_EXCERPT] + "…"
        lines.append(f"[{block.block_id[:_REF_PREFIX]}] ({block.source_id}, {block.tier}) {excerpt}")
    return "\n".join(lines)


def _resolve(reference: str, blocks: Mapping[str, Block]) -> tuple[Block | None, str | None]:
    exact = blocks.get(reference)
    if exact is not None:
        return exact, None
    matched = [block for block in blocks.values() if block.block_id.startswith(reference)]
    if not matched:
        return None, CITATION_UNKNOWN_BLOCK
    if len(matched) > 1:
        return None, CITATION_AMBIGUOUS
    return matched[0], None


def check_citations(
    citations: Iterable[Mapping[str, Any]],
    blocks: Mapping[str, Block],
    exposed_ids: frozenset[str],
) -> tuple[CitationMeasure, ...]:
    """One typed measure per claimed citation. Nothing here changes a standing."""

    measures: list[CitationMeasure] = []
    for entry in citations:
        recovered = entry.get("recovered")
        raw_ref = entry.get("block")
        if type(raw_ref) is not str or not raw_ref:
            measures.append(
                CitationMeasure(CITATION_UNKNOWN_BLOCK, "", None, False, "the citation names no block", recovered)
            )
            continue
        quote = entry.get("quote")
        quoted = type(quote) is str and bool(quote.strip())
        block, failure = _resolve(raw_ref, blocks)
        if failure is not None:
            detail = (
                "no admitted block carries that id"
                if failure == CITATION_UNKNOWN_BLOCK
                else "that id prefix names more than one admitted block"
            )
            measures.append(CitationMeasure(failure, raw_ref, None, quoted, detail, recovered))
            continue
        if block.block_id not in exposed_ids:
            measures.append(
                CitationMeasure(
                    CITATION_WITHHELD,
                    raw_ref,
                    block.block_id,
                    quoted,
                    "that block was not shown to this artifact's seat",
                    recovered,
                )
            )
            continue
        if quoted and folded(str(quote)) not in folded(block.text):
            measures.append(
                CitationMeasure(
                    CITATION_QUOTE_MISMATCH,
                    raw_ref,
                    block.block_id,
                    True,
                    "the quoted words do not occur in that block (whitespace folded on both sides)",
                    recovered,
                )
            )
            continue
        measures.append(
            CitationMeasure(
                CITATION_VERIFIED,
                raw_ref,
                block.block_id,
                quoted,
                "the block resolves and the quoted words occur in it" if quoted else "the block resolves; nothing was quoted",
                recovered,
            )
        )
    return tuple(measures)
