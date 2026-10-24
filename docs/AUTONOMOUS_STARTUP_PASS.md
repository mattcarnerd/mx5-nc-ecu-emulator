# Autonomous firmware startup investigation

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

## B80/#87

B80: implement modulo32 register ADD without changing T.

Validation: Ran 380 tests in 6.356s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b80-no-clock-unknown.json and b80-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 380 tests pass. Boundary/wrap/alias/unknown-input guards verified. Declared completion scenario reaches1047, PCE5C/op2C21, mailbox0 identifier word FFFFD100 value0037. Next bounded work is documented mailbox identifier/control latches; no traffic inferred. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five ROM-only tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B81/#88

B81: accept documented mailbox identifier configuration words.

Validation: Ran 382 tests in 4.399s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b81-no-clock-unknown.json and b81-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 382 tests pass. First identifier word reserved bit15 guarded; second fullword accepted including values resembling control data at a different address. No receive data synthesized. Declared run reaches1057 at mailbox0 control2308 with prohibited MBC011. Next audit must verify CPU/arguments and applicable documentation, not silently accept undefined mode. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five ROM-only tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.


## Milestone acceptance and current evidence gate

The user authorized autonomous work toward sustained original-firmware initialization and recurring interrupts. This remains an active, unachieved objective. B72-B82 are bounded implementation/research results, not a complete ECU milestone.

Acceptance requires original firmware reaching identifiable initialization completion/main operation under a reproducible declared virtual profile, enabling and servicing modelled module interrupts repeatedly (at least3 completed handler entries/returns with main progress between them). A held unacknowledged request, repeated PCs, generated handler firmware or instruction-limit-only run does not count. Direct CPU interrupt injection cannot substitute for modelled recurring module requests. Physical clock/engine validation remains a separate goal.

Implemented: partial extensions; opt-in CAN reset/recessive event fixtures; CAN bit-configuration latches/masks and mailbox identifier commands; CMP/HI, NOT, MULU.W, STS MACL and register ADD. No ROM bytes changed. Strict188 and original conditional592 preserved. No-completion bit6=0 reaches976. Explicit reset1/bus64 or256 reaches1057/1056 and no interrupt entries.

The [mailbox-mode audit](MAILBOX_MODE_AUDIT.md) and [25-case matrix](evidence/b82-startup-matrix.json) document the new gate: mailbox0 control2308 contains prohibited MBC011. SH7058 Rev.3, related-part Rev.5 and the Renesas technical update all prohibit it. Independent generated arithmetic and the local caller audit confirm the value calculation; no applicable behavioral waiver found.

### Completion fixture semantics and reproduction

--hcan-reset-completion-ticks and --hcan-recessive-bus-ticks are optional supplied events, measured only in completed-instruction scheduling ticks. Neither is a measured peripheral delay, oscillator or serial bus timing. Omission retains unknown processing. At least one supplied delay must be positive. Both channel generations invalidate stale scheduled events. No frame receive/transmit or CAN IRQ is created.

A supplied reset completion establishes documented low reset GSR bits and resets modelled BCR/MBIMR latches; mailbox RAM content is not invented. A separately supplied11-recessive-bit event proves only GSR3 clear. Where the fixture starts with known reset status, it holds that status until the declared event. Delays1 versus64 can change whether configuration writes are allowed; both are explicit experiments. BCR reserved readback remains unknown; cross-register constraints are reported, not a baud rate or validated bus.

Windows CLI example:

```
MX5-NC-ECU-Emulator.exe --rom YOUR_LOCAL_IMAGE --reset power --nmi high --steps 100000 --hudi-scenario trst-reset --phi-cycles-per-instruction 1 --experimental-mcr-bit6 0 --hcan-reset-completion-ticks 1 --hcan-recessive-bus-ticks 64 --report local-diagnostic.json
```

Detailed reports/baselines/reduced exports preserve all assumptions and reject mismatch/missing execution provenance. No new GUI controls claimed. The final executable release validates this implementation, not the unachieved milestone.

Next evidence: applicable documented MBC011 behavior, an independent CPU/profile correction or a separately identified compatible ROM/profile. User was asked for additional public source/reference if available; a physical ECU is not required to provide such a reference. Do not accept undefined modes merely to advance instruction counts.

## B82/#89

B82: audit prohibited MBC011 with independent arithmetic and primary-source constraints.

Validation: Ran 386 tests in 4.738s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b82-no-clock-unknown.json and b82-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 386 tests pass;25-case matrix and user-input request recorded. Both reviewed chip manuals and technical update prohibit mode011; no behavior waiver found. No physical ECU requirement invented, no prohibited mode accepted. Autonomous milestone unachieved and parents retain evidence gate; additional source/profile evidence genuinely needed for faithful progress. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five ROM-only tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.
