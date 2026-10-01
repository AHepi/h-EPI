# Summary: logs 43 to 49

Log entry 50. One page in place of seven logs, as log 43 was for logs 25 to 42. Nothing new was run for it; every number comes from the reports it names.

## The short answer

- **The world's answers correct DeepSeek only where they land, and they land only where some current guess already points.** Asked by DeepSeek or by the program, on the grudge and on the heater, the questions that would have shown a missing part were almost never asked, so the missing part was almost never found.
- **DeepSeek does change its mind when the world contradicts it.** Told its own mistakes in the same conversation, it dropped its first answer at least as readily as a fresh DeepSeek did. Your prediction that it would cling to its first answer was ruled out (log 45).
- **Nothing that keeps or chooses among DeepSeek's guesses has helped reliably yet.** Keeping surviving rivals failed twice (logs 47 and 48). Letting rivals choose the questions helped on one device and did worst on the other (logs 46 and 49).

## An example first: one missing situation

The heater (log 49): turning the dial up twice trips a cut-out, and only waiting resets it. Among all 106 situations of up to four actions that were not observations, just one shows the reset: "up, up, wait, up", which ends warm.

- **DeepSeek's rivals** never gave waiting that part, so they never disagreed about that situation, so the program never asked about it.
- **Random questions** could have hit it by luck, and did not.
- **The five best explanations** of the whole run each got 105 of 106 short situations right, and all five missed exactly that one.

The grudge showed the same thing earlier. When DeepSeek chose its own questions, the situations that show a deep grudge were asked in 1 run of 12 (log 45). When the rivals chose, the long situations they disagreed on crowded out the short ones that show it, which were asked in 0 runs of 6 (log 48).

## What was tested, log by log

| Log | Question | What happened |
|---|---|---|
| 44 | Told "you predicted X; the world says Y" in the same conversation, does DeepSeek defend its first answer, compared with a fresh DeepSeek given only the facts? | Seemed to favour your prediction on the grudge, but two replies were cut off, and I misnamed a rule "the true explanation" |
| 45 | The same on the grudge, six times each, with nothing cut off | Ruled out your prediction: in the same conversation it dropped its running score in 5 of 6 runs, a fresh one in 3 of 6. What moved it was the world contradicting a prediction |
| 46 | Do rival explanations choose better questions than DeepSeek does? | On the grudge, yes: the telling situations were asked in 4 of 6 runs, and DeepSeek built new kinds of explanation. Still not the true grudge, and a rival that fitted everything was thrown away |
| 47 | Does keeping the survivors help? | No: a fresh DeepSeek shown only the facts did best. A lone survivor was the old habit, and DeepSeek copied survivors |
| 48 | Does it help if the world can be asked longer questions? | No, worse: long questions killed nearly every rival, and the telling short situations were never asked |
| 49 | Does any of this carry to a second device, the heater? | No run found the true heater. Rivals choose did worst. Same blind spot |

## What holds on both devices

1. **Contradiction from the world moves DeepSeek.** In log 45, the one run set up to measure it, every run where a prediction was contradicted changed its rule, and the two that kept the old habit were the two never contradicted. Logs 46 to 49 fit this, but did not measure it.
2. **The questions decide what can be found.** New parts appeared exactly where the world's answers showed them:
   - "a gift softens a deep grudge" appeared only in runs that had asked "insult, insult, gift, apologise" (log 47);
   - the heater's reset appeared nowhere, because nothing asked "up, up, wait, up" (log 49).
3. **Every way of choosing questions tried so far looks where current guesses point.** That includes DeepSeek's own choices and the program's choices made from DeepSeek's rivals.
4. **"Not yet refuted" does not pick out a good explanation.** Tested too little, poor guesses survive; tested hard, almost nothing does (logs 47 and 48).

## What did not carry over

- **Rivals choosing the questions** helped on the grudge (559 against random answers' 527 short sequences right, log 46) and did worst on the heater (4,604 against random answers' 5,049 long sequences right, log 49).
- **DeepSeek's habit.** On the grudge, DeepSeek had a strong wrong habit that fitted every observation: the running score. On the heater it had no single habit; its explanations were scattered, some with the dial running backwards.

## Where DeepSeek sits in your semantics

Unchanged from log 43, and sharper:
- **DeepSeek is a selected source of guesses**, strong but bounded by what it has imagined.
- **The criticism that worked came from outside it**, the world, but only where something aimed it.
- **What is missing is a way to aim criticism outside the current guesses.** Your semantics' account of a recognized problem, a criticism that bears on a conjunction, needs a question to be asked before it can bear. Nothing in the system yet produces a question that no current guess suggests.

## Claims of mine that went too far

- **"The true explanation" (log 44).** It was the unresolved-insult count, right on 118 of 120 short sequences, not the true grudge. Corrected in log 45.
- **"Rivals choosing the questions helps" (log 46).** It did on one device and not on the other (log 49).
- **"Keeping survivors is the obvious next step" (log 46).** It did not help, twice.

## What people still supplied

People still supplied the devices, the true answers, which situations count as observations and test cases, every plan and conjecture, and the grading. DeepSeek supplied guesses, rivals and final explanations; the program ran them and asked the world.

## Open questions

1. **Can anything choose questions outside the current guesses?** For example: situations least like anything observed so far, or questions about each action in a context never tried.
2. **What should prefer one surviving explanation over another?** Your semantics deliberately leaves that outside the theory; the records show something is needed (logs 37, 47, 48).
3. **When DeepSeek invents a part nothing has shown it, can the system keep it?** Its rivals did invent such parts. In log 46, round 1, before any telling fact, one rival had an anger level that an apology only partly mends. But in the final explanations, new parts showed up only after a fact had shown them.
4. **Humanity as the universal explainer** (log 33), still kept for later.

## Next step

Test open question 1 on both devices. Add a question-chooser that ignores the guesses: it asks about the situation least like any observed so far, judged by which actions follow which. Compare it with random answers and rivals choose, six repeats each. Plan and conjectures committed first; about $1.50 of the $10.70 left.
