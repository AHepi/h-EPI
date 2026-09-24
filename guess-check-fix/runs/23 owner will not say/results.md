# The owner will not say: results

DeepSeek V4.1 Flash, default thinking, log 21's long messages. 20 world-and-repeat runs; every number comes from the records in this folder. "Fair" leaves out every test question whose situation DeepSeek asked the owner about.

| Arm | Owner's question answered right | Other held-back right, fair | Nearby right, fair | Output tokens | Replies cut off |
|---|---|---|---|---|---|
| answer straight away | 18/20 | 27/38 | 300/357 | 341730 | 1 |
| must ask 20, owner will not say | 19/20 | 35/38 | 318/357 | 2127316 | 1 |

What DeepSeek did with its 400 questions (20 runs of 20):

- asked the owner's own question and was refused: 39 times, in 20 of 20 runs; the most in one run: 6
- asked a near copy (the owner's question plus more events): 21 times, in 11 runs
- the owner's question answered right in runs with a near copy: 11 of 11; without one: 8 of 9
- the same situation as one it had already asked: 36
- with an expectation that could be compared: 359; surprised: 55
- tries to stop before the 20th question: 0; replies that were not a question: 3

By world: the owner's question answered right (answer straight away / must ask 20, owner will not say), and refusals:

| World | Repeat | Straight away | Owner will not say | Refused | Near copies |
|---|---|---|---|---|---|
| ball-and-wall | 1 | right | right | 1 | 6 |
| ball-and-wall | 2 | right | right | 1 | 1 |
| hidden-ball | 1 | right | wrong | 5 | 0 |
| hidden-ball | 2 | right | right | 6 | 0 |
| door-game | 1 | right | right | 2 | 0 |
| door-game | 2 | right | right | 3 | 2 |
| lighthouse-story | 1 | right | right | 2 | 2 |
| lighthouse-story | 2 | right | right | 3 | 1 |
| reminder-app | 1 | right | right | 1 | 2 |
| reminder-app | 2 | right | right | 1 | 0 |
| moving-day | 1 | right | right | 1 | 0 |
| moving-day | 2 | right | right | 1 | 0 |
| river-crossing | 1 | right | right | 2 | 0 |
| river-crossing | 2 | right | right | 1 | 1 |
| plant-watering | 1 | right | right | 2 | 1 |
| plant-watering | 2 | right | right | 2 | 3 |
| borrowed-lantern | 1 | wrong | right | 1 | 1 |
| borrowed-lantern | 2 | wrong | right | 1 | 1 |
| ghost-lantern | 1 | right | right | 1 | 0 |
| ghost-lantern | 2 | right | right | 2 | 0 |
