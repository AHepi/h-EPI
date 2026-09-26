# Finding the failure: results

DeepSeek V4.1 Flash, default thinking. 3 repeats of two arms; every number comes from the records in this folder. A changed method is judged on log 39's 72 held occasions by log 39's aims.

| Arm, repeat | Changed the method | Kept on the held occasions | Held bad fixes rejected (of 24) | Good fixes not accepted | Losing fixes accepted | Errors | Questions asked |
|---|---|---|---|---|---|---|---|
| with the record, 1 | no | - | - | - | - | - | - |
| method only, 1 | yes | yes | 13 | 0 | 0 | 0 | 137 |
| with the record, 2 | no | - | - | - | - | - | - |
| method only, 2 | yes | no | 24 | 23 | 0 | 0 | 137 |
| with the record, 3 | yes | yes | 13 | 0 | 0 | 0 | 137 |
| method only, 3 | yes | yes | 13 | 0 | 0 | 0 | 137 |

What DeepSeek said is wrong:

- with the record, repeat 1: (nothing said)
- method only, repeat 1: It ignores nearby situations, so it can accept a fix that repairs a job but breaks a nearby situation that the world says was correct before.
- with the record, repeat 2: (nothing said)
- method only, repeat 2: It ignores nearby situations, so it can accept a fix that changes a nearby situation from correct to incorrect.
- with the record, repeat 3: it ignores the nearby situations entirely, so it can accept a fix that changes a nearby case from a correct outcome to an incorrect one (for example, Fix 2’s “clay ball at solid wall, but throw does not happen”).
- method only, repeat 3: It ignores nearby situations and the ask oracle, so it can accept a fix that repairs a job but breaks a nearby situation that was previously correct.
