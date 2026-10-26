# Autonomous firmware startup investigation

## B72/#79

B72: propagate partial values through byte/word sign and zero extension.

Validation: Ran 361 tests in 4.212s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b72-no-clock-unknown.json and b72-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 361 tests pass. Experimental run reaches976 at BF on unknown GSR reset flag; next bounded work is opt-in explicit CAN reset-completion input, never an inferred hardware delay. Autonomous milestone requires original firmware recurring interrupts, not a larger count. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B73/#80

B73: add explicit synthetic CAN completion events with full provenance.

Validation: Ran 365 tests in 5.640s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b73-no-clock-unknown.json and b73-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 365 tests pass. Generation checks cancel stale requests; default no completion unchanged. Supplied reset completion establishes low reset flags; supplied11-recessive event proves only reset flag clear. Assumed delay1 run reaches984 at BCR1 write E320, PC1CE. Next bounded register task follows; milestone not achieved. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B74/#81

B74: model CAN configuration latches and supplied configuration-window timing.

Validation: Ran 368 tests in 3.952s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b74-no-clock-unknown.json and b74-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 368 tests pass. BCR1/BCR0 reserved readback remains unknown, writes require known configuration mode; cross-register constraints reported without oscillator/baud assumption. Reset completion resets latches. Too-early bus event remains a rejection; declared reset1/bus64 experiment reaches1012 at CMP/HI PCDF6/op3E36. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B75/#82

B75: implement unsigned strictly-greater CMP/HI.

Validation: Ran 370 tests in 4.144s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b75-no-clock-unknown.json and b75-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 370 tests pass. Boundary/equality/alias and unknown-operand behavior verified against SH-2E section7 CMP semantics. Declared completion scenario reaches1017 at NOT R4,R2 PC E0E/op6247; no interrupt milestone yet. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B76/#83

B76: implement NOT with alias and partial-bit semantics.

Validation: Ran 372 tests in 4.412s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b76-no-clock-unknown.json and b76-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 372 tests pass. Explicit completion scenario reaches1022 attempts at FFFFD052 word read PC E18/op6331. No physical completion defaults or recurring interrupt claims introduced. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B77/#84

B77: model aligned mailbox interrupt-mask registers on both CAN channels.

Validation: Ran 374 tests in 6.710s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b77-no-clock-unknown.json and b77-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 374 tests pass. Mask latches resetFFFF, unknown manual/processing states retained, explicit reset completion restores masks. No CAN events or CPU interrupts fabricated. Completion scenario reaches1024 at MULU.W PCE1C/op204E. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B78/#85

B78: implement unsigned low-word multiplication into MACL.

Validation: Ran 376 tests in 5.491s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b78-no-clock-unknown.json and b78-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 376 tests pass. Unknown high bits do not matter to MULU.W; unknown low operands remain guarded. MACH/T/source registers unchanged. Declared scenario reaches1026 at STS MACL,R0 PCE20/op001A; next MACL transfer scoped separately. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B79/#86

B79: implement STS MACL register transfer without interrupt inhibition.

Validation: Ran 378 tests in 7.930s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b79-no-clock-unknown.json and b79-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 378 tests pass. Undefined MACL transports unknown bits; computed products transfer exactly and preserve T/MACH. Declared scenario reaches1042 at ADD R7,R2 PCE52/op327C. Milestone still requires sustained original-firmware execution and recurring interrupts. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B80/#87

B80: implement modulo32 register ADD without changing T.

Validation: Ran 380 tests in 6.356s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b80-no-clock-unknown.json and b80-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 380 tests pass. Boundary/wrap/alias/unknown-input guards verified. Declared completion scenario reaches1047, PCE5C/op2C21, mailbox0 identifier word FFFFD100 value0037. Next bounded work is documented mailbox identifier/control latches; no traffic inferred. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B81/#88

B81: accept documented mailbox identifier configuration words.

Validation: Ran 382 tests in 4.399s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b81-no-clock-unknown.json and b81-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 382 tests pass. First identifier word reserved bit15 guarded; second fullword accepted including values resembling control data at a different address. No receive data synthesized. Declared run reaches1057 at mailbox0 control2308 with prohibited MBC011. Next audit must verify CPU/arguments and applicable documentation, not silently accept undefined mode. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.


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

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 386 tests pass;25-case matrix and user-input request recorded. Both reviewed chip manuals and technical update prohibit mode011; no behavior waiver found. No physical ECU requirement invented, no prohibited mode accepted. Autonomous milestone unachieved and parents retain evidence gate; additional source/profile evidence genuinely needed for faithful progress. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## Packaged launcher correction (B83/#90)

Verification found earlier EXEs always launched GUI: diagnostic flags were source-CLI capabilities, not a functioning packaged CLI. B83 routes supplied arguments to the existing diagnostic entry point and preserves no-argument GUI launch. Windows CI now executes the actual one-file EXE against a generated synthetic image and validates the JSON result/fixture provenance before release. The Windows command above applies to the B83 release and later; earlier EXEs contain their core changes but do not support that command path. This packaging fix does not resolve the mailbox evidence gate or achieve the autonomous milestone.

## B83/#90

B83: route packaged CLI arguments and require actual Windows EXE smoke verification.

Validation: Ran 388 tests in 41.535s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b83-no-clock-unknown.json and b83-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 388 local tests passed, including original-hash regressions; completed suite reused rather than redundantly rerun. Packaging bug corrected; CI must exercise generated image/fixture provenance through actual EXE. Prior packaged CLI examples corrected. Prohibited mailbox evidence gate remains; autonomous milestone unachieved. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five ROM-only tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## Separate effect-deferral investigation (B84/#91)

Strict validation still rejects prohibited MBC011. A separately opted-in --experimental-record-can-commands experiment records unsupported/prohibited aligned mailbox word commands without applying their state. It assumes CPU stores complete and confines unresolved effects to CAN; it does not assert actual silicon behavior. Device feedback remains unknown, queued completion inputs cannot clear taint, and bad widths/gaps/unknown CPU values still stop. All exports preserve the opt-in policy and unresolved-command count. This can expose independent downstream gaps but cannot resolve B82 or by itself satisfy the faithful milestone. The user has no technical evidence to provide; public-source investigation continues without requiring them to interpret hardware registers.

## B84/#91

B84: isolate an opt-in CAN command-recording investigation with unknown feedback.

Validation: Ran 392 tests in 49.777s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b84-no-clock-unknown.json and b84-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 392-test full suite passed, plus expanded CLI recorder cases. Strict prohibited write still rejected; recorder logs without applying mailbox state and taints CAN feedback. Delayed completion cannot clear taint. Separate experiment reaches1059 at documented byte data initialization, PCE74/op2D50; faithful milestone and hardware gate remain unresolved. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B85/#92

B85: accept documented byte/word mailbox data configuration writes.

Validation: Ran 394 tests in 50.616s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b85-no-clock-unknown.json and b85-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 394 tests cover both channels/all mailboxes and big-endian overlap without invented receive contents or transmission. Strict scenario unchanged; separate recording experiment reaches1140 at software-owned MBIMR read. Next task examines whether unknown-effect scope unnecessarily hides documented static latches; dynamic CAN status remains unresolved. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

B86/#93 refines the recording experiment: MBIMR bits are software-owned R/W mask latches (section16.5.7), not bus-activity feedback. Reads may retain their actual prior CPU-written or explicitly reset-established value. An unknown reset-processing value remains unknown; no constant is selected to satisfy a read. Dynamic status and prohibited mailbox effects remain unknown, and the unresolved marker persists. This isolation contract is part of the experiment, not validated prohibited-mode behavior.

## B86/#93

B86: preserve software-owned mailbox mask values under isolated unresolved effects.

Validation: Ran 396 tests in 38.640s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b86-no-clock-unknown.json and b86-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 396 tests pass. MBIMR reads retain only CPU/reset-established latch values; pending reset unknown remains a stop. Dynamic CAN status remains unknown and recorder marker persists. Separate experiment reaches1222 at GSR reset-status branch PCDD6/op8903. Strict scene still rejects2308; next work can isolate explicitly supplied reset-status inputs without validating prohibited mailbox behavior. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

B87/#94 adds a further independent opt-in --experimental-isolate-can-reset-status (requires --experimental-record-can-commands). Its preserve_supplied_reset_status fixture key confines deferred mailbox uncertainty away from the prior known reset-status bit and explicit reset/recessive event inputs. Only GSR3 can retain/receive knowledge; other dynamic status remains unknown and unresolved effects are not cleared. Default strict and legacy recording behavior remain unchanged. This is a stronger declared isolation hypothesis for investigation, not evidence that prohibited mailbox011 works.

## B87/#94

B87: isolate prior known and explicitly supplied CAN reset-status bit in a separate investigation.

Validation: Ran 400 tests in 35.946s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b87-no-clock-unknown.json and b87-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 400 tests pass. Only GSR3 may follow supplied reset/recessive events despite deferred mailbox effects; all other dynamic status remains unknown and taint persists. Existing strict/legacy behavior unchanged. Conditional isolation scenario reaches1227, PC226/op22A1 TXACK0_0 write FFFFD032=FFFE. No faithful CAN or recurring-interrupt milestone claim. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B88/#95

B88: model CAN transmit/abort acknowledge W1C status banks.

Validation: Ran 403 tests in 35.894s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b88-no-clock-unknown.json and b88-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 403 tests pass. Reset/manual/processing masks, low-word fixed mailbox0 bit, partial clear knowledge, widths/channels verified. No transmit/abort event synthesized. Isolated investigation reaches1236 at RXPR0_0 write FFFFD042=FFFF, PC238/op23E1. Strict prohibited-mode gate and unresolved marker remain. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B89/#96

B89: model receive/remote/overrun W1C mailbox status banks.

Validation: Ran 406 tests in 26.392s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b89-no-clock-unknown.json and b89-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 406 tests pass. All16 receive flags including mailbox0, partial/manual/reset masks, W1C and bank/channel isolation verified with no CAN frames or IRQs synthesized. Isolated investigation reaches1248 at IRR0 word write FFFFD008=FFFF, PC250/op23E1. Strict mode and unresolved marker remain unchanged. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

26 October continuation: B88-B90 add documented acknowledgement/receive/remote/overrun W1C status banks and IRR/IMR. CPU writes clear only documented bits; derived IRQ bits clear only when their entire source status group is proven zero. No transmit/receive/abort/timer event is fabricated. The reset-status-isolated recording investigation reaches1651/1650 at a read of unwritten reset RAM FFFFBFFC (PC68E/op6022). Strict and earlier scenarios remain distinct; this is not initialization/interrupt milestone completion.

## B90/#97

B90: model CAN IRR/IMR W1C, derived clears and software mask latches.

Validation: Ran 410 tests in 4.971s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b90-no-clock-unknown.json and b90-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 410 tests pass. Read-only derived bits ignore direct writes and clear only with proven source-bank clears; unknown manual/processing states retained. No CAN events synthesized. Separate isolated investigation reaches1651 at unwritten reset RAM FFFFBFFC, PC68E/op6022; strict mailbox-mode gate remains unresolved. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B91/#98

B91: implement documented CMP/PL signed-positive comparison.

Validation: Ran 413 tests in 4.549s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b91-no-clock-unknown.json and b91-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 413 tests pass, including all16 target registers, signed boundaries, unknown operand preservation and branch delay-slot execution. Strict scenarios unchanged. Separate local RAM-word experiments0/FFFFFFFF (explicit synthetic prior contents, never physical reset defaults) now reach1744/1743 at SUB R2,R4 opcode3428/PC562; neither is a baseline or boot claim. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B92/#99

B92: implement documented SUB and CMP/PZ for firmware delay-loop path.

Validation: Ran 418 tests in 5.900s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b92-no-clock-unknown.json and b92-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 418 tests pass. Source SH-2E Rev2 sections7.2.60 and7.2.15. Experimental RAM0/FFFFFFFF investigation now completes100000 instructions with zero IRQ entries, looping in startup; no sustained initialization claim. Strict188 and conditional hardware gates unchanged. Next examine repeated control flow and timing inputs, with assumptions explicit. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B93/#100

B93: add reproducible startup investigation with explicit prior-RAM, clock and optional pin hypotheses.

Validation: Ran 422 tests in 4.980s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b93-no-clock-unknown.json and b93-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 422 tests pass. Exploration envelope is separate from baseline and rejected by baseline reviewer; explicit hypotheses preserved, no physical reset RAM asserted. Matrix of8 cases distinguishes instruction-limit/delay/external-input stops. Phi16 +RAM0+PortB0/FFFF reaches58525/58524 at FFFFF708 byte write1, PCC3C4/op2010,7 watchdog overflows,0 firmware IRQs. Next identify SCI register from Rev3; strict and CAN-prohibition gates remain open. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B94/#101

B94: add byte-only SYSCR1 already-enabled RAM command and partial readback.

Validation: Ran 425 tests in 8.819s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b94-no-clock-unknown.json and b94-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 425 tests pass. Corrected FFFFF708 identification to SYSCR1 (not SCI), source Rev3 table25.3/25.2.2. Only byte1 when RAME already known1 accepted; reserved/clock/AUD/RAM-disable transitions rejected atomically. Conflicting AUDSRST initial descriptions and unsupplied OSCSTOP preserved unknown. New experiment reaches58527/58526 then unknown physical Port D FFFFF746 word at PCC3C8/op6031,0 IRQs. Strict/CAN gates unchanged. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B95/#102

B95: preserve explicit Port C/D hypotheses in separate exploration.

Validation: Ran 427 tests in 9.428s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b95-no-clock-unknown.json and b95-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 427 tests pass. Missing pins stay unknown; explicit values validated and recorded. Paired PB/PD0 orFFFF with PC0/RAM0/phi16 reaches58532/58531 at MOVT R0 opcode0029/PCC3D2. All assumptions remain hypotheses;0 IRQs, strict/CAN gates remainopen. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B96/#103

B96: implement MOVT with exact known/unknown T transfer.

Validation: Ran 430 tests in 10.456s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b96-no-clock-unknown.json and b96-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 430 tests pass. All16 targets, partial bit0 knowledge, guarded consumer and delay-slot coverage. Explicit RAM0/phi16/PC0/PBPD0 orFFFF investigations now reach58566/58564 attempts at FFFFEC00 long write7FFFFFFF, PCBD9C/op2342;0 firmware IRQs. Need identify next hardware register before implementation. Defaults unchanged. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B97/#104

B97: implement inactive UBC configuration with atomic big-endian accesses.

Validation: Ran 433 tests in 6.342s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b97-no-clock-unknown.json and b97-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 433 tests pass. Rev3 table8.1/8.2-8.3 support UBAR/UBAMR/UBBR/UBCR storage only with proveninactive breakconditions. Module stop resets UBC, unknown manual/clock state guarded; reserved writes/combined accesses atomic. Experimental PBPD0/FFFF reaches58571/58569 attempts at UBBR E8 enabling data-write breakconditions, PCBDA6/op2011,0 IRQs. Next examine active UBC semantics rather than ignoring debug interrupts. Strict and CAN gates remainopen. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B98/#105

B98: accept known CPU data-write UBC setup with fail-closed match guard.

Validation: Ran 435 tests in 6.607s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b98-no-clock-unknown.json and b98-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 435 tests pass. Address-mask/size matching guards concrete/partial stores before any sideeffect; unsupported read/fetch/unknown matching rejects setup. No UBC IRQ or trigger timing fabricated. PBPD0/FFFF experiments now reach58586/58584 attempts at FFFFF400 byte0, PCBE2C/op2740,0 IRQs. Next identify ATU control register. Strict/CAN gates unchanged. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B99/#106

B99: add stopped TSTR2/TSTR3 and PSCR2-4 common-control subset.

Validation: Ran 438 tests in 5.997s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b99-no-clock-unknown.json and b99-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 438 tests pass. Source Rev3 table11.3/11.2.1/11.2.2. Only byte stop0 commands and stopped-counter fivebitprescaler config accepted; other channel starts/combined widths guarded. No other timer clock/events modelled. PBPD0/FFFF experiments reach58590/58588 attempts at FFFFF666 word0, PCBE34/op2141,0IRQs; next identify required timer register. Strict gates unchanged. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B100/#107

B100: implement documented DSTR zero-command no-op without inventing clears.

Validation: Ran 440 tests in 5.129s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b100-no-clock-unknown.json and b100-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 440 tests pass. Rev3 11.2.11 permits only1writes; zero preserves reset/retained/seeded state, no downcounterstart or physicalpulse fabricated. Incorrectwidth/onebitstart remains guarded. PBPD0/FFFF experiments reach58601/58599 attempts at ITVRR1 FFFFF424 byte0, PCBE4A/op2240,0 IRQs. Strict hardware gates remainopen. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B101/#108

B101: add stopped TCNT0 interval/ADC trigger configuration controls.

Validation: Ran 442 tests in 6.327s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b101-no-clock-unknown.json and b101-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 442 tests pass. Rev3 11.2.7 defines8bit R/W ITVRR1/2A/2B; no interval/ADC event without TCNT0 execution. Unknown manual/width guards retained; explicit zero disables controls. PBPD0/FFFF experiments reach58609/58607 attempts at TCR1B FFFFF45C byte4, PCBE5A/op2150,0IRQs. Backlog current checkpoint updated; next stopped TCR1B config. Strict gates unchanged. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B102/#109

B102: add stopped TCR1B clock-selection configuration without counter aliasing.

Validation: Ran 444 tests in 5.794s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b102-no-clock-unknown.json and b102-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 444 tests pass. Rev3 11.2.3 internal/TCLKA/B selection stored only with knownstopped TCNT1B; otherclocks/reserved/paired widths rejected. Existing1A counter/IRQs unaffected. Explicit PBPD0/FFFF experiments reach58612/58610 attempts at TRGMDR FFFFF466 byte80, PCBE60/op2030,0IRQs. Next inspect trigger effects from manual before accepting. Strict/CAN gates unchanged. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B103/#110

B103: package explicit exploration route and verify both executable modes in Windows CI.

Validation: Ran 445 tests in 5.153s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b103-no-clock-unknown.json and b103-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 445 tests pass. Launcher --explore-startup explicitly imports module into packagedEXE; full priorRAM/phi/B/C/D assumptions checked by actual generated-ROM Windows smoke. Local downloadedEXE verification remains required before closing#110. Strict behavior and firmware progress unchanged. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B104/#111

B104: add TRGMDR only with disabled channel8 trigger connections.

Validation: Ran 447 tests in 5.205s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b104-no-clock-unknown.json and b104-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 447 tests pass. Rev3 11.2.8/12/13: TRGMDR0/80 stored only with known DSTR/TCNR/OTR0; TCNR/OTR word0 disables connections; unknown/active/reserved/width writes rejected. No pulses or IRQs invented. PBPD0/FFFF experiments reach58614/58612 attempts at TCR2A FFFFF62B byte4, PCBE64/op2250. Next stopped TCR2A/Bclockconfig from same verified section11.2.3. Strict gates unchanged. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B105/#112

B105: add separate stopped TCR2A/TCR2B clock-selection latches.

Validation: Ran 449 tests in 5.138s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b105-no-clock-unknown.json and b105-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 449 tests pass. Rev3 11.2.3/table11.3 stopguard perSTR2A/STR1B2B, reserved/AGCK/paired widths guarded. No counteralias or IRQ generation. PBPD0/FFFF investigations reach58618/58616 attempts at TMDR FFFFF484 byte0, PCBE6C/op2140. Strict/CAN gates remainopen; next timer mode initialization. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

B103 downloaded Windows verification: release v0.2.0-dev.169.1, SHA256725fad5c090676fd1e2599867a9af0508ed7bd15376b9090305f93afea7cd6eb matched published SHA256SUMS before execution. Actual EXE exited0 and produced strict188/187 plus explicit-exploration58612/58611 with assumptions retained; zero firmware IRQs. This confirms packaging/reproducibility, not initialization. See evidence/b103-packaged-verification.json. Later source checkpoints can advance the experimental stop.

## B106/#113

B106: add stopped timer3-5 non-PWM mode and separate clock configurations.

Validation: Ran 452 tests in 9.133s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b106-no-clock-unknown.json and b106-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 452 tests pass. TMDR0 only with channels3-5 stopped; individual TCR3/4/5 latches enforce reserved/clock/stop guards. No PWM/pin/counter/IRQ effects invented. Explicit PBPD0/FFFF investigations reach58628/58626 attempts at TCR6A FFFFF521 byte44, PCBE80/op2260. B103 downloaded release169 checksum and actualEXE strict/exploration verification recorded. Next stopped timer6/7 clockfields from verified manual section11.2.3. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B107/#114

B107: add stopped timer6/7 clockfields and observed PMDR0 configuration.

Validation: Ran 454 tests in 8.639s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b107-no-clock-unknown.json and b107-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 455 tests pass. Paired divisorfields0..5 /reservedbits validate atomically, perTSTR2stopguard; PMDR0 only with timer6stopped. No PWM/counters/IRQs invented. Next stop recorded in b107-exploration; strict gates unchanged. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

B107 correction before issue closure: a local relative-path edit failed while the later test command succeeded. The first B107 publication therefore contained clockfields only (454tests), despite its appended decision text anticipating PMDR. Applied the missing PMDR edit in the correct repository directory, added its test and reran the full suite/scenarios before final publication. The corrected checkpoint below supersedes that incomplete scope/count; no initialization claim follows.

## B107/#114

B107 corrected: complete stopped timer6/7 clocks and PMDR0 initialization.

Validation: Ran 455 tests in 6.783s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b107-no-clock-unknown.json and b107-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 455 tests now pass; missing PMDR edit corrected and rerun before issueclosure. Clockfield and PMDR0 stop/mode guards verified. Updated exploration reports record nextstop. No PWM/counter/IRQ claim; strict gates unchanged. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B108/#115

B108: accept trigger connections only with proven zero downcounters/no reload.

Validation: Ran 457 tests in 8.223s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b108-no-clock-unknown.json and b108-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 457 tests pass. Documented power DCNT8A..P0 and no reload tracked; manualunknown/nonzero/running/reloadpossible states reject nonzero connectionchanges. TCNR/OTR zero disables retained; TRGMDR requiresquiescence. No downcounter/pulse/IRQ generated. PBPD0/FFFF exploration reaches58644/58642 attempts at TCR8 FFFFF668 byte44, PCBEA0/op2360. Next exact TCR8 fields, source11.2.3. Strict gates unchanged. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B109/#116

B109: add quiescent TCR8 clocks and observed RLDENR disable.

Validation: Ran 460 tests in 5.968s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b109-no-clock-unknown.json and b109-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 460 tests pass. TCR8 divisorfields and quiescence guards; RLDENR0 disablesreload without changing known/unknowncounter contents. Otherreload/clock/states remainexplicitstops. Nextstop in b109-exploration; no firmwareIRQ/init claim. Strict hardware gates unchanged. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B110/#117

B110: add stopped TCR11 clock configuration with exact reserved-bit3 rule.

Validation: Ran 462 tests in 5.542s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b110-no-clock-unknown.json and b110-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 462 tests pass. TCR11 fields/stop/reserved/unknownmanual/width checks; no counter11execution. Explicit PBPD0/FFFF experiments reach58650/58648 attempts at TCNT0 FFFFF430 long0, PCBEAC/op2342. Next stopped-counter initialization from Rev3 11.2.15/table11.3; strict/CAN gates remainopen. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B111/#118

B111: implement documented stopped TCNT initialization with distinct widths/reset values.

Validation: Ran 464 tests in 5.489s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b111-no-clock-unknown.json and b111-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 464 tests pass. TCNT0 long32reset0; independent1B/2A/2B/3/4/5/11 wordsreset0 and6/7 wordsreset1. Per-counter start/read/write/width/manual guards. No alias/counting/events invented; existing1Amodel unchanged. Explicit PBPD0/FFFF runs reach58669/58667 attempts at TSTR1 FFFFF401 bytewrite, PCBED2/op2340. Need exact requestedstartset and declaredtimerclocks before runtime implementation. Strict gates unchanged. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B112/#119

B112: audit TSTR1 FF runtime dependencies and preserve rejected command evidence.

Validation: Ran 465 tests in 10.239s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b112-no-clock-unknown.json and b112-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 465 tests pass. Generated exactFF request rejects atomically withvalue retained,0completed/ticks/events/IRQs. Source audit enumerates simultaneous0/1/2/3/4/5/10 starts; no silentmask/frozenruntime. Next TCNT0 explicitPphi/moduleflags, then sharedvector80/OVI0routes, then othergroup/clocks/trigger models. Originalexplicitbranch58669/58667 attempts unchanged; strict/CANgates unresolved. Backlog currentruntime dependency updated. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B113/#120

B113: add separately bound TCNT0 Pphi runtime and interval/overflow requests.

Validation: Ran 470 tests in 7.232s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b113-no-clock-unknown.json and b113-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 470 tests pass. Zero-phase explicitPphi/PSCR1 counting,32bitwrap, repeatedintervalrises and sharedflags, read-before-zero clear, OVE0 request; no ADCtrigger/capture/otherstart accepted. Unmasked configured newrequests stop explicitly as unsupportedCPUroute, ratherthan disappearing. ActualTSTRFF remainsblocked; no originalfirmware IRQ/init claim. Next verify table7.3 routes/generated recurringhandlers. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B114/#121

B114: route ATU0 interval/overflow to CPU and verify recurring generated handlers.

Validation: Ran 474 tests in 5.822s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b114-no-clock-unknown.json and b114-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 474 tests pass. Sharedvector80/IPRC7:4 and OVI0vector92/IPRD11:8 verified priority/mask/ack/RTE/stack/SR/held/delay-slot paths. Generated firmware handles3 repeated interval entries; no originalfirmware IRQ/initclaim. Othercounter/ADC/capture/FFstarts remainguarded. Next remaining timer runtime groups/channel10; currentbacklog updated. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User authorized autonomous milestone work; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.
