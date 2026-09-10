"""R30 and R31: a fenced reply is read, and citations are fixed at both ends."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from creib.errors import RecordError
from creib.forge.mini.evidence import (
    CITATION_VERIFIED,
    check_citations,
    cut_source,
)
from creib.forge.mini.formats import RECOVERED_CONTROL, compile_format_spec, loads_admitting_control
from creib.forge.mini.kinds import (
    RECOVERED_FENCE,
    RECOVERED_PROSE,
    kind_from_dict,
    read_submission,
    recover_prose_citations,
    strip_fence,
)
from creib.forge.mini.log import ARTIFACT_SUBMITTED, FORMAT_FAILURE, BlobStore, replay

from .helpers import CONJECTURE_KIND, MiniTestCase, base_manifest, submission

GPT_RUN = Path(__file__).resolve().parents[2] / "forge" / "mini" / "runs" / "default-gpt-oss-120b"


def _kind():
    return kind_from_dict(copy.deepcopy(CONJECTURE_KIND), "kind")


class ControlCharacterTests(MiniTestCase):
    """M13: a model that writes a raw line break inside a JSON string meant the line break.

    The strict reading is tried first, the lenient one admits a control character and nothing
    else, and the artifact says which reading served.
    """

    #: The outer reply's own JSON carries a raw line break inside a string, where a model
    #: should have written the two characters backslash and n.
    RAW = '{"body": "a body", "commitments": "line one\nline two"}'

    def test_the_strict_reading_is_tried_first_and_every_other_refusal_stands(self) -> None:
        self.assertEqual(loads_admitting_control('{"a": 1}'), ({"a": 1}, False))
        self.assertEqual(loads_admitting_control('{"a": "x\ny"}'), ({"a": "x\ny"}, True))
        for refused in ('{"a": 1, "a": 2}', '{"a": 1.5}', "not json at all"):
            with self.assertRaises(RecordError):
                loads_admitting_control(refused)

    def test_a_reply_whose_own_json_carries_a_raw_line_break_is_read_and_says_so(self) -> None:
        read = read_submission(self.RAW, _kind())
        self.assertEqual((read.body, read.commitments), ("a body", "line one\nline two"))
        self.assertIn(RECOVERED_CONTROL, read.recovered)
        self.assertNotIn(RECOVERED_CONTROL, read_submission(submission("a body", "c"), _kind()).recovered)

    def test_a_commitments_string_whose_json_carries_a_raw_line_break_fits_its_schema_and_says_so(self) -> None:
        spec = {"commitments": {"all_of": [{"check": "json_schema", "schema": {"type": "object", "required": ["input"], "properties": {"input": {"type": "string"}}}}]}}
        compiled = compile_format_spec(spec, "kind.format")
        fields = {"body": "a body", "commitments": '{"input": "line one\nline two"}'}
        self.assertEqual(compiled.failures(fields), ())
        self.assertEqual(compiled.recoveries(fields), (RECOVERED_CONTROL,))
        strict = {"body": "a body", "commitments": '{"input": "line one"}'}
        self.assertEqual((compiled.failures(strict), compiled.recoveries(strict)), ((), ()))
        broken = {"body": "a body", "commitments": '{"input": 1, "input": 2}'}
        self.assertTrue(compiled.failures(broken))
        self.assertEqual(compiled.recoveries(broken), (), "a field that cannot be read at all recovered nothing")

    def test_the_artifact_records_the_reading(self) -> None:
        manifest = base_manifest()
        kind = next(k for k in manifest["kinds"] if k["kind_id"] == "k.conjecture")
        kind["format"] = {"commitments": {"all_of": [{"check": "json_schema", "schema": {"type": "object", "required": ["input"], "properties": {"input": {"type": "string"}}}}]}}
        stage = next(item for item in manifest["stages"] if item.get("kind_id") == "k.conjecture")
        script = {stage["stage_id"]: [submission("a body", '{"input": "line one\nline two"}')], "x1": [submission("a criticism", "c")]}
        plan, outcome = self.run_manifest(manifest, script)
        events = [json.loads(line) for line in (outcome.root / "log.jsonl").read_text(encoding="utf-8").splitlines()]
        submitted = next(e for e in events if e["type"] == ARTIFACT_SUBMITTED and e["kind_id"] == "k.conjecture")
        self.assertEqual(submitted["payload"]["recovered"], [RECOVERED_CONTROL])


class FencedRepliesTests(MiniTestCase):
    """R30: FAILURE_MODES M4, decided in the direction of stripping."""

    def test_valid_json_inside_a_fence_is_read(self) -> None:
        fenced = "```json\n" + submission("a body", "a commitment") + "\n```"
        read = read_submission(fenced, _kind())
        self.assertEqual(read.body, "a body")
        self.assertIn(RECOVERED_FENCE, read.recovered)

    def test_a_fence_with_no_language_tag_is_read(self) -> None:
        fenced = "```\n" + submission("a body", "c") + "\n```"
        self.assertIn(RECOVERED_FENCE, read_submission(fenced, _kind()).recovered)

    def test_an_unfenced_reply_records_no_recovery(self) -> None:
        self.assertEqual(read_submission(submission("a body", "c"), _kind()).recovered, ())

    def test_a_reply_that_is_not_json_after_stripping_is_still_refused(self) -> None:
        self.assertRefuses(
            "MINI_SUBMISSION_NOT_JSON", read_submission, "```json\nstill not json\n```", _kind()
        )

    def test_the_recovery_is_on_the_record_beside_the_stored_reply(self) -> None:
        fenced = "```json\n" + submission("The two paragraphs disagree.", "c") + "\n```"
        _, outcome = self.run_manifest(base_manifest(), {"c1": [fenced], "x1": [submission("a", "b")]})
        submitted = self.events_of(outcome, ARTIFACT_SUBMITTED)[0]
        self.assertEqual(submitted["payload"]["recovered"], [RECOVERED_FENCE])
        stored = BlobStore(outcome.root / "blobs").get(submitted["payload"]["reply_ref"]).decode("utf-8")
        self.assertEqual(stored, fenced)
        self.assertTrue(stored.startswith("```"))
        parsed = BlobStore(outcome.root / "blobs").get(submitted["body_ref"]).decode("utf-8")
        self.assertEqual(parsed, "The two paragraphs disagree.")

    def test_the_fence_stripper_leaves_ordinary_text_alone(self) -> None:
        self.assertEqual(strip_fence("plain"), ("plain", False))
        self.assertEqual(strip_fence("a ``` in the middle"), ("a ``` in the middle", False))


class DeclaredCitationTests(MiniTestCase):
    """R31, the declaring end: FAILURE_MODES M2."""

    def test_an_empty_block_is_a_format_failure_not_an_unknown_block(self) -> None:
        self.assertRefuses(
            "MINI_SUBMISSION_FIELD_TYPE",
            read_submission,
            submission("b", "c", citations=[{"block": "", "quote": "x"}]),
            _kind(),
        )

    def test_an_empty_quote_is_refused(self) -> None:
        self.assertRefuses(
            "MINI_SUBMISSION_FIELD_TYPE",
            read_submission,
            submission("b", "c", citations=[{"block": "abcd1234abcd1234", "quote": "   "}]),
            _kind(),
        )

    def test_a_missing_quote_is_refused(self) -> None:
        self.assertRefuses(
            "MINI_SUBMISSION_FIELD_TYPE",
            read_submission,
            submission("b", "c", citations=[{"block": "abcd1234abcd1234"}]),
            _kind(),
        )

    def test_the_empty_pair_reaches_the_record_as_a_format_failure(self) -> None:
        bad = submission("a body", "c", citations=[{"block": "", "quote": ""}])
        _, outcome = self.run_manifest(base_manifest(), {"c1": [bad, bad], "x1": [submission("a", "b")]})
        failures = self.events_of(outcome, FORMAT_FAILURE)
        self.assertTrue(failures)
        self.assertEqual(failures[0]["payload"]["code"], "MINI_SUBMISSION_FIELD_TYPE")

    def test_the_live_wire_schema_requires_both_to_be_non_empty(self) -> None:
        from creib.forge.mini.executor import WIRE_SCHEMA

        properties = WIRE_SCHEMA["properties"]["citations"]["items"]["properties"]
        self.assertEqual(properties["block"]["minLength"], 1)
        self.assertEqual(properties["quote"]["minLength"], 1)

    def test_a_declared_citation_is_marked_as_declared(self) -> None:
        read = read_submission(
            submission("b", "c", citations=[{"block": "abcd1234abcd1234", "quote": "x"}]), _kind()
        )
        self.assertIsNone(read.citations[0]["recovered"])


class ProseCitationTests(MiniTestCase):
    """R31, the recovering end: FAILURE_MODES M1."""

    def test_a_bracketed_pair_in_the_body_is_recovered(self) -> None:
        read = read_submission(
            submission('as [dcd587efbf453c90] "some words" shows', "c"), _kind()
        )
        self.assertEqual(len(read.citations), 1)
        self.assertEqual(read.citations[0]["recovered"], RECOVERED_PROSE)
        self.assertIn(RECOVERED_PROSE, read.recovered)

    def test_prose_without_a_block_id_recovers_nothing(self) -> None:
        self.assertEqual(recover_prose_citations('he said "some words" and left'), ())

    def test_a_recovered_citation_never_displaces_a_declared_one(self) -> None:
        read = read_submission(
            submission(
                'as [dcd587efbf453c90] "some words" shows',
                "c",
                citations=[{"block": "dcd587efbf453c90", "quote": "some words"}],
            ),
            _kind(),
        )
        self.assertEqual([item["recovered"] for item in read.citations], [None, RECOVERED_PROSE])

    def test_the_gpt_oss_run_yields_eleven_recovered_citations_all_verified(self) -> None:
        """The amendment's own test: the run that put its citations in prose."""

        from creib.forge.mini.common import RUN_HEADER_DOMAIN, content_id
        from creib.forge.mini.runner import _as_block
        from creib.strict_json import load_strict

        genesis = content_id(RUN_HEADER_DOMAIN, load_strict(GPT_RUN / "run-header.json"))
        state = replay(GPT_RUN / "log.jsonl", genesis)
        store = BlobStore(GPT_RUN / "blobs")
        blocks = {str(item["block_id"]): _as_block(store, item) for item in state.blocks}
        exposed = frozenset(blocks)

        measures = []
        for key in state.artifact_order:
            body = store.get(str(state.artifacts[key]["body_ref"])).decode("utf-8")
            measures.extend(check_citations(recover_prose_citations(body), blocks, exposed))
        self.assertEqual(len(measures), 11)
        self.assertEqual({measure.code for measure in measures}, {CITATION_VERIFIED})
        self.assertEqual({measure.recovered for measure in measures}, {RECOVERED_PROSE})

    def test_a_recovered_citation_is_byte_checked_exactly_as_a_declared_one(self) -> None:
        blocks = {block.block_id: block for block in cut_source("s1", b"The first paragraph.", "evidence")}
        block_id = next(iter(blocks))
        good = check_citations(
            recover_prose_citations(f'[{block_id[:16]}] "first paragraph"'), blocks, frozenset(blocks)
        )
        bad = check_citations(
            recover_prose_citations(f'[{block_id[:16]}] "words never written"'), blocks, frozenset(blocks)
        )
        self.assertEqual(good[0].code, CITATION_VERIFIED)
        self.assertEqual(bad[0].code, "MINI_CITATION_QUOTE_MISMATCH")
        self.assertEqual((good[0].recovered, bad[0].recovered), (RECOVERED_PROSE, RECOVERED_PROSE))


class WorkedExampleTests(MiniTestCase):
    def test_the_brief_shows_one_worked_citation_using_a_block_the_stage_can_see(self) -> None:
        from creib.forge.mini.runner import render_brief

        plan, outcome = self.run_manifest(base_manifest())
        state = replay(outcome.root / "log.jsonl", plan.genesis)
        brief, exposed = render_brief(plan, state, BlobStore(outcome.root / "blobs"), plan.stage("c1"), 1)
        self.assertIn('"citations": [{"block": "', brief)
        self.assertTrue(any(block_id[:16] in brief for block_id in exposed))

    def test_a_stage_with_no_evidence_shows_no_example(self) -> None:
        from creib.forge.mini.runner import render_brief

        manifest = base_manifest()
        manifest["stages"][0]["ports"] = ["problem"]
        plan, outcome = self.run_manifest(manifest)
        state = replay(outcome.root / "log.jsonl", plan.genesis)
        brief, _ = render_brief(plan, state, BlobStore(outcome.root / "blobs"), plan.stage("c1"), 1)
        self.assertNotIn('"citations": [{"block": "', brief)
