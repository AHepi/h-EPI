"""The endpoint a mini run calls is the conformance harness's own, read by its reader and used
through its executor, so the key is handled in exactly one place.

A manifest may declare an endpoint in the pilot's shape; absent, the shipped default applies
and the header carries no key, so every manifest written before endpoints existed keeps its
identity. A live run records the endpoint actually sent to, run-time overrides included, in its
first event. An endpoint whose auth is bearer refuses to start without the key in the
environment; one whose auth is none needs no key at all.
"""

from __future__ import annotations

import copy
import json
import os
from unittest import mock

from creib.forge.conformance.executor import API_KEY_ENV, ChatRequest
from creib.forge.conformance.spec import Endpoint
from creib.forge.mini.executor import DEFAULT_ENDPOINT, LiveResponder, Request, endpoint_with_overrides
from creib.forge.mini.log import RUN_STARTED, replay
from creib.forge.mini.runner import run_mini

from .helpers import MiniTestCase, base_manifest, submission

LOCAL = {
    "kind": "ollama-chat",
    "base_url": "http://localhost:11434",
    "timeout_seconds": 60,
    "options": {"temperature": 0, "seed": 3},
    "think": "low",
    "auth": "none",
}


class _Capture:
    """An executor double that records the request and answers with a well-formed artifact."""

    def __init__(self) -> None:
        self.requests: list[ChatRequest] = []

    def complete(self, request: ChatRequest):
        from creib.forge.conformance import response_from_content

        self.requests.append(request)
        return response_from_content(submission("a body", "a commitment"))


class EndpointInTheManifestTests(MiniTestCase):
    def test_absent_is_the_default_and_writes_no_header_key(self) -> None:
        plan = self.compile(base_manifest())
        self.assertIs(plan.endpoint, DEFAULT_ENDPOINT)
        self.assertFalse(plan.endpoint_declared)
        self.assertNotIn("endpoint", plan.header)

    def test_a_declared_endpoint_is_read_by_the_conformance_reader_and_moves_the_identity(self) -> None:
        manifest = base_manifest()
        manifest["endpoint"] = copy.deepcopy(LOCAL)
        plan = self.compile(manifest)
        self.assertIsInstance(plan.endpoint, Endpoint)
        self.assertEqual((plan.endpoint.base_url, plan.endpoint.auth, plan.endpoint.think, plan.endpoint.seed), ("http://localhost:11434", "none", "low", 3))
        self.assertEqual(plan.header["endpoint"], plan.endpoint.to_dict())
        self.assertNotEqual(plan.run_id, self.compile(base_manifest()).run_id)

    def test_a_malformed_endpoint_is_refused_at_compile(self) -> None:
        manifest = base_manifest()
        manifest["endpoint"] = {**copy.deepcopy(LOCAL), "auth": "password"}
        self.assertRefuses("MINI_MANIFEST_INVALID", self.compile, manifest)
        manifest["endpoint"] = {**copy.deepcopy(LOCAL), "think": "maximum"}
        self.assertRefuses("MINI_MANIFEST_INVALID", self.compile, manifest)


class OverridesTests(MiniTestCase):
    def test_think_and_timeout_override_the_endpoint_for_one_run(self) -> None:
        changed = endpoint_with_overrides(DEFAULT_ENDPOINT, think="high", timeout_seconds=30)
        self.assertEqual((changed.think, changed.timeout_seconds), ("high", 30))
        self.assertEqual((DEFAULT_ENDPOINT.think, DEFAULT_ENDPOINT.timeout_seconds), (None, 180))
        self.assertIs(endpoint_with_overrides(DEFAULT_ENDPOINT), DEFAULT_ENDPOINT)
        self.assertEqual(endpoint_with_overrides(DEFAULT_ENDPOINT, think="false").think, False)
        self.assertIsNone(endpoint_with_overrides(DEFAULT_ENDPOINT, think="none").think)

    def test_a_bad_override_is_refused(self) -> None:
        self.assertRefuses("MINI_ENDPOINT_INVALID", endpoint_with_overrides, DEFAULT_ENDPOINT, think="deep")
        self.assertRefuses("MINI_ENDPOINT_INVALID", endpoint_with_overrides, DEFAULT_ENDPOINT, timeout_seconds=0)


class TheKeyIsHandledOnceTests(MiniTestCase):
    def test_a_bearer_endpoint_without_the_key_is_refused_before_any_record(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(API_KEY_ENV, None)
            self.assertRefuses("MINI_LIVE_KEY_MISSING", LiveResponder, "a-model", endpoint=DEFAULT_ENDPOINT)

    def test_an_auth_none_endpoint_needs_no_key(self) -> None:
        manifest = base_manifest()
        manifest["endpoint"] = copy.deepcopy(LOCAL)
        plan = self.compile(manifest)
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(API_KEY_ENV, None)
            responder = LiveResponder("a-model", endpoint=plan.endpoint)
        self.assertEqual(responder._executor.auth, "none")
        self.assertEqual(responder._executor.base_url, "http://localhost:11434")
        self.assertEqual(responder._executor.timeout_seconds, 60)

    def test_the_endpoint_settings_reach_every_request(self) -> None:
        manifest = base_manifest()
        manifest["endpoint"] = copy.deepcopy(LOCAL)
        plan = self.compile(manifest)
        capture = _Capture()
        LiveResponder("a-model", capture, endpoint=plan.endpoint).reply(Request("c1", "k.conjecture", 0, "brief"))
        request = capture.requests[0]
        self.assertEqual((request.options, request.think, request.model), ({"temperature": 0, "seed": 3}, "low", "a-model"))


class TheRecordSaysWhatWasSentToTests(MiniTestCase):
    def test_a_live_run_records_the_endpoint_used_and_a_scripted_run_records_none(self) -> None:
        manifest = base_manifest()
        manifest["endpoint"] = copy.deepcopy(LOCAL)
        plan = self.compile(manifest)
        sent = endpoint_with_overrides(plan.endpoint, timeout_seconds=45)
        outcome = run_mini(plan, self.tmp / "live", LiveResponder("a-model", _Capture(), endpoint=sent), "model:a-model", endpoint=sent)
        started = self.events_of(outcome, RUN_STARTED)[0]["payload"]
        self.assertEqual(started["endpoint"]["timeout_seconds"], 45)
        self.assertEqual(started["endpoint"]["auth"], "none")
        self.assertEqual(plan.header["endpoint"]["timeout_seconds"], 60, "the plan is unchanged by a run-time override")
        _, scripted = self.run_manifest(base_manifest())
        self.assertNotIn("endpoint", self.events_of(scripted, RUN_STARTED)[0]["payload"])
        state = replay(outcome.root / "log.jsonl", plan.genesis)
        self.assertTrue(state.ended)
