# Who picks the questions: results

DeepSeek V4.1 Flash, default thinking. 30 world-and-repeat runs; every number comes from the records in this folder. "Fair" leaves out every test question whose situation any arm asked the world about.

| Arm | Held-back right | Nearby right | Held-back right, asked-about left out | Nearby right, asked-about left out | Answers from the world given | Output tokens |
|---|---|---|---|---|---|---|
| guesser fixes first | 77/93 | 482/564 | 49/65 | 462/543 | (its own questions) | 558330 |
| DeepSeek alone | 77/93 | 469/564 | 54/65 | 452/543 | 0 | 391757 |
| ask then answer (the loop picks the questions) | 83/93 | 536/564 | 55/65 | 516/543 | 270 | 333408 |
| random questions, then answer | 88/93 | 543/564 | 60/65 | 524/543 | 262 | 346176 |
| DeepSeek picks questions, then answer | 84/93 | 508/564 | 57/65 | 488/543 | 270 | 827524 |

Fair count by world (held-back and nearby right together):

| world | guesser fixes first | DeepSeek alone | ask then answer (the loop picks the questions) | random questions, then answer | DeepSeek picks questions, then answer |
|---|---|---|---|---|---|
| ball-and-wall | 44 | 45 | 45 | 52 | 47 |
| borrowed-lantern | 57 | 42 | 60 | 60 | 60 |
| door-game | 64 | 64 | 64 | 64 | 64 |
| ghost-lantern | 62 | 57 | 66 | 63 | 66 |
| hidden-ball | 14 | 14 | 14 | 14 | 14 |
| lighthouse-story | 57 | 62 | 63 | 66 | 66 |
| moving-day | 65 | 60 | 69 | 69 | 59 |
| plant-watering | 56 | 71 | 69 | 72 | 69 |
| reminder-app | 58 | 64 | 58 | 61 | 65 |
| river-crossing | 34 | 27 | 63 | 63 | 35 |

Fair count by repeat (held-back and nearby right together):

| repeat | guesser fixes first | DeepSeek alone | ask then answer (the loop picks the questions) | random questions, then answer | DeepSeek picks questions, then answer |
|---|---|---|---|---|---|
| repeat 1 | 174 | 169 | 192 | 197 | 172 |
| repeat 2 | 172 | 170 | 191 | 194 | 184 |
| repeat 3 | 165 | 167 | 188 | 193 | 189 |
