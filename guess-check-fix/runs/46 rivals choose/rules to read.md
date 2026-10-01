# Final grudge rules, to read by hand

Scrambled; the arm of each is in "rules key.json". Read each against the categories in "46 Plan - rivals choose.md" and write the reading into "hand reading.json" before opening the key.

**R1.** Hidden mood starts at 0. Insult subtracts 1; apologise and gift each add 1. Warm if the final value is greater than 0, otherwise cold. Equivalently, warm iff the number of apologise+gift actions exceeds the number of insults.

**R2.** Track two hidden quantities: resentment R and goodwill W. Start at R=0, W=0. Insult: if W>0, set W=0; otherwise R+=1. Apology: if R>0, R-=1; otherwise W+=1. Gift: no effect. Final mood is warm iff R=0 and W>0; otherwise cold.

**R3.** Track a hidden score starting at 0. Insult subtracts 2, apologise adds 1, and gift adds 2. Robin is warm if the final score is positive (>0), otherwise cold.

**R4.** Track three hidden states: Warm, Upset (cold but recoverable), and Angry (cold and permanent). Start Warm. Insult: Warm->Upset, Upset->Angry, Angry->Angry. Apologise: Warm->Warm, Upset->Warm, Angry->Angry. Gift: Warm->Warm, Upset->Upset, Angry->Angry. Mood is warm only in Warm; otherwise cold.

**R5.** Track a hidden warmth score starting at 0. Insult decreases it by 2, apologise increases it by 1, and gift increases it by 2. The mood is warm if the final score is greater than 0, otherwise cold.

**R6.** Robin has a hidden mood level: cold, neutral, warm (starting neutral). Insult lowers by one (min cold). Apologise raises by one (max warm). Gift raises cold to neutral, but does not raise neutral or warm further. Warm is observed only at the warm level.

**R7.** Robin starts warm. Insult makes Robin cold and increases the consecutive-insult counter. Apology makes Robin warm if the counter is at most 1; if it is 2 or more, the apology fails and Robin stays cold, then the counter resets to 0. Gift does not change mood but resets the consecutive-insult counter to 0.

**R8.** Ignore gifts. For the remaining sequence of insults (I) and apologies (A): if it ends with I, mood is cold. If it ends with A, let n be the length of the last run of I's (0 if none), and let totalA be the total number of A's. Mood is warm if n is odd or totalA is odd; otherwise cold. If no I or A (all gifts), mood is cold.

**R9.** Maintain a hidden count of unapologized insults, starting at 0. Insult adds 1; apologise subtracts 1 but never below 0; gift does nothing. The final mood is WARM if the count is 0, otherwise COLD.

**R10.** Track outstanding insults: start at 0. Insult adds 1. Apologise subtracts 1 if the count is positive, otherwise it stays 0. Gift does nothing. Mood is warm if the final count is 0, cold if it is positive.

**R11.** Start with hidden score 0. Insult subtracts 2 but the score never falls below -2; apologise adds 1; gift adds 2. Mood is warm if the score is > 0, otherwise cold.

**R12.** Start at score 0; insult changes score by -2, apology by +1, gift by +2. Final mood is warm if score > 0, otherwise cold.
