"""R8, R9, R10: the format grammar, compiled at run start, freeform by default."""

from __future__ import annotations

import copy
import json

from creib.forge.mini.formats import FREEFORM, compile_format_spec
from creib.forge.mini.log import ARTIFACT_SUBMITTED, FORMAT_FAILURE

from .helpers import MiniTestCase, base_manifest, submission

KEYWORD_SPEC = {"body": {"all_of": [{"check": "keywords", "keywords": ["BECAUSE"]}]}}
JSON_SPEC = {
    "commitments": {
        "all_of": [
            {
                "check": "json_schema",
                "schema": {"type": "object", "required": ["commit"], "properties": {"commit": {"type": "string"}}},
            }
        ]
    }
}


class FreeformTests(MiniTestCase):
    def test_no_specification_checks_nothing_beyond_the_two_fields(self) -> None:
        """R8: absent a specification, anything non-empty is accepted."""

        plan, outcome = self.run_manifest(base_manifest())
        self.assertTrue(plan.formats["k.conjecture"].freeform)
        self.assertEqual(self.events_of(outcome, FORMAT_FAILURE), [])
        self.assertEqual(len(self.events_of(outcome, ARTIFACT_SUBMITTED)), 3)

    def test_an_empty_body_is_still_refused(self) -> None:
        manifest = base_manifest()
        script = {"c1": [submission("   ", "a commitment"), submission("   ", "a commitment")], "x1": [submission("a", "b")]}
        _, outcome = self.run_manifest(manifest, script)
        failures = self.events_of(outcome, FORMAT_FAILURE)
        self.assertTrue(failures)
        self.assertEqual(failures[0]["payload"]["code"], "MINI_SUBMISSION_MISSING_FIELD")

    def test_the_freeform_checker_finds_nothing_to_fail(self) -> None:
        self.assertEqual(FREEFORM.failures({"body": "anything", "commitments": "anything"}), ())


class KeywordGrammarTests(MiniTestCase):
    def _manifest(self) -> dict:
        manifest = base_manifest()
        manifest["kinds"][0]["format"] = copy.deepcopy(KEYWORD_SPEC)
        manifest["kinds"][0]["failure_policy"] = {"retries": 1}
        return manifest

    def test_a_body_missing_the_keyword_is_a_typed_failure_on_the_record(self) -> None:
        script = {
            "c1": [submission("No such word here.", "c"), submission("No such word here either.", "c")],
            "x1": [submission("a", "b")],
        }
        _, outcome = self.run_manifest(self._manifest(), script)
        failures = self.events_of(outcome, FORMAT_FAILURE)
        self.assertEqual(len(failures), 2)
        self.assertIn("BECAUSE", failures[0]["payload"]["reasons"][0])
        self.assertEqual(self.events_of(outcome, "SUBMISSION_DROPPED")[0]["kind_id"], "k.conjecture")

    def test_a_body_carrying_the_keyword_is_accepted(self) -> None:
        script = {"c1": [submission("It holds BECAUSE the source says so.", "c")], "x1": [submission("a", "b")]}
        _, outcome = self.run_manifest(self._manifest(), script)
        self.assertEqual(self.events_of(outcome, FORMAT_FAILURE), [])
        self.assertEqual(len(self.events_of(outcome, ARTIFACT_SUBMITTED)), 3)

    def test_the_format_error_is_shown_to_the_seat_on_the_retry(self) -> None:
        """R10: a failing submission is re-asked with the reason in the brief."""

        seen: list[str] = []

        class Recording:
            def __init__(self, inner) -> None:
                self._inner = inner

            def reply(self, request):
                seen.append(request.brief)
                return self._inner.reply(request)

        from creib.forge.mini.executor import ScriptedResponder
        from creib.forge.mini.runner import run_mini

        plan = self.compile(self._manifest())
        script = {
            "c1": [submission("nothing here", "c"), submission("now BECAUSE it is", "c")],
            "x1": [submission("a", "b")],
        }
        run_mini(plan, self.tmp / "run", Recording(ScriptedResponder(script)))
        self.assertNotIn("The last reply was refused", seen[0])
        self.assertIn("The last reply was refused", seen[1])
        self.assertIn("BECAUSE", seen[1])


class OtherChecksTests(MiniTestCase):
    def test_a_schema_fragment_rejects_malformed_json_in_the_commitments(self) -> None:
        compiled = compile_format_spec(copy.deepcopy(JSON_SPEC), "format")
        reasons = compiled.failures({"body": "anything", "commitments": "{not json"})
        self.assertEqual(len(reasons), 1)
        self.assertIn("not readable as JSON", reasons[0])

    def test_a_schema_fragment_rejects_json_of_the_wrong_shape(self) -> None:
        compiled = compile_format_spec(copy.deepcopy(JSON_SPEC), "format")
        self.assertTrue(compiled.failures({"body": "x", "commitments": json.dumps({"other": "x"})}))
        self.assertEqual(compiled.failures({"body": "x", "commitments": json.dumps({"commit": "x"})}), ())

    def test_section_markers_must_begin_lines_in_order(self) -> None:
        compiled = compile_format_spec(
            {"body": {"all_of": [{"check": "sections", "markers": ["## Claim", "## Ground"]}]}}, "format"
        )
        self.assertEqual(compiled.failures({"body": "## Claim\nx\n## Ground\ny", "commitments": "c"}), ())
        self.assertTrue(compiled.failures({"body": "## Ground\ny\n## Claim\nx", "commitments": "c"}))

    def test_a_regular_expression_check(self) -> None:
        compiled = compile_format_spec({"body": {"all_of": [{"check": "regex", "pattern": "^C-[0-9]+"}]}}, "format")
        self.assertEqual(compiled.failures({"body": "C-12 and so on", "commitments": "c"}), ())
        self.assertTrue(compiled.failures({"body": "no code here", "commitments": "c"}))

    def test_a_line_shape_over_every_line_and_over_any_line(self) -> None:
        every = compile_format_spec(
            {"body": {"all_of": [{"check": "line_shape", "pattern": "^- ", "applies_to": "every_line"}]}}, "format"
        )
        self.assertEqual(every.failures({"body": "- one\n- two", "commitments": "c"}), ())
        self.assertTrue(every.failures({"body": "- one\ntwo", "commitments": "c"}))
        some = compile_format_spec(
            {"body": {"all_of": [{"check": "line_shape", "pattern": "^- ", "applies_to": "any_line"}]}}, "format"
        )
        self.assertEqual(some.failures({"body": "- one\ntwo", "commitments": "c"}), ())
        self.assertTrue(some.failures({"body": "one\ntwo", "commitments": "c"}))

    def test_keywords_may_ignore_case(self) -> None:
        compiled = compile_format_spec(
            {"body": {"all_of": [{"check": "keywords", "keywords": ["because"], "case_sensitive": False}]}}, "format"
        )
        self.assertEqual(compiled.failures({"body": "BECAUSE", "commitments": "c"}), ())

    def test_checks_combine(self) -> None:
        compiled = compile_format_spec(
            {"body": {"all_of": [{"check": "keywords", "keywords": ["A"]}, {"check": "regex", "pattern": "B"}]}}, "format"
        )
        self.assertEqual(len(compiled.failures({"body": "nothing", "commitments": "c"})), 2)
        self.assertEqual(compiled.failures({"body": "A and B", "commitments": "c"}), ())


class MalformedSpecificationTests(MiniTestCase):
    """R8: a specification that cannot be compiled refuses the run before any call."""

    def _refuse(self, code: str, spec: dict) -> None:
        manifest = base_manifest()
        manifest["kinds"][0]["format"] = spec
        self.assertRefuses(code, self.compile, manifest)

    def test_an_unknown_check_refuses_the_run(self) -> None:
        self._refuse("MINI_FORMAT_SPEC_INVALID", {"body": {"all_of": [{"check": "vibes"}]}})

    def test_an_uncompilable_expression_refuses_the_run(self) -> None:
        self._refuse("MINI_FORMAT_SPEC_INVALID", {"body": {"all_of": [{"check": "regex", "pattern": "([unclosed"}]}})

    def test_an_empty_keyword_list_refuses_the_run(self) -> None:
        self._refuse("MINI_FORMAT_SPEC_INVALID", {"body": {"all_of": [{"check": "keywords", "keywords": []}]}})

    def test_a_keyword_flag_that_is_not_a_flag_refuses_the_run(self) -> None:
        self._refuse(
            "MINI_FORMAT_SPEC_INVALID",
            {"body": {"all_of": [{"check": "keywords", "keywords": ["A"], "case_sensitive": "yes"}]}},
        )

    def test_an_unknown_line_scope_refuses_the_run(self) -> None:
        self._refuse(
            "MINI_FORMAT_SPEC_INVALID",
            {"body": {"all_of": [{"check": "line_shape", "pattern": "x", "applies_to": "some_lines"}]}},
        )

    def test_an_invalid_schema_fragment_refuses_the_run(self) -> None:
        self._refuse(
            "MINI_FORMAT_SPEC_INVALID",
            {"commitments": {"all_of": [{"check": "json_schema", "schema": {"type": "not-a-type"}}]}},
        )

    def test_a_fragment_that_would_fetch_a_schema_refuses_the_run(self) -> None:
        self._refuse(
            "MINI_FORMAT_SPEC_INVALID",
            {"commitments": {"all_of": [{"check": "json_schema", "schema": {"$ref": "https://example.invalid/x.json"}}]}},
        )

    def test_a_line_shape_over_a_body_with_no_lines_fails_the_check(self) -> None:
        compiled = compile_format_spec(
            {"body": {"all_of": [{"check": "line_shape", "pattern": "^- ", "applies_to": "any_line"}]}}, "format"
        )
        self.assertTrue(compiled.failures({"body": "   ", "commitments": "c"}))


class TheFormatIsShownTests(MiniTestCase):
    """R24: the compiled format is rendered in full, on every attempt."""

    def test_the_schema_text_is_in_the_dispatched_request_bytes_on_attempt_one(self) -> None:
        """Not the rendered brief — the bytes that would have gone over the wire."""

        import json as json_module

        from creib.forge.mini.executor import LiveResponder
        from creib.forge.mini.runner import run_mini

        manifest = base_manifest()
        manifest["kinds"][0]["format"] = copy.deepcopy(JSON_SPEC)
        manifest["stages"] = [
            {"stage_id": "c1", "kind_id": "k.conjecture", "ports": ["problem"]},
            {"stage_id": "end", "end": True},
        ]
        plan = self.compile(manifest)

        sent: list[bytes] = []

        class _Stub:
            def complete(self, request):
                sent.append(json_module.dumps(request.body(), ensure_ascii=False).encode("utf-8"))
                from creib.forge.conformance.executor import ChatResponse

                return ChatResponse(
                    content=json_module.dumps({"body": "b", "commitments": json_module.dumps({"commit": "x"})}),
                    thinking_present=False,
                    done=True,
                    done_reason="stop",
                    prompt_eval_count=1,
                    eval_count=1,
                    total_duration_ns=None,
                    http_status=200,
                    transport_error=None,
                    response_digest="0" * 64,
                )

        run_mini(plan, self.tmp / "run", LiveResponder("a-model", _Stub()))
        self.assertEqual(len(sent), 2)  # a body call and a commitments call
        first = sent[0].decode("utf-8")
        self.assertIn('\\"commit\\"', first)
        self.assertIn("required", first)
        self.assertIn("must be JSON fitting exactly this schema", first)

    def test_the_keyword_list_is_written_out_in_full(self) -> None:
        compiled = compile_format_spec(
            {"body": {"all_of": [{"check": "keywords", "keywords": ["BECAUSE", "THEREFORE"]}]}}, "format"
        )
        rendered = "\n".join(compiled.describe())
        self.assertIn("- BECAUSE", rendered)
        self.assertIn("- THEREFORE", rendered)
        self.assertIn("exactly as written", rendered)

    def test_every_check_kind_renders_something_a_seat_could_act_on(self) -> None:
        compiled = compile_format_spec(
            {
                "body": {
                    "all_of": [
                        {"check": "sections", "markers": ["## Claim"]},
                        {"check": "regex", "pattern": "^C-[0-9]+"},
                        {"check": "line_shape", "pattern": "^- ", "applies_to": "any_line"},
                    ]
                },
                "commitments": {"all_of": [{"check": "json_schema", "schema": {"type": "object"}}]},
            },
            "format",
        )
        rendered = "\n".join(compiled.describe())
        for expected in ("## Claim", "^C-[0-9]+", "at least one line", '"type": "object"'):
            self.assertIn(expected, rendered)

    def test_the_format_is_in_the_brief_on_the_first_attempt_and_the_error_beside_it_on_the_retry(self) -> None:
        seen: list[str] = []

        class Recording:
            def __init__(self, inner) -> None:
                self._inner = inner

            def reply(self, request):
                seen.append(request.brief)
                return self._inner.reply(request)

        from creib.forge.mini.executor import ScriptedResponder
        from creib.forge.mini.runner import run_mini

        manifest = base_manifest()
        manifest["kinds"][0]["format"] = copy.deepcopy(KEYWORD_SPEC)
        manifest["kinds"][0]["failure_policy"] = {"retries": 1}
        plan = self.compile(manifest)
        run_mini(
            plan,
            self.tmp / "run",
            Recording(ScriptedResponder({"c1": [submission("no", "c"), submission("BECAUSE", "c")], "x1": [submission("a", "b")]})),
        )
        self.assertIn("- BECAUSE", seen[0])
        self.assertNotIn("was refused", seen[0])
        self.assertIn("- BECAUSE", seen[1])
        self.assertIn("was refused", seen[1])
