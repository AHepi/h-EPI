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


class ClaimConditionRefusals(unittest.TestCase):
    def test_a_grounding_condition_must_name_a_verdict(self) -> None:
        with self.assertRaisesRegex(RecordError, "must name at least one grounding verdict"):
            claims_module.compile_condition({"criticised_field": {"grounding_verdict": []}})
        self.assertTrue(callable(claims_module.compile_condition({"criticised_field": {"grounding_verdict": ["GROUNDED"]}})))


if __name__ == "__main__":
    unittest.main()
