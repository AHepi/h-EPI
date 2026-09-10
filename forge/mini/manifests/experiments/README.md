# Experiments: can the blind-spot loop find what its authors did not?

Pre-registered before any of these manifests was run. Three rounds of five
concurrent live runs, each run a different shape, the shapes mutated between
rounds on what the records show. The operator's brief: figure out what might be
wrong first, then mutate; if three rounds show nothing, the angle needs a
rethink.

## The diagnosis the shapes test

The four runs of `forge/mini/manifests/conformance-blind-spot/` found only rows
the kernel table already covers by implication. Four things looked wrong:

1. **The transform registry is closed.** A proposer could only name rewrites the
   authors wrote, so the loop could rediscover their rows and nothing else. Pair
   proposals (`mini.pair-proposal.*`) let the proposer write the rewritten input
   itself; the executor runs the kernel on both texts and compares with what the
   proposer expected.
2. **The proposer never saw the check.** It saw one-line descriptions and
   reasoned by analogy with the catalogue. A machine seat
   (`mini.kernel-source.v1`) now emits the kernels' source as an artifact the
   proposer reads whole.
3. **Repetition.** Three stages of one kind at temperature zero produced one
   triple three times. Kinds with distinct targets and instructions, and an
   executor that names a duplicate instead of re-running it.
4. **Only reply-level checks, only a small model.** Grounding kernels over a JSON
   object (value, span, document), and the larger models in some shapes.

## The positive control

The tree these runs execute against carries a known, fixed defect in JSON
recovery: a fence that holds a sentence beside its object is not read as a
fenced candidate, so a bare object after the fence is scored instead of the
fenced one, against the docstring's stated rule (register entry H44 on the
`claude/harness-repeatability-and-grounding-options` branch, not yet on `main`).
A shape that works should be able to find it, or something of its kind, without
being told.

## What "works" means, decided before the runs

A run works when its verdicts hold at least one of:

- a `defect`: a catalogued invariance refuted by an input, or a row's own example
  shown wrong;
- for a pair shape, a pair whose executed outcome differs from the proposer's
  stated expectation, where the expectation was a fair reading of the docstring
  and the pair is not an instance of a row the catalogue already holds;
- for a transform shape, a `candidate point` whose pair is not covered by the
  catalogue or by a sentence in `docs/kernel.md`.

And at least half its proposals must have run: not dropped, not duplicates, not
unrunnable. Whether a candidate is "not covered" is a person's reading, made
after the run and written down with the run; the machine cannot decide it and is
not asked to.

## Round 1

| Shape | Model | What it varies |
|---|---|---|
| `s1-pairs-targeted` | gemma4:31b | pair proposals; three proposer kinds, one per check family; source shown; criticisms fed back |
| `s2-source-adversary` | mistral-large-3:675b | pair proposals; two proposers told to find where code and docstring disagree; source shown; criticisms fed back |
| `s3-refute-invariances` | qwen3.5:397b | registered transforms; proposers told to refute a catalogued "does not move" row with an input of its class; source shown |
| `s4-grounding-pairs` | gemma4:31b | pair proposals on the grounding kernels only; source shown |
| `s5-registry-feedback` | nemotron-3-nano:30b | the previous template with duplicates named, criticisms and executions fed back |

Three cycles each. Records under `forge/mini/runs/experiments/round-1/`.
