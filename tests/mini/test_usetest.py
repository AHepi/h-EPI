"""MINI-USE-TEST-1: the subject, the frozen grammar, the validator, the packet and the arms.

The protocol is only worth running if its parts do what it says: a mutation is one edit with an
observable consequence, an interaction defect leaves one-dimensional behaviour alone, a rule
reader is shown no code, and a cell counts only when a validator proves the text that ran is
the cell it claims. Each of those is asserted here, offline and without a model.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from creib.forge.mini import usetest
from creib.forge.mini.common import MiniError
from creib.forge.mini.manifest import compile_manifest

from .helpers import MiniTestCase, submission

CONTROL = "```\nHere is the result:\n{\"a\": 1}\n```\n{\"b\": 2}"


class SubjectTests(MiniTestCase):
    def _subject(self, source: str, name: str):
        path = self.tmp / name
        path.write_text(source, encoding="utf-8")
        return usetest.load_subject(path)

    def test_the_subject_is_the_harness_code_and_answers_as_it_does(self) -> None:
        source = usetest.subject_source()
        subject = self._subject(source, "clean.py")
        self.assertIn("def recover_json_object", source)
        self.assertEqual(usetest.run_kernel(subject, "recovery", '{"a": 1}'), '{"a":1}')
        self.assertEqual(usetest.run_kernel(subject, "recovery", CONTROL), '{"b":2}', "H43 is in the copy, as it is in the tree")
        self.assertEqual(usetest.run_kernel(subject, "recovery", '```\n{"a": 1}\n```\n{"b": 2}'), '{"a":1}')
        self.assertEqual(usetest.run_kernel(subject, "refusal-phrase", "I cannot do that."), "I cannot")

    def test_every_mutation_is_one_edit_with_an_observable_consequence(self) -> None:
        source = usetest.subject_source()
        clean = self._subject(source, "clean.py")
        for mutation in usetest.CORPUS:
            with self.subTest(mutation=mutation.mutation_id):
                self.assertEqual(source.count(mutation.find), 1, "a mutation is a single determinate edit")
                mutated = self._subject(usetest.apply_mutation(source, mutation), f"{mutation.mutation_id}.py")
                before = usetest.run_kernel(clean, mutation.kernel, mutation.reproducer)
                after = usetest.run_kernel(mutated, mutation.kernel, mutation.reproducer)
                self.assertNotEqual(before, after, "its reproducer must tell the two subjects apart")

    def test_an_interaction_defect_leaves_one_dimensional_behaviour_alone(self) -> None:
        """S2: the failure is in the conjunction, so neither dimension alone shows it."""

        source = usetest.subject_source()
        clean = self._subject(source, "clean.py")
        controls = {
            "s2-fence-single-only": ('```json\n{"a": 1}\n```\n{"z": 9}', '{"a": 1}\n{"z": 9}'),
            "s2-duplicates-outside-fence-only": ('{"a": 1, "a": 2}', '```json\n{"a": 1, "a": 2}\n```'),
            "s2-span-normalised-one-side": (
                json.dumps({"span": "five days", "document": "away for five  days."}),
                json.dumps({"span": "five days", "document": "away for five days."}),
            ),
        }
        for mutation_id, inputs in controls.items():
            mutation = usetest.CORPUS_BY_ID[mutation_id]
            mutated = self._subject(usetest.apply_mutation(source, mutation), f"{mutation_id}.py")
            for text in inputs:
                with self.subTest(mutation=mutation_id, control=text[:30]):
                    self.assertEqual(
                        usetest.run_kernel(clean, mutation.kernel, text),
                        usetest.run_kernel(mutated, mutation.kernel, text),
                        "one dimension at a time must behave as the clean subject does",
                    )

    def test_a_rule_reader_is_shown_the_rules_and_never_the_code(self) -> None:
        source = usetest.subject_source()
        rules = usetest.rules_text(source)
        self.assertIn("last one inside a code fence", rules, "the rule the control is read against")
        self.assertIn("REFUSAL_PHRASES", rules)
        for fragment in ("_FENCE.finditer", "return value", "for pool in", "decoder.raw_decode"):
            self.assertNotIn(fragment, rules, fragment)

    def test_a_mutation_changes_no_documented_rule(self) -> None:
        """The defect must not be visible in what a rule reader is given."""

        clean_rules = usetest.rules_text(usetest.subject_source())
        for mutation in usetest.CORPUS:
            with self.subTest(mutation=mutation.mutation_id):
                mutated = usetest.apply_mutation(usetest.subject_source(), mutation)
                self.assertEqual(usetest.rules_text(mutated), clean_rules)


class GrammarTests(MiniTestCase):
    def test_the_grid_is_twenty_cells_each_of_which_parses(self) -> None:
        self.assertEqual(len(usetest.RECOVERY_GRID), 20)
        self.assertEqual(len(set(usetest.RECOVERY_GRID)), 20)
        for cell in usetest.RECOVERY_GRID:
            with self.subTest(cell=cell):
                self.assertEqual(usetest.parse_cell(cell).notation, cell)

    def test_a_validator_proves_the_text_is_the_cell_or_says_why_not(self) -> None:
        self.assertIsNone(usetest.validate_cell("fence[ S A ] B", CONTROL))
        self.assertIsNone(usetest.validate_cell("fence[ A ] A", '```\n{"a": 1}\n```\n{"a": 1}'))
        self.assertIsNone(usetest.validate_cell("fence[ A B ] fence[ C ]", '```\n{"a": 1}\n{"b": 2}\n```\n```\n{"c": 3}\n```'))
        for cell, text, expected in (
            ("fence[ S A ] B", '```\n{"a": 1}\n```\n{"b": 2}', "hold 2 part"),
            ("fence[ S A ] B", 'Here is the result:\n{"a": 1}\n{"b": 2}', "fenced region"),
            ("fence[ A ] B", '```\n{"a": 1}\n```\n{"a": 1}', "same as another object"),
            ("fence[ A ] A", '```\n{"a": 1}\n```\n{"b": 2}', "written twice with different content"),
            ("fence[ A ]", '```\n{\n  "a": 1\n}\n```', "holds 3"),
            ("fence[ A ] S", '```\n{"a": 1}\n```', "after the fence"),
        ):
            with self.subTest(cell=cell):
                reason = usetest.validate_cell(cell, text)
                self.assertIsNotNone(reason, "this text is not that cell")
                self.assertIn(expected, reason)

    def test_a_family_whose_cells_cannot_be_validated_is_named_non_enumerable(self) -> None:
        self.assertEqual(set(usetest.NON_ENUMERABLE), {"span-occurs", "grounding"})
        for kernel_id, reason in usetest.NON_ENUMERABLE.items():
            self.assertTrue(reason.strip(), kernel_id)


class PacketTests(MiniTestCase):
    def test_a_packet_is_eight_fields_and_nothing_that_names_its_arm(self) -> None:
        packet = usetest.packet_from(
            {"claim": "the fenced object is passed over", "observed": '{"z":9}', "expected": '{"b":2}', "reproducer": "x"},
            "i1",
            usetest.ARM_C,
            "a-model",
        )
        self.assertIsNotNone(packet)
        self.assertEqual(list(packet.neutral()), list(usetest.PACKET_FIELDS))
        self.assertEqual(packet.leaks(), ())
        leaky = usetest.packet_from({"claim": "the mini grid cell moved", "observed": "x"}, "i1", usetest.ARM_C, "m")
        self.assertTrue(leaky.leaks(), "a packet that names the method is reported, not quietly cleaned")

    def test_a_fenced_packet_is_a_packet(self) -> None:
        """Version 1 threw one away, so an arm that had found something was recorded as silent."""

        fenced = '```json\n{"claim": "the fenced object is passed over", "observed": "{\\"z\\":9}", "reproducer": "r"}\n```'
        packet = usetest.packet_from(fenced, "i1", usetest.ARM_C, "m")
        self.assertIsNotNone(packet)
        self.assertEqual(packet.neutral()["claim"], "the fenced object is passed over")

    def test_a_reply_that_is_not_a_packet_is_no_packet(self) -> None:
        self.assertIsNone(usetest.packet_from("not json at all", "i1", usetest.ARM_A, "m"))
        self.assertIsNone(usetest.packet_from({"claim": "", "observed": ""}, "i1", usetest.ARM_A, "m"))

    def test_the_ceiling_is_counted_and_not_trusted_to_a_prompt(self) -> None:
        ceiling = usetest.Ceiling(invocations=2, completion_tokens=100)
        ceiling.charge(10, 40)
        self.assertFalse(ceiling.spent)
        ceiling.charge(10, 40)
        self.assertTrue(ceiling.spent, "the invocations are spent")
        self.assertEqual(ceiling.as_dict()["completion_tokens"], 80)


class ArmTests(MiniTestCase):
    def test_each_mini_arm_compiles_and_costs_what_the_protocol_says(self) -> None:
        for arm, calls in ((usetest.ARM_C, 1), (usetest.ARM_D, 2), (usetest.ARM_E, 2)):
            with self.subTest(arm=arm):
                manifest = usetest.arm_manifest(arm, "i1", cycles=7, max_calls=7)
                path = self.tmp / f"{arm}.json"
                path.write_text(json.dumps(manifest), encoding="utf-8")
                plan = compile_manifest(path)
                model_stages = [stage for stage in plan.stages if not stage.end and stage.seat != "machine"]
                self.assertEqual(len(model_stages), calls, "the core spends one call a cycle and the full loop two")
        self.assertNotIn("attention", usetest.arm_manifest(usetest.ARM_D, "i1", 7, 7))
        self.assertEqual(usetest.arm_manifest(usetest.ARM_E, "i1", 7, 7)["attention"]["policy"], "mini.attention.most-unanswered-criticisms")

    def test_the_execution_seat_refuses_when_no_subject_is_bound(self) -> None:
        os.environ.pop(usetest.SUBJECT_ENV, None)
        with self.assertRaises(MiniError):
            usetest.bound_subject()

    def test_a_text_that_is_not_its_cell_is_thrown_away_and_covers_nothing(self) -> None:
        """The anti-cheating rule, end to end: the seat validates before it executes."""

        from creib.forge.mini.log import BlobStore, replay

        subject = self.tmp / "subject.py"
        subject.write_text(usetest.subject_source(), encoding="utf-8")
        os.environ[usetest.SUBJECT_ENV] = str(subject)
        try:
            manifest = usetest.arm_manifest(usetest.ARM_C, "i1", cycles=2, max_calls=2)
            self.assertEqual(usetest.METHOD_VERSION, 3, "a changed method starts a new block")
            # The machine hands out the grid's first cell, so a conforming proposal builds that
            # one; a proposal that builds another cell is not conforming however good it is.
            conforming = submission(
                "built as given",
                json.dumps({"kernel": "recovery", "expect": "unchanged"}),
                input='```\n{"a": 1}\n```',
                rewritten='```\n{"a": 1}\n```\n{"b": 2}',
                rewrite="added a bare object after the fence",
                cell="fence[ A ]",
            )
            wrong = submission(
                "claims the cell and builds another",
                json.dumps({"kernel": "recovery", "expect": "moves"}),
                input='{"a": 1}\n{"b": 2}',
                rewritten='{"a": 1}',
                rewrite="removed the second object",
                cell="fence[ S A ] B",
            )
            plan, outcome = self.run_manifest(manifest, {"propose": [conforming, wrong]})
            state = replay(outcome.root / "log.jsonl", plan.genesis)
            blobs = BlobStore(outcome.root / "blobs")
            executed = [
                entry
                for key in state.artifact_order
                if str(state.artifacts[key]["kind_id"]) == usetest.EXECUTION_KIND
                for entry in json.loads(blobs.get(str(state.artifacts[key]["commitments_ref"])).decode("utf-8"))["executions"]
            ]
            self.assertEqual([item["executed"] for item in executed], ["unchanged", "INVALID_INSTANTIATION"])
            self.assertEqual(executed[0]["cell_assigned"], "fence[ A ]", "the cell under test is the one the machine handed out")
            self.assertEqual((executed[0]["before"], executed[0]["after"]), ('{"a":1}', '{"a":1}'), "the fenced object wins either way")
            self.assertTrue(executed[0]["as_expected"])
            self.assertEqual(executed[0]["rewritten_cell"], "fence[ A ] B", "the rewrite lands in another cell of the grammar")
            self.assertIn("not the cell it names", executed[1]["detail"])
            self.assertNotIn("before", executed[1], "an invalid instantiation is not a result")
        finally:
            os.environ.pop(usetest.SUBJECT_ENV, None)
