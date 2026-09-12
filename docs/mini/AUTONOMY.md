# What runs without a person, and what does not

The operator's requirement: the harness completes without a human in the loop.
This says exactly how far that goes, where it stops, why it stops there, and
what would have to change for it to stop somewhere else. It is written from the
code and the records of the thirty experiment runs under
`forge/mini/runs/experiments/`, and it is meant to be argued with.

## The short answer

Three different things were being asked for under one phrase, and they have
three different answers.

| | Answer |
|---|---|
| Running a campaign of rounds unattended: launching, reading, deciding the next round, recording | **Yes**, and it does; `tools/mini_campaign.py` |
| Refuting a claim someone wrote down | **Yes**, mechanically, and it has: five catalogue rows fell in one run with nobody reading anything |
| Deciding that a disagreement nobody wrote down is a blind spot | **No**, and not for want of engineering |

The third is the one that matters, and the reason it is no is not that mini is
unfinished. It is that this repository exists to refuse exactly that step.

## What now runs without anybody

`tools/mini_campaign.py run --plan … --rounds N --concurrency 5 --commit` takes
a campaign to its end:

- runs each round's shapes live, at most N at a time, one model each;
- replays every record it wrote and writes the reading beside it
  (`creib.forge.mini.report`): proposals, what the executor could run, every
  execution whose answer contradicted the proposal with the two texts that
  produced it, how many cells of a grid were named, how many pairs changed more
  than one part;
- decides the next round from those measurements alone
  (`creib.forge.mini.campaign`), writes its manifests and a note saying which
  rule fired on which measurement, and commits both **before** the round runs,
  so the pre-registration is on the record before the records exist;
- stops when the rounds are spent, when every shape's rules say it has nothing
  left to run, or when a round contradicts nothing and changes nothing.

The rules are not a heuristic layer invented for the occasion. They are the
five rewrites the five rounds of experiments made by hand, each stated once and
fired by a measurement whose register entry it names: the fields form when more
replies were refused than run (M13), a sentence about real line breaks when the
escape sequence was written out (M16), a sentence about one change per pair when
most pairs changed several (M14), more cycles when a grid ended uncovered, and a
stop when a covered grid starts returning duplicates (M10). `test_campaign.py`
asserts that each fires on the committed record that motivated it and that none
fires on the run that did what was asked.

The key is read in one place, inside the harness's own executor, and the
campaign runner never touches it. It never pushes.

## What is mechanical about a finding, and what is not

A verdict seat already refutes written claims with no reading by anybody. In
`forge/mini/runs/experiments/round-1/s3-refute-invariances/`, five catalogue
rows that said a pair does not move were refuted by inputs of their own class,
and the standing `defect` was computed, not judged: a row is a universal claim
over an input class, an execution is an instance, and one instance settles it.
That is a complete loop with no person in it.

What a person did afterwards was different in kind. Of those five refutations,
two were trivial (a sentence with no object, under a transform that adds one),
two showed that the row's invariance had been written over its own example
rather than its class, and one was worth a new boundary point (`P-09`, a JSON
literal under a change of case). **The machine can say that a written claim is
false. It cannot say that a false claim matters.** Significance is a judgement
about what the check is for, and nothing in the tree holds that.

## Why the third answer is no

Three reasons, and they are independent: removing any one leaves the other two.

### 1. The constitution reserves it

`CLAUDE.md` is not decoration. "Never promote." "Mini mints no standing." "A
candidate point becomes a row of `docs/kernel.md` only by a person's reading,
written into `tests/kernel_boundaries.py` with the record cited." "Readiness is
never inferred from records." A campaign that promoted its own candidates would
not be a more autonomous version of this system; it would be a different system,
one whose central claim — that nothing here confirms anything — had been
withdrawn. The step is not missing. It is refused.

### 2. There is no oracle for the judgement, and a model cannot be one

A candidate is a pair on which a seat's expectation and the machine's answer
differ. There are three reasons that happens: the seat misread the documented
rule; the rule and the code genuinely part; or the rule is ambiguous and both
readings are fair. Telling those apart means reading an English sentence and
saying what it commits its author to. The tree holds no representation of that
sentence's meaning — only the sentence.

The obvious move is to ask a model to judge. It does not work here, and the rule
against it is the same rule that makes the rest of the harness worth anything:
agreement between models never confirms. A judge seat would produce a second
opinion of exactly the kind whose unreliability the whole apparatus is built to
expose. The records show why this is not paranoia: on the two shapes where the
machine handed a seat both texts and asked only for the expectation, the seat
agreed with the code on thirty-four of forty-two pairs and *every one of its
eight disagreements was its own misreading of a row already written down*
(`round-5/r5-4-grounding-pairs-given`, `round-5/r5-5-verdict-pairs-given`). A
judge with that error rate, judging its own kind, would manufacture findings.

### 3. The space is not machine-invented

The defect this series found (`docs/failure-modes.md` H43) was found because a
person wrote its cell into a grid: `fence[ S A ] B`, a fence holding a sentence
beside its object with a bare object after it. Three models then found it, which
is the strong part of the result; but no shape proposed that dimension. The
shapes that let a seat choose its own inputs produced thirty-three proposals in
the control's neighbourhood and none on it. Enumerating a space means deciding
which distinctions could matter, and that decision is the same kind of thing as
reading a rule.

## The step can be moved, and that is the useful answer

The human step is not removable, but it is movable, and moving it changes the
economics completely.

Today a person reads *every candidate* — unbounded work, growing with every
round. But the mechanical loop above needs only one thing to close: a claim
written down in a form an execution can contradict. So write the rule down once.

`docs/kernel.md` is already exactly this: every row is a claim with both sides
executable, and `tests/test_kernel.py` asserts them. The blind-spot catalogue
under `forge/mini/manifests/conformance-blind-spot/` is drawn from it. When a
row exists, refutation is mechanical and unattended, as `s3` showed. The control
was missed for sixteen runs precisely because the rule it violates lived in a
docstring, in prose, where nothing can execute it.

So the work that buys autonomy is not more machinery. It is: **for each check,
write what it is supposed to do as a claim in the catalogue, once.** After that
the campaign runs unattended and refutes; a person is called only when a written
claim falls, and reads one thing — whether that mattered. Per rule, bounded, and
done once, instead of per candidate, unbounded, and done forever.

## The third thing has been started, for three checks

Written 12 September 2026. The section above says the work that buys autonomy is to write each check's
own rule down in a form an execution can contradict, once, and that this is the only one of the three
changes worth making. `creib.forge.mini.rule_readings` is that work, begun: it implements the documented
rule of `recover_json_object`, `refusal_phrase_in` and `_plain_quotes` from their docstrings rather than
from their bodies, so the rule's answer on a text can be computed and set beside the code's.

What that bought immediately. A find claims two things -- the check answers the same on two texts, and
the rule requires it to answer differently -- and until this existed only the first was ever checked;
the second came from the model's prose. Adjudicated, 111 of block 2's 166 finds hold up under every
reading of the rule, 54 do not hold under at least one, and one was false (`docs/mini/ERRATA.md`, C24).
That adjudication is mechanical and unattended, which is the thing this document said was worth buying.

What it did not buy. Each rule carries the readings its own words cannot settle, and every count is
reported under each, so a person still chooses between readings when they disagree -- and that is a
smaller and better-bounded question than reading every candidate. Three checks of many are done.

## Whether a model can decide has now been put to one

Also 12 September. This document's first row says a campaign runs unattended, and the row is about the
MACHINE: `creib.forge.mini.campaign` picks the next round from six numbers by five fixed rules. A model
has never been asked to make that choice, or any other. `docs/mini/DECIDE_TEST_1.md` pre-registers the
block that asks -- what to work on next, what to add, and what the campaign's own rules decide -- and
scores what can be scored against a grid of runs and a function of six numbers, with nothing larger than
the model under test adjudicating anything. Its results, whatever they are, belong in that document and
change nothing here until they are read.

## What stays human whatever happens

Publication. Work happens on a branch, publication is a pull request, and
merging is a human action. The campaign runner commits and never pushes, by
design and not by omission.

## What would have to change for the third answer to be yes

Stated so it can be argued with rather than assumed away:

1. **Withdraw "never promote" for boundary points**, and let a verdict seat write
   a row into `tests/kernel_boundaries.py` when a disagreement survives some
   mechanical filter. The cost is the thing the repository is for: a row would
   then rest on a seat's reading of a docstring, which is the same kind of
   evidence the harness refuses to accept about a model.
2. **Admit a model as a judge of significance**, with the records showing it
   wrong eight times out of eight on cases where a row already existed. The cost
   is that agreement between models would start to count as evidence.
3. **Give the machine the rule in an executable form** — which is not a change to
   the constitution at all, and is the one described above.

Only the third is worth doing, and it is ordinary work: write the checks' own
rules down as claims, one at a time, and let the loop run.
