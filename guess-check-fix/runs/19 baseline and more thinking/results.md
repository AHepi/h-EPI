# Baseline and more thinking: results

Guesser: DeepSeek V4.1 Flash. Every number below comes from the records in this folder, summed over 20 world-and-repeat runs.

| Arm | Held-back questions right | Nearby questions right | DeepSeek calls | Output tokens (thinking included) |
|---|---|---|---|---|
| DeepSeek alone, low thinking | 51/62 | 318/376 | 20 | 211293 |
| one guess, low thinking | 48/62 | 294/376 | 20 | 87044 |
| guesser fixes first, low thinking | 52/62 | 322/376 | 49 | 228287 |
| DeepSeek alone, high thinking | 49/62 | 300/376 | 20 | 262212 |
| one guess, high thinking | 52/62 | 303/376 | 20 | 156723 |
| guesser fixes first, high thinking | 54/62 | 338/376 | 45 | 331609 |
| DeepSeek alone, high thinking, with the world's answers | 60/62 | 356/376 | 20 | 216420 |
| DeepSeek alone, high thinking, majority of 5 | 50/62 | 310/376 | 100 | 1341899 |
| DeepSeek alone, max thinking | 42/62 | 263/376 | 20 | 389908 |
| one guess, max thinking | 51/62 | 310/376 | 20 | 188085 |
| guesser fixes first, max thinking | 54/62 | 337/376 | 50 | 497387 |
