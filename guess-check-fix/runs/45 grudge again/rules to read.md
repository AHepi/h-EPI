# Final grudge rules, to read by hand

Shuffled; the arm of each is in "rules key.json". Read each against the categories in "45 Plan - grudge again.md" and write the reading into "hand reading.json" before opening the key.

**R1.** Track unresolved insults. An insult adds one unresolved insult; an apology removes one if any, otherwise does nothing; a gift has no effect. Robin is warm exactly when the unresolved insult count is zero, otherwise cold.

**R2.** Start with hidden score 0. Insult subtracts 2; apologise and gift each add 1. Robin is warm if the final score is positive (>=1), otherwise cold.

**R3.** Maintain a hidden score starting at 0. Insult subtracts 5, apologise adds 2, gift adds 1. Robin is warm if the score is at least 0, otherwise cold.

**R4.** Start neutral at 0. Each insult decreases the mood by 1; each apology or gift increases it by 1. Robin is warm if the final mood is greater than 0 (i.e., positive actions strictly outnumber insults), otherwise cold.

**R5.** Track a hidden resentment counter starting at 0. Insult increases it by 1. Apologise decreases it by 1, but never below 0. Gift does not change it. Final mood is warm iff the counter is 0; otherwise it is cold.

**R6.** Maintain a hidden grudge count starting at 0. Insult increases it by 1. Apology decreases it by 1, but never below 0. Gift leaves it unchanged. Robin is warm if the count is 0, and cold if the count is greater than 0.

**R7.** Ignore gifts entirely. After removing gifts, Robin is warm only if the remaining sequence contains no consecutive insults (II) and ends with an apology (A); if the remaining sequence is empty or ends with an insult, or if it contains II, Robin is cold.

**R8.** Gifts have no effect. Start with an upset level of 0; insults increase it by 1 (maximum 2), apologies decrease it by 1 (minimum 0). Robin is warm if the level is 0, otherwise cold.

**R9.** Robin has a hidden score starting at 0; each insult subtracts 1, each apology or gift adds 1, and Robin is warm exactly when the score is positive.

**R10.** Start with anger score 0; insult increases it by 1, apologise decreases it by 1 but not below 0, and gift leaves it unchanged. Robin is warm if the score is 0, cold if it is greater than 0.

**R11.** Keep a hidden grudge counter starting at 0. Insult increases it by 1, apology decreases it by 1 but never below 0, and gift leaves it unchanged. Robin is warm exactly when the counter is 0; otherwise Robin is cold.

**R12.** Maintain a hidden count of unresolved insults: insult adds 1, apology subtracts 1 but never below 0, and gift does nothing; Robin is warm exactly when the count is 0.

**R13.** Warm if the number of apologies is strictly greater than the number of insults; gifts have no effect. Equivalently, start at 0, insult -1, apology +1, gift 0, and be warm iff the score is > 0.

**R14.** Track a hidden grudge counter starting at 0. Insult increases it by 1. Apologise decreases it by 1, but never below 0. Gift does nothing. Robin is warm if the counter is 0, and cold if it is greater than 0.

**R15.** Ignore gifts entirely. For the remaining sequence of insults and apologies: if it is empty or ends with an insult, the mood is cold. If it ends with an apology, then: if there is no earlier apology, it is warm; otherwise, count the number of consecutive insults immediately before this final apology. If that count is 0 or 1, it is warm; if it is 2 or more, it is cold.

**R16.** Each insult decreases a hidden mood score by 1, each apology increases it by 1, and gifts do not change it. Starting score is 0. The final mood is warm if the score is greater than 0, otherwise cold.

**R17.** Start with hidden score 0. Insult subtracts 1, apologise adds 1, gift adds 0. At the end, the mood is warm iff the score is greater than 0 (i.e. apologies outnumber insults); otherwise it is cold.

**R18.** Robin tracks a hidden grudge count starting at 0. Insult adds 1; apologise subtracts 1 but never below 0; gift changes nothing. Mood is warm iff the grudge count is 0, otherwise cold.
