# Active ECU emulator backlog

Reviewed against main, the open parent and explicitly scoped child GitHub issues, source and the latest completed pass on **24 October 2026**.

The goal is a virtual NC ECU executing supported firmware and interacting with an engine model. It is not currently a fully booted ECU. The earlier eight-task list described bounded feature subsets; completing it did not complete this goal.

## Verified current position

- **335 local tests passed** in the last implementation pass, including locally supplied original-hash regressions. Public CI passed; private ROM-dependent cases are skipped there. Timer/clock pass B57-B61 reran the full suite and declared ROM scenarios; research gates remain unresolved.
- Previous verified application baseline: [v0.2.0-dev.114.1](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/releases/tag/v0.2.0-dev.114.1), with downloaded EXE checksum verified. [Implementation/test evidence](docs/EIGHT_TASK_COMPLETION.md).
- **Default reference:** original LF9VEB SHA-256, power reset, NMI high, 300-instruction budget, no supplied physical pins, H-UDI/clock unknown. Stops at **188 attempted instructions**, reading SDSR at `0xFFFFF7C2`, PC `0x00000EF8`, opcode `6321`: unknown H-UDI state.
- **Separate conditional investigation:** explicit H-UDI assumption plus artificial phi-per-completed-instruction=1 and a **10,000** budget stops at **592 attempts / 591 completed**, PC `0x000007B6`, opcode `2301`, word store to MCR0 `0xFFFFD000`. The written value still contains unknown reserved bit6 after read/OR1. No concrete value or reset side effect is selected. The same conditional run with a 300 budget reaches only the instruction limit.
- No physical instruction timing, CAN synchronization, successful firmware main loop, injector/ignition behavior or engine operation has been established.

## Open work in priority order

There are **three open parent workstreams**. The five requested children B57-B61/#64-68 are complete within their documented research/implementation scope; per-issue commit/CI/release links record closure. Research children may close with documented unresolved evidence; their parent gates remain open. The items below are work packages and evidence gates, not an invented fixed countdown or percentage to completion. Split implementation packages into bounded child issues only after their register/trace evidence and acceptance tests are specific enough.

| Priority | Work package | Current limitation / next concrete result | Tracked under |
|---|---|---|---|
| Evidence gate | Resolve the default H-UDI startup state | Verify actual TRST/reset/debug history and relevant board wiring, or produce a documented unresolved evidence report. A ROM dump alone does not establish this state. Keep alternative assumptions conditional. | [Hardware #1](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/1) |
| P1 software / evidence gate | Investigate the conditional MCR read/modify/write stop | Review verified MCU revision, official documentation/errata and justified read/write treatment for reserved bit6. Retain the reduced reproducer and unknown mask. Inactive mailbox2700 also retains NMC contrary to the documented unused-mailbox initialization requirement; command recording is not proof of valid CAN operation. | [Hardware #1](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/1), [CPU #2](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/2) |
| P1 | Establish a verified clock/reset/board profile | Identify oscillator/dividers, MCU/memory/reset behavior and input/output pin mapping for the tested hardware family. Separate documented facts, supplied scenarios and unknowns. | [Hardware #1](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/1) |
| P1 | Complete CPU behavior required by execution | Extend missing integer/FPU/exception behavior from concrete executed evidence; finite FPU support is not a complete CPU. Compare independent synthetic vectors and, where available, hardware/reference traces. | [CPU #2](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/2) |
| P1 | Deliver ATU/ADC interrupt requests to CPU | IMI1A, IMI1B, OVI1A and ADI0 now reach the CPU through B54/B55/B57/B58. Other timer/ADC sources remain outside this bounded route subset. Scope one source at a time with verified vector, priority/mask, acknowledgement, entry/return and delayed-slot tests. The existing ITI CPU route is not an ATU/ADC route. | [Peripherals #3](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/3), [CPU #2](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/2) |
| P1 | Extend peripherals and timing as firmware requires | Add required CAN lifecycle/status/traffic, timer channels/prescalers, ADC channels/triggers, watchdog and other accessed interfaces. Selected-counter ticks, zero-phase supplied Pphi packets with PSCR1/TCR1A division, TCLKA/B levels and ADC completion delay are explicit fixtures, not measured hardware timing. Clock reconfiguration after binding, TI10/AGCKM and other timer channels remain unsupported. | [Peripherals #3](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/3) |
| P1 milestone | Demonstrate sustained firmware initialization/main-loop execution | Define and verify firmware-specific initialization/main-loop evidence, functioning scheduled interrupts and absence of unexplained stops under a declared hardware profile. More instructions or repeated PCs alone do not meet this milestone. | [CPU #2](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/2) |
| P2 | Replace generic fixtures with verified NC engine inputs | Establish crank/cam pattern, phase and pin routing; sensor channels, reference supplies and scaling; required switches/network inputs. Current square waves and AN0 input do not establish those mappings. | [Hardware #1](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/1), [Peripherals #3](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/3) |
| P2 | Identify firmware actuator commands | Map outputs to documented ECU circuitry and capture injector/ignition/throttle commands with verified timing. Current PortC records are raw latch commands; physical levels and ECU function are unknown. | [Hardware #1](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/1), [Peripherals #3](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/3) |
| P2 milestone | Add and validate an engine feedback model | Make firmware commands affect simulated engine state and subsequent inputs; test start, idle, RPM changes, deceleration and faults against external evidence. No current combustion/engine feedback model is claimed. | [Peripherals #3](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/3) |
| P3 | Validate supported hardware/ROM families | Obtain authorized representative ROMs/board evidence and run identical declared scenarios; publish per-family support and failures. One LF9VEB regression does not establish all NC compatibility. | [Hardware #1](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/1), [Peripherals #3](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/3) |

**Next development path (ROM-only setup):** B62 provenance and B63 constraint reconciliation establish what public sources support. B64 adds explicit experimental MCR bit6 readback choices; B65 implements the next documented command; B66 regresses the scenario matrix and records subsequent dependencies. Physical verification stays open under #1; it does not block all software development. Strict defaults remain unknown and experimental assumptions never become hardware facts. See [scenario contract](docs/ROM_ONLY_CONSTRAINTS.md).

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
