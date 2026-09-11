---
name: mini-config
description: Read, register, audit and test a mini configuration. Use when changing a manifest, designing an experimental arm, reading a block's result, or asking why a config worked or did not. Keeps CONFIG_MAP, CONFOUNDS, ERRATA and the configuration registry in agreement.
---

# Working on a mini configuration

Four documents and one command. **The command is the point**: a cross-reference nobody checks rots,
and this repository has already paid for two documents that disagreed with the code.

```
python tools/config_map.py audit              # every tag resolves, or it fails
python tools/config_map.py show --config CONF-ARMS-W
```

| what | where | tags |
|---|---|---|
| every setting, what it decides, how it is misread | `docs/mini/CONFIG_MAP.md` | `CFG-*`, `MIS-*` |
| settings that move together and what that does to a comparison | `docs/mini/CONFOUNDS.md` | `CON-*` |
| what has already gone wrong, and what it cost | `docs/mini/ERRATA.md` | `A*`, `M*`, `C*` |
| configurations run or designed, and what each proves | `forge/mini/configs/registry.json` | `CONF-*` |
| alarms that stop a run | `src/creib/forge/mini/alarms.py` | `ALM-*` |

## Before you run anything

1. **Preflight.** `python tools/creativity_arms.py alarms --manifest <path>`. A seat the *tool* does
   not register costs a whole block and is visible here for free (CON-SEAT-REGISTRATION).
2. **Read the confounds your change touches.** If you are varying `CFG-FORMAT`, read
   CON-FORMAT-KILLS-RUN before you vary it, not after.
3. **Say which single setting differs across arms**, and check the others really are identical —
   `tools/config_map.py show` prints what each registered config sets.

## Between segments

`python tools/creativity_arms.py alarms --segment <run-dir>` exits non-zero on anything fatal, and
the runner stops the arm on it. **A fatal alarm means the machinery cannot measure anything**, which
is a different claim from the subject being uninteresting. Conflating those produced three of the
withdrawn conclusions in ERRATA.

## After a block

Add a `CONF-*` entry. Four fields are not optional and the audit fails without them:

- `shows` — the numbers, without interpretation;
- `proven` — what follows, and nothing more;
- `not_proven` — what a reader might wrongly take from it. **Write this one first.**
- `confounds` — every `CON-*` that applies, including ones that make the reading unattributable.

A `status` is about the **configuration**, never the subject: `fails` means *this config could not
measure*, not *the loop is worthless*.

## When you add a setting, a confound or an alarm

Add it in all the places at once, and run the audit; it fails on a tag that resolves to nothing.
A new alarm is `Alarm("NAME", FATAL|WARN, ...)` in `alarms.py`, referenced in prose as `ALM-NAME`,
and needs a test that reaches it.

## What this cannot do

It checks that the documents agree with each other and with the schema. It does **not** check that a
config measures what it claims — that is what a pre-registration and a control are for, and the
audit passing is not evidence about a result.
