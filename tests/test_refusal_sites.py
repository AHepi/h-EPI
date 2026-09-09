"""Refusal sites the deletion sweep listed as surviving, each reached by a test.

``tools/refusal_sweep.py`` deletes each ``raise`` under ``src/creib`` in turn and runs the suite;
a site the suite still passes with is a refusal nothing exercises. The sweep of 9 September 2026
listed these among them, and each test below supplies the input that trips the site, so that
its deletion is noticed. Sites the sweep lists as masked by an earlier guard (the appraisal
loader's checks of ``schema_version``, ``kind`` and ``readiness``, which the JSON schema refuses
first) or as invariants no input reaches (the appraisal's fixed-point checks) are recorded in
the sweep report, not tested here: a test cannot reach them without bypassing the guard in front.
"""

from __future__ import annotations

import unittest

from creib.canonical import canonical_bytes
from creib.errors import RecordError
from creib.forge.conformance import claims as claims_module
from creib.forge.conformance.common import any_string, array_value, identifier, object_value, optional_text, text


class CanonicalProfileRefusals(unittest.TestCase):
    def test_a_non_string_object_key_is_refused(self) -> None:
        with self.assertRaisesRegex(RecordError, "non-string object key at \\$"):
            canonical_bytes({1: "one"})
        with self.assertRaisesRegex(RecordError, r"non-string object key at \$\.outer"):
            canonical_bytes({"outer": {2: "two"}})

    def test_a_value_outside_the_profile_is_refused_where_it_stands(self) -> None:
        with self.assertRaisesRegex(RecordError, r"value outside canonical profile at \$\.total: float"):
            canonical_bytes({"total": 1.5})
        with self.assertRaisesRegex(RecordError, r"value outside canonical profile at \$\[1\]: tuple"):
            canonical_bytes([1, (2, 3)])
        with self.assertRaisesRegex(RecordError, r"value outside canonical profile at \$: bytes"):
            canonical_bytes(b"raw")


class ValueHelperRefusals(unittest.TestCase):
    """The loaders' value helpers, reached directly and through a claim condition, which is not schema-checked when compiled."""

    def test_object_and_array_shapes_are_refused_by_name(self) -> None:
        with self.assertRaisesRegex(RecordError, "here must be an object"):
            object_value(["not", "an", "object"], "here")
        with self.assertRaisesRegex(RecordError, "here must be an array"):
            array_value({"not": "an array"}, "here")
        with self.assertRaisesRegex(RecordError, r"condition\.field_value must be an object"):
            claims_module.compile_condition({"field_value": "destination_city"})
        with self.assertRaisesRegex(RecordError, r"condition\.field_value\.values must be an array"):
            claims_module.compile_condition({"field_value": {"field": "destination_city", "values": "Melbourne"}})

    def test_text_must_be_non_empty_and_free_of_surrogates(self) -> None:
        with self.assertRaisesRegex(RecordError, "here must be a non-empty string"):
            text("   ", "here")
        with self.assertRaisesRegex(RecordError, "here must be a non-empty string"):
            text(7, "here")
        with self.assertRaisesRegex(RecordError, "here contains a Unicode surrogate"):
            text("bad \ud800 text", "here")
        self.assertIsNone(optional_text(None, "here"))
        with self.assertRaisesRegex(RecordError, "here contains a Unicode surrogate"):
            optional_text("\udfff", "here")
        with self.assertRaisesRegex(RecordError, r"condition\.trigger must be a non-empty string"):
            claims_module.compile_condition({"trigger": ""})

    def test_any_string_admits_empty_and_refuses_non_strings_and_surrogates(self) -> None:
        self.assertEqual(any_string("", "here"), "")
        with self.assertRaisesRegex(RecordError, "here must be a string"):
            any_string(None, "here")
        with self.assertRaisesRegex(RecordError, "here contains a Unicode surrogate"):
            any_string("x\ud83dx", "here")

    def test_an_identifier_must_be_stable(self) -> None:
        with self.assertRaisesRegex(RecordError, "here must be a stable identifier"):
            identifier("has a space", "here")
        with self.assertRaisesRegex(RecordError, "here must be a stable identifier"):
            identifier("ünstable", "here")
        self.assertEqual(identifier("TRV-001", "here"), "TRV-001")


class ClaimConditionRefusals(unittest.TestCase):
    def test_a_grounding_condition_must_name_a_verdict(self) -> None:
        with self.assertRaisesRegex(RecordError, "must name at least one grounding verdict"):
            claims_module.compile_condition({"criticised_field": {"grounding_verdict": []}})
        self.assertTrue(callable(claims_module.compile_condition({"criticised_field": {"grounding_verdict": ["GROUNDED"]}})))


if __name__ == "__main__":
    unittest.main()
