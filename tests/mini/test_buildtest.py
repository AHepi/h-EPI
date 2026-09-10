"""BUILD-TEST-1: the two briefs, the reading, the execution, and the measures.

The protocol is only worth running if its parts do what it says: the arms differ in exactly what
they are shown, a reply that is not a proposal is not repaired into one, a pair whose two texts
are the same is not scored, and a contradiction is the machine disagreeing with the arm's own
expectation rather than with anything a person believes.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from creib.forge.mini import buildtest
from creib.forge.mini.common import MiniError
from creib.forge.mini.usetest import load_subject, subject_source

from .helpers import MiniTestCase

CONTROL = "```\nHere is the result:\n{\"a\": 1}\n```\n{\"b\": 2}"


class BriefTests(MiniTestCase):
    def test_the_arms_differ_in_exactly_what_they_are_shown(self) -> None:
        source = subject_source()
        r_system, r_user = buildtest.brief(buildtest.ARM_RECONSTRUCT, source)
        l_system, l_user = buildtest.brief(buildtest.ARM_RELAY, source)
        self.assertIn("none of their code", r_system)
        self.assertIn("their complete source", l_system)
        tail = "You are testing one check"
        self.assertEqual(r_system[r_system.index(tail):], l_system[l_system.index(tail):], "one task, two openings")
        # Both are shown every signature; only one is shown a body. A lowercase indented
        # ``return`` occurs in the code and in no docstring of this subject.
        self.assertNotIn("\n    return ", r_user, "the reconstruction arm is shown no code")
        self.assertIn("\n    return ", l_user, "the relay arm is shown the code")
        self.assertIn("def recover_json_object", r_user, "both arms are shown the signatures")
        self.assertIn("## The documented rules", r_user)
        self.assertIn("## The documented rules", l_user)

    def test_an_arm_that_is_not_an_arm_is_refused(self) -> None:
        with self.assertRaises(MiniError) as caught:
            buildtest.brief("C", subject_source())
        self.assertEqual(caught.exception.code, "MINI_BUILDTEST_ARM_UNKNOWN")

    def test_no_grid_is_offered_in_either_brief(self) -> None:
        """ECS 2.0 section 8.3: an enabling condition may not deliver a functioning solution."""

        for arm in buildtest.ARMS:
            system, user = buildtest.brief(arm, subject_source())
            self.assertNotIn("fence[", system)
            self.assertNotIn("fence[", user)


class ReadingTests(MiniTestCase):
    def _proposal(self, **overrides):
        base = {"kernel": "recovery", "expect": "moves", "input": "a", "rewritten": "b", "reading": "because"}
        return json.dumps({**base, **overrides})

    def test_a_proposal_is_read_when_every_field_is_a_string_of_the_right_kind(self) -> None:
        parsed = buildtest.read_proposal(self._proposal())
        self.assertIsNotNone(parsed)
        self.assertEqual((parsed.kernel, parsed.expect), ("recovery", "moves"))

    def test_a_reply_that_is_not_a_proposal_is_not_repaired_into_one(self) -> None:
        for reply in ("not json", "[]", json.dumps({"kernel": "recovery"}),
                      self._proposal(kernel="no-such-kernel"), self._proposal(expect="maybe"),
                      json.dumps({"kernel": "recovery", "expect": "moves", "input": 1, "rewritten": "b", "reading": "c"})):
            with self.subTest(reply=reply[:40]):
                self.assertIsNone(buildtest.read_proposal(reply))

    def test_a_reply_carrying_control_characters_is_still_read(self) -> None:
        self.assertIsNotNone(buildtest.read_proposal('{"kernel":"recovery","expect":"moves","input":"a\nb","rewritten":"c","reading":"d"}'))


class ExecutionTests(MiniTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.scratch = tempfile.TemporaryDirectory()
        path = Path(self.scratch.name) / "subject.py"
        path.write_text(subject_source(), encoding="utf-8")
        self.subject = load_subject(path)
        self.addCleanup(self.scratch.cleanup)

    def _run(self, **kwargs):
        base = {"kernel": "recovery", "expect": "moves", "input": '{"a": 1}', "rewritten": '{"b": 2}', "reading": "r"}
        return buildtest.execute(self.subject, buildtest.Proposal(**{**base, **kwargs}))

    def test_a_pair_of_the_same_text_is_degenerate_and_is_not_scored(self) -> None:
        outcome = self._run(rewritten='{"a": 1}')
        self.assertEqual(outcome.executed, "degenerate")
        self.assertFalse(outcome.contradicted)

    def test_a_pair_that_moves_when_the_arm_said_it_would_is_no_contradiction(self) -> None:
        outcome = self._run()
        self.assertEqual(outcome.executed, "moved")
        self.assertFalse(outcome.contradicted)

    def test_a_contradiction_is_the_machine_disagreeing_with_the_arm(self) -> None:
        outcome = self._run(expect="unchanged")
        self.assertEqual(outcome.executed, "moved")
        self.assertTrue(outcome.contradicted)

    def test_the_known_boundary_is_identified_by_shape_and_not_by_a_string(self) -> None:
        self.assertTrue(buildtest.reproduces_h43(self.subject, CONTROL))
        self.assertFalse(buildtest.reproduces_h43(self.subject, '```\n{"a": 1}\n```\n{"b": 2}'), "no prose in the fence")
        self.assertFalse(buildtest.reproduces_h43(self.subject, '{"a": 1}'), "no fence at all")

    def test_the_measures_count_what_the_protocol_fixed(self) -> None:
        executions = [self._run(), self._run(expect="unchanged"), self._run(rewritten='{"a": 1}')]
        m = buildtest.measures(executions, self.subject)
        self.assertEqual((m["proposals"], m["executed"], m["degenerate"], m["contradicted"]), (3, 2, 1, 1))
        self.assertEqual(m["distinct_behaviours"], 1, "both runnable pairs have the same behaviour triple")

    def test_unique_to_arm_is_a_set_difference_of_behaviour_and_not_a_score(self) -> None:
        mine = {"measures": {"behaviours": [["recovery", "x", "y"], ["recovery", "p", "q"]]}}
        theirs = {"measures": {"behaviours": [["recovery", "x", "y"]]}}
        self.assertEqual(buildtest.unique_to_arm(mine, theirs), [["recovery", "p", "q"]])
        self.assertEqual(buildtest.unique_to_arm(theirs, mine), [])


class EndpointTests(MiniTestCase):
    def test_a_path_records_whether_its_weights_are_the_vendors(self) -> None:
        self.assertIn("unquantised", buildtest.Endpoint(buildtest.PATH_DEEPSEEK, "m", None).quantisation)
        self.assertIn("may be quantised", buildtest.Endpoint(buildtest.PATH_OLLAMA, "m", None).quantisation)

    def test_a_path_that_is_not_a_path_is_refused_before_any_key_is_read(self) -> None:
        with self.assertRaises(MiniError) as caught:
            buildtest.ask(buildtest.Endpoint("example.com", "m", None), "s", "u")
        self.assertEqual(caught.exception.code, "MINI_BUILDTEST_PATH_UNKNOWN")

    def test_a_condition_names_itself_by_every_factor_that_varies(self) -> None:
        condition = buildtest.Condition("R", buildtest.Endpoint(buildtest.PATH_DEEPSEEK, "deepseek-flash", True))
        self.assertEqual(condition.condition_id, "api.deepseek.com/deepseek-flash/arm-R/think-on/nogrid")
