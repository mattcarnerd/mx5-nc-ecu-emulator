# Eight requested bounded tasks

## B13/#16

Implement SH-2E FPU reset state and system register transfers (B13)
Software manual2.6/4.2/7.3.16-17: FR/FPUL unknown, FPSCR reset40001; writable18C60, fixed DN/RM retained. LDS/STS direct and stack forms commit base changes only after successful access. No SH-4 banks or precision mode invented.

Validation: Ran 294 tests in 2.298s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b13-no-clock-unknown.json and b13-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. B13 enables B14, which enables B15. Timer/ADC/input/output tasks retain dependencies. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User explicitly requested these eight bounded features; synthetic coverage is distinguished from observed firmware use.
