# Active ECU emulator backlog

Reviewed against main, the open parent and explicitly scoped child GitHub issues, source and the latest completed pass on **24 October 2026**.

The goal is a virtual NC ECU executing supported firmware and interacting with an engine model. It is not currently a fully booted ECU. The earlier eight-task list described bounded feature subsets; completing it did not complete this goal.

## Verified current position

- **312 local tests passed** in the last implementation pass, including locally supplied original-hash regressions. Public CI passed; private ROM-dependent cases are skipped there. This documentation audit does not represent a new test run.
- Latest verified application: [v0.2.0-dev.114.1](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/releases/tag/v0.2.0-dev.114.1), with downloaded EXE checksum verified. [Implementation/test evidence](docs/EIGHT_TASK_COMPLETION.md).
- **Default reference:** original LF9VEB SHA-256, power reset, NMI high, 300-instruction budget, no supplied physical pins, H-UDI/clock unknown. Stops at **188 attempted instructions**, reading SDSR at `0xFFFFF7C2`, PC `0x00000EF8`, opcode `6321`: unknown H-UDI state.
- **Separate conditional investigation:** explicit H-UDI assumption plus artificial phi-per-completed-instruction=1 and a **10,000** budget stops at **592 attempts / 591 completed**, PC `0x000007B6`, opcode `2301`, word store to MCR0 `0xFFFFD000`. The written value still contains unknown reserved bit6 after read/OR1. No concrete value or reset side effect is selected. The same conditional run with a 300 budget reaches only the instruction limit.
- No physical instruction timing, CAN synchronization, successful firmware main loop, injector/ignition behavior or engine operation has been established.

## Open work in priority order

There are **three open parent workstreams**, plus the five explicitly requested bounded children B52-B56/#59-63 during this pass. Research children may close with documented unresolved evidence; their parent gates remain open. The items below are work packages and evidence gates, not an invented fixed countdown or percentage to completion. Split implementation packages into bounded child issues only after their register/trace evidence and acceptance tests are specific enough.

| Priority | Work package | Current limitation / next concrete result | Tracked under |
|---|---|---|---|
| P0 | Resolve the default H-UDI startup state | Verify actual TRST/reset/debug history and relevant board wiring, or produce a documented unresolved evidence report. A ROM dump alone does not establish this state. Keep alternative assumptions conditional. | [Hardware #1](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/1) |
| P0 | Investigate the conditional MCR read/modify/write stop | Review verified MCU revision, official documentation/errata and justified read/write treatment for reserved bit6. Retain the reduced reproducer and unknown mask. Inactive mailbox2700 also retains NMC contrary to the documented unused-mailbox initialization requirement; command recording is not proof of valid CAN operation. | [Hardware #1](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/1), [CPU #2](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/2) |
| P1 | Establish a verified clock/reset/board profile | Identify oscillator/dividers, MCU/memory/reset behavior and input/output pin mapping for the tested hardware family. Separate documented facts, supplied scenarios and unknowns. | [Hardware #1](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/1) |
| P1 | Complete CPU behavior required by execution | Extend missing integer/FPU/exception behavior from concrete executed evidence; finite FPU support is not a complete CPU. Compare independent synthetic vectors and, where available, hardware/reference traces. | [CPU #2](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/2) |
| P1 | Deliver ATU/ADC interrupt requests to CPU | Existing ATU/ADC models expose module request levels only. Scope one source at a time with verified vector, priority/mask, acknowledgement, entry/return and delayed-slot tests. The existing ITI CPU route is not an ATU/ADC route. | [Peripherals #3](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/3), [CPU #2](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/2) |
| P1 | Extend peripherals and timing as firmware requires | Add required CAN lifecycle/status/traffic, timer channels/prescalers, ADC channels/triggers, watchdog and other accessed interfaces. Current selected-counter ticks and ADC completion delay are explicit fixtures, not measured hardware timing. | [Peripherals #3](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/3) |
| P1 milestone | Demonstrate sustained firmware initialization/main-loop execution | Define and verify firmware-specific initialization/main-loop evidence, functioning scheduled interrupts and absence of unexplained stops under a declared hardware profile. More instructions or repeated PCs alone do not meet this milestone. | [CPU #2](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/2) |
| P2 | Replace generic fixtures with verified NC engine inputs | Establish crank/cam pattern, phase and pin routing; sensor channels, reference supplies and scaling; required switches/network inputs. Current square waves and AN0 input do not establish those mappings. | [Hardware #1](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/1), [Peripherals #3](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/3) |
| P2 | Identify firmware actuator commands | Map outputs to documented ECU circuitry and capture injector/ignition/throttle commands with verified timing. Current PortC records are raw latch commands; physical levels and ECU function are unknown. | [Hardware #1](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/1), [Peripherals #3](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/3) |
| P2 milestone | Add and validate an engine feedback model | Make firmware commands affect simulated engine state and subsequent inputs; test start, idle, RPM changes, deceleration and faults against external evidence. No current combustion/engine feedback model is claimed. | [Peripherals #3](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/3) |
| P3 | Validate supported hardware/ROM families | Obtain authorized representative ROMs/board evidence and run identical declared scenarios; publish per-family support and failures. One LF9VEB regression does not establish all NC compatibility. | [Hardware #1](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/1), [Peripherals #3](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/3) |

**Next default development action:** investigate the two documented startup evidence gates under existing #1/#2. If external evidence is unavailable, report exactly what is missing and deliberately select an independently scoped interrupt/peripheral task. Do not turn an assumption into a hardware fact to get past a stop.

## Completed bounded capabilities and their limits

| Completed task | What is implemented | What it does not establish |
|---|---|---|
| [B13/#16](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/16) | FR/FPUL unknown after reset; FPSCR documented reset `0x00040001`, fixed/writable bits, system transfers | Full FPU or firmware use of these instructions |
| [B14/#17](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/17) | Raw FMOV forms, immediates and bounded FLOAT/FTRC | All conversions or exceptional cases |
| [B15/#18](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/18) | Finite FADD/FSUB/FMUL/FDIV with exact rational truncation, signed zero and fixed DN | NaN/infinity/divide-zero/overflow/enabled-exception execution; these stop explicitly |
| [B22/#29](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/29) | Bounded ATU1A counter/compare/capture and module request events; B24 extends the shared counter capture to GR1B | CPU dispatch of these sources, other timer channels, physical prescaling/timing |
| [B23/#30](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/30) | Ideal single AN0 conversion with explicit voltage/reference/completion, data/status and request handling | All ADC modes, physical sampling accuracy/timing or sensor identity |
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

## Current five-task execution queue

1. B52/#59 H-UDI evidence audit: report at docs/HUDI_STARTUP_AUDIT.md; board state unresolved.
2. B53/#60 CAN startup constraints audit.
3. B54/#61 ATU IMI1A CPU route.
4. B55/#62 ADC ADI0 CPU route.
5. B56/#63 integrated synthetic firmware fixture.

B52/#59 completed scope/test review: see [eight-task pass](docs/STARTUP_IRQ_PASS.md). B52 research scope complete; hardware1 gate remains unresolved. B53 CAN audit next, B54/B55 verified vector routes then B56 integration. No duplicate broad research issue.
