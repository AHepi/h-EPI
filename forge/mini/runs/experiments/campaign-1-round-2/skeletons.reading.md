# skeletons

model:gemma4:31b on mini.campaign.campaign-1-round-2.skeletons, run c6711a8cef2f42a7.
Ended after 7 cycles (cycle_cap).

- proposals: 21, of which the executor ran 21
- executions: moved 4, unchanged 17
- standings: candidate point 9, rejected 12
- columns: unchanged 9
- readings: no prediction 21
- refused replies: 0, submissions dropped: 0
- pairs changing more than one part: 0 of 21 run (M14)
- grid: 20 of 20 cells named

## Where the machine contradicted the proposal

### cycle 2, proposal 2c601d56d60026a4, cell `fence[ S A ]`

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

### cycle 3, proposal 0a32c450a9eafdb0, cell `fence[ S A ] B`

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

### cycle 4, proposal 447b030ec43b11f5, cell `fence[ S A ] fence[ B ]`

conformance.kernel.recovery: expected to moves, unchanged, '{"b":2}' to '{"b":2}'.

```
```
Here is the result:
{"a": 1}
```
```
{"b": 2}
```
```

```
```
Here is the result:
{"a": 1}
```
{"b": 2}
```

### cycle 4, proposal 11681bf3a07f18e9, cell `fence[ A S ]`

conformance.kernel.recovered-from-prose: expected to moves, unchanged, 'yes' to 'yes'.

```
```
{"a": 1}
Here is the result:
```
```

```
{"a": 1}
Here is the result:
```

### cycle 5, proposal 5e2fc3d9ffd328c7, cell `fence[ A S ] B`

conformance.kernel.recovery: expected to moves, unchanged, '{"b":2}' to '{"b":2}'.

```
```
{"a": 1}
Here is the result:
```
{"b": 2}
```

```
{"a": 1}
Here is the result:
{"b": 2}
```

### cycle 5, proposal 47eea02590072f93, cell `fence[ A S ] fence[ B ]`

conformance.kernel.recovery: expected to moves, unchanged, '{"b":2}' to '{"b":2}'.

```
```
{"a": 1}
Here is the result:
```
```
{"b": 2}
```
```

```
```
{"a": 1}
Here is the result:
```
{"b": 2}
```

### cycle 6, proposal 8f9ab6a16e1d2c1a, cell `fence[ A B ] C`

conformance.kernel.recovery: expected to moves, unchanged, '{"c":3}' to '{"c":3}'.

```
```
{"a": 1}
{"b": 2}
```
{"c": 3}
```

```
{"a": 1}
{"b": 2}
{"c": 3}
```

### cycle 7, proposal b5268b1e671e4128, cell `fence[ A B ] A`

conformance.kernel.recovery: expected to moves, unchanged, '{"a":1}' to '{"a":1}'.

```
```
{"a": 1}
{"b": 2}
```
{"a": 1}
```

```
{"a": 1}
{"b": 2}
{"a": 1}
```

### cycle 7, proposal 14c2ed49574f364f, cell `fence[ A B ] fence[ C ]`

conformance.kernel.recovery: expected to moves, unchanged, '{"c":3}' to '{"c":3}'.

```
```
{"a": 1}
{"b": 2}
```
```
{"c": 3}
```
```

```
```
{"a": 1}
{"b": 2}
```
{"c": 3}
```
