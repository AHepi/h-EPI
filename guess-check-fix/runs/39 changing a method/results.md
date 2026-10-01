# Changing a method: results

DeepSeek V4.1 Flash, default thinking. 3 repeats of two arms; every number comes from the records in this folder. Held occasions: 72 (24 bad, 24 good, 24 losing), from eight worlds DeepSeek never saw. A method is kept only if it rejects at least one held bad fix, accepts every good fix, rejects every losing fix, and never fails.

| Method | Kept | Held bad fixes rejected (of 24) | Good fixes not accepted | Losing fixes accepted | Errors | Questions asked | Says it asks the world | Asked the world |
|---|---|---|---|---|---|---|---|---|
| current method | no | 0 | 0 | 0 | 0 | 0 | - | no |
| log 17's repair (written by a person) | yes | 13 | 0 | 0 | 0 | 137 | - | yes |
| shown the failure, repeat 1 | yes | 16 | 0 | 0 | 0 | 116 | yes | yes |
| told the aim, repeat 1 | yes | 13 | 0 | 0 | 0 | 137 | no | yes |
| shown the failure, repeat 2 | yes | 20 | 0 | 0 | 0 | 118 | no | yes |
| told the aim, repeat 2 | yes | 13 | 0 | 0 | 0 | 137 | no | yes |
| shown the failure, repeat 3 | yes | 18 | 0 | 0 | 0 | 112 | yes | yes |
| told the aim, repeat 3 | yes | 13 | 0 | 0 | 0 | 137 | yes | yes |

What DeepSeek said each method does:

- shown the failure, repeat 1: It accepts a fix only when it repairs at least one failing job without breaking any passing job, then queries up to three changed nearby situations (prioritizing those not already covered by jobs and likely to have been correct before) to reject the fix if it broke a previously correct nearby situation.
- told the aim, repeat 1: Accepts a fix only if it repairs at least one failing job, loses no previously passing job, and among up to three changed nearby situations it does not turn a previously correct prediction into an incorrect one.
- shown the failure, repeat 2: It accepts a fix only if it repairs at least one job without breaking any passing job, then checks up to three nearby situations most similar to jobs that were already passing (or repaired if none), rejecting if any was correct before the fix and wrong after.
- told the aim, repeat 2: It accepts a fix only if it repairs at least one failing job, loses no passing jobs, and does not change any nearby situation from a correct ending to an incorrect one (checking up to three changed nearby situations).
- shown the failure, repeat 3: It rejects any fix that loses a previously passing job or repairs nothing, then asks the world about up to three nearby situations that are most suspicious for regressions—specifically variants of jobs that already passed before, or negated variants of repaired jobs—and rejects if any of those was correct before but wrong after.
- told the aim, repeat 3: It accepts only fixes that repair at least one failing job and lose none, then checks changed nearby situations (up to three) against the world and rejects if the fix broke a nearby situation that the model previously got right.
