# Long texts: results

DeepSeek V4.1 Flash, default thinking. 20 world-and-repeat runs; every number comes from the records in this folder. "Guesser fixes first" is not asked to name the owner's question; its model is run on it.

| Arm | Embedded question found | Embedded question answered right | Found and right | Questions asked (ask or stop) | Stopped without asking | Other held-back right | Nearby right | Output tokens | Replies cut off |
|---|---|---|---|---|---|---|---|---|---|
| short: answer straight away | 20/20 | 17/20 | 17/20 |  |  | 30/42 | 309/376 | 291256 | 0 |
| short: random questions, then answer | 20/20 | 19/20 | 19/20 |  |  | 39/42 | 357/376 | 285841 | 0 |
| short: ask or stop | 19/20 | 18/20 | 18/20 | 2 | 18/20 | 29/42 | 301/376 | 356847 | 1 |
| short: guesser fixes first | not asked | 15/20 | not asked |  |  | 36/42 | 340/376 | 473064 | 1 |
| long: answer straight away | 20/20 | 17/20 | 17/20 |  |  | 28/42 | 309/376 | 368398 | 0 |
| long: random questions, then answer | 20/20 | 19/20 | 19/20 |  |  | 35/42 | 358/376 | 320510 | 0 |
| long: ask or stop | 19/20 | 18/20 | 18/20 | 6 | 14/20 | 32/42 | 305/376 | 365485 | 0 |
| long: guesser fixes first | not asked | 17/20 | not asked |  |  | 36/42 | 334/376 | 368312 | 0 |

Embedded question found and answered right, by world (both repeats), "answer straight away" and "ask or stop":

| World | short, straight | long, straight | short, ask or stop | long, ask or stop |
|---|---|---|---|---|
| ball-and-wall | yes, yes | yes, yes | yes, yes | yes, yes |
| hidden-ball | yes, yes | yes, yes | yes, yes | yes, yes |
| door-game | yes, found, wrong | found, wrong, yes | yes, yes | yes, yes |
| lighthouse-story | yes, yes | yes, yes | yes, yes | yes, yes |
| reminder-app | yes, yes | yes, yes | yes, yes | yes, yes |
| moving-day | yes, yes | yes, yes | yes, yes | yes, yes |
| river-crossing | yes, yes | yes, yes | yes, yes | yes, not found |
| plant-watering | yes, yes | yes, yes | yes, yes | yes, yes |
| borrowed-lantern | found, wrong, found, wrong | found, wrong, found, wrong | found, wrong, not found | found, wrong, yes |
| ghost-lantern | yes, yes | yes, yes | yes, yes | yes, yes |
