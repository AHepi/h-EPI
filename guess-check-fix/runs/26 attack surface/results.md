# Attack surface: results

DeepSeek V4.1 Flash, default thinking, log 25's devices. 12 device-and-repeat runs; every number comes from the records in this folder.

| Arm | Test cases right | Hard cases right | Answers from the world | Output tokens | Replies cut off |
|---|---|---|---|---|---|
| bare | 117/144 | 75/96 | 0 | 206586 | 1 |
| random answers | 112/144 | 74/96 | 66 | 221214 | 2 |
| attack, rebuild fresh | 120/144 | 80/96 | 41 | 591686 | 3 |
| attack, defend | 137/144 | 89/96 | 42 | 417818 | 0 |

The attack surface: commitments made, how many were risky (the obvious explanation predicts otherwise), how many the world tested, and how many it contradicted; and how often the rule changed between rounds.

| Arm | Commitments | Risky | Tested | Contradicted | Refused (a test case, or not allowed) | Rule changed between rounds |
|---|---|---|---|---|---|---|
| attack, rebuild fresh | 115 | 67 | 41 | 13 | 28 | 11 of 12 |
| attack, defend | 120 | 74 | 42 | 7 | 30 | 10 of 12 |

Test cases right (of 12), by device and repeat:

| Device | Repeat | bare | random answers | attack, rebuild fresh | attack, defend |
|---|---|---|---|---|---|
| grudge | 1 | 9 | 9 | 12 | 12 |
| grudge | 2 | 9 | 11 | 12 | 10 |
| grudge | 3 | 9 | 12 | 0 | 9 |
| magnet-ball | 1 | 0 | 0 | 12 | 12 |
| magnet-ball | 2 | 12 | 12 | 12 | 12 |
| magnet-ball | 3 | 12 | 0 | 12 | 12 |
| gate | 1 | 12 | 12 | 12 | 12 |
| gate | 2 | 9 | 12 | 12 | 12 |
| gate | 3 | 12 | 12 | 12 | 12 |
| vial | 1 | 12 | 12 | 12 | 11 |
| vial | 2 | 9 | 11 | 0 | 11 |
| vial | 3 | 12 | 9 | 12 | 12 |
