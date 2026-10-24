# ROM-only investigation pass

## B72/#79

B72: propagate partial values through byte/word sign and zero extension.

Validation: Ran 361 tests in 4.212s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b72-no-clock-unknown.json and b72-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 361 tests pass. Experimental run reaches976 at BF on unknown GSR reset flag; next bounded work is opt-in explicit CAN reset-completion input, never an inferred hardware delay. Autonomous milestone requires original firmware recurring interrupts, not a larger count. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five ROM-only tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B73/#80

B73: add explicit synthetic CAN completion events with full provenance.

Validation: Ran 365 tests in 5.640s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b73-no-clock-unknown.json and b73-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 365 tests pass. Generation checks cancel stale requests; default no completion unchanged. Supplied reset completion establishes low reset flags; supplied11-recessive event proves only reset flag clear. Assumed delay1 run reaches984 at BCR1 write E320, PC1CE. Next bounded register task follows; milestone not achieved. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five ROM-only tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.
