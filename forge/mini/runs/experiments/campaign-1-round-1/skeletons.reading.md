# skeletons

model:gemma4:31b on mini.campaign.campaign-1-round-1.skeletons, run 10f327a232724128.
Ended after 3 cycles (cycle_cap).

- proposals: 9, of which the executor ran 9
- executions: moved 3, unchanged 6
- standings: candidate point 2, rejected 7
- columns: unchanged 2
- readings: no prediction 9
- refused replies: 0, submissions dropped: 0
- pairs changing more than one part: 0 of 9 run (M14)
- grid: 9 of 20 cells named; not named: fence[ S A ] fence[ B ]; fence[ A S ]; fence[ A S ] S; fence[ A S ] B; fence[ A S ] A; fence[ A S ] fence[ B ]; fence[ A B ]; fence[ A B ] S; fence[ A B ] C; fence[ A B ] A; fence[ A B ] fence[ C ]

## Where the machine contradicted the proposal

### cycle 2, proposal 4626bfb9a75e76e5, cell `fence[ S A ]`

conformance.kernel.recovered-from-prose: expected to moves, unchanged, 'yes' to 'yes'.

```
```
Here is the result:
{"a": 1}
```
```

```
Here is the result:
{"a": 1}
```

### cycle 3, proposal 2e02245748079a6e, cell `fence[ S A ] B`

conformance.kernel.recovery: expected to moves, unchanged, '{"b":2}' to '{"b":2}'.

```
```
Here is the result:
{"a": 1}
```
{"b": 2}
```

```
Here is the result:
{"a": 1}
{"b": 2}
```
