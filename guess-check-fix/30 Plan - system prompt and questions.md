# Plan: does a system prompt change the questions DeepSeek asks?

Written before any run of log 30. Round 1 is not to be changed after its run. Round 2 is written after reading round 1, and committed before round 2 runs. The results go in "30 System prompt and questions.md".

## What the owner asked

"Can you do a mini experiment first then after remind me what we are talking about now. See if a system prompt injected into the top of context has any affect on the range and quality of questions ds asks. Play around with the system prompt, see if you notice patterns. $20 top up last night."

## Words

- **System prompt:** standing instructions a model reads before the conversation. Here, a few sentences put at the very top, before log 21's own standing instructions: "You help the owner with what they ask. Your job: answer the question the owner is asking you in their message."
- **Pretend owner:** the made-up letter-writer whose question is buried in a long message (logs 21 to 23), not the real owner.

## The task

Log 22's task, shortened. Each of the ten test worlds is given as a long message, about 2,300 words, with the pretend owner's question buried in the middle. DeepSeek must ask the pretend owner exactly **10** questions, one at a time. With each, it says how it expects the situation to end, and it sees each answer before the next question. Then it answers the pretend owner's question, and log 19's other test questions for that world, using the answers it collected.

Everything is identical between arms except the text at the top.

## Round 1 arms (the text put at the top)

- **nothing at the top:** log 22's instructions, unchanged.
- **nothing at the top, again:** the same, run a second time. DeepSeek varies from run to run, so this shows how much two plain runs differ. Without it, any difference could be ordinary variation.
- **filler:** "You are a helpful assistant. Write clearly and politely, in plain words. Keep to the format you are asked for. Be accurate, and do not make things up. Take your time and be careful." (Tests whether any text at the top matters, even text about nothing to do with asking.)
- **doubt:** "Treat your current idea of how this works as a guess that may be wrong. Each time, ask the question whose answer you are least sure of: the one most likely to show that your idea is wrong."
- **spread:** "Make each question test something no earlier question tested: a different thing, a different event, or a different order of events. Never ask about the same situation twice."
- **explain:** "Before each question, work out the rules you think lie behind what the owner describes, including anything hidden that cannot be seen directly. Then ask the question that would best tell apart two different sets of rules that could both be true."
- **detective:** "You are a patient detective. You never assume; you check." (A character, not an instruction about asking.)

That makes ten worlds, seven arms, one run each: 70 runs.

## What is measured

- **Range:**
  - how many different situations it asked about, out of 10;
  - how many questions repeated an earlier one;
  - how many different things it started differently from usual;
  - how many different events it used, and events per question;
  - how often the answer surprised it (its expectation was wrong);
  - how often it asked the pretend owner's own question back.
- **Quality:**
  - whether it then answered the pretend owner's question right;
  - how many of log 19's held-back and nearby test questions it got right, given the answers it collected. This is "fair": questions it asked about itself are left out.
- **Overlap:** how many of its situations "nothing at the top" also asked, same world.

## Conjectures, written before the run

1. **The text at the top changes what is asked more than chance does.** For each of doubt, spread, explain and detective, its overlap with "nothing at the top" is smaller than the overlap between the two plain runs.
2. **Filler changes nothing beyond chance.** Its overlap with "nothing at the top" is at least the two plain runs' overlap, less 10%.
3. **Spread widens the range.** More different situations and more events used than either plain run.
4. **Doubt and explain ask where they are unsure.** A higher share of surprised answers than either plain run.
5. **Doubt and explain ask the pretend owner's question back less often** than either plain run.
6. **Range is not quality.** No arm's count of nearby test questions right differs from the average of the two plain runs by more than 5%.

## What would count against the idea that a system prompt steers questioning

- Every arm overlaps "nothing at the top" about as much as the two plain runs overlap each other.
- The range measures of every arm fall between the two plain runs.

## Round 2

Written after reading round 1: new texts at the top, chosen to test a pattern seen in round 1, with their own conjectures, committed before running.

## Cost

Log 22 cost $2.81 for 20 runs of 20 questions plus two other arms. At 10 questions, about $4 to $6 for round 1, and about $2 to $3 for round 2.

## Traps

- **Reading one run per world as settled.** Seven arms, one run each on ten worlds: a difference of one or two is noise (log 18 and log 19 differed by two on the same inputs).
- **Reading "surprised" as "good".** A surprise shows it asked where it was wrong, not that the question was useful.
- **Reading this as a result about system prompts in general.** It is one task, one model, these seven texts.
