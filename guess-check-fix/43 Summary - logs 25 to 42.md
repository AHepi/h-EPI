# Summary: logs 25 to 42

Log entry 43. One page in place of eighteen logs, so the next direction can be chosen from here. Nothing new was run for it; every number comes from the reports it names.

## The short answer

- **DeepSeek is a strong source of guesses and a weak critic of its own.** Asking it again, voting, telling it to doubt, or giving it a character never fixed a wrong habit. What changed its answers was something outside it: new facts from the world, a program drawing out consequences, or a language that could hold the explanation.
- **Error correction happened in the system around DeepSeek, and once the system corrected one of its own methods.** DeepSeek rewrote the checker's rule for accepting fixes, and the program kept the new rule only because it did better on fixes DeepSeek never saw (log 39). The kept rule then did its job in the checker's own loop (log 40).
- **People still set everything that decides what counts:** the aims, the test occasions, which method was open to change, and the tools. And two of my own claims were too strong and were withdrawn.

## An example first

The checker had a rule for accepting a fix to a model: accept it if it makes a failing job pass and breaks no job. That rule cannot see a fix that breaks something no job checks. In log 17 a person noticed this and wrote a better rule.

In logs 39 to 42 the program asked DeepSeek to rewrite that rule instead. Its new rules caught 9 to 20 of 24 bad fixes on occasions it never saw, where the person's rule catches 13, and the program kept each one only after checking it lost nothing it was told to keep. Used in the checker's loop, the broken-by-a-fix count fell from 84 to 11, 25 and 28. Asked only "Is anything wrong with this method?", DeepSeek named the failure every time a reply arrived.

What it did not do: decide that this rule was the one to question, choose the test occasions, or set the aims. People did.

## What we set out to test

Error correction as your semantics means it: not spotting tricks, but guessing an explanation, criticising it, and keeping what survives, including new explanations with new parts (construction), not just re-tuning an old one (selection). The question each time was where the correcting actually happens: in DeepSeek, in the program, or in a person.

## What was found, in five groups

**1. Correcting a guess with fixed evidence (log 25).** Four made-up devices, the same 14 observations for every arm, no way to ask for more. The loop of guessing and criticism did not beat DeepSeek on its own (84 of 96 hard cases against 85). On one device, the grudge, every bare answer made the same mistake, a running score of kind acts against insults, even asked five times or made to check itself. Writing an explicit explanation did better there, but only because of the form: the first explanation fitted all 14 observations every time, so criticism never had anything to bite on. The hard-to-vary check helped a little (58 against 55).

**2. Cause and effect (logs 28 and 29).** The checker can now answer "what if" by holding a thing and running the model, and tells seeing from making. On 150 questions other people wrote and answered, it agreed with them on 101; a direct answer from the same kind of AI agreed on 128. Almost the whole gap was things the model left out: where the model held both ends of the question, 53 of 70 against 58. Claude wrote the models, not DeepSeek. What the checker takes for granted about cause is listed in "28 What the causal checker presupposes.md".

**3. Steering DeepSeek with text (logs 30 to 32).** No text at the top of its instructions, and no character to play, changed which questions DeepSeek asked. Two runs with the same text differed as much as runs with different texts. Direct instructions were mostly ignored. One steady, unexplained effect: any text, even "Reference number 4471-B.", made answers surprise it more often (18 to 34 of 100 against 15).

**4. The language the explanation is written in (logs 34 and 35).** Where the right explanation needs an unlimited count or a pile, DeepSeek wrote it in JavaScript every time (36 of 36 long tests) and not in the checker's rule language (15 of 36): big enough models were too long to write, small ones broke past their size. Let the rule language gain new kinds of thing, and DeepSeek added a number or a pile and matched JavaScript (63 of 63). The fixed language once surprised me: DeepSeek invented binary counting, which broke at 256. But on the grudge the new freedom let the old running-score habit straight back in.

**5. Changing a method (logs 39 to 42).** The example above. Told only the aim, DeepSeek wrote the person's rule exactly. Shown two failures, it wrote better ones. In the loop, all the stricter rules sometimes left a job failing where the old rule had made it pass by breaking something else; my two declared aims conflicted there (log 40). Asked only whether anything was wrong, DeepSeek found the failure, but from the description of what the rule could see and ignored, not from the record of its mistakes: my control pointed at the answer (logs 41 and 42).

## Where DeepSeek sits in your semantics

- **A selected source of guesses.** Its history is text people wrote, so it is right where people wrote correctly and often, and wrong in the usual way where the world differs from common talk (the grudge).
- **Not the one that criticises or keeps.** What criticised was the world's answers, the checker running a model, and the program testing a rule on unseen occasions. What kept a change was the program's check against declared aims.
- **Construction, where it happened, was in the system:** the growing language (log 35) and the kept method (log 39) each needed a program to run the guess and a record to judge it by.
- This is what log 26 was built to test directly, and it has not been run.

## Claims of mine that went too far

- "Condition 2 stands up here" (log 34). That a fixed list of states cannot hold an unlimited count follows from an argument, not from the runs (log 36).
- "Binary counting is a small construction." Withdrawn: no record shows the history your semantics asks for (log 36).
- "Too big to write" (log 34). Binary counting made a big count cheap to write; the limit is where it breaks (log 35).
- "The loop's value is in choosing the right questions" (log 19), overturned in log 20: random questions helped as much.

## What people still supplied

Which method to open up, the test occasions and the aims (logs 39 to 42); the models in log 28 (written by Claude); the choice of every device, every world and every question asked of DeepSeek.

## Open questions

1. **Can the system find a failure from evidence alone?** Log 41's control hinted at the answer, and no clean test exists yet.
2. **Does feeding criticism back make DeepSeek defend its first answer, as you expect?** Built as log 26, not run.
3. **What to do when declared aims conflict** (log 40). Your semantics leaves the choice to whoever declares them.
4. **Is "hard to vary", or something doing its work, needed for correction to keep going** (logs 37 and 38)? You may choose to change the semantics here.
5. **Humanity as the universal explainer**, kept for later at your request (log 33).

## Next step

Run log 26, the attack surface. It is built and tested, it costs about $1 to $1.50 of the $14.08 left, and it tests open question 2 head on: whether DeepSeek, shown the world's answers to its own riskiest predictions, does better when a fresh DeepSeek rebuilds from the facts than when it is told "you predicted X; the world says Y".
