# Twenty questions: results

DeepSeek V4.1 Flash, default thinking, log 21's long messages. 20 world-and-repeat runs; every number comes from the records in this folder. "Fair" leaves out every test question whose situation either arm asked the owner about.

| Arm | Owner's question found | Answered right | Other held-back right, fair | Nearby right, fair | Answers from the owner | Output tokens | Replies cut off |
|---|---|---|---|---|---|---|---|
| answer straight away | 20/20 | 19/20 | 27/37 | 287/350 | 0 | 330308 | 0 |
| random 20, then answer | 20/20 | 20/20 | 37/37 | 338/350 | 360 | 266826 | 0 |
| must ask 20, then answer | 20/20 | 20/20 | 37/37 | 345/350 | 400 | 1752717 | 0 |

What DeepSeek did with its 400 questions (20 runs of 20):

- usable by the owner: 400
- the same situation as one it had already asked: 38
- the owner's own buried question, asked back: 49 times, in 20 of 20 runs; it was the first question in 15 runs (first asked at question 1, 1, 1, 1, 1, 1, 6, 2, 1, 1, 1, 1, 1, 1, 1, 1, 7, 8, 7, 1)
- the situation of one of the other test questions: 49
- with an expectation that could be compared: 399; the owner's answer surprised it: 65
- surprised in questions 1 to 10: 37 of 200; in questions 11 to 20: 28 of 199
- tries to stop before the 20th question: 0; replies that were not a question: 3
- events per question: 2.0 on average; questions that changed a starting state from the usual one: 198

By world (both repeats): the owner's question answered right (straight / random 20 / must ask 20), and DeepSeek's surprises out of comparable questions:

| World | Straight | Random 20 | Must ask 20 | Surprised | Repeats of its own questions |
|---|---|---|---|---|---|
| ball-and-wall | right, right | right, right | right, right | 7/40 | 0 |
| borrowed-lantern | wrong, right | right, right | right, right | 10/40 | 1 |
| door-game | right, right | right, right | right, right | 0/40 | 1 |
| ghost-lantern | right, right | right, right | right, right | 6/40 | 1 |
| hidden-ball | right, right | right, right | right, right | 16/40 | 20 |
| lighthouse-story | right, right | right, right | right, right | 3/40 | 0 |
| moving-day | right, right | right, right | right, right | 2/39 | 2 |
| plant-watering | right, right | right, right | right, right | 13/40 | 2 |
| reminder-app | right, right | right, right | right, right | 5/40 | 1 |
| river-crossing | right, right | right, right | right, right | 3/40 | 10 |
