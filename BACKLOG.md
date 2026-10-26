# Active ECU emulator backlog

Reviewed against main, the open parent and explicitly scoped child GitHub issues, source and the latest completed pass on **24 October 2026**.

The goal is a virtual NC ECU executing supported firmware and interacting with an engine model. It is not currently a fully booted ECU. The earlier eight-task list described bounded feature subsets; completing it did not complete this goal.

## Verified current position

- **438 local tests passed** in the last implementation pass, including locally supplied original-hash regressions. Public CI passed; private ROM-dependent cases are skipped there. Autonomous startup pass B72-B82 reran the full suite and strict/conditional scenario matrix; hardware evidence gates remain unresolved.
- Previously downloaded and checksum-verified application baseline: [v0.2.0-dev.136.1](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/releases/tag/v0.2.0-dev.136.1). Latest implementation/release evidence is linked from [B82/#89](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/89) and [pass report](docs/AUTONOMOUS_STARTUP_PASS.md).
- **Default reference:** original LF9VEB SHA-256, power reset, NMI high, 300-instruction budget, no supplied physical pins, H-UDI/clock unknown. Stops at **188 attempted instructions**, reading SDSR at `0xFFFFF7C2`, PC `0x00000EF8`, opcode `6321`: unknown H-UDI state.
- **Separate conditional investigation:** explicit H-UDI assumption plus artificial phi-per-completed-instruction=1 and a **10,000** budget stops at **592 attempts / 591 completed**, PC `0x000007B6`, opcode `2301`, word store to MCR0 `0xFFFFD000`. The written value still contains unknown reserved bit6 after read/OR1. No concrete value or reset side effect is selected. The same conditional run with a 300 budget reaches only the instruction limit.
- **Additional experimental branch:** explicit MCR bit6=0 plus declared H-UDI state/artificial phi1/budget10000 without a completion fixture reaches **976 attempts /975 completed**, PC00000DB8/op8B03 branching on unknown GSR reset status. Stack saves now preserve reset-undefined R11 through RAM without selecting a value. Bit6=1 still rejects word0041 at592. These are hypothetical input branches, not a resolved hardware profile. Public provenance matches the NC Flash example Git blob; it does not establish physical MCU revision or reset wiring.
- No physical instruction timing, CAN synchronization, successful firmware main loop, injector/ignition behavior or engine operation has been established.

## Open work in priority order

There are **three open parent workstreams**. The current autonomous milestone is unachieved: no sustained original-firmware main operation or recurring interrupts observed. The five requested children B67-B71/#74-78 are complete within their documented research/implementation scope; per-issue commit/CI/release links record closure. Research children may close with documented unresolved evidence; their parent gates remain open. The items below are work packages and evidence gates, not an invented fixed countdown or percentage to completion. Split implementation packages into bounded child issues only after their register/trace evidence and acceptance tests are specific enough.

| Priority | Work package | Current limitation / next concrete result | Tracked under |
|---|---|---|---|
| P0 evidence/model | Resolve prohibited mailbox0 MBC011 command | Explicit completion scenario stops1057 at control2308. CPU/argument audit confirms literal mode3; reviewed primary manuals and technical update prohibit011. Need applicable behavior evidence or independent CPU/profile correction. Partial extension and new integer instructions are implemented. | [CPU #2](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/2) |
| Evidence gate | Resolve the default H-UDI startup state | Verify actual TRST/reset/debug history and relevant board wiring, or produce a documented unresolved evidence report. A ROM dump alone does not establish this state. Keep alternative assumptions conditional. | [Hardware #1](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/1) |
| P1 software / evidence gate | Investigate the conditional MCR read/modify/write stop | Review verified MCU revision, official documentation/errata and justified read/write treatment for reserved bit6. Default unknown mode retains the reduced reproducer and unknown mask; explicit zero/one readback fixtures do not resolve hardware behavior. Reset/release commands0/1 are accepted; GSR typed reads preserve uncertain status and reserved readback. Completion/status transitions remain unmodelled. Inactive mailbox2700 also retains NMC contrary to the documented unused-mailbox initialization requirement; command recording is not proof of valid CAN operation. | [Hardware #1](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/1), [CPU #2](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/2) |
| P1 | Establish a verified clock/reset/board profile | Identify oscillator/dividers, MCU/memory/reset behavior and input/output pin mapping for the tested hardware family. Separate documented facts, supplied scenarios and unknowns. | [Hardware #1](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/1) |
| P1 | Complete CPU behavior required by execution | Extend missing integer/FPU/exception behavior from concrete executed evidence; finite FPU support is not a complete CPU. Compare independent synthetic vectors and, where available, hardware/reference traces. | [CPU #2](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/2) |
| P1 | Deliver ATU/ADC interrupt requests to CPU | IMI1A, IMI1B, OVI1A and ADI0 now reach the CPU through B54/B55/B57/B58. Other timer/ADC sources remain outside this bounded route subset. Scope one source at a time with verified vector, priority/mask, acknowledgement, entry/return and delayed-slot tests. The existing ITI CPU route is not an ATU/ADC route. | [Peripherals #3](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/3), [CPU #2](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/2) |
| P1 | Extend peripherals and timing as firmware requires | Add required CAN lifecycle/status/traffic, timer channels/prescalers, ADC channels/triggers, watchdog and other accessed interfaces. Selected-counter ticks, zero-phase supplied Pphi packets with PSCR1/TCR1A division, TCLKA/B levels and ADC completion delay are explicit fixtures, not measured hardware timing. Clock reconfiguration after binding, TI10/AGCKM and other timer channels remain unsupported. | [Peripherals #3](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/3) |
| P1 milestone | Demonstrate sustained firmware initialization/main-loop execution | Define and verify firmware-specific initialization/main-loop evidence, functioning scheduled interrupts and absence of unexplained stops under a declared hardware profile. More instructions or repeated PCs alone do not meet this milestone. | [CPU #2](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/2) |
| P2 | Replace generic fixtures with verified NC engine inputs | Establish crank/cam pattern, phase and pin routing; sensor channels, reference supplies and scaling; required switches/network inputs. Current square waves and AN0 input do not establish those mappings. | [Hardware #1](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/1), [Peripherals #3](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/3) |
| P2 | Identify firmware actuator commands | Map outputs to documented ECU circuitry and capture injector/ignition/throttle commands with verified timing. Current PortC records are raw latch commands; physical levels and ECU function are unknown. | [Hardware #1](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/1), [Peripherals #3](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/3) |
| P2 milestone | Add and validate an engine feedback model | Make firmware commands affect simulated engine state and subsequent inputs; test start, idle, RPM changes, deceleration and faults against external evidence. No current combustion/engine feedback model is claimed. | [Peripherals #3](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/3) |
| P3 | Validate supported hardware/ROM families | Obtain authorized representative ROMs/board evidence and run identical declared scenarios; publish per-family support and failures. One LF9VEB regression does not establish all NC compatibility. | [Hardware #1](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/1), [Peripherals #3](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/3) |

**Next dependency:** the declared reset1/bus64 or256 experiment reaches1057/1056, PCE70/op81C2, mailbox0 control2308 (prohibited MBC011). Check applicable primary behavior evidence or independent CPU/profile correction before accepting it; current reviewed manuals and technical update prohibit it. See [audit and evidence needed](docs/MAILBOX_MODE_AUDIT.md). No silent mode conversion, ignored write, firmware patch or guessed bus response. The user has no matching ECU; a public technical reference/trace or another suitably identified ROM can supply evidence without purchasing hardware.

## Completed bounded capabilities and their limits

| Completed task | What is implemented | What it does not establish |
|---|---|---|
| [B13/#16](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/16) | FR/FPUL unknown after reset; FPSCR documented reset `0x00040001`, fixed/writable bits, system transfers | Full FPU or firmware use of these instructions |
| [B14/#17](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/17) | Raw FMOV forms, immediates and bounded FLOAT/FTRC | All conversions or exceptional cases |
| [B15/#18](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/18) | Finite FADD/FSUB/FMUL/FDIV with exact rational truncation, signed zero and fixed DN | NaN/infinity/divide-zero/overflow/enabled-exception execution; these stop explicitly |
| [B22/#29](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/29) | Bounded ATU1A counter/compare/capture and module request events; B24 extends the shared counter capture to GR1B | Other timer channels and physical timing; B57-B60 add IMI1B/OVI1A and explicit internal/external clock sources |
| [B23/#30](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/30) | Ideal single AN0 conversion with explicit voltage/reference/completion, data/status and request handling | Other ADC modes, physical sampling accuracy/timing or sensor identity; ADI0 CPU dispatch was added by B55 |
| [B24/#31](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/31) | Deterministic explicitly phased synthetic crank/cam square waves reaching captures | Actual NC tooth pattern, physical pin/engine routing |
| [B25/#32](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/32) | Timestamped raw PortC latch commands and known/changed masks | Identified injector/ignition/throttle outputs or physical pin activity |
| [B28/#35](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/35) | Optional AN0 GUI/CLI controls; synthetic firmware reads change with the input; provenance persists | Original firmware consuming a mapped real engine sensor or successful ECU operation |

Earlier closed tasks cover bounded reset, memory/integer instructions, GPIO, ITI dispatch, watchdog interval fixtures, H-UDI scenarios, HCAN command subsets and reporting. Their original acceptance criteria and releases remain linked in their closed issues and pass reports. None is reopened merely because its larger parent goal is incomplete.

## Working agreement and completion checks

- One child issue must have a bounded scope and observable finish line. Parent milestones are not one-pass tickets.
- Before closure: implement on main, run focused and full appropriate tests, rerun declared representative ROM scenarios, review every open issue for scope/dependencies/duplication, update this active backlog, verify successful CI and a versioned Windows EXE, and record commit/test/release/review links in the issue.
- Keep private ROM bytes, local paths and full traces out of public artifacts; publish only reduced evidence.
- Distinguish attempted/completed instructions, exact failure PC/opcode/access, supplied inputs and physical observations. Instruction limits/repetition are not boot evidence.
- Prefer narrowing an existing issue over a duplicate. Missing hardware evidence can be a completed research result only when the blocker and reproducer are documented; it is not emulation success.
- Preserve unknown states and unsupported-mode stops. Synthetic fixtures must retain provenance and cannot become the default physical profile.
- Documentation-only audits do not change emulator behavior or require redundant runtime tests. Executable releases validate the implementation revision they identify; publishing a later document does not imply another implementation milestone.

## Review record and history

**24 October 2026 audit:** compared all open parent issue bodies, current source and eight-task evidence. Found stale P0/P1 introductions, completed tasks presented in a priority queue, an incorrect implication that FPSCR reset was unknown, and an obsolete B28 stop line that did not enumerate further work. Replaced the mixed queue with the active work packages above; retained the three existing parents, with no duplicate issues or fabricated task estimate. Updated parent status/next milestones. This is a planning/documentation correction; no emulator behavior or support claim changed.

- [Historical backlog and original review entries](docs/BACKLOG_HISTORY_2026-10-24.md) — historical priorities only.
- [Third five-task pass](docs/THIRD_FIVE_TASK_PASS.md)
- [Fourth five-task pass](docs/FOURTH_FIVE_TASK_PASS.md)
- [Eight-task completion evidence](docs/EIGHT_TASK_COMPLETION.md)

## Completed five-task pass and remaining gates

1. B52/#59 H-UDI evidence audit: report at docs/HUDI_STARTUP_AUDIT.md; board state unresolved.
2. B53/#60 CAN startup constraints audit: docs/HCAN_STARTUP_AUDIT.md; no reserved-bit waiver established.
3. B54/#61 ATU IMI1A CPU route: implemented vector96/IPRD[7:4], held flag/acknowledgement and arbitration tests.
4. B55/#62 ADC ADI0 CPU route: implemented vector190/IPRJ[11:8], firmware conversion-read/acknowledgement ISR.
5. B56/#63 integrated synthetic firmware fixture: implemented source CLI and ordered nested/simultaneous evidence in docs/STARTUP_IRQ_PASS.md.

The current application implementation and Windows releases are linked in [B56/#63](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/63); the older baseline link above is retained for history. No claim that a closed research child resolved its parent evidence gate.

B52/#59 completed scope/test review: see [eight-task pass](docs/STARTUP_IRQ_PASS.md). B52 research scope complete; hardware1 gate remains unresolved. B53 CAN audit next, B54/B55 verified vector routes then B56 integration. No duplicate broad research issue.

B53/#60 completed scope/test review: see [eight-task pass](docs/STARTUP_IRQ_PASS.md). B53 research complete with unresolved evidence gate; parents1-3 stay open. B54 ATU source route then B55 ADC and B56 integrated fixture are independent synthetic implementation work.

B54/#61 completed scope/test review: see [eight-task pass](docs/STARTUP_IRQ_PASS.md). B54 implemented; B55 adds ADI0 vector190/IPRJ[11:8], then B56 integration. B52/B53 evidence gates remain open under parents despite completed research.

B55/#62 completed scope/test review: see [eight-task pass](docs/STARTUP_IRQ_PASS.md). B54/B55 routes implemented; only IMI1A/ADI0/ITI supported. B56 combines actual synthetic firmware configuration, explicit capture/conversion events and raw output. Hardware evidence gates stay unresolved.

Current bounded result: IMI1A and ADI0 CPU routes and generated capture/ADC/GPIO integration are tested. Other sources remain unsupported. B52/B53 research is complete as documented unresolved evidence; no physical-profile gate is marked resolved. [Current pass](docs/STARTUP_IRQ_PASS.md).

B56/#63 completed scope/test review: see [eight-task pass](docs/STARTUP_IRQ_PASS.md). All five requested bounded tasks completed in scope, subject to final CI/release. Research1/2 retain unresolved evidence under parent1; IMI1A/ADI0 routes and integration implemented. Other sources and physical/engine work remain open; no speculative duplicate issue added.

B57/#64 completed scope/test review: see [timer/clock pass](docs/TIMER_CLOCK_PASS.md). B57 closes existing capture-route gap. B58 overflow, B59 internal clock packets, B60 external edges and B61 integration are explicit requested child scopes; hardware gates unchanged.

B58/#65 completed scope/test review: see [timer/clock pass](docs/TIMER_CLOCK_PASS.md). B58 overflow prerequisite complete. B59 internal supplied clocks and B60 external selected edges follow; B61 integrates dual captures through rollover. Hardware gates remain unchanged.

B59/#66 completed scope/test review: see [timer/clock pass](docs/TIMER_CLOCK_PASS.md). All 192 divider combinations checked; supplied fixture phase is explicit, clock frequency and physical timing remain unknown.

B60/#67 completed scope/test review: see [timer/clock pass](docs/TIMER_CLOCK_PASS.md). Both sources and all four edge selections tested; first level establishes a baseline, unselected pins cannot advance the counter. TI10 and AGCKM remain unsupported.

B61 adds generated dual-capture firmware: both supplied clock sources produce GR1A=FFFF, GR1B=0001, interrupt order IMI1A/OVI1A/IMI1B, independent flag clearing and restored stack. This does not remove either startup gate. See [timer/clock evidence](docs/TIMER_CLOCK_PASS.md).

B61/#68 completed scope/test review: see [eight-task pass](docs/TIMER_CLOCK_PASS.md). All five child scopes reviewed against remaining work packages. Dual captures, overflow priority, independent acknowledgement, RTE and deterministic repeated reports verified; startup hardware gates remain unresolved.

B62/#69 completed scope/test review: see [eight-task pass](docs/ROM_ONLY_PASS.md). ROM-only path selected from user context. No matching ECU available; provenance match does not resolve silicon or reset gates. Review keeps existing parents and five bounded children, no duplicate broad hardware task.

B63/#70 completed scope/test review: see [eight-task pass](docs/ROM_ONLY_PASS.md). No new evidence resolves actual TRST history, silicon revision or reserved readback. Backlog separates physical evidence gates from executable software scenarios. B64/B65/B66 remain bounded; no duplicated physical research.

B64/#71 completed scope/test review: see [eight-task pass](docs/ROM_ONLY_PASS.md). 341 tests pass. Unknown default and both hypothetical readback branches checked; known-one writes remain rejected. B65 is limited to the next documented command exposed by the zero branch; no bus or board state invented.

B65/#72 completed scope/test review: see [eight-task pass](docs/ROM_ONLY_PASS.md). 342 tests pass. Explicit zero-readback run reaches960 attempts/959 completed at reset-undefined R11 stack save; one-readback remains rejected at592. Strict188 and original conditional592 preserved. Full reset processing, bus state and unknown-stack handling remain open.

## ROM-only completion and remaining work

B62/#69 establishes a pinned public blob-identity match; B63/#70 records unresolved profile constraints; B64/#71 adds explicit readback choices with export provenance; B65/#72 accepts documented reset requests without completion; B66/#73 regresses the 19-case matrix. See [ROM-only pass](docs/ROM_ONLY_PASS.md). Earlier pass descriptions above are historical snapshots. Three broad parents remain open, with no fixed remaining count.

B66/#73 completed scope/test review: see [eight-task pass](docs/ROM_ONLY_PASS.md). 346 tests pass including deterministic full-image matrix repeats. All five bounded scopes reviewed; next software dependency is unknown R11 stack save, not a physical ECU purchase or repeat of an unchanged audit. Strict188, existing conditional592 and new hypothetical960 remain distinct; hardware/engine goals stay open.

B67/#74 completed scope/test review: see [eight-task pass](docs/UNKNOWN_STACK_PASS.md). 349 tests pass; partial RAM transport preserves overlap masks while concrete reads/peripheral writes require known bits. Updated earlier RAM-store test to the new documented transport contract; strict and ROM-only stops unchanged before B68 stack opcodes.

B68/#75 completed scope/test review: see [eight-task pass](docs/UNKNOWN_STACK_PASS.md). 351 tests pass. Zero-readback experiment now reaches973 attempts at GSR0 word read FFFFD002, PCDB2/op6351. No register initialized artificially; raw RAM/peripheral/control guards remain. B70 will be narrowed to GSR reset-status uncertainty after B69.

B69/#76 completed scope/test review: see [eight-task pass](docs/UNKNOWN_STACK_PASS.md). Supported integer MOV memory paths and register copies now transport masks consistently; unknown addresses and peripheral values still stop. Expected experimental dependency remains GSR0 at PCDB2. Other CPU/floating-point consumers remain concrete-only.

B70/#77 completed scope/test review: see [eight-task pass](docs/UNKNOWN_STACK_PASS.md). 356 tests pass. GSR low6 reset bits are0x0C; reserved15:6 readback is not guaranteed. After software reset/release requests dynamic flags remain unknown. Zero-readback experiment reaches974 attempts, PCDB4/op633D EXTU.W on partial GSR; no reset completion or CAN state guessed.

## Unknown-stack pass current result

B67-B69 add RAM masks and supported MOV transport; B70 adds conservative GSR status reads; B71 verifies generated call/save/restore/return, dangerous-use guards and the19-case matrix. See [current pass](docs/UNKNOWN_STACK_PASS.md). Earlier pass counts/stops above are historical snapshots. Three broad parents remain open; no fixed remaining task count or full-boot claim.

B71/#78 completed scope/test review: see [eight-task pass](docs/UNKNOWN_STACK_PASS.md). 359 tests pass. All open issue bodies and backlog rows reviewed: partial EXTU/EXTS is next concrete software scope; CAN completion, board verification and engine operation stay open. Earlier strict188 and original conditional592 preserved; new experimental974 remains labelled, not full boot.

B72/#79 completed scope/test review: see [autonomous startup pass](docs/AUTONOMOUS_STARTUP_PASS.md). 361 tests pass. Experimental run reaches976 at BF on unknown GSR reset flag; next bounded work is opt-in explicit CAN reset-completion input, never an inferred hardware delay. Autonomous milestone requires original firmware recurring interrupts, not a larger count.

B73/#80 completed scope/test review: see [autonomous startup pass](docs/AUTONOMOUS_STARTUP_PASS.md). 365 tests pass. Generation checks cancel stale requests; default no completion unchanged. Supplied reset completion establishes low reset flags; supplied11-recessive event proves only reset flag clear. Assumed delay1 run reaches984 at BCR1 write E320, PC1CE. Next bounded register task follows; milestone not achieved.

B74/#81 completed scope/test review: see [autonomous startup pass](docs/AUTONOMOUS_STARTUP_PASS.md). 368 tests pass. BCR1/BCR0 reserved readback remains unknown, writes require known configuration mode; cross-register constraints reported without oscillator/baud assumption. Reset completion resets latches. Too-early bus event remains a rejection; declared reset1/bus64 experiment reaches1012 at CMP/HI PCDF6/op3E36.

B75/#82 completed scope/test review: see [autonomous startup pass](docs/AUTONOMOUS_STARTUP_PASS.md). 370 tests pass. Boundary/equality/alias and unknown-operand behavior verified against SH-2E section7 CMP semantics. Declared completion scenario reaches1017 at NOT R4,R2 PC E0E/op6247; no interrupt milestone yet.

B76/#83 completed scope/test review: see [autonomous startup pass](docs/AUTONOMOUS_STARTUP_PASS.md). 372 tests pass. Explicit completion scenario reaches1022 attempts at FFFFD052 word read PC E18/op6331. No physical completion defaults or recurring interrupt claims introduced.

B77/#84 completed scope/test review: see [autonomous startup pass](docs/AUTONOMOUS_STARTUP_PASS.md). 374 tests pass. Mask latches resetFFFF, unknown manual/processing states retained, explicit reset completion restores masks. No CAN events or CPU interrupts fabricated. Completion scenario reaches1024 at MULU.W PCE1C/op204E.

B78/#85 completed scope/test review: see [autonomous startup pass](docs/AUTONOMOUS_STARTUP_PASS.md). 376 tests pass. Unknown high bits do not matter to MULU.W; unknown low operands remain guarded. MACH/T/source registers unchanged. Declared scenario reaches1026 at STS MACL,R0 PCE20/op001A; next MACL transfer scoped separately.

B79/#86 completed scope/test review: see [autonomous startup pass](docs/AUTONOMOUS_STARTUP_PASS.md). 378 tests pass. Undefined MACL transports unknown bits; computed products transfer exactly and preserve T/MACH. Declared scenario reaches1042 at ADD R7,R2 PCE52/op327C. Milestone still requires sustained original-firmware execution and recurring interrupts.

B80/#87 completed scope/test review: see [autonomous startup pass](docs/AUTONOMOUS_STARTUP_PASS.md). 380 tests pass. Boundary/wrap/alias/unknown-input guards verified. Declared completion scenario reaches1047, PCE5C/op2C21, mailbox0 identifier word FFFFD100 value0037. Next bounded work is documented mailbox identifier/control latches; no traffic inferred.

B81/#88 completed scope/test review: see [autonomous startup pass](docs/AUTONOMOUS_STARTUP_PASS.md). 382 tests pass. First identifier word reserved bit15 guarded; second fullword accepted including values resembling control data at a different address. No receive data synthesized. Declared run reaches1057 at mailbox0 control2308 with prohibited MBC011. Next audit must verify CPU/arguments and applicable documentation, not silently accept undefined mode.

## Autonomous startup current result

B72-B82 implemented and audited within their bounded scopes; the broader user milestone is not achieved.386 local tests and a25-case strict/conditional/completion matrix cover known behavior. Explicit completion events permit investigation but do not verify physical timing. Original-firmware interrupt entries remain0. See [current pass](docs/AUTONOMOUS_STARTUP_PASS.md), [mailbox mode gate](docs/MAILBOX_MODE_AUDIT.md). Earlier stop counts/task lists are historical.

B82/#89 completed scope/test review: see [autonomous startup pass](docs/AUTONOMOUS_STARTUP_PASS.md). 386 tests pass;25-case matrix and user-input request recorded. Both reviewed chip manuals and technical update prohibit mode011; no behavior waiver found. No physical ECU requirement invented, no prohibited mode accepted. Autonomous milestone unachieved and parents retain evidence gate; additional source/profile evidence genuinely needed for faithful progress.

B83/#90 corrects the packaged launcher: CLI arguments now use diagnostics, no-argument launch retains GUI. Actual EXE smoke test is required in Windows CI before publication. Earlier packaged CLI examples were inaccurate; use the B83 release or later. Hardware/milestone gate remains unchanged.

B83/#90 completed scope/test review: see [eight-task pass](docs/AUTONOMOUS_STARTUP_PASS.md). 388 local tests passed, including original-hash regressions; completed suite reused rather than redundantly rerun. Packaging bug corrected; CI must exercise generated image/fixture provenance through actual EXE. Prior packaged CLI examples corrected. Prohibited mailbox evidence gate remains; autonomous milestone unachieved.

B84/#91 adds a separate explicit effect-deferral investigation, without changing strict validation: unresolved mailbox writes are recorded, not applied, and later CAN feedback remains unknown. This may expose independent downstream gaps; it does not resolve prohibited-mode semantics or complete the milestone.

B84/#91 completed scope/test review: see [autonomous startup pass](docs/AUTONOMOUS_STARTUP_PASS.md). 392-test full suite passed, plus expanded CLI recorder cases. Strict prohibited write still rejected; recorder logs without applying mailbox state and taints CAN feedback. Delayed completion cannot clear taint. Separate experiment reaches1059 at documented byte data initialization, PCE74/op2D50; faithful milestone and hardware gate remain unresolved.

B85/#92 completed scope/test review: see [autonomous startup pass](docs/AUTONOMOUS_STARTUP_PASS.md). 394 tests cover both channels/all mailboxes and big-endian overlap without invented receive contents or transmission. Strict scenario unchanged; separate recording experiment reaches1140 at software-owned MBIMR read. Next task examines whether unknown-effect scope unnecessarily hides documented static latches; dynamic CAN status remains unresolved.

B86/#93 completed scope/test review: see [autonomous startup pass](docs/AUTONOMOUS_STARTUP_PASS.md). 396 tests pass. MBIMR reads retain only CPU/reset-established latch values; pending reset unknown remains a stop. Dynamic CAN status remains unknown and recorder marker persists. Separate experiment reaches1222 at GSR reset-status branch PCDD6/op8903. Strict scene still rejects2308; next work can isolate explicitly supplied reset-status inputs without validating prohibited mailbox behavior.

B87/#94 completed scope/test review: see [autonomous startup pass](docs/AUTONOMOUS_STARTUP_PASS.md). 400 tests pass. Only GSR3 may follow supplied reset/recessive events despite deferred mailbox effects; all other dynamic status remains unknown and taint persists. Existing strict/legacy behavior unchanged. Conditional isolation scenario reaches1227, PC226/op22A1 TXACK0_0 write FFFFD032=FFFE. No faithful CAN or recurring-interrupt milestone claim.

B88/#95 completed scope/test review: see [autonomous startup pass](docs/AUTONOMOUS_STARTUP_PASS.md). 403 tests pass. Reset/manual/processing masks, low-word fixed mailbox0 bit, partial clear knowledge, widths/channels verified. No transmit/abort event synthesized. Isolated investigation reaches1236 at RXPR0_0 write FFFFD042=FFFF, PC238/op23E1. Strict prohibited-mode gate and unresolved marker remain.

B89/#96 completed scope/test review: see [autonomous startup pass](docs/AUTONOMOUS_STARTUP_PASS.md). 406 tests pass. All16 receive flags including mailbox0, partial/manual/reset masks, W1C and bank/channel isolation verified with no CAN frames or IRQs synthesized. Isolated investigation reaches1248 at IRR0 word write FFFFD008=FFFF, PC250/op23E1. Strict mode and unresolved marker remain unchanged.

B90/#97 completed scope/test review: see [autonomous startup pass](docs/AUTONOMOUS_STARTUP_PASS.md). 410 tests pass. Read-only derived bits ignore direct writes and clear only with proven source-bank clears; unknown manual/processing states retained. No CAN events synthesized. Separate isolated investigation reaches1651 at unwritten reset RAM FFFFBFFC, PC68E/op6022; strict mailbox-mode gate remains unresolved.

B91/#98 completed scope/test review: see [autonomous startup pass](docs/AUTONOMOUS_STARTUP_PASS.md). 413 tests pass, including all16 target registers, signed boundaries, unknown operand preservation and branch delay-slot execution. Strict scenarios unchanged. Separate local RAM-word experiments0/FFFFFFFF (explicit synthetic prior contents, never physical reset defaults) now reach1744/1743 at SUB R2,R4 opcode3428/PC562; neither is a baseline or boot claim.

B92/#99 completed scope/test review: see [autonomous startup pass](docs/AUTONOMOUS_STARTUP_PASS.md). 418 tests pass. Source SH-2E Rev2 sections7.2.60 and7.2.15. Experimental RAM0/FFFFFFFF investigation now completes100000 instructions with zero IRQ entries, looping in startup; no sustained initialization claim. Strict188 and conditional hardware gates unchanged. Next examine repeated control flow and timing inputs, with assumptions explicit.

B93/#100 completed scope/test review: see [autonomous startup pass](docs/AUTONOMOUS_STARTUP_PASS.md). 422 tests pass. Exploration envelope is separate from baseline and rejected by baseline reviewer; explicit hypotheses preserved, no physical reset RAM asserted. Matrix of8 cases distinguishes instruction-limit/delay/external-input stops. Phi16 +RAM0+PortB0/FFFF reaches58525/58524 at FFFFF708 byte write1, PCC3C4/op2010,7 watchdog overflows,0 firmware IRQs. Next identify SCI register from Rev3; strict and CAN-prohibition gates remain open.

B94/#101 completed scope/test review: see [autonomous startup pass](docs/AUTONOMOUS_STARTUP_PASS.md). 425 tests pass. Corrected FFFFF708 identification to SYSCR1 (not SCI), source Rev3 table25.3/25.2.2. Only byte1 when RAME already known1 accepted; reserved/clock/AUD/RAM-disable transitions rejected atomically. Conflicting AUDSRST initial descriptions and unsupplied OSCSTOP preserved unknown. New experiment reaches58527/58526 then unknown physical Port D FFFFF746 word at PCC3C8/op6031,0 IRQs. Strict/CAN gates unchanged.

B95/#102 completed scope/test review: see [autonomous startup pass](docs/AUTONOMOUS_STARTUP_PASS.md). 427 tests pass. Missing pins stay unknown; explicit values validated and recorded. Paired PB/PD0 orFFFF with PC0/RAM0/phi16 reaches58532/58531 at MOVT R0 opcode0029/PCC3D2. All assumptions remain hypotheses;0 IRQs, strict/CAN gates remainopen.

B96/#103 completed scope/test review: see [autonomous startup pass](docs/AUTONOMOUS_STARTUP_PASS.md). 430 tests pass. All16 targets, partial bit0 knowledge, guarded consumer and delay-slot coverage. Explicit RAM0/phi16/PC0/PBPD0 orFFFF investigations now reach58566/58564 attempts at FFFFEC00 long write7FFFFFFF, PCBD9C/op2342;0 firmware IRQs. Need identify next hardware register before implementation. Defaults unchanged.

B97/#104 completed scope/test review: see [autonomous startup pass](docs/AUTONOMOUS_STARTUP_PASS.md). 433 tests pass. Rev3 table8.1/8.2-8.3 support UBAR/UBAMR/UBBR/UBCR storage only with proveninactive breakconditions. Module stop resets UBC, unknown manual/clock state guarded; reserved writes/combined accesses atomic. Experimental PBPD0/FFFF reaches58571/58569 attempts at UBBR E8 enabling data-write breakconditions, PCBDA6/op2011,0 IRQs. Next examine active UBC semantics rather than ignoring debug interrupts. Strict and CAN gates remainopen.

B98/#105 completed scope/test review: see [autonomous startup pass](docs/AUTONOMOUS_STARTUP_PASS.md). 435 tests pass. Address-mask/size matching guards concrete/partial stores before any sideeffect; unsupported read/fetch/unknown matching rejects setup. No UBC IRQ or trigger timing fabricated. PBPD0/FFFF experiments now reach58586/58584 attempts at FFFFF400 byte0, PCBE2C/op2740,0 IRQs. Next identify ATU control register. Strict/CAN gates unchanged.

B99/#106 completed scope/test review: see [autonomous startup pass](docs/AUTONOMOUS_STARTUP_PASS.md). 438 tests pass. Source Rev3 table11.3/11.2.1/11.2.2. Only byte stop0 commands and stopped-counter fivebitprescaler config accepted; other channel starts/combined widths guarded. No other timer clock/events modelled. PBPD0/FFFF experiments reach58590/58588 attempts at FFFFF666 word0, PCBE34/op2141,0IRQs; next identify required timer register. Strict gates unchanged.
