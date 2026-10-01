# A language that grows: results

DeepSeek V4.1 Flash, default thinking. 9 device-and-repeat runs; every number comes from the records in this folder. "Rival-wrong" tests are the peg-tube cases that separate counts of each colour get wrong.

| Device | Arm | Runs | Long tests right | Short tests right | Hard tests right | Rival-wrong tests right | Runs fitting every observation | Replies cut off | Output tokens |
|---|---|---|---|---|---|---|---|---|---|
| balance gate | fixed language | 3 | 23/24 | 18/18 | 21/21 | - | 3/3 | 3 | 175903 |
| balance gate | growing language | 3 | 24/24 | 18/18 | 21/21 | - | 3/3 | 0 | 14965 |
| balance gate | universal language | 3 | 24/24 | 18/18 | 21/21 | - | 3/3 | 0 | 20267 |
| peg tube | fixed language | 3 | 0/39 | 0/18 | 0/24 | 0/15 | 0/3 | 18 | 576000 |
| peg tube | growing language | 3 | 39/39 | 18/18 | 24/24 | 15/15 | 3/3 | 0 | 54779 |
| peg tube | universal language | 3 | 39/39 | 18/18 | 24/24 | 15/15 | 3/3 | 0 | 45345 |
| grudge | fixed language | 3 | 0/0 | 27/36 | 15/24 | - | 3/3 | 1 | 87373 |
| grudge | growing language | 3 | 0/0 | 30/36 | 19/24 | - | 3/3 | 0 | 28361 |
| grudge | universal language | 3 | 0/0 | 28/36 | 16/24 | - | 3/3 | 1 | 68217 |

Growing language, the best model of each run: new kinds, new things, rules, and the kinds' expressions (changes and tests):

- balance gate repeat 1: 1 kinds, 1 new things, 4 rules, 3 expressions; fits 20 of 20
- balance gate repeat 2: 1 kinds, 1 new things, 4 rules, 3 expressions; fits 20 of 20
- balance gate repeat 3: 1 kinds, 1 new things, 4 rules, 3 expressions; fits 20 of 20
- peg tube repeat 1: 2 kinds, 2 new things, 9 rules, 10 expressions; fits 24 of 24
- peg tube repeat 2: 2 kinds, 2 new things, 9 rules, 9 expressions; fits 24 of 24
- peg tube repeat 3: 1 kinds, 1 new things, 7 rules, 8 expressions; fits 24 of 24
- grudge repeat 1: 1 kinds, 1 new things, 5 rules, 3 expressions; fits 14 of 14
- grudge repeat 2: 1 kinds, 1 new things, 4 rules, 3 expressions; fits 14 of 14
- grudge repeat 3: 1 kinds, 1 new things, 5 rules, 3 expressions; fits 14 of 14
