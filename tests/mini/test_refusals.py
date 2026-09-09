"""One negative test per refusal site the other files do not already reach.

Every ``raise`` in the package is a refusal site; h-EPI's rule is that each gets
a test that reaches it, so a deleted guard is a failing suite rather than a
silent widening.
"""

from __future__ import annotations

import json
from pathlib import Path

from creib.errors import RecordError
from creib.forge.mini.common import (
    MiniError,
    array_value,
    identifier,
    object_value,
    text,
    validate_instance,
)
from creib.forge.mini.executor import Request, ScriptedResponder
from creib.forge.mini.log import BlobStore, read_run_header
from creib.forge.mini.manifest import compile_manifest
from creib.forge.mini.runner import block_text, run_mini

from .helpers import MiniTestCase, base_manifest


class VocabularyTests(MiniTestCase):
    def test_a_refusal_code_nobody_declared_cannot_be_raised(self) -> None:
        with self.assertRaises(RecordError):
            raise MiniError("MINI_INVENTED_CODE", "this code is not in the vocabulary")

    def test_the_small_readers_refuse_what_they_are_for(self) -> None:
        self.assertRefuses("MINI_MANIFEST_INVALID", identifier, "9 not an identifier", "where")
        self.assertRefuses("MINI_MANIFEST_INVALID", text, "", "where")
        self.assertRefuses("MINI_MANIFEST_INVALID", text, 3, "where")
        self.assertRefuses("MINI_MANIFEST_INVALID", object_value, [], "where")
        self.assertRefuses("MINI_MANIFEST_INVALID", array_value, {}, "where")

    def test_an_instance_the_schema_rejects_is_refused_with_the_code_asked_for(self) -> None:
        self.assertRefuses(
            "MINI_MANIFEST_INVALID", validate_instance, {"nothing": "useful"}, "mini-manifest.schema.json", "MINI_MANIFEST_INVALID"
        )


class ManifestReadingTests(MiniTestCase):
    def test_a_manifest_that_is_not_there_is_refused(self) -> None:
        self.assertRefuses("MINI_MANIFEST_INVALID", compile_manifest, self.tmp / "absent.json")

    def test_a_manifest_that_is_not_json_is_refused(self) -> None:
        path = self.tmp / "manifest.json"
        path.write_text("{not json", encoding="utf-8")
        self.assertRefuses("MINI_MANIFEST_INVALID", compile_manifest, path)

    def test_a_manifest_whose_shape_is_wrong_is_refused(self) -> None:
        path = self.tmp / "manifest.json"
        path.write_text(json.dumps({"schema_version": "creib.mini.manifest.v1"}), encoding="utf-8")
        self.assertRefuses("MINI_MANIFEST_INVALID", compile_manifest, path)

    def test_compile_takes_a_path_and_says_so(self) -> None:
        with self.assertRaises(TypeError):
            compile_manifest("forge/mini/manifests/default/manifest.json")

    def test_a_kind_file_that_is_not_there_is_refused(self) -> None:
        manifest = base_manifest()
        manifest["kinds"].append("kinds/absent.json")
        self.assertRefuses("MINI_KIND_FILE_UNREADABLE", self.compile, manifest)

    def test_a_kind_file_whose_shape_is_wrong_is_refused(self) -> None:
        self.write_json("kinds/bad.json", {"schema_version": "creib.mini.kind.v1"})
        manifest = base_manifest()
        manifest["kinds"].append("kinds/bad.json")
        self.assertRefuses("MINI_KIND_FILE_UNREADABLE", self.compile, manifest)


class ResponderTests(MiniTestCase):
    def test_a_script_with_nothing_left_to_say_is_refused(self) -> None:
        responder = ScriptedResponder({"c1": ["one"]})
        responder.reply(Request(stage_id="c1", kind_id="k", attempt=0, brief="b"))
        self.assertRefuses(
            "MINI_SCRIPT_EXHAUSTED", responder.reply, Request(stage_id="c1", kind_id="k", attempt=1, brief="b")
        )

    def test_a_script_that_never_mentioned_the_stage_is_refused(self) -> None:
        responder = ScriptedResponder({})
        self.assertRefuses(
            "MINI_SCRIPT_EXHAUSTED", responder.reply, Request(stage_id="c1", kind_id="k", attempt=0, brief="b")
        )

    def test_the_responder_reports_what_it_used(self) -> None:
        responder = ScriptedResponder({"c1": ["one", "two"]})
        responder.reply(Request(stage_id="c1", kind_id="k", attempt=0, brief="a brief"))
        self.assertEqual(responder.used, {"c1": 1})


class StoreTests(MiniTestCase):
    def test_a_block_whose_span_does_not_match_its_digest_is_refused(self) -> None:
        store = BlobStore(self.tmp / "blobs")
        reference = store.put(b"a source of some words")
        block = {
            "block_id": "0" * 64,
            "source_ref": reference,
            "span_start": 0,
            "span_end": 8,
            "text_sha256": "1" * 64,
        }
        self.assertRefuses("MINI_BLOB_CORRUPT", block_text, store, block)

    def test_the_stores_take_paths_and_say_so(self) -> None:
        with self.assertRaises(TypeError):
            BlobStore("not/a/path")

    def test_a_run_root_must_be_a_path(self) -> None:
        plan = self.compile(base_manifest())
        with self.assertRaises(TypeError):
            run_mini(plan, "not/a/path", ScriptedResponder({}))

    def test_an_event_log_takes_a_path_and_says_so(self) -> None:
        from creib.forge.mini.log import EventLog

        with self.assertRaises(TypeError):
            EventLog("not/a/path", "0" * 64)


class RunHeaderTests(MiniTestCase):
    def test_a_run_header_that_is_not_there_is_refused(self) -> None:
        self.assertRefuses("MINI_LOG_UNREADABLE", read_run_header, self.tmp)

    def test_a_run_header_is_read_back_from_a_run(self) -> None:
        _, outcome = self.run_manifest(base_manifest())
        header = read_run_header(outcome.root)
        self.assertEqual(header["manifest_id"], "test.base")


class ShippedManifestTests(MiniTestCase):
    """The manifests in the tree compile, so a broken example fails the suite."""

    def test_every_shipped_manifest_compiles(self) -> None:
        root = Path(__file__).resolve().parents[2] / "forge" / "mini" / "manifests"
        manifests = sorted(root.glob("*/manifest.json"))
        self.assertTrue(manifests)
        for path in manifests:
            with self.subTest(manifest=path.name):
                plan = compile_manifest(path)
                self.assertTrue(plan.stages[-1].end)
