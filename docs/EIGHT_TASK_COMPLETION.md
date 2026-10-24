# Eight requested bounded tasks

## B13/#16

Implement SH-2E FPU reset state and system register transfers (B13)
Software manual2.6/4.2/7.3.16-17: FR/FPUL unknown, FPSCR reset40001; writable18C60, fixed DN/RM retained. LDS/STS direct and stack forms commit base changes only after successful access. No SH-4 banks or precision mode invented.

Validation: Ran 294 tests in 2.298s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b13-no-clock-unknown.json and b13-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. B13 enables B14, which enables B15. Timer/ADC/input/output tasks retain dependencies. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User explicitly requested these eight bounded features; synthetic coverage is distinguished from observed firmware use.

## B14/#17

Implement raw FPU transfers and bounded conversion instructions (B14)
FMOV raw32 register/direct/indexed/predecrement/postincrement forms preserve every bit including NaNs; FLDI0/1, FLDS/FSTS, FLOAT/FTRC added. Integer conversion uses exact rational binary32 truncation, fixed SH-2E DN flushing; unsupported NaN/infinity/out-of-range/enabled exception modes fail before destination update. Stack addressing changes only on successful access.

Validation: Ran 297 tests in 2.517s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b14-no-clock-unknown.json and b14-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. B14 enables B15 arithmetic; timer and ADC remain next independent scopes. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User explicitly requested these eight bounded features; synthetic coverage is distinguished from observed firmware use.
