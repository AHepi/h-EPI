# OPEN-SWEEP-1: the same question with the answer space opened

A pre-registration. Written and committed before any run of this block exists.

## What it changes, and the one thing it does not

ARCH-SWEEP-1 asked whether a loop finds boundary points nobody wrote down, and told its proposer
which four checks it was allowed to look at. M24 records that as a grid with its cells written into
prose, in a block whose own text refused a grid. This block asks the same question with that
removed, and holds **everything else** fixed: the same wiring, the same model, the same three
cycles, temperature 0, seed 7, the same problem text, the same critic.

The proposer is now told the rule for naming a kernel and the fifteen modules it may name one in.
**It is given no list of functions.** 66 functions of one string are reachable; four were before.

**The architecture is not varied here.** ARCH-SWEEP-1's control showed the endpoint returns six
different answers to a byte-identical prompt, so a 36-architecture comparison could not attribute
its gain. Varying two things at once when one of them is already known to be unattributable would
buy nothing. This block runs the **synchronous architecture only**, 36 times, against the control
already in the tree — `forge/mini/runs/arch-sweep-control/`, 36 repeats of the same architecture
under the closed instruction. **The two differ in the answer space and in nothing else.**

## The comparison

| | closed (already run) | open (this block) |
|---|---|---|
| runs | 36 | 36 |
| architecture | `a00` synchronous | `a00` synchronous |
| kernels nameable | 4, listed in the instruction | 66, none listed |
| everything else | — | identical |

Read with the same reader: `entries`, `ran`, `duplicate`, `unrunnable`, `contradicted`, `quoted`,
distinct behaviours, distinct probes.

## What is predicted, before the run

- **O1.** At least one proposal names a function outside the ten registered kernels and it runs.
  If none does, the widening is unused and the block says nothing about it; the instruction would
  then be the binding constraint, not the registry.
- **O2 — the one that matters.** The open arm produces **at least one contradiction that quotes the
  rule**. K1 got zero across 72 closed runs, and M24 attributes that to the enumeration. If the
  open arm also produces zero, **that attribution is refuted**: the enumeration was not what
  suppressed rule-quoting contradictions, and M24's reading of K1 must be withdrawn.
- **O3.** `unrunnable` is **higher** in the open arm than the closed arm's zero. A wider space
  means paths that do not resolve and functions that raise. A widening that costs nothing would
  suggest the proposer is not using the width.
- **O4.** The union of distinct behaviours over the open arm is larger than the closed arm's 15.

**O2 is the experiment**, and it is written so it can lose in the direction that costs me most: a
zero in the open arm refutes my own explanation of why K1 failed.

## What it cannot settle

The open arm is bounded by an import rule, so "unconfined" means 66 functions and fifteen modules,
not the space of boundary points. One wiring, one model, one task, three cycles, one repeat count,
and a proposer whose answer to an identical prompt varies six ways — so a difference of one or two
between arms is noise, and will be reported as noise. Nothing here is `Origin`; `New` remains
unestablishable.

And the honest risk: 66 functions is a much harder brief than 4. The open arm may do **worse**
because the proposer spends its calls resolving paths instead of reading rules. That is a real
outcome and O3 is where it would show.

## What the 36 runs show

All 36 reached `RUN_ENDED`. Both arms: 216 executor rows, 36 runs, three cycles, same everything
but the answer space.

| measure | closed (4 kernels named) | open (66 reachable, none named) |
|---|---|---|
| rows | 216 | 216 |
| ran | 106 | 85 |
| duplicate | 110 | 85 |
| **unrunnable** | **0** | **46** |
| contradicted | 1 | 1 |
| **quoted** | **0** | **0** |
| contradictions per 100 ran | 0.9 | 1.2 |
| distinct behaviours | 15 | **19** |
| distinct probes | 9 | 9 |
| distinct kernels named | 5 | 8 |

**O1 holds.** Four kernels outside the registry were named and **two ran**:
`oracle.recover_json_object` (152 rows) and `oracle._plain_quotes` (6). The widening was used, so
the block is about it.

**O2 fails, and O2 was the experiment.** The open arm produced **one** contradiction and **zero**
quoting the rule — the closed arm's numbers exactly. The pre-registration says what follows: *"If
the open arm also produces zero, that attribution is refuted... M24's reading of K1 must be
withdrawn."* **It is withdrawn.** The enumeration is not what suppressed rule-quoting
contradictions. Zero in 72 closed runs, zero in 36 open runs, and opening the answer space
sixteenfold changed nothing about it.

**How strongly it fails, stated honestly.** One contradiction per arm. A *rate* of rule-quoting over
a single contradiction is not a measurement, so this block cannot separate "the enumeration did not
matter" from "contradictions are too rare in either arm for anything to be measurable". What it can
say, and does, is that the prediction M24's attribution implied did not occur. That is enough to
withdraw the attribution and not enough to put another in its place.

**O3 holds, and the cost is not the one expected.** 46 of 216 rows did not run, against zero in the
closed arm. The breakdown matters more than the total:

- **32 — `oracle` has no `_grounding_kernel`.** The model invented a function.
- **3 — `records` has no `recover_json_object`.** A real function name, the wrong module.
- **8 — the `open:` prefix dropped**, so the registry refused a path it had no entry for.
- **3 — the function raised**, on either side of the pair, so the row is `unrunnable` and not a
  move. This is the M11 rule doing exactly the job it was added for.

**Thirty-five of the 46 are invented or misplaced names.** The notation tax that looked like the
risk during the smoke test is the smaller half, and the decision not to loosen the resolver after
seeing it would have bought back 8 rows out of 46.

**O4 holds, and repeats a pattern.** 19 distinct behaviours against 15, on **fewer** executed rows
(85 against 106). But distinct probes are **9 and 9**. This is the split ARCH-SWEEP-1's control
found: the wider space moves what gets written and not what gets tested. Two different widenings —
the architecture lattice and the answer space — have now produced more behaviour triples and the
same number of probe cells.

**The one contradiction, in full.** `open:creib.forge.conformance.oracle.recover_json_object` on

```
```json
{"a": 1}
```
{"b": 2}
```

with the opening fence changed from ` ``` ` to `___`: expected `unchanged`, the answer moved from
`({'a': 1}, ())` to `({'b': 2}, ())`. It is the fence-and-bare-object class the round-3 control
already found, reached this time through a function named by import path rather than a registered
kernel — and it quotes no rule, so it does not satisfy O2.

## What this block does not license

It does not say the answer space should be closed again. O1 and O4 both hold, and the machinery
that resolves a function by path is the only reason the boundary point above could be stated at all
in a run whose instruction named no kernels. It says the enumeration was not the reason K1 failed,
and that I attributed K1's failure to the thing I had most recently been shown to have done wrong.
