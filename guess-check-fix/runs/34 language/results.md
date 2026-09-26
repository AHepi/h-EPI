# Can the language express it: results

DeepSeek V4.1 Flash, default thinking. 9 device-and-repeat runs; every number comes from the records in this folder. "Largest hidden thing" is how many states the best rule model's largest unseen thing has, in each run: how far it can count.

| Device | Arm | Runs | Long tests right | Short tests right | Hard tests right | Runs fitting every observation | Largest hidden thing (fixed language) | Output tokens |
|---|---|---|---|---|---|---|---|---|
| balance gate | fixed language | 3 | 3/18 | 6/18 | 5/18 | 1/3 | 0, 6, 101 | 403532 |
| balance gate | universal language | 3 | 18/18 | 18/18 | 18/18 | 3/3 | - | 39094 |
| balance gate | bare | 3 | 18/18 | 18/18 | 18/18 | - | - | 34505 |
| peg tube | fixed language | 3 | 12/18 | 12/18 | 6/9 | 2/3 | 0, 11, 2 | 378991 |
| peg tube | universal language | 3 | 18/18 | 18/18 | 9/9 | 3/3 | - | 52613 |
| peg tube | bare | 3 | 6/18 | 6/18 | 3/9 | - | - | 83287 |
| grudge | fixed language | 3 | 0/0 | 27/36 | 15/24 | 3/3 | 3, 3, 2 | 239206 |
| grudge | universal language | 3 | 0/0 | 27/36 | 15/24 | 3/3 | - | 51586 |
| grudge | bare | 3 | 0/0 | 18/36 | 10/24 | - | - | 74992 |
