# Decisions

Every decision that shapes the project. The owner's decisions are quoted exactly. Routine choices Claude made are marked as such, with the reason, so they can be overturned. New decisions go at the bottom of their section.

## The owner's decisions

**O1. What the project is for.**
> "I wanted to combine these two somehow to allow small LLMs to plan, reason and execute. Not just code, but: write stories that work, comprehend vague user input, plan a video game with minimal coding skill, reason physically about cause and effect. The hard to vary is derived from the semantics."

**O2. What the tool must do, and what matters most.**
> "Right now, the two zip tools conflict rather than work together. I was hoping for an tool that can guess solutions, explore possibilities, and most importantly, error correct. Error correction is probably the single most important ability highlighted in the semantics. Can you help?"

**O3. Go-ahead to finish the new loop, run every test world, and deliver the files.**
> "Continue"

**O4. Run the work on Sonnet now; the small AI later.** (Log 15 and 16.)
> "Can you continue work of last model on Sonnet? Small model work comes later."

**O5. Finish the project on DeepSeek, error correction first.** (Log 17 and 18.)
> "Can you finish this project. Use Deepseek V4.1 Flash though. It needs to test for error correction foremost. The ability to supplement planning, problem solving, interpretating vague prose, creating stories, exploring creatively and so on. Hard to vary mixed with strata have mixed results. Can you take over."

**O6. Test against a baseline, and rule out more tokens.** (Log 19.)
> "Great! Test against baseline as well. And rule out the possibility that spending more tokens solves the problems."

**O7. Go ahead with the next step.** (Log 20.)
> "What's the guesser? I'm confused. Also go ahead."

**O8. Test long texts, a buried question, and the option to exit.** (Log 21.)
> "Can you verify that this translates to long texts? When you give it an embedded question, and it has to find it when give the option to exit a loop. If not, test that next."

**O9. Make it ask 20 questions first, and watch.** (Log 22.)
> "No. That's not smart enough. Get it to ask 20 questions first. See what it does"

**O10. Run the refusal test if the budget allows.** (Log 23.)
> "Is there enough budget? If so, do it."

**O11. Test error correction as the semantics means it.** (Log 25.)
> "My actual goal is error correction. This is a good start, but the semantics I gave you is about creativity, not spotting little semantic tricks. At the heart of creativity is error correction. Maybe go over the semantics to see what I'm actually testing. Then run a test that meets the standards. If anything, we know Deepseek has a limited knowledge base. But can we get it to solve a problem a bare run can't? Even with repeated loops. You have a small budget left. See what you can do."

**O12. Try an attack surface first; wait for a top-up before running.** (Log 26.)
> "Ok. Don't start yet until I top up. What about a series of commitments DeepSeek (ds) has to fill in that asks "what would it take to prove this conjecture is wrong". Error correction comes from spotting holes, sure. But it also comes from exposing your guesses to attack. A conjecture is worthless without an attack surface. So try that first. Try getting ds to imagine what it would take to refute a conjecturer. Or, actually, what it would take to cast doubt. You can't feed the conjecture and possible refutation back to Deepseek because it'll just "disagree", reject the attack and default to its first answer. Any thoughts? Go back to the semantics, see what it suggests given the type of generators LLMs actually are. Because that determines where it sits in this scheme. I'm now testing the semantics here."

**O13. Add the discussion to the story; fit causal relations into the checker, with a corpus; say what it presupposes.** (Logs 27 and 28.)
> "Yes please. Do that. And also see if you can fit causal relations into the checker. For this you will need a corpus of text. I'm not sure how you will select it though. Once you have a working checker, I'll be interested to know what it presupposes about causality."

**O14. Report a failure and why before changing it; say what worked and what may be overlooked.** (Log 29.)
> "Ok. But don't just randomly change a failure. Can you report what failed, and why you think it failed. If it works, can you tell me what worked and what may have been overlooked?"

**O15. A mini experiment on the system prompt and DeepSeek's questions; $20 topped up.** (Log 30.)
> "Can you do a mini experiment first then after remind me what we are talking about now. See if a system prompt injected into the top of context has any affect on the range and quality of questions ds asks. Play around with the system prompt, see if you notice patterns. $20 top up last night."

**O16. Try role-play.** (Log 32.)
> "What about role playing? Does that work?"

**O17. Test condition 2.** (Log 34.)
> "Do it!"

**O18. Test a language that grows.** (Log 35.)
> "Do it"

**O19. Read the revised semantics against the project.** (Log 36.)
> "Does this change anything?" (with the revised semantics attached)

**O20. The owner's pushback on finite states, and a question about the semantics.** (Log 37.)
> "I want to push back on your claim regarding log 34. Languages are combinatorial. There's no reason to believe it represents a finite number of states. Unless I'm misunderstanding you. Also, do you agree with the semantics or where do you disagree?"

**O21. Whether an agent must know "hard to vary" for it to count.** (Log 38.)
> "Hmm. That may be correct. The only reason I left it out was because the agent may not know the rule, or may never use it at all. But then that raises the question: can such an agent actually be creative? Having knowledge that something has occured and the fact that it occurs are two separate phenomenon. Is this what you mean?"

**O22. Test condition 6.** (Log 39.)
> "Do it!"

## Claude's routine choices

**C1. A new small language of things and rules, rather than extending Strata.** Strata refused cause-and-effect sentences (log 01), its instructions drop causes, and its checker answers "does this follow?" while the hard-to-vary tests need "what happens when something is changed?".

**C2. Keep Strata's lessons, not its code.** Kept: fill-in forms for small AIs; fix the word list first; every answer names what it rests on; the rule with more conditions wins; disagreements are reported, not allowed to break everything. Strata and the hard-to-vary skill stay unchanged.

**C3. The checker never guesses.** It only runs models and reports. Guessing belongs to the guesser; the checker's own searches are marked as fitted.

**C4. Time: after each event, everything settles before the next event.** Forced by log 04.

**C5. No backsliding.** A fix is kept only if it repairs at least one failing job and breaks none that passed. From the semantics' Repair condition (Part XI).

**C6. The checker applies small fixes itself; the guesser is asked only for new parts.** Forced by log 08.

**C7. When several fixes work equally, ask the world instead of picking.** The semantics says fitting on seen cases leaves unseen cases open (Derivation 3).

**C8. In the tests, a hidden true model stands in for the world or the owner.** In real use, the owner or a real experiment answers.

**C9. The small AI is Qwen 2.5, 1.5 billion size,** run locally with its replies held to the fill-in shape. Small enough to be a hard test; runs without an account.

**C10. Instructions to the guesser are positive only** (things to do), because the models the owner hands work to follow those more reliably.

**C11. Compare the ways of running from one shared first guess,** so differences come from the loop and not from a luckier guess.

**C12. Project name: "Guess Check Fix".**

**C13. The owner's word list is added to the model before fixing** (log 13).

**C14. The one-new-rule search runs only after the guesser's tries are used up, and its rules are marked fitted** (log 13).

**C15. Rebuild from the earlier chat's record, not from scratch** (log 15). Replaying the recorded text and changes keeps the project the same one the log describes; each change was checked to find its exact old text.

**C16. One word for the role: "guesser".** "Small AI" means Qwen 1.5B only; "Sonnet" means Claude Sonnet 4.6 only.

**C17. Sonnet runs in a page inside the chat, built from the same code files** (log 16). This computer has no account key. The build copies the files in unchanged, so the page runs the code the tests run.

**C18. Sonnet gets the same messages as the small AI, plus one sentence naming the reply shape** (log 16). The small AI's server held replies to a shape; nothing can hold Sonnet that way from the page. Sonnet's replies are capped at 1000 tokens by the page's connection, and cut-off replies are counted.

**C19. Clearing out: after a new part, the checker also tries the model without the old rules that disagree with it** (log 16). Forced by the loop refusing a right new part. Removing a rule is a variation the checker already uses, so this is selection, not guessing.

**C20. Keep the "rewrite from report" way for Sonnet.** A bigger model may be able to use the checker's report, which the small AI could not (log 14).

**C21. File numbers: the log entry that first created the file.** Rebuilt files keep their first number.

**C22. A small fix may swap a condition for one about a different thing** (log 17). Forced by the lighthouse story: "Mara lights the lamp" had to become "the lamp is dark", and no other one-step change reaches it. Such swaps rank after dropping a condition, so when both work equally the full loop asks the world to choose.

**C23. A fix is a guess too: the full loop cross-checks each checker fix with the world before keeping it** (log 17). One question per fix, about a situation not yet a job where the model before and after the fix disagree. From the hard-to-vary skill: "a fix is a new part too: try it on the case that forced it and on the cases it must leave alone".

**C24. The full loop looks for surprises** (log 17): questions to the world about situations one change from the jobs where the model takes a route no job takes, plus one poke per round at a thing no rule reads. From the theory's point that surprise needs an incomplete history (Derivation 4). The situations are chosen from the model and the jobs only; the world is not looked at until it is asked. The default question budget went from 8 to 12.

**C25. Every result lists the held-back jobs whose situation the world was asked about** (log 17), because a held-back job the world was asked about is no longer unseen.

**C26. Add "guesser fixes first"** (log 18). Forced by the river puzzle, where the checker's one-step patches passed every job and broke a right answer. DeepSeek, unlike the small AI, can use the checker's report (log 17), so it gets the first go.

**C27. Plant the mistakes by a fixed shuffle, not by hand** (log 18), so the test is not chosen to flatter any corrector. The two mistakes that need a new thing are written by hand and marked so. "Repaired" also requires no difference from the world in 400 nearby situations, so a repair that only fits the jobs does not count.

**C28. Add "self review"** (log 18): the guesser rereads the model against the request with no report. It is the only way besides asking the world that can find a hidden mistake.

**C29. Add "review first"** (log 18) to combine self review with guesser fixes first. Kept as a way of running, but it did not beat guesser fixes first: see log 18.

**C30. The project lives in the owner's h-EPI repository, folder `guess-check-fix`** (log 17), so it is not lost when the computer resets (log 15). It does not touch the repository's conformance harness.

**C31. The DeepSeek account key is read from the DEEPSEEK_API_KEY setting at each call, and never written into a file, a record or an error message** (log 17). The same rule as the h-EPI repository's own model key.

**C32. Same first guesses for a way added later** (log 18). The run script can reuse an earlier run's first guesses, so a way added later is compared on the same guesses (C11).

**C33. The baseline is DeepSeek alone, with the same information as the loop's first guess** (log 19): the request, the owner's word list and the shown jobs with their answers, answering the questions directly. Anything less would make the loop look better than it is.

**C34. One fixed set of questions for every arm** (log 19): the held-back jobs, and 20 nearby situations per world by a fixed shuffle. Held-back jobs about a particular step are left out for every arm, because "step" is the checker's own idea.

**C35. "More tokens" is tested three ways** (log 19): DeepSeek's thinking setting (lowest, default, highest), asking five times with a majority vote, and reviewing three times. Tokens are counted per call, so arms are compared at their real cost.

**C36. A cut-off reply is rerun with a higher limit, not counted against thinking harder** (log 19). The limit is this project's, not DeepSeek's.

**C37. Every comparison is also made leaving out the situations the loop asked the world about** (log 19), since the loop's answers there are information, not reasoning.

**C38. Test the choice of questions before building on it** (log 20). Log 19's next step assumed the loop's questions were what helped; the step was changed to compare the loop's questions with random ones and DeepSeek's own at the same number, before building "ask then answer" into the loop.

**C39. Random questions come from the same place as the loop's: situations one or two changes from the jobs, by a fixed shuffle that differs per repeat, never a test question** (log 20).

**C40. Three repeats, not two, for log 20**, because log 18 and 19 showed differences of about two between repeats.

**C41. The long message keeps the request's exact sentences and adds only filler that names nothing from any world** (log 21), so the long and short forms carry the same information and differ only in length and burying.

**C42. The embedded question is a held-back job chosen by a fixed shuffle, asked in the middle paragraph, and DeepSeek is told only to answer what the owner asks** (log 21). It is never told the question is buried.

**C43. "Found" means naming the same situation in exact names; misses are then read one by one** (log 21), because a strict check can refuse a question that was found in substance.

**C44. Six random questions for log 21's random arm**, fewer than log 20's nine or so, to leave room for the scarce-questions step.

**C45. The 20 questions are asked one at a time, each answer seen before the next, with DeepSeek's expectation stated each time** (log 22), so what it does can be watched: where it probes, and whether the answers surprise it.

**C46. Compared with 20 random questions and with answering straight away, on log 21's long messages** (log 22), and scored on the fair count, since DeepSeek may ask about test situations.

**C47. A refused question still uses up one of the 20, and a near copy is counted, not refused** (log 23), so DeepSeek's behaviour shows in the record rather than being shaped by extra rules.

**C48. The construction test gives every arm the same evidence and no way to ask for more** (log 25), so any difference comes from error correction, not information (the confound found in logs 19 and 20).

**C49. The devices are made up and each needs a hidden thing, checked offline before any run** (log 25): the observations refute the obvious explanation, and contain the same visible state and action leading to different outcomes, so no explanation using only what can be seen fits them. Test cases: 8 the obvious explanation gets wrong, 4 it gets right, picked by a fixed shuffle.

**C50. The plan and its conjectures are committed before the runs they are tested on** (log 25), including the sixth arm, which was designed after repeat 1 and is tested on repeats 2 and 3 only.

**C51. The hard-to-vary arm aims for the fewest parts the observations do not hold in place, not none** (log 25), because the true explanations themselves have up to two parts the observations happen not to test.

**C52. The attack lives outside DeepSeek** (log 26): its commitments are recorded before any test, the verdict is a mechanical comparison with the world's answer, and a fresh conversation gets only facts. The owner's expected failure, defending in the same conversation, is an arm of its own so it can be seen.

**C53. The attack-surface test gives every arm at most 6 answers from the world, and random answers as a control** (log 26), so a win for the attack surface is not just more information (the lesson of log 20).

**C54. Cause is asked by holding a thing, built on the checker's existing hold** (log 28), not by a new kind of rule, so the causal part only draws consequences the same way the checker always has.

**C55. The corpus is WIQA, picked by a fixed scramble, and not stored in the repository** (log 28): written and answered by other people before this project, with exactly "what if" questions; its licence is not stated where it is published, so only the picked ids, and what was made from them, are kept.

**C56. Claude plays translator, reader and direct answerer in separate conversations** (log 28), because DeepSeek waits on the top-up; the reader sees the model but not the paragraph, and none sees people's answers.

**C57. Any clash on or upstream of the thing asked about reads "unsettled"** (log 28): without sizes, the checker cannot weigh opposite pushes, and a run should not let the nearer push win by arriving first.

**C58. The universal language is JavaScript, run in a separate process with no files, network or account key, and a time limit** (log 34): DeepSeek writes it well, and anything it writes may reach whatever the process can.

**C59. Probes run after a result are kept and marked as such** (log 34): they check a gap the result revealed, and are never counted as planned tests.

**C60. A new kind's changes and tests are short JavaScript expressions, run in a separate process** (log 35): a kind needs something that can hold values the rule language cannot, and the process keeps it away from files, the network and the key.

**C61. The method opened up is fix acceptance, and a method may ask the world three questions per fix** (log 39): it has a known failure (log 17), a person's repair to compare with, and a tool the checker already has.

## Traps

- **Treating a routine choice as settled.** C1 to C61 are Claude's choices; any can be overturned. The ones forced by a failure say which log entry forced them.
- **Losing the owner's exact words.** Paraphrasing a decision changes it. Quote it.
