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
