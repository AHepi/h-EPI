# Baseline and more thinking: summary

From 20 world-and-repeat records in `19 baseline and more thinking`, `19 DeepSeek alone, max thinking, no low limit`. 60 loop runs were replayed from their recorded replies and all reproduced their final models.

## Every question

| Arm | Held-back right | Nearby right | DeepSeek calls | Output tokens | Replies cut off |
|---|---|---|---|---|---|
| DeepSeek alone, low thinking | 51/62 | 318/376 | 20 | 211293 | 0 |
| one guess, low thinking | 48/62 | 294/376 | 20 | 87044 | 0 |
| guesser fixes first, low thinking | 52/62 | 322/376 | 49 | 228287 | 0 |
| DeepSeek alone, high thinking | 49/62 | 300/376 | 20 | 262212 | 1 |
| one guess, high thinking | 52/62 | 303/376 | 20 | 156723 | 0 |
| guesser fixes first, high thinking | 54/62 | 338/376 | 45 | 331609 | 0 |
| DeepSeek alone, high thinking, with the world's answers | 60/62 | 356/376 | 20 | 216420 | 0 |
| DeepSeek alone, high thinking, majority of 5 | 50/62 | 310/376 | 100 | 1341899 | not recorded |
| DeepSeek alone, max thinking | 42/62 | 263/376 | 20 | 389908 | 3 |
| one guess, max thinking | 51/62 | 310/376 | 20 | 188085 | 0 |
| guesser fixes first, max thinking | 54/62 | 337/376 | 50 | 497387 | 0 |
| DeepSeek alone, max thinking, reply limit 200,000 | 52/62 | 312/376 | 20 | 384911 | 0 |

## Leaving out every situation the loop asked the world about

| Arm | Held-back right | Nearby right |
|---|---|---|
| DeepSeek alone, low thinking | 32/37 | 309/365 |
| one guess, low thinking | 28/37 | 285/365 |
| guesser fixes first, low thinking | 30/37 | 313/365 |
| DeepSeek alone, high thinking | 30/37 | 292/365 |
| one guess, high thinking | 29/37 | 292/365 |
| guesser fixes first, high thinking | 29/37 | 327/365 |
| DeepSeek alone, high thinking, with the world's answers | 35/37 | 345/365 |
| DeepSeek alone, high thinking, majority of 5 | 32/37 | 301/365 |
| DeepSeek alone, max thinking | 26/37 | 255/365 |
| one guess, max thinking | 31/37 | 299/365 |
| guesser fixes first, max thinking | 33/37 | 326/365 |
| DeepSeek alone, max thinking, reply limit 200,000 | 32/37 | 303/365 |

## Each world: questions right (held-back and nearby), both repeats

| World | DeepSeek alone, high thinking | guesser fixes first, high thinking | DeepSeek alone, high thinking, with the world's answers | DeepSeek alone, high thinking, majority of 5 | DeepSeek alone, max thinking, reply limit 200,000 |
|---|---|---|---|---|---|
| ball-and-wall | 34 | 46 | 40 | 34 | 34 |
| borrowed-lantern | 25 | 40 | 37 | 28 | 28 |
| door-game | 46 | 46 | 46 | 46 | 46 |
| ghost-lantern | 42 | 42 | 48 | 42 | 42 |
| hidden-ball | 20 | 20 | 20 | 20 | 20 |
| lighthouse-story | 38 | 41 | 44 | 38 | 36 |
| moving-day | 40 | 42 | 46 | 40 | 40 |
| plant-watering | 48 | 42 | 48 | 48 | 48 |
| reminder-app | 44 | 47 | 48 | 44 | 44 |
| river-crossing | 12 | 26 | 39 | 20 | 26 |
