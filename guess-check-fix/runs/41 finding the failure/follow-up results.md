# Finding the failure, follow-up: results

The with-the-record arm only, reply limit 200,000 tokens, planned after log 41's first results. Every number comes from the "follow-up" records in this folder.

| Repeat | Cut off | Changed the method | Kept | Held bad fixes rejected (of 24) | Good fixes not accepted | Output tokens | What is wrong |
|---|---|---|---|---|---|---|---|
| 1 | 0 | yes | yes | 19 | 0 | 26681 | The current method ignores `fix_case.nearby` and `ask`, so it can accept fixes that repair jobs but break nearby situations that were already correct (e.g., Fix 2’s “throw does not happen” case). |
| 2 | 0 | yes | yes | 16 | 0 | 29101 | The original method ignores `fix_case.nearby` and the `ask` oracle entirely, so it accepts fixes that repair a job but break nearby situations that were previously correct. The new version checks up to 3 changed nearby situations (prioritizing likely regressions) and rejects if the fix turns a correct nearby situation into an incorrect one. |
| 3 | 0 | yes | yes | 9 | 0 | 25958 | the current method ignores nearby situations and the world, so it accepts fixes that repair jobs but break nearby situations that were already correct. The new method checks up to three suspicious nearby situations with `ask` and rejects if a previously correct nearby situation becomes incorrect. |
