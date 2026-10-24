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

## B74/#81

B74: model CAN configuration latches and supplied configuration-window timing.

Validation: Ran 368 tests in 3.952s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b74-no-clock-unknown.json and b74-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 368 tests pass. BCR1/BCR0 reserved readback remains unknown, writes require known configuration mode; cross-register constraints reported without oscillator/baud assumption. Reset completion resets latches. Too-early bus event remains a rejection; declared reset1/bus64 experiment reaches1012 at CMP/HI PCDF6/op3E36. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five ROM-only tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B75/#82

B75: implement unsigned strictly-greater CMP/HI.

Validation: Ran 370 tests in 4.144s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b75-no-clock-unknown.json and b75-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 370 tests pass. Boundary/equality/alias and unknown-operand behavior verified against SH-2E section7 CMP semantics. Declared completion scenario reaches1017 at NOT R4,R2 PC E0E/op6247; no interrupt milestone yet. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five ROM-only tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B76/#83

B76: implement NOT with alias and partial-bit semantics.

Validation: Ran 372 tests in 4.412s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b76-no-clock-unknown.json and b76-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 372 tests pass. Explicit completion scenario reaches1022 attempts at FFFFD052 word read PC E18/op6331. No physical completion defaults or recurring interrupt claims introduced. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five ROM-only tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B77/#84

B77: model aligned mailbox interrupt-mask registers on both CAN channels.

Validation: Ran 374 tests in 6.710s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b77-no-clock-unknown.json and b77-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 374 tests pass. Mask latches resetFFFF, unknown manual/processing states retained, explicit reset completion restores masks. No CAN events or CPU interrupts fabricated. Completion scenario reaches1024 at MULU.W PCE1C/op204E. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five ROM-only tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B78/#85

B78: implement unsigned low-word multiplication into MACL.

Validation: Ran 376 tests in 5.491s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b78-no-clock-unknown.json and b78-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 376 tests pass. Unknown high bits do not matter to MULU.W; unknown low operands remain guarded. MACH/T/source registers unchanged. Declared scenario reaches1026 at STS MACL,R0 PCE20/op001A; next MACL transfer scoped separately. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five ROM-only tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B79/#86

B79: implement STS MACL register transfer without interrupt inhibition.

Validation: Ran 378 tests in 7.930s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b79-no-clock-unknown.json and b79-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 378 tests pass. Undefined MACL transports unknown bits; computed products transfer exactly and preserve T/MACH. Declared scenario reaches1042 at ADD R7,R2 PCE52/op327C. Milestone still requires sustained original-firmware execution and recurring interrupts. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five ROM-only tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.
