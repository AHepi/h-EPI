"""The CYCLE family: configuration, planning, materialisation, the prompt, the runner chain,
routing, the claim predicates, and the cycles table.

The property these tests hold the family to is that a cycle never learns the answer key:
what the model is shown is its own previous answer and, at most, the checks the form schema
and the document alone can fail. Everything else is bookkeeping: the chain of records, the
replay of ids and digests, and counts that describe two records without scoring either.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from creib.errors import PolicyViolation, RecordError
from creib.forge.conformance import (
    ChatRequest,
    Criticism,
    FakeExecutor,
    Family,
    ReplayExecutor,
    load_corpus,
    load_observation_directory,
    load_pilot_config,
    load_run,
    materialize_cycle,
    plan,
    render_cycles_markdown,
    response_from_content,
    route,
    run_pilot,
    score,
    summarise_cycles,
)
from creib.forge.conformance import claims as claims_module
from creib.forge.conformance import families as families_module
from creib.forge.conformance import oracle as oracle_module
from creib.forge.conformance.prompt import CYCLE_REVISION_SENTENCE, build_chat_request, build_user_prompt
from creib.forge.conformance.records import enumerate_record_directory, load_observation
from creib.forge.conformance.spec import Cycles, cycles_from_dict
from creib.strict_json import loads_strict

ROOT = Path(__file__).resolve().parents[1]
PILOT_DIR = ROOT / "forge" / "conformance" / "pilots" / "incident-form"
CREATED_ON = "2026-09-06T00:00:00Z"
LONG_TAIL = " " + "x" * 200  # pushes summary past its maxLength of 200 without touching the rest


def _pilot_with_cycles(directory: Path, count: int = 2, criticism=("none", "external")) -> Path:
    target = directory / "pilot"
    shutil.copytree(PILOT_DIR, target)
    pilot = target / "pilot.json"
    raw = loads_strict(pilot.read_text(encoding="utf-8"))
    raw["cycles"] = {"count": count, "criticism": list(criticism)}
    pilot.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    return pilot


def _reference(corpus, case_id: str) -> dict:
    """The case's reference output, which the incident-form key accepts on every scored field."""

    case = corpus.case(case_id)
    return dict(case.reference_output or ())


class _Loaded:
    def __init__(self, directory: Path, **kwargs) -> None:
        self.pilot = _pilot_with_cycles(directory, **kwargs)
        self.config = load_pilot_config(self.pilot)
        self.spec = self.config.spec
        self.corpus = load_corpus(self.config.corpus_path, self.spec)
        self.plan = plan(self.spec, self.corpus)


def _fake_for(loaded: _Loaded) -> FakeExecutor:
    """Baseline replies: ORD-001 with an over-long summary, ORD-002 unparseable, others the reference.

    A cycle that lists the length check returns the reference summary; a cycle that lists no
    check, or a self-revision cycle, returns exactly the previous answer.
    """

    good = {case.case_id: _reference(loaded.corpus, case.case_id) for case in loaded.corpus.cases if case.reference_output is not None}
    long_summary = dict(good["ORD-001"]); long_summary["summary"] = good["ORD-001"]["summary"] + LONG_TAIL

    def respond(request: ChatRequest):
        case_id = next((c.case_id for c in loaded.corpus.cases if c.renderings[c.rendering] in request.user), None)
        if "## Previous answer" in request.user:
            if "LENGTH_VIOLATION" in request.user:
                return response_from_content(json.dumps(good[case_id]))
            previous = request.user.split("```json\n", 1)[1].split("\n```", 1)[0]
            return response_from_content(previous)
        if case_id == "ORD-002":
            return response_from_content("not a form at all")
        if case_id == "ORD-001":
            return response_from_content(json.dumps(long_summary))
        return response_from_content(json.dumps(good.get(case_id, good["ORD-001"])))

    return FakeExecutor(respond)


class CyclesConfigurationTests(unittest.TestCase):
    def test_absent_means_off_and_leaves_every_variant_id_unchanged(self) -> None:
        config = load_pilot_config(PILOT_DIR / "pilot.json")
        self.assertEqual(config.spec.cycles, Cycles(count=0, criticism=()))
        self.assertFalse(config.spec.cycles.active)
        with tempfile.TemporaryDirectory() as directory:
            explicit = _Loaded(Path(directory), count=0, criticism=())
            before = plan(config.spec, load_corpus(config.corpus_path, config.spec))
            self.assertEqual([v.variant_id for v in explicit.plan.variants], [v.variant_id for v in before.variants])
            self.assertEqual(dict(explicit.plan.counts)["CYCLE"], 0)

    def test_configuration_checks(self) -> None:
        self.assertEqual(cycles_from_dict({"count": 1, "criticism": ["none"]}), Cycles(count=1, criticism=("none",)))
        with self.assertRaisesRegex(RecordError, "at most 5"):
            cycles_from_dict({"count": 6, "criticism": ["none"]})
        with self.assertRaisesRegex(RecordError, "not a known criticism source"):
            cycles_from_dict({"count": 1, "criticism": ["oracle"]})
        with self.assertRaisesRegex(RecordError, "repeats 'none'"):
            cycles_from_dict({"count": 1, "criticism": ["none", "none"]})
        with self.assertRaisesRegex(RecordError, "no criticism source is named"):
            cycles_from_dict({"count": 2, "criticism": []})
        with self.assertRaisesRegex(RecordError, "count is 0"):
            cycles_from_dict({"count": 0, "criticism": ["none"]})
        with tempfile.TemporaryDirectory() as directory:
            pilot = _pilot_with_cycles(Path(directory), count=1, criticism=("oracle",))
            with self.assertRaises(RecordError):
                load_pilot_config(pilot)

    def test_oracle_free_vocabularies_exclude_the_key(self) -> None:
        self.assertTrue(set(families_module.ORACLE_FREE_FIELD_VERDICTS) <= set(oracle_module.FIELD_VERDICTS))
        self.assertTrue(set(families_module.ORACLE_FREE_GROUNDING_VERDICTS) <= set(oracle_module.GROUNDING_CRITICISMS))
        for verdict in ("MISMATCH", "UNEXPECTED_PRESENT", "MATCH", "NOT_SCORED"):
            self.assertNotIn(verdict, families_module.ORACLE_FREE_FIELD_VERDICTS)


class CyclePlanningTests(unittest.TestCase):
    def test_plan_chains_each_source_from_the_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            loaded = _Loaded(Path(directory), count=3)
            counts = dict(loaded.plan.counts)
            self.assertEqual(counts["CYCLE"], counts["BASELINE"] * 2 * 3)
            cycles = [v for v in loaded.plan.variants if v.family is Family.CYCLE and v.base_case_id == "ORD-001"]
            base = next(v for v in loaded.plan.variants if v.family is Family.BASELINE and v.base_case_id == "ORD-001")
            for source in ("none", "external"):
                chain = [v for v in cycles if v.cycle_criticism == source]
                self.assertEqual([v.cycle_index for v in chain], [1, 2, 3])
                self.assertEqual(chain[0].cycle_of, base.variant_id)
                self.assertEqual(chain[1].cycle_of, chain[0].variant_id)
                self.assertEqual(chain[2].cycle_of, chain[1].variant_id)
                for v in chain:
                    self.assertIsNone(v.cycle_previous_output)
                    self.assertIsNone(v.cycle_criticisms)
                    self.assertEqual(v.criticised_fields, ())
                    self.assertTrue(v.model_call)
                    self.assertEqual(v.expected, base.expected)
            self.assertEqual(len({v.variant_id for v in cycles}), 6)
            # boundary cases have no baseline and get no cycles
            self.assertFalse(any(v.base_case_id.startswith("BND") for v in loaded.plan.variants if v.family is Family.CYCLE))

    def test_materialisation_refuses_the_key(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            loaded = _Loaded(Path(directory))
            external = next(v for v in loaded.plan.variants if v.family is Family.CYCLE and v.cycle_criticism == "external")
            self_revision = next(v for v in loaded.plan.variants if v.family is Family.CYCLE and v.cycle_criticism == "none")
            previous = '{"site":"Dock 3"}'
            with self.assertRaisesRegex(RecordError, "not oracle-free"):
                materialize_cycle(external, previous, (Criticism("site", "MISMATCH", None),))
            with self.assertRaisesRegex(RecordError, "not oracle-free"):
                materialize_cycle(external, previous, (Criticism("site", "UNEXPECTED_PRESENT", None),))
            with self.assertRaisesRegex(RecordError, "self-revision cycle shows no criticism"):
                materialize_cycle(self_revision, previous, (Criticism("site", "LENGTH_VIOLATION", None),))
            baseline = next(v for v in loaded.plan.variants if v.family is Family.BASELINE)
            with self.assertRaisesRegex(RecordError, "only CYCLE variants"):
                materialize_cycle(baseline, previous, ())
            filled = materialize_cycle(external, previous, (Criticism("site", "LENGTH_VIOLATION", "60 characters allowed"),))
            self.assertNotEqual(filled.variant_id, external.variant_id)
            self.assertEqual(filled.criticised_fields, ("site",))
            self.assertEqual(filled.cycle_of, external.cycle_of)
            # a materialised variant replays from its record
            rebuilt = families_module.variant_from_dict(filled.to_dict())
            self.assertEqual(rebuilt.variant_id, filled.variant_id)
            record = filled.to_dict(); record["cycle_criticisms"] = None
            with self.assertRaisesRegex(RecordError, "set together or not at all"):
                families_module.variant_from_dict(record)
            record = baseline.to_dict(); record["cycle_of"] = "0" * 64
            with self.assertRaisesRegex(RecordError, "without cycle_index"):
                families_module.variant_from_dict(record)

    def test_prompt_shows_the_previous_answer_and_only_oracle_free_checks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            loaded = _Loaded(Path(directory))
            external = next(v for v in loaded.plan.variants if v.family is Family.CYCLE and v.cycle_criticism == "external" and v.cycle_index == 1)
            self_revision = next(v for v in loaded.plan.variants if v.family is Family.CYCLE and v.cycle_criticism == "none" and v.cycle_index == 1)
            with self.assertRaisesRegex(RecordError, "materialise it first"):
                build_user_prompt(external)
            previous = json.dumps({"summary": "z", "site": "Dock 3", "extra": 1}, sort_keys=True, separators=(",", ":"))
            filled = materialize_cycle(external, previous, (Criticism("site", "LENGTH_VIOLATION", "value exceeds maxLength"),))
            prompt = build_user_prompt(filled)
            self.assertIn("## Previous answer", prompt)
            self.assertIn("## Checks on the previous answer", prompt)
            self.assertIn("- `site`: LENGTH_VIOLATION (value exceeds maxLength)", prompt)
            self.assertIn(CYCLE_REVISION_SENTENCE, prompt)
            self.assertNotIn("MISMATCH", prompt)
            # declared fields in prompt order come first, the undeclared key last
            body = prompt.split("```json\n", 1)[1].split("\n```", 1)[0]
            self.assertEqual(list(json.loads(body)), ["site", "summary", "extra"])
            self.assertEqual(build_user_prompt(filled), prompt, "rendering is a function of the variant alone")
            quiet = materialize_cycle(external, previous, ())
            self.assertIn("No automatic check failed on the previous answer.", build_user_prompt(quiet))
            alone = materialize_cycle(self_revision, previous, ())
            self.assertNotIn("## Checks", build_user_prompt(alone))
            self.assertIn("## Previous answer", build_user_prompt(alone))
            # the request digest covers the cycle section, so two different previous answers are two requests
            other = materialize_cycle(external, json.dumps({"site": "Dock 4"}), ())
            self.assertNotEqual(build_chat_request(quiet, model="m", endpoint=loaded.spec.endpoint).request_digest, build_chat_request(other, model="m", endpoint=loaded.spec.endpoint).request_digest)


class CycleRunTests(unittest.TestCase):
    def _run(self, loaded: _Loaded, out: Path, executor=None, executor_kind="fake"):
        return run_pilot(
            spec=loaded.spec, corpus=loaded.corpus, plan=loaded.plan, model="gpt-oss:20b",
            executor=executor or _fake_for(loaded), executor_kind=executor_kind, output_dir=out, created_on=CREATED_ON,
            families=(Family.BASELINE, Family.CYCLE), limit=None,
        )

    def _by_step(self, observations, case_id):
        steps = {}
        for o in observations:
            if o.variant.base_case_id != case_id:
                continue
            if o.variant.family is Family.BASELINE:
                steps["baseline"] = o
            elif o.variant.family is Family.CYCLE:
                steps[(o.variant.cycle_criticism, o.variant.cycle_index)] = o
        return steps

    def test_cycles_follow_their_step_and_never_see_the_key(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            loaded = _Loaded(Path(directory))
            executor = _fake_for(loaded)
            result = self._run(loaded, Path(directory) / "out", executor)
            steps = self._by_step(result.observations, "ORD-001")
            base = steps["baseline"]
            self.assertEqual({v.field: v.verdict for v in base.scoring.field_verdicts}["summary"], "LENGTH_VIOLATION")
            first = steps[("external", 1)]
            self.assertEqual(first.baseline_observation_id, base.observation_id)
            self.assertEqual(first.variant.criticised_fields, ("summary",))
            self.assertEqual([c.verdict for c in first.variant.cycle_criticisms], ["LENGTH_VIOLATION"])
            self.assertTrue(first.scoring.changed_vs_baseline)
            self.assertEqual({v.field: v.verdict for v in first.scoring.field_verdicts}["summary"], "MATCH")
            self.assertEqual(first.planned_variant_id, next(v.variant_id for v in loaded.plan.variants if v.family is Family.CYCLE and v.base_case_id == "ORD-001" and v.cycle_criticism == "external" and v.cycle_index == 1))
            self.assertNotEqual(first.variant.variant_id, first.planned_variant_id)
            second = steps[("external", 2)]
            self.assertEqual(second.baseline_observation_id, first.observation_id, "cycle 2 follows cycle 1, not the baseline")
            self.assertEqual(second.variant.cycle_criticisms, ())
            self.assertFalse(second.scoring.changed_vs_baseline)
            alone = steps[("none", 1)]
            self.assertEqual(alone.baseline_observation_id, base.observation_id)
            self.assertEqual(alone.variant.cycle_criticisms, ())
            self.assertFalse(alone.scoring.changed_vs_baseline, "the fake self-revision returns the previous answer")
            self.assertEqual({v.field: v.verdict for v in alone.scoring.field_verdicts}["summary"], "LENGTH_VIOLATION")
            # nothing the key knows reached any cycle request
            cycle_requests = [r for r in executor.requests if "## Previous answer" in r.user]
            self.assertEqual(len(cycle_requests), 4 * (dict(loaded.plan.counts)["BASELINE"] - 1), "ORD-002's chain made no call")
            for request in cycle_requests:
                self.assertNotIn("MISMATCH", request.user)
                self.assertNotIn("UNEXPECTED_PRESENT", request.user)
                self.assertNotIn("oracle", request.user.lower())
            # the run record counts the family and every record reloads with its ids replaying
            self.assertEqual(dict(result.run_record.family_counts)["CYCLE"], dict(loaded.plan.counts)["CYCLE"])
            reloaded = load_observation_directory(Path(directory) / "out")
            self.assertEqual(len(reloaded), len(result.observations))
            self.assertEqual(load_run(result.run_path).run_id, result.run_record.run_id)

    def test_an_unusable_step_makes_the_chain_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            loaded = _Loaded(Path(directory))
            result = self._run(loaded, Path(directory) / "out")
            steps = self._by_step(result.observations, "ORD-002")
            self.assertEqual(steps["baseline"].scoring.response_verdict, "INVALID_JSON")
            for key in (("none", 1), ("external", 1)):
                self.assertEqual(steps[key].scoring.response_verdict, "PREREQUISITE_UNAVAILABLE")
                self.assertIn("INVALID_JSON", steps[key].scoring.response_detail or "")
                self.assertEqual(steps[key].baseline_observation_id, steps["baseline"].observation_id)
                self.assertEqual(steps[key].variant.variant_id, steps[key].planned_variant_id, "an unmaterialised cycle is recorded as planned")
            second = steps[("external", 2)]
            self.assertEqual(second.scoring.response_verdict, "PREREQUISITE_UNAVAILABLE")
            self.assertIn("PREREQUISITE_UNAVAILABLE", second.scoring.response_detail or "")
            self.assertEqual(second.baseline_observation_id, steps[("external", 1)].observation_id)

    def test_replay_reproduces_every_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            loaded = _Loaded(Path(directory))
            first = self._run(loaded, Path(directory) / "out")
            replayed = self._run(loaded, Path(directory) / "again", ReplayExecutor(Path(directory) / "out"), "replay")
            digests = lambda result: sorted(o.request_digest for o in result.observations if o.request_digest is not None)
            self.assertEqual(digests(first), digests(replayed))
            self.assertEqual(
                sorted((o.variant.variant_id, o.scoring.response_verdict) for o in first.observations),
                sorted((o.variant.variant_id, o.scoring.response_verdict) for o in replayed.observations),
            )

    def test_a_cycle_that_misses_routes_to_plural_loci(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            loaded = _Loaded(Path(directory))
            external = next(v for v in loaded.plan.variants if v.family is Family.CYCLE and v.base_case_id == "ORD-001" and v.cycle_criticism == "external")
            reference = _reference(loaded.corpus, "ORD-001")
            filled = materialize_cycle(external, json.dumps(reference, sort_keys=True), ())
            wrong = dict(reference); wrong["site"] = "somewhere else"
            scoring = score(filled, response_from_content(json.dumps(wrong)), baseline_output=reference)
            routing = route(filled, scoring)
            self.assertIn("MISMATCH", routing.triggers)
            self.assertEqual(routing.loci, ("CANDIDATE", "AUXILIARY", "TEST"))
            self.assertTrue(scoring.changed_vs_baseline)


class CycleClaimTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        loaded = _Loaded(Path(self.directory.name))
        self.loaded = loaded
        self.result = run_pilot(
            spec=loaded.spec, corpus=loaded.corpus, plan=loaded.plan, model="gpt-oss:20b", executor=_fake_for(loaded), executor_kind="fake",
            output_dir=Path(self.directory.name) / "out", created_on=CREATED_ON, families=(Family.BASELINE, Family.CYCLE), limit=None,
        )
        self.observations = list(self.result.observations)
        self.context = claims_module.Context(self.observations)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def _holds(self, condition, observation) -> bool:
        return claims_module.compile_condition(condition, "c")(observation, self.context)

    def _step(self, case_id, key):
        for o in self.observations:
            if o.variant.base_case_id == case_id and o.variant.family is Family.CYCLE and (o.variant.cycle_criticism, o.variant.cycle_index) == key:
                return o
        raise AssertionError(key)

    def test_previous_of_follows_the_chain(self) -> None:
        first = self._step("ORD-001", ("external", 1))
        second = self._step("ORD-001", ("external", 2))
        self.assertEqual(self.context.previous_of(second).observation_id, first.observation_id)
        self.assertEqual(self.context.previous_of(first).variant.family, Family.BASELINE)
        baseline = self.context.baseline_of(first)
        self.assertEqual(self.context.previous_of(baseline), baseline, "a baseline names no step and falls back to itself")

    def test_cycle_and_previous_predicates(self) -> None:
        first = self._step("ORD-001", ("external", 1))
        alone = self._step("ORD-001", ("none", 1))
        self.assertTrue(self._holds({"cycle": {"criticism": "external", "criticised": True, "index": 1}}, first))
        self.assertFalse(self._holds({"cycle": {"criticism": "none"}}, first))
        self.assertFalse(self._holds({"cycle": {"criticised": True}}, alone))
        self.assertTrue(self._holds({"cycle": {}}, alone))
        self.assertFalse(self._holds({"cycle": {}}, self.context.baseline_of(first)))
        self.assertTrue(self._holds({"previous": {"field_verdict": {"verdict": "LENGTH_VIOLATION", "field": "summary"}}}, first))
        self.assertTrue(self._holds({"previous": {"cycle": {"index": 1}}}, self._step("ORD-001", ("external", 2))))
        with self.assertRaisesRegex(RecordError, "not a known criticism source"):
            claims_module.compile_condition({"cycle": {"criticism": "oracle"}}, "c")
        with self.assertRaisesRegex(RecordError, "positive integer"):
            claims_module.compile_condition({"cycle": {"index": 0}}, "c")

    def test_verdict_move_and_criticised_field(self) -> None:
        first = self._step("ORD-001", ("external", 1))
        alone = self._step("ORD-001", ("none", 1))
        second = self._step("ORD-001", ("external", 2))
        self.assertTrue(self._holds({"verdict_move": {"from": "LENGTH_VIOLATION", "to": "MATCH"}}, first))
        self.assertTrue(self._holds({"verdict_move": {"from": "miss", "to": "MATCH", "criticised": True, "field": "summary"}}, first))
        self.assertFalse(self._holds({"verdict_move": {"from": "miss", "to": "MATCH", "criticised": False}}, first), "the repaired field was the criticised one")
        self.assertFalse(self._holds({"verdict_move": {"from": "MATCH", "to": "miss"}}, first))
        self.assertFalse(self._holds({"verdict_move": {"from": "miss", "to": "MATCH"}}, alone))
        self.assertFalse(self._holds({"verdict_move": {"from": "miss", "to": "MATCH"}}, second))
        self.assertTrue(self._holds({"criticised_field": {"changed": True}}, first))
        self.assertFalse(self._holds({"criticised_field": {"changed": False}}, first))
        self.assertFalse(self._holds({"criticised_field": {"verdict": "LENGTH_VIOLATION"}}, first), "the named check no longer fails")
        self.assertTrue(self._holds({"criticised_field": {"verdict": "MATCH"}}, first))
        self.assertFalse(self._holds({"criticised_field": {"changed": True}}, alone), "no field was criticised")
        unavailable = self._step("ORD-002", ("external", 1))
        self.assertFalse(self._holds({"verdict_move": {"from": "miss", "to": "MATCH"}}, unavailable))
        for bad in ({"verdict_move": {"from": "GOOD", "to": "MATCH"}}, {"verdict_move": {"from": [], "to": "MATCH"}}, {"criticised_field": {}}, {"criticised_field": {"grounding_verdict": "FLOATING"}}):
            with self.assertRaises(RecordError):
                claims_module.compile_condition(bad, "c")
        fields, triggers = claims_module.condition_footprint({"verdict_move": {"field": "summary", "from": "miss", "to": "MATCH"}})
        self.assertEqual(fields, frozenset({"summary"}))
        self.assertIsNone(claims_module.condition_footprint({"criticised_field": {"changed": True}})[0])

    def test_claims_file_with_cycle_predicates_loads_and_evaluates(self) -> None:
        raw = {
            "schema_version": claims_module.CLAIMS_SCHEMA_VERSION,
            "title": "t",
            "claims": [
                {"claim_id": "CYC-T1", "statement": "A criticised field is never left unchanged.", "kind": "never", "scope": {"families": ["CYCLE"], "cases": None, "models": None, "model_call": True},
                 "condition": {"all_of": [{"cycle": {"criticism": "external", "criticised": True}}, {"criticised_field": {"changed": False}}]}, "note": None},
                {"claim_id": "CYC-T2", "statement": "A further cycle never turns a miss into a match.", "kind": "never", "scope": {"families": ["CYCLE"], "cases": None, "models": None, "model_call": True},
                 "condition": {"all_of": [{"cycle": {}}, {"verdict_move": {"from": "miss", "to": "MATCH"}}]}, "note": None},
            ],
        }
        claims = claims_module.claims_from_dict(raw)
        results = claims_module.evaluate_claims(claims, self.observations)
        by_id = {r.claim.claim_id: r for r in results}
        self.assertEqual(by_id["CYC-T1"].status, "UNREFUTED_FOR_DECLARED_SCOPE")
        self.assertEqual(by_id["CYC-T2"].status, "REFUTED")
        self.assertEqual(by_id["CYC-T2"].refuting, 1)


class CyclesTableTests(unittest.TestCase):
    def test_summary_rows_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            loaded = _Loaded(Path(directory))
            out = Path(directory) / "out"
            result = run_pilot(
                spec=loaded.spec, corpus=loaded.corpus, plan=loaded.plan, model="gpt-oss:20b", executor=_fake_for(loaded), executor_kind="fake",
                output_dir=out, created_on=CREATED_ON, families=(Family.BASELINE, Family.CYCLE), limit=None,
            )
            runs = [load_run(path) for path in enumerate_record_directory(out).run_paths]
            summary = summarise_cycles(runs, load_observation_directory(out))
            rows = {(r["kind"], r["criticism"], r["cycle"]): r for r in summary["rows"]}
            baselines = dict(loaded.plan.counts)["BASELINE"]
            external_1 = rows[("cycle", "external", 1)]
            self.assertEqual(external_1["observations"], baselines)
            self.assertEqual(external_1["prerequisite_unavailable"], 1)
            self.assertEqual(external_1["differing_from_previous"], 1)
            self.assertEqual(external_1["identical_to_previous"], baselines - 2)
            self.assertEqual(external_1["miss_to_match"], 1)
            self.assertEqual(external_1["match_to_miss"], 0)
            self.assertEqual(external_1["with_criticism"], 1)
            self.assertEqual((external_1["criticised_fields"], external_1["criticised_fields_changed"], external_1["criticised_fields_still_failing"]), (1, 1, 0))
            self.assertEqual(external_1["field_moves"], [{"move": "summary: LENGTH_VIOLATION -> MATCH", "count": 1}])
            none_1 = rows[("cycle", "none", 1)]
            self.assertEqual((none_1["identical_to_previous"], none_1["differing_from_previous"], none_1["miss_to_match"]), (baselines - 1, 0, 0))
            floor = rows[("repeat", None, None)]
            self.assertEqual(floor["observations"], 0, "the incident form configures no repeats; the floor row is present and empty")
            markdown = render_cycles_markdown(summary)
            self.assertIn("cycle 1, criticism external", markdown)
            self.assertIn("summary: LENGTH_VIOLATION -> MATCH", markdown)
            for word in ("accuracy", "best", "worst", "score:"):
                self.assertNotIn(word, markdown.lower())
            with self.assertRaisesRegex(RecordError, "was not supplied"):
                summarise_cycles(runs, list(load_observation_directory(out))[:-1])


class ReplayDisambiguationTests(unittest.TestCase):
    """H31: variants of different cases can send one request; the replay returns each its own reply."""

    def _observation(self, base, variant_id: str, content: str, digest: str):
        import dataclasses
        from creib.forge.conformance.records import build_observation
        variant = dataclasses.replace(base.variant, held_fixed=variant_id)  # a different content, hence a different id
        variant = families_module.make_variant(**{f: getattr(variant, f) for f in variant.__dataclass_fields__ if f != "variant_id"})
        fields = {f.name: getattr(base, f.name) for f in dataclasses.fields(base) if f.name != "observation_id"}
        fields.update(variant=variant, request_digest=digest, response=response_from_content(content))
        return build_observation(**fields)

    def test_same_text_is_accepted_and_different_texts_need_the_variant(self) -> None:
        from creib.forge.conformance.records import publish_record
        base = load_observation(sorted((ROOT / "forge" / "conformance" / "runs" / "leave-request").glob("observation.*.json"))[0])
        digest = "sha256:" + "a" * 64
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            one = self._observation(base, "one", '{"x": 1}', digest)
            two = self._observation(base, "two", '{"x": 1}', digest)
            for o in (one, two):
                publish_record(o, out)
            request = ChatRequest(model="m", system="s", user="u", format_schema=None, options={"temperature": 0, "seed": 7}, think=False)
            self.assertEqual(ReplayExecutor(out).complete(dataclasses_replace(request, variant_id=None, digest=digest)).content, '{"x": 1}')
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            one = self._observation(base, "one", '{"x": 1}', digest)
            two = self._observation(base, "two", '{"x": 2}', digest)
            for o in (one, two):
                publish_record(o, out)
            replay = ReplayExecutor(out)
            self.assertEqual(replay.complete(dataclasses_replace(request, variant_id=one.variant.variant_id, digest=digest)).content, '{"x": 1}')
            self.assertEqual(replay.complete(dataclasses_replace(request, variant_id=two.variant.variant_id, digest=digest)).content, '{"x": 2}')
            with self.assertRaisesRegex(RecordError, "2 different replies"):
                replay.complete(dataclasses_replace(request, variant_id=None, digest=digest))
            with self.assertRaisesRegex(RecordError, "no recorded response"):
                replay.complete(dataclasses_replace(request, variant_id=None, digest="sha256:" + "b" * 64))


def dataclasses_replace(request: ChatRequest, *, variant_id, digest: str) -> ChatRequest:
    """A request whose digest is forced to ``digest`` so that the replay's keying can be tested directly."""

    import dataclasses

    class Forced(ChatRequest):
        @property
        def request_digest(self) -> str:  # type: ignore[override]
            return digest

    fields = {f.name: getattr(request, f.name) for f in dataclasses.fields(request)}
    fields["variant_id"] = variant_id
    return Forced(**fields)


if __name__ == "__main__":
    unittest.main()
