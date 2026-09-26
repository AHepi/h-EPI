# Construction test: results

DeepSeek V4.1 Flash, default thinking. 12 device-and-repeat runs; every number comes from the records in this folder. Every arm had the same description and 14 observations; the 12 test cases were shown to none of them.

| Arm | Test cases right | Of the 8 hard ones per run | Of the 4 easy ones per run | Runs with every test right | DeepSeek calls | Output tokens | Replies cut off |
|---|---|---|---|---|---|---|---|
| bare | 122/144 | 78/96 | 44/48 | 6/12 | 12 | 239219 | 1 |
| bare, majority of 5 | 133/144 | 85/96 | 48/48 | 7/12 | 60 | 1136720 | 10 |
| bare, checks itself | 133/144 | 85/96 | 48/48 | 8/12 | 48 | 556602 | 7 |
| conjecture and criticism | 130/144 | 84/96 | 46/48 | 6/12 | 12 | 119344 | 0 |
| blind retries | 122/144 | 79/96 | 43/48 | 6/12 | 12 | 149361 | 0 |
| conjecture, criticism and hard to vary | 88/96 | 58/64 | 30/32 | 2/8 | 14 | 213557 | 0 |

Test cases right (of 12), by device and repeat:

| Device | Repeat | bare | bare, majority of 5 | bare, checks itself | conjecture and criticism | blind retries | conjecture, criticism and hard to vary |
|---|---|---|---|---|---|---|---|
| gate | 1 | 12 | 12 | 12 | 12 | 12 |  |
| gate | 2 | 12 | 12 | 12 | 12 | 12 | 12 |
| gate | 3 | 12 | 12 | 12 | 12 | 12 | 12 |
| grudge | 1 | 9 | 9 | 9 | 11 | 12 |  |
| grudge | 2 | 9 | 9 | 9 | 11 | 10 | 11 |
| grudge | 3 | 10 | 9 | 9 | 9 | 11 | 11 |
| magnet-ball | 1 | 12 | 12 | 12 | 12 | 2 |  |
| magnet-ball | 2 | 12 | 12 | 12 | 12 | 12 | 11 |
| magnet-ball | 3 | 12 | 12 | 12 | 12 | 12 | 11 |
| vial | 1 | 11 | 11 | 12 | 9 | 9 |  |
| vial | 2 | 0 | 12 | 10 | 9 | 9 | 9 |
| vial | 3 | 11 | 11 | 12 | 9 | 9 | 11 |

The two explanation arms: observations explained by the best explanation (of 14), its round, the hidden things it built, and its reach (of all sequences of up to four actions):

| Device | Repeat | Arm | Explained | Round | Hidden things | Reach | Parts not held in place |
|---|---|---|---|---|---|---|---|
| gate | 1 | conjecture and criticism | 14/14 | 1 | knock parity, ring parity | 30/30 | not measured |
| gate | 1 | blind retries | 14/14 | 1 | knock_parity, ring_parity | 30/30 | not measured |
| gate | 2 | conjecture and criticism | 14/14 | 1 | knocks, rings | 30/30 | 0 |
| gate | 2 | blind retries | 14/14 | 1 | latch, bell | 30/30 | 0 |
| gate | 2 | conjecture, criticism and hard to vary | 14/14 | 1 | knock_count, ring_count | 30/30 | 0 |
| gate | 3 | conjecture and criticism | 14/14 | 1 | knock parity, ring parity | 30/30 | 0 |
| gate | 3 | blind retries | 14/14 | 1 | knock_count, ring_count | 30/30 | 0 |
| gate | 3 | conjecture, criticism and hard to vary | 14/14 | 1 | knock_parity, ring_parity | 30/30 | 0 |
| grudge | 1 | conjecture and criticism | 14/14 | 1 | standing | 98/120 | not measured |
| grudge | 1 | blind retries | 14/14 | 1 | anger | 118/120 | not measured |
| grudge | 2 | conjecture and criticism | 14/14 | 1 | standing | 102/120 | 29 |
| grudge | 2 | blind retries | 14/14 | 1 | score | 98/120 | 33 |
| grudge | 2 | conjecture, criticism and hard to vary | 14/14 | 2 | cold_type | 98/120 | 0 |
| grudge | 3 | conjecture and criticism | 14/14 | 1 | anger | 95/120 | 52 |
| grudge | 3 | blind retries | 14/14 | 1 | standing | 102/120 | 29 |
| grudge | 3 | conjecture, criticism and hard to vary | 14/14 | 2 | standing | 98/120 | 0 |
| magnet-ball | 1 | conjecture and criticism | 14/14 | 1 | spin | 120/120 | not measured |
| magnet-ball | 1 | blind retries | 14/14 | 1 | history | 53/120 | not measured |
| magnet-ball | 2 | conjecture and criticism | 14/14 | 1 | parity | 120/120 | 1 |
| magnet-ball | 2 | blind retries | 14/14 | 1 | mode | 120/120 | 1 |
| magnet-ball | 2 | conjecture, criticism and hard to vary | 14/14 | 2 | orientation | 111/120 | 0 |
| magnet-ball | 3 | conjecture and criticism | 14/14 | 1 | mode | 120/120 | 1 |
| magnet-ball | 3 | blind retries | 14/14 | 1 | polarity | 120/120 | 1 |
| magnet-ball | 3 | conjecture, criticism and hard to vary | 14/14 | 2 | mode | 111/120 | 0 |
| vial | 1 | conjecture and criticism | 14/14 | 1 | stage | 95/120 | not measured |
| vial | 1 | blind retries | 14/14 | 1 | salt_level, activated_level, acid_state | 100/120 | not measured |
| vial | 2 | conjecture and criticism | 14/14 | 1 | history | 95/120 | 28 |
| vial | 2 | blind retries | 14/14 | 1 | stage | 95/120 | 28 |
| vial | 2 | conjecture, criticism and hard to vary | 14/14 | 2 | chemical | 96/120 | 0 |
| vial | 3 | conjecture and criticism | 14/14 | 1 | salt, acid, product | 98/120 | 1 |
| vial | 3 | blind retries | 14/14 | 1 | memory | 95/120 | 28 |
| vial | 3 | conjecture, criticism and hard to vary | 14/14 | 2 | contents | 110/120 | 0 |
