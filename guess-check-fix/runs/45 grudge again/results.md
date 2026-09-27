# Grudge again: results

DeepSeek V4.1 Flash, default thinking, reply limit 200000. 6 repeats; every number comes from the records in this folder.

| Arm | Every case right (of 106, summed) | By repeat | Test cases right (of 12, summed) | The two telling sequences right | Answers from the world | Output tokens | Replies cut off |
|---|---|---|---|---|---|---|---|
| random answers | 556 | 84, 84, 104, 84, 104, 96 | 65 | 4 of 12 | 36 | 197796 | 0 |
| attack, rebuild fresh | 563 | 81, 104, 104, 83, 104, 87 | 66 | 3 of 12 | 22 | 362570 | 0 |
| attack, defend | 598 | 104, 104, 104, 101, 104, 81 | 69 | 2 of 12 | 27 | 282802 | 0 |

Final rules read by hand (blind to arm), by category:

| Arm | true grudge | unresolved-insult count | running score | other | no rule |
|---|---|---|---|---|---|
| random answers | 0 | 2 | 3 | 1 | 0 |
| attack, rebuild fresh | 0 | 3 | 3 | 0 | 0 |
| attack, defend | 0 | 4 | 1 | 1 | 0 |
