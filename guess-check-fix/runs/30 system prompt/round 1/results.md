# System prompt and questions: results

DeepSeek V4.1 Flash, default thinking, log 21's long messages, 10 questions a run. 70 runs; every number comes from the records in this folder. "Fair" leaves out every test question the run asked the pretend owner about.

| Arm | Runs | Different situations | Repeats | Things started differently | Events used | Events per question | Surprised / comparable | Owner's question asked back | Also asked by "nothing at the top" | Owner's question right | Held-back right, fair | Nearby right, fair | Output tokens |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| nothing at the top | 10 | 93 | 7 | 16 | 31 | 2.2 | 15/100 | 17 | - | 10/10 | 13/17 | 153/183 | 509973 |
| nothing at the top, again | 10 | 95 | 5 | 17 | 30 | 2.1 | 15/100 | 15 | 59 | 10/10 | 16/17 | 164/183 | 432993 |
| filler | 10 | 91 | 9 | 19 | 30 | 1.8 | 27/100 | 19 | 40 | 10/10 | 18/20 | 164/186 | 482704 |
| doubt | 10 | 92 | 8 | 19 | 28 | 1.9 | 18/100 | 16 | 46 | 10/10 | 17/20 | 156/182 | 513353 |
| spread | 10 | 96 | 4 | 19 | 30 | 1.7 | 19/100 | 11 | 47 | 10/10 | 15/18 | 149/182 | 544867 |
| explain | 10 | 95 | 5 | 17 | 31 | 1.9 | 24/100 | 15 | 47 | 10/10 | 18/19 | 171/182 | 599910 |
| detective | 10 | 91 | 9 | 23 | 30 | 1.9 | 29/100 | 16 | 47 | 10/10 | 16/19 | 158/185 | 583344 |

Different situations asked, by world:

| World | nothing at the top | nothing at the top, again | filler | doubt | spread | explain | detective |
|---|---|---|---|---|---|---|---|
| ball-and-wall | 10 | 10 | 9 | 10 | 10 | 10 | 10 |
| hidden-ball | 6 | 7 | 3 | 5 | 7 | 6 | 3 |
| door-game | 10 | 9 | 10 | 10 | 10 | 10 | 10 |
| lighthouse-story | 10 | 10 | 10 | 10 | 10 | 10 | 9 |
| reminder-app | 10 | 10 | 10 | 10 | 10 | 10 | 10 |
| moving-day | 9 | 9 | 10 | 10 | 10 | 10 | 10 |
| river-crossing | 9 | 10 | 9 | 10 | 10 | 10 | 9 |
| plant-watering | 10 | 10 | 10 | 9 | 9 | 9 | 10 |
| borrowed-lantern | 9 | 10 | 10 | 9 | 10 | 10 | 10 |
| ghost-lantern | 10 | 10 | 10 | 9 | 10 | 10 | 10 |
