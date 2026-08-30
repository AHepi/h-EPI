from __future__ import annotations

import unittest

from creib.evidence import (
    Availability,
    Evidence,
    Outcome,
    Polarity,
    Resolution,
    ReviewStatus,
    resolve_th3b_witness,
)


SCOPE = "pilot:model-1"


def accepted(evidence_id: str, polarity: Polarity, scope: str = SCOPE) -> Evidence:
    return Evidence(Availability.AVAILABLE, ReviewStatus.ACCEPTED, polarity, scope, evidence_id)


class EvidenceResolutionTests(unittest.TestCase):
    def test_resolution_has_no_boolean_coercion(self) -> None:
        with self.assertRaises(TypeError):
            bool(Resolution(Outcome.BLOCKED, "unknown"))

    def test_missing_ke_blocks_countermodel(self) -> None:
        result = resolve_th3b_witness(
            [accepted("ccp", Polarity.POSITIVE)],
            [accepted("retained", Polarity.POSITIVE)],
            [],
            SCOPE,
        )
        self.assertEqual(result.outcome, Outcome.BLOCKED)

    def test_explicit_negative_ke_supports_countermodel(self) -> None:
        result = resolve_th3b_witness(
            [accepted("ccp", Polarity.POSITIVE)],
            [accepted("retained", Polarity.POSITIVE)],
            [accepted("ke-negative", Polarity.NEGATIVE)],
            SCOPE,
        )
        self.assertEqual(result.outcome, Outcome.SUPPORTED)

    def test_positive_ke_refutes_countermodel(self) -> None:
        result = resolve_th3b_witness(
            [accepted("ccp", Polarity.POSITIVE)],
            [accepted("retained", Polarity.POSITIVE)],
            [accepted("ke-positive", Polarity.POSITIVE)],
            SCOPE,
        )
        self.assertEqual(result.outcome, Outcome.REFUTED)

    def test_contradictory_ke_is_error(self) -> None:
        result = resolve_th3b_witness(
            [accepted("ccp", Polarity.POSITIVE)],
            [accepted("retained", Polarity.POSITIVE)],
            [
                accepted("ke-positive", Polarity.POSITIVE),
                accepted("ke-negative", Polarity.NEGATIVE),
            ],
            SCOPE,
        )
        self.assertEqual(result.outcome, Outcome.ERROR)

    def test_scope_mismatch_is_blocked(self) -> None:
        result = resolve_th3b_witness(
            [accepted("ccp", Polarity.POSITIVE)],
            [accepted("retained", Polarity.POSITIVE)],
            [accepted("ke-negative", Polarity.NEGATIVE, "different:model")],
            SCOPE,
        )
        self.assertEqual(result.outcome, Outcome.BLOCKED)

    def test_unknown_unreviewed_and_contested_atoms_block_witness(self) -> None:
        states = {
            "unknown": (ReviewStatus.ACCEPTED, Polarity.UNKNOWN),
            "unreviewed": (ReviewStatus.UNREVIEWED, None),
            "contested": (ReviewStatus.CONTESTED, None),
        }
        atoms = {
            "CCPResult": 0,
            "Retained": 1,
            "K_E": 2,
        }
        for atom, index in atoms.items():
            for state, (review_status, polarity_override) in states.items():
                inputs = [
                    [accepted("ccp", Polarity.POSITIVE)],
                    [accepted("retained", Polarity.POSITIVE)],
                    [accepted("ke-negative", Polarity.NEGATIVE)],
                ]
                baseline_polarity = (
                    Polarity.NEGATIVE if atom == "K_E" else Polarity.POSITIVE
                )
                inputs[index] = [
                    Evidence(
                        Availability.AVAILABLE,
                        review_status,
                        polarity_override or baseline_polarity,
                        SCOPE,
                        f"{atom}-{state}",
                    )
                ]
                with self.subTest(atom=atom, state=state):
                    result = resolve_th3b_witness(*inputs, SCOPE)
                    self.assertEqual(result.outcome, Outcome.BLOCKED)
                    self.assertIn(atom, result.reason)


if __name__ == "__main__":
    unittest.main()
