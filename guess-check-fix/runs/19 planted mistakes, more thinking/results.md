# Planted mistakes: results

32 planted mistakes, guesser deepseek-flash. Every number below comes from the records in this folder.

## visible mistakes (10)

| Corrector | repaired | better | unchanged | worse | failed to run | DeepSeek asked, in total | Questions to the world, in total | DeepSeek output tokens, in total |
|---|---|---|---|---|---|---|---|---|
| self review | 5 | 5 | 0 | 0 | 0 | 10 | 0 | 108945 |
| guesser fixes first | 10 | 0 | 0 | 0 | 0 | 11 | 111 | 42958 |
| self review, max thinking | 3 | 4 | 2 | 1 | 0 | 10 | 0 | 184414 |
| self review, three rounds | 2 | 6 | 0 | 2 | 0 | 30 | 0 | 505563 |
| guesser fixes first, max thinking | 10 | 0 | 0 | 0 | 0 | 11 | 108 | 69410 |
| self review, max thinking, reply limit 200,000 | 5 | 4 | 0 | 1 | 0 | 10 | 0 | 147698 |

## hidden mistakes (20)

| Corrector | repaired | better | unchanged | worse | failed to run | DeepSeek asked, in total | Questions to the world, in total | DeepSeek output tokens, in total |
|---|---|---|---|---|---|---|---|---|
| self review | 9 | 5 | 2 | 4 | 0 | 20 | 0 | 301815 |
| guesser fixes first | 13 | 2 | 5 | 0 | 0 | 16 | 216 | 74252 |
| self review, max thinking | 13 | 1 | 2 | 4 | 0 | 20 | 0 | 335155 |
| self review, three rounds | 7 | 10 | 0 | 3 | 0 | 60 | 0 | 963717 |
| guesser fixes first, max thinking | 14 | 1 | 5 | 0 | 0 | 15 | 210 | 86184 |
| self review, max thinking, reply limit 200,000 | 11 | 5 | 1 | 3 | 0 | 20 | 0 | 440414 |

## needs a new thing mistakes (2)

| Corrector | repaired | better | unchanged | worse | failed to run | DeepSeek asked, in total | Questions to the world, in total | DeepSeek output tokens, in total |
|---|---|---|---|---|---|---|---|---|
| self review | 0 | 0 | 1 | 1 | 0 | 2 | 0 | 26615 |
| guesser fixes first | 1 | 0 | 0 | 1 | 0 | 3 | 11 | 32383 |
| self review, max thinking | 0 | 0 | 1 | 1 | 0 | 2 | 0 | 35199 |
| self review, three rounds | 0 | 0 | 2 | 0 | 0 | 6 | 0 | 104292 |
| guesser fixes first, max thinking | 1 | 0 | 0 | 1 | 0 | 3 | 11 | 23421 |
| self review, max thinking, reply limit 200,000 | 0 | 0 | 2 | 0 | 0 | 2 | 0 | 33559 |

## Every planted mistake

Each cell: held-back jobs passed, then nearby situations that differ from the world (before correction: the "planted" column).

| World | Kind | Mistake | Planted | self review | guesser fixes first | self review, max thinking | self review, three rounds | guesser fixes first, max thinking | self review, max thinking, reply limit 200,000 |
|---|---|---|---|---|---|---|---|---|---|
| ball-and-wall | visible | in rule "throwing": condition "ball is in hand" changed to "ball is back in hand" | 1/3, 42 | 3/3, 0 (repaired) | 3/3, 0 (repaired) | 3/3, 10 (better) | 3/3, 10 (better) | 3/3, 0 (repaired) | 3/3, 0 (repaired) |
| ball-and-wall | hidden | in rule "passing through": condition "wall is holed" replaced by "material is rubber" | 2/3, 13 | 3/3, 0 (repaired) | 3/3, 0 (repaired) | 3/3, 0 (repaired) | 3/3, 0 (repaired) | 3/3, 0 (repaired) | 3/3, 0 (repaired) |
| ball-and-wall | hidden | in rule "passing through": condition "ball is flying" replaced by "material is rubber" | 2/3, 22 | 3/3, 0 (repaired) | 3/3, 0 (repaired) | 3/3, 0 (repaired) | 3/3, 10 (better) | 3/3, 0 (repaired) | 3/3, 0 (repaired) |
| borrowed-lantern | visible | in rule "lending": condition "ada is on the road" changed to "ada is lost" | 2/3, 278 | 2/3, 52 (better) | 3/3, 0 (repaired) | 3/3, 11 (better) | 2/3, 52 (better) | 3/3, 0 (repaired) | 2/3, 52 (better) |
| borrowed-lantern | hidden | in rule "lending": condition "ada is on the road" left out | 2/3, 59 | 3/3, 11 (better) | 3/3, 0 (repaired) | 1/3, 111 (worse) | 2/3, 52 (better) | 3/3, 0 (repaired) | 3/3, 11 (better) |
| borrowed-lantern | hidden | in rule "lost in the dark": condition "ada is on the road" replaced by "stranger is at home" | 2/3, 94 | 3/3, 11 (better) | 3/3, 0 (repaired) | 3/3, 0 (repaired) | 2/3, 52 (better) | 2/3, 52 (better) | 3/3, 0 (repaired) |
| door-game | visible | in rule "take key": condition "pick up key happens" replaced by "lives is 1" | 1/3, 302 | 3/3, 0 (repaired) | 3/3, 0 (repaired) | 3/3, 0 (repaired) | 3/3, 0 (repaired) | 3/3, 0 (repaired) | 3/3, 0 (repaired) |
| door-game | hidden | in rule "win": condition "door is open" replaced by "key is carried" | 2/3, 65 | 3/3, 0 (repaired) | 3/3, 0 (repaired) | 3/3, 0 (repaired) | 3/3, 0 (repaired) | 3/3, 0 (repaired) | 3/3, 0 (repaired) |
| door-game | hidden | in rule "unlock": condition "use door happens" left out | 2/3, 55 | 3/3, 0 (repaired) | 3/3, 0 (repaired) | 3/3, 0 (repaired) | 3/3, 0 (repaired) | 3/3, 0 (repaired) | 3/3, 0 (repaired) |
| ghost-lantern | visible | in rule "win": condition "game is playing" replaced by "lives is 0" | 2/4, 178 | 3/4, 40 (better) | 4/4, 0 (repaired) | 2/4, 178 (unchanged) | 3/4, 40 (better) | 4/4, 0 (repaired) | 3/4, 40 (better) |
| ghost-lantern | hidden | in rule "light the lantern": condition "key is carried" left out | 3/4, 39 | 3/4, 40 (worse) | 3/4, 38 (better) | 3/4, 40 (worse) | 3/4, 40 (worse) | 4/4, 0 (repaired) | 3/4, 40 (worse) |
| ghost-lantern | hidden | in rule "take key": condition "key is on floor" replaced by "lives is 2" | 2/4, 56 | 3/4, 40 (better) | 4/4, 0 (repaired) | 3/4, 40 (better) | 3/4, 40 (better) | 4/4, 0 (repaired) | 3/4, 40 (better) |
| hidden-ball | visible | in rule "see 4": condition "place is 4" changed to "place is 1" | 0/3, 10 | 3/3, 0 (better) | 3/3, 0 (repaired) | 3/3, 0 (better) | 3/3, 0 (better) | 3/3, 0 (repaired) | 3/3, 0 (repaired) |
| hidden-ball | hidden | in rule "see 1": result "seen is at 1" changed to "seen is nothing" | 2/3, 0 | 2/3, 0 (unchanged) | 2/3, 0 (unchanged) | 3/3, 0 (repaired) | 3/3, 0 (repaired) | 2/3, 0 (unchanged) | 2/3, 0 (unchanged) |
| hidden-ball | hidden | rule "see 2" removed | 2/3, 0 | 3/3, 0 (repaired) | 2/3, 0 (unchanged) | 2/3, 0 (unchanged) | 3/3, 0 (repaired) | 2/3, 0 (unchanged) | 3/3, 0 (repaired) |
| hidden-ball | needs a new thing | no "where the ball really is": what is seen follows only what was seen before | 2/3, 3 | 2/3, 3 (unchanged) | 3/3, 0 (repaired) | 2/3, 3 (unchanged) | 2/3, 3 (unchanged) | 3/3, 0 (repaired) | 2/3, 3 (unchanged) |
| lighthouse-story | visible | in rule "stays": condition "mara is at lighthouse" changed to "mara is staying for good" | 2/2, 149 | 2/2, 0 (repaired) | 2/2, 0 (repaired) | 2/2, 0 (repaired) | 2/2, 0 (repaired) | 2/2, 0 (repaired) | 2/2, 0 (repaired) |
| lighthouse-story | hidden | in rule "leaves": condition "mara is at lighthouse" replaced by "lamp is dark" | 1/2, 95 | 2/2, 0 (repaired) | 2/2, 0 (repaired) | 2/2, 0 (repaired) | 2/2, 0 (repaired) | 2/2, 0 (repaired) | 2/2, 0 (repaired) |
| lighthouse-story | hidden | in rule "storm shows Tev failing": condition "lamp is dark" replaced by "letter is hidden" | 1/2, 51 | 1/2, 51 (unchanged) | 2/2, 0 (repaired) | 2/2, 0 (repaired) | 2/2, 0 (repaired) | 2/2, 0 (repaired) | 2/2, 0 (repaired) |
| moving-day | visible | in rule "packing": result "boxes is packed" changed to "boxes is in van" | 2/3, 125 | 3/3, 8 (better) | 3/3, 0 (repaired) | 3/3, 8 (better) | 3/3, 135 (worse) | 3/3, 0 (repaired) | 3/3, 8 (better) |
| moving-day | hidden | in rule "returning the key": condition "van is not driven off" replaced by "boxes is in van" | 2/3, 40 | 3/3, 0 (repaired) | 3/3, 0 (repaired) | 3/3, 0 (repaired) | 3/3, 8 (better) | 3/3, 0 (repaired) | 3/3, 0 (repaired) |
| moving-day | hidden | in rule "booking": condition "book van happens" replaced by "boxes is unpacked" | 2/3, 76 | 3/3, 8 (better) | 3/3, 0 (repaired) | 3/3, 0 (repaired) | 3/3, 8 (better) | 3/3, 0 (repaired) | 3/3, 8 (better) |
| plant-watering | visible | in rule "water wets dry soil": result "soil is damp" changed to "soil is soaked" | 1/4, 101 | 4/4, 0 (repaired) | 4/4, 0 (repaired) | 4/4, 131 (worse) | 4/4, 139 (worse) | 4/4, 0 (repaired) | 4/4, 139 (worse) |
| plant-watering | hidden | in rule "sun dries soaked soil": condition "sunny day happens" left out | 3/4, 166 | 4/4, 18 (better) | 4/4, 0 (repaired) | 3/4, 166 (unchanged) | 4/4, 18 (better) | 4/4, 0 (repaired) | 4/4, 18 (better) |
| plant-watering | hidden | in rule "sun dries soaked soil": condition "soil is soaked" changed to "soil is damp" | 3/4, 85 | 4/4, 139 (worse) | 3/4, 85 (unchanged) | 4/4, 0 (repaired) | 4/4, 18 (better) | 3/4, 85 (unchanged) | 4/4, 0 (repaired) |
| reminder-app | visible | in rule "second snooze": result "snoozes is 2" changed to "snoozes is 1" | 3/4, 123 | 4/4, 0 (repaired) | 4/4, 0 (repaired) | 3/4, 123 (unchanged) | 3/4, 70 (better) | 4/4, 0 (repaired) | 4/4, 0 (repaired) |
| reminder-app | hidden | in rule "overdue after a day when urgent": result "task is overdue" changed to "task is urgent" | 3/4, 85 | 4/4, 0 (repaired) | 3/4, 85 (unchanged) | 4/4, 0 (repaired) | 4/4, 66 (better) | 3/4, 85 (unchanged) | 4/4, 0 (repaired) |
| reminder-app | hidden | in rule "overdue after a day when urgent": condition "task is urgent" replaced by "snoozes is 1" | 3/4, 129 | 4/4, 0 (repaired) | 3/4, 85 (better) | 4/4, 0 (repaired) | 3/4, 70 (better) | 4/4, 0 (repaired) | 4/4, 19 (better) |
| reminder-app | needs a new thing | no count of put-offs: one put-off makes a task urgent | 3/4, 44 | 2/4, 53 (worse) | 3/4, 52 (worse) | 2/4, 53 (worse) | 3/4, 44 (unchanged) | 3/4, 52 (worse) | 3/4, 44 (unchanged) |
| river-crossing | visible | in rule "farmer rows left with goose": condition "cross with goose happens" left out | 1/3, 297 | 3/3, 207 (better) | 3/3, 0 (repaired) | 3/3, 0 (repaired) | 3/3, 207 (better) | 3/3, 0 (repaired) | 3/3, 207 (better) |
| river-crossing | hidden | in rule "fox eats goose on the right": condition "farmer is left" replaced by "grain_is is eaten" | 2/3, 33 | 3/3, 260 (worse) | 2/3, 33 (unchanged) | 3/3, 207 (worse) | 3/3, 251 (worse) | 2/3, 33 (unchanged) | 3/3, 207 (worse) |
| river-crossing | hidden | in rule "farmer rows right with grain": condition "farmer is left" replaced by "fox is right" | 2/3, 128 | 3/3, 251 (worse) | 3/3, 0 (repaired) | 3/3, 207 (worse) | 3/3, 207 (worse) | 3/3, 0 (repaired) | 3/3, 207 (worse) |
