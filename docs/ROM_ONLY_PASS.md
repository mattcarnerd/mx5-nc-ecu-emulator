# ROM-only investigation pass

## B62/#69

B62: pin LF9VEB public blob identity and separate ROMDrop metadata from hardware evidence.

Validation: Ran 335 tests in 2.821s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b62-no-clock-unknown.json and b62-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. ROM-only path selected from user context. No matching ECU available; provenance match does not resolve silicon or reset gates. Review keeps existing parents and five bounded children, no duplicate broad hardware task. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five ROM-only tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B63/#70

B63: reconcile public ROM identity with startup constraints and define opt-in ROM-only experiments.

Validation: Ran 335 tests in 2.781s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b63-no-clock-unknown.json and b63-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. No new evidence resolves actual TRST history, silicon revision or reserved readback. Backlog separates physical evidence gates from executable software scenarios. B64/B65/B66 remain bounded; no duplicated physical research. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five ROM-only tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B64/#71

B64: add explicit experimental HCAN reserved-bit6 readback choices with end-to-end provenance.

Validation: Ran 341 tests in 2.904s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b64-no-clock-unknown.json and b64-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 341 tests pass. Unknown default and both hypothetical readback branches checked; known-one writes remain rejected. B65 is limited to the next documented command exposed by the zero branch; no bus or board state invented. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five ROM-only tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B65/#72

B65: accept documented HCAN software-reset request without inventing completion.

Validation: Ran 342 tests in 3.981s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b65-no-clock-unknown.json and b65-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 342 tests pass. Explicit zero-readback run reaches960 attempts/959 completed at reset-undefined R11 stack save; one-readback remains rejected at592. Strict188 and original conditional592 preserved. Full reset processing, bus state and unknown-stack handling remain open. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five ROM-only tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.


## Scenario matrix and user-facing reproduction

[Provenance](ROM_PROVENANCE.md), [constraint contract](ROM_ONLY_CONSTRAINTS.md) and [reset command boundary](HCAN_RESET_COMMAND.md) contain the evidence and limits. [Reduced matrix](evidence/b66-rom-only-matrix.json) contains19 independent runs: one strict300 reference setting plus all3 H-UDI choices x2 clock choices (unknown/artificial1) x3 reserved-bit choices (unknown/0/1) at declared10000 budget. NMI high is an explicit input, not a board measurement. Every row has attempted/completed counts and exact reduced dependency.

| Scenario | Attempts/completed | Result |
|---|---|---|
| Strict300, H-UDI/clock/bit unknown |188/187|Unknown SDSR at EF8|
| Explicit H-UDI, clock unknown (any bit choice) |225/224|Watchdog enable requires supplied clock|
| Explicit H-UDI and artificial phi1, bit unknown |592/591|MCR write contains unknown bit6|
| Same, bit6=1 |592/591|Reserved-one word0041 rejected|
| Same, bit6=0 |960/959|Reset-undefined R11 stack save at PC1BA/op2FB6|

If H-UDI is unknown, supplying clock/bit choices still stops188; the report remains conditional because assumptions were supplied, even if not consumed. No supplied branch is promoted to hardware truth.

Updated Windows EXE CLI supports the readback argument:

```
MX5-NC-ECU-Emulator.exe --rom YOUR_LOCAL_IMAGE --reset power --nmi high --steps 10000 --hudi-scenario trst-reset --phi-cycles-per-instruction 1 --experimental-mcr-bit6 0 --report local-diagnostic.json
```

Omit the readback flag to retain unknown bit6. Choose1 to exercise the rejected-write branch. Add --baseline for a compact baseline. The source-only matrix command is:

```
python -m ecu_workbench.rom_only_matrix --rom YOUR_LOCAL_IMAGE --nmi high --steps 10000 --output local-matrix.json
```

There is no new GUI control. Full local diagnostics remain private; the matrix uses whitelisted reduced reports and never publishes file paths or firmware bytes. The matrix command reports stops; it does not treat a longer trace as successful boot. Unknown RAM values/stack saves, full HCAN reset completion/status, verified clock/pins, sustained firmware operation, engine inputs/feedback and multi-ROM support remain open.

## B66/#73

B66: regress and publish 19 explicit ROM-only scenarios with attempted/completed counts and refreshed priorities.

Validation: Ran 346 tests in 3.733s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b66-no-clock-unknown.json and b66-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 346 tests pass including deterministic full-image matrix repeats. All five bounded scopes reviewed; next software dependency is unknown R11 stack save, not a physical ECU purchase or repeat of an unchanged audit. Strict188, existing conditional592 and new hypothetical960 remain distinct; hardware/engine goals stay open. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five ROM-only tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.
