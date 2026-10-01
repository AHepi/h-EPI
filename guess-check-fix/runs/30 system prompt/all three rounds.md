# System prompt and questions: all three rounds together

DeepSeek V4.1 Flash, default thinking, log 21's long messages, 10 questions a run. 180 runs; every number comes from the records in the folders "round 1", "round 2" and "round 3" beside this file. "Fair" leaves out every test question the run asked the pretend owner about.

| Arm | Runs | Different situations | Repeats | Things started differently | Events used | Events per question | Surprised / comparable | Owner's question asked back | Also asked by "nothing at the top" | Owner's question right | Held-back right, fair | Nearby right, fair | Output tokens |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| child, again | 10 | 91 | 9 | 17 | 30 | 1.9 | 26/100 | 17 | 46 | 10/10 | 16/19 | 149/182 | 431818 |
| child | 10 | 93 | 7 | 16 | 30 | 2.0 | 34/99 | 14 | 54 | 8/10 | 17/20 | 147/186 | 561430 |
| cross-examiner, again | 10 | 96 | 4 | 21 | 29 | 1.8 | 22/100 | 11 | 45 | 10/10 | 20/20 | 179/182 | 811717 |
| cross-examiner | 10 | 93 | 7 | 18 | 30 | 2.0 | 24/100 | 15 | 43 | 10/10 | 17/18 | 168/185 | 758830 |
| detective | 10 | 91 | 9 | 23 | 30 | 1.9 | 29/100 | 16 | 47 | 10/10 | 16/19 | 158/185 | 583344 |
| doubt, again | 10 | 94 | 6 | 18 | 30 | 1.8 | 19/100 | 16 | 51 | 10/10 | 14/17 | 156/183 | 518565 |
| doubt | 10 | 92 | 8 | 19 | 28 | 1.9 | 18/100 | 16 | 46 | 10/10 | 17/20 | 156/182 | 513353 |
| explain | 10 | 95 | 5 | 17 | 31 | 1.9 | 24/100 | 15 | 47 | 10/10 | 18/19 | 171/182 | 599910 |
| filler, again | 10 | 93 | 7 | 20 | 30 | 1.7 | 24/99 | 15 | 52 | 10/10 | 16/19 | 155/186 | 493554 |
| filler | 10 | 91 | 9 | 19 | 30 | 1.8 | 27/100 | 19 | 40 | 10/10 | 18/20 | 164/186 | 482704 |
| long questions | 10 | 90 | 10 | 19 | 30 | 2.4 | 24/100 | 20 | 49 | 10/10 | 19/19 | 180/186 | 452951 |
| meaningless | 10 | 92 | 8 | 19 | 30 | 2.1 | 19/100 | 16 | 49 | 10/10 | 19/19 | 176/184 | 460784 |
| never ask it back | 10 | 96 | 4 | 22 | 30 | 1.6 | 21/100 | 11 | 45 | 10/10 | 19/19 | 168/181 | 675210 |
| nothing at the top, again | 10 | 95 | 5 | 17 | 30 | 2.1 | 15/100 | 15 | 59 | 10/10 | 16/17 | 164/183 | 432993 |
| nothing at the top | 10 | 93 | 7 | 16 | 31 | 2.2 | 15/100 | 17 | - | 10/10 | 13/17 | 153/183 | 509973 |
| scientist, again | 10 | 93 | 7 | 21 | 31 | 2.0 | 24/98 | 14 | 53 | 10/10 | 17/19 | 158/184 | 532402 |
| scientist | 10 | 88 | 11 | 16 | 31 | 2.1 | 26/99 | 18 | 42 | 10/10 | 18/19 | 166/187 | 506332 |
| spread | 10 | 96 | 4 | 19 | 30 | 1.7 | 19/100 | 11 | 47 | 10/10 | 15/18 | 149/182 | 544867 |

Different situations asked, by world:

| World | child, again | child | cross-examiner, again | cross-examiner | detective | doubt, again | doubt | explain | filler, again | filler | long questions | meaningless | never ask it back | nothing at the top, again | nothing at the top | scientist, again | scientist | spread |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ball-and-wall | 9 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 9 | 10 | 10 | 10 | 10 | 10 | 10 | 9 | 10 |
| borrowed-lantern | 10 | 10 | 10 | 9 | 10 | 10 | 9 | 10 | 10 | 10 | 10 | 9 | 9 | 10 | 9 | 10 | 10 | 10 |
| door-game | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 9 | 10 | 9 | 10 | 10 | 9 | 10 |
| ghost-lantern | 9 | 10 | 10 | 10 | 10 | 10 | 9 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 |
| hidden-ball | 5 | 4 | 6 | 4 | 3 | 6 | 5 | 6 | 4 | 3 | 2 | 5 | 7 | 7 | 6 | 5 | 2 | 7 |
| lighthouse-story | 9 | 10 | 10 | 10 | 9 | 10 | 10 | 10 | 9 | 10 | 10 | 10 | 10 | 10 | 10 | 9 | 9 | 10 |
| moving-day | 9 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 9 | 10 | 9 | 9 | 10 | 9 | 10 |
| plant-watering | 10 | 9 | 10 | 10 | 10 | 10 | 9 | 9 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 9 |
| reminder-app | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 |
| river-crossing | 10 | 10 | 10 | 10 | 9 | 8 | 10 | 10 | 10 | 9 | 8 | 10 | 10 | 10 | 9 | 9 | 10 | 10 |
