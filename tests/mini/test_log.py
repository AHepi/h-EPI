"""R13: the append-only log — chained, replayable, and unchanged by a new kind."""

from __future__ import annotations

import copy
import json

from creib.forge.mini.log import (
    ARTIFACT_SUBMITTED,
    EVENT_TYPES,
    BlobStore,
    EventLog,
    MiniState,
    apply_event,
    build_event,
    event_from_dict,
    replay,
)

from .helpers import MiniTestCase, base_manifest, submission

A_THIRD_KIND = {
    "kind_id": "example.note.v1",
    "title": "Note",
    "input_ports": [{"port_id": "problem", "port_type": "problem"}],
    "output_port": {"port_id": "out", "produces_kind": "example.note.v1"},
}


class ReplayTests(MiniTestCase):
    def test_replay_of_the_log_alone_reproduces_the_final_state_digest(self) -> None:
        plan, outcome = self.run_manifest(base_manifest())
        self.assertEqual(replay(outcome.root / "log.jsonl", plan.genesis).digest(), outcome.state_digest)

    def test_replaying_twice_gives_the_same_digest(self) -> None:
        plan, outcome = self.run_manifest(base_manifest())
        first = replay(outcome.root / "log.jsonl", plan.genesis).digest()
        second = replay(outcome.root / "log.jsonl", plan.genesis).digest()
        self.assertEqual(first, second)

    def test_the_same_plan_and_script_write_the_same_record_twice(self) -> None:
        manifest = base_manifest()
        _, first = self.run_manifest(manifest, name="run-a")
        _, second = self.run_manifest(manifest, name="run-b")
        self.assertEqual(first.state_digest, second.state_digest)
        self.assertEqual(
            (first.root / "log.jsonl").read_bytes(),
            (second.root / "log.jsonl").read_bytes(),
        )


class ChainTests(MiniTestCase):
    def _tamper(self, path, line_index: int, change) -> None:
        lines = path.read_text(encoding="utf-8").splitlines()
        entry = json.loads(lines[line_index])
        change(entry)
        lines[line_index] = json.dumps(entry, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_flipping_one_byte_of_an_event_breaks_its_own_identity(self) -> None:
        """One character of one blob reference, still well shaped, still refused."""

        plan, outcome = self.run_manifest(base_manifest())
        path = outcome.root / "log.jsonl"
        raw = bytearray(path.read_bytes())
        marker = raw.index(b'"body_ref":"') + len(b'"body_ref":"')
        raw[marker] = ord("0") if raw[marker] != ord("0") else ord("1")
        path.write_bytes(bytes(raw))
        self.assertRefuses("MINI_LOG_EVENT_ID_MISMATCH", lambda: list(EventLog(path, plan.genesis).read()))

    def test_replacing_an_event_id_breaks_the_link_to_the_next_event(self) -> None:
        plan, outcome = self.run_manifest(base_manifest())
        path = outcome.root / "log.jsonl"
        self.assertRefuses("MINI_LOG_EVENT_ID_MISMATCH", lambda: self._tamper(path, 0, _replace_event_id) or list(EventLog(path, plan.genesis).read()))

    def test_dropping_an_event_breaks_the_chain(self) -> None:
        plan, outcome = self.run_manifest(base_manifest())
        path = outcome.root / "log.jsonl"
        lines = path.read_text(encoding="utf-8").splitlines()
        path.write_text("\n".join(lines[:1] + lines[2:]) + "\n", encoding="utf-8")
        self.assertRefuses("MINI_LOG_SEQUENCE_BROKEN", lambda: list(EventLog(path, plan.genesis).read()))

    def test_a_wrong_genesis_breaks_the_chain_at_the_first_event(self) -> None:
        _, outcome = self.run_manifest(base_manifest())
        self.assertRefuses("MINI_LOG_CHAIN_BROKEN", lambda: list(EventLog(outcome.root / "log.jsonl", "0" * 64).read()))

    def test_a_line_that_is_not_json_is_refused(self) -> None:
        plan, outcome = self.run_manifest(base_manifest())
        path = outcome.root / "log.jsonl"
        path.write_text("not json\n", encoding="utf-8")
        self.assertRefuses("MINI_LOG_UNREADABLE", lambda: list(EventLog(path, plan.genesis).read()))

    def test_a_missing_log_reads_as_nothing(self) -> None:
        self.assertEqual(list(EventLog(self.tmp / "absent.jsonl", "0" * 64).read()), [])


class EventShapeTests(MiniTestCase):
    def test_a_new_artifact_kind_adds_no_event_type(self) -> None:
        manifest = base_manifest()
        manifest["kinds"].append(copy.deepcopy(A_THIRD_KIND))
        manifest["stages"] = [
            {"stage_id": "n1", "kind_id": "example.note.v1", "ports": ["problem"]},
            {"stage_id": "end", "end": True},
        ]
        _, outcome = self.run_manifest(manifest, {"n1": [submission("A note.", "c")]})
        types = {event["type"] for event in self.events(outcome)}
        self.assertTrue(types <= set(EVENT_TYPES))
        submitted = self.events_of(outcome, ARTIFACT_SUBMITTED)[0]
        self.assertEqual(submitted["kind_id"], "example.note.v1")
        self.assertRegex(submitted["body_ref"], r"^[0-9a-f]{64}$")
        self.assertRegex(submitted["commitments_ref"], r"^[0-9a-f]{64}$")

    def test_body_and_commitments_are_blob_references_not_inline_text(self) -> None:
        _, outcome = self.run_manifest(base_manifest())
        raw = (outcome.root / "log.jsonl").read_text(encoding="utf-8")
        self.assertNotIn("The two paragraphs disagree", raw)
        store = BlobStore(outcome.root / "blobs")
        submitted = self.events_of(outcome, ARTIFACT_SUBMITTED)[0]
        self.assertEqual(store.get(submitted["body_ref"]).decode("utf-8"), "The two paragraphs disagree.")

    def test_building_an_event_of_an_unknown_type_is_refused(self) -> None:
        self.assertRefuses("MINI_LOG_EVENT_TYPE_UNKNOWN", build_event, seq=0, prev="0" * 64, type="INVENTED", payload={})

    def test_reading_an_event_of_an_unknown_type_is_refused(self) -> None:
        event = build_event(seq=0, prev="0" * 64, type=ARTIFACT_SUBMITTED, payload={})
        record = event.to_dict()
        record["type"] = "INVENTED"
        self.assertRefuses("MINI_LOG_EVENT_TYPE_UNKNOWN", event_from_dict, record, "line 1")

    def test_applying_an_event_of_an_unknown_type_is_refused(self) -> None:
        event = build_event(seq=0, prev="0" * 64, type=ARTIFACT_SUBMITTED, payload={})
        from dataclasses import replace as dataclass_replace

        self.assertRefuses("MINI_LOG_EVENT_TYPE_UNKNOWN", apply_event, MiniState(), dataclass_replace(event, type="INVENTED"))

    def test_an_event_whose_shape_is_wrong_is_refused_on_read(self) -> None:
        event = build_event(seq=0, prev="0" * 64, type=ARTIFACT_SUBMITTED, payload={})
        record = event.to_dict()
        del record["payload"]
        self.assertRefuses("MINI_LOG_UNREADABLE", event_from_dict, record, "line 1")


class BlobTests(MiniTestCase):
    def test_the_same_bytes_store_once(self) -> None:
        store = BlobStore(self.tmp / "blobs")
        self.assertEqual(store.put(b"same"), store.put(b"same"))
        self.assertEqual(store.get(store.put(b"same")), b"same")

    def test_a_blob_that_is_not_there_is_refused(self) -> None:
        self.assertRefuses("MINI_BLOB_MISSING", BlobStore(self.tmp / "blobs").get, "0" * 64)

    def test_a_blob_that_does_not_carry_its_own_digest_is_refused(self) -> None:
        store = BlobStore(self.tmp / "blobs")
        reference = store.put(b"original")
        (self.tmp / "blobs" / reference).write_bytes(b"tampered")
        self.assertRefuses("MINI_BLOB_CORRUPT", store.get, reference)

    def test_storing_over_a_corrupted_blob_is_refused(self) -> None:
        store = BlobStore(self.tmp / "blobs")
        reference = store.put(b"original")
        (self.tmp / "blobs" / reference).write_bytes(b"tampered")
        self.assertRefuses("MINI_BLOB_CORRUPT", store.put, b"original")

    def test_a_run_never_writes_over_an_existing_record(self) -> None:
        manifest = base_manifest()
        plan, _ = self.run_manifest(manifest, name="run")
        self.assertRefuses("MINI_RUN_ROOT_OCCUPIED", self.run_plan, plan, dict(), "run")


def _replace_event_id(entry: dict) -> None:
    entry["event_id"] = "0" * 64
