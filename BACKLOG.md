# Ordered development backlog

> **Goal:** a virtual Mazda MX-5 NC engine ECU that executes real firmware from **any valid NC engine-ECU ROM**, regardless of calibration ID. Do not build a ROM editor/diff tool or duplicate NCFlash.

**Current status after B05 (23 October 2026):** 5 of the 28 one-pass tickets completed. With the original LF9VEB ROM and NMI explicitly high, startup reaches **59 attempted instructions** before a documented 16-bit PCDR write at `0xFFFFF73E` (opcode `2201` at `0x00000C8C`). Neither this nor the earlier 46-instruction result constitutes a successful ECU boot. NC1/NC2/NC3 ECU hardware and ROM profiles still require independent verification.

## Working agreement — one issue = one development pass

- Each ticket must be narrow enough for one bounded source change, synthetic unit tests, updated documentation where necessary, and GitHub CI verification. No promise that a complex firmware milestone can be finished merely by extending the instruction limit.
- **Definition of done:** implementation on `main`, new focused tests passing with the existing suite, no regressions or imaginary sensor values, clear ROM execution limitations, **a backlog review**, and a successful Windows pre-release under [Releases](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/releases). Do not close a task issue until both release and backlog review are recorded.
- Synthetic fixtures must run in public CI. Optionally use `MX5_NC_TEST_ROM` for a privately held test ROM; do not commit Mazda binaries or any proprietary calibration data.
- Priority levels express **current order**, subject to evidence. After *every completed backlog item*, rerun the available representative ROM traces, compare their stops with the previous baseline, inspect adjacent task dependencies, reprioritise existing tickets, and add or split only genuinely missing one-pass tasks. Record the outcome even when no changes are needed.
- Research that reveals missing ECU-specific evidence is still a bounded task when it produces a documented blocker and reproducer. It is **not** a successful emulation milestone.

## Mandatory post-task backlog review — every completed ticket

A task is **not complete** until its implementation, tests, release **and** backlog review are done in the same development pass. After every task:

1. Rerun all synthetic CI tests and the same available locally held ROM scenario (LF9VEB power-on/NMI-high/300-step baseline; add NC1/NC2/NC3 profiles as verified). Never publish third-party ROM bytes.
2. Compare failing **instruction PC/opcode**, memory address, register, data/access width, stop category, executed instruction count, and external inputs with the previous baseline. Count increases alone do not prove improvement or full boot.
3. Review **every open backlog task** for scope duplication, newly revealed prerequisites, incorrect technical assumptions, outdated dependencies, realistic one-pass sizing, and priority relative to the new first failure.
4. **Promote or narrow existing issues before creating duplicates.** Split broad work into new one-pass GitHub issues only when real evidence makes the scope clear. Defer unobserved CPU/peripheral families instead of implementing them speculatively.
5. Update this file, any changed GitHub issue titles/bodies, and a short entry in the review log below. If no reprioritisation is justified, write **"no changes"** and give the reason.
6. Ensure a successful Windows EXE is published in GitHub Releases and link the code commit, release, test run and backlog-review outcome in the completed issue **before closing it**.

Do this **automatically as part of handling a "do next task" request**. The user should not need to request a separate review. This is a per-development-pass checklist, not a promise of unattended future execution.

## Backlog review log

| When | Completed item | Evidence and decisions |
|---|---|---|
| 2026-10-23 | B04 (retrospective review after B01–B04) | LF9VEB blocker confirmed: `MOV.W R0,@R2` at `0x00000C8C`, write `0x001F` to PCDR `0xFFFFF73E`. Keep B05 next for reset/NMI regression protection. **Promote and narrow existing B18 to P0, immediately after B05**; no duplicate Port C ticket. **Promote B26 to P1**, early hardware-family/ROM inventory. **Defer B13–B15 FPU to P2** until a real executed ROM needs those instructions. All other tickets retain current scope; revisit CPU instruction ordering when the next blocker is known. |
| 2026-10-23 | B05 | **No priority changes.** Tested power/manual reset × all NMI states, separated missing physical NMI pin from unknown manual-reset ICR latch, and made GUI report generation headless/testable. Original LF9VEB power-on/NMI-high remains 59 attempted instructions, stopping on PCDR `0xFFFFF73E` (opcode `2201` at `0x00000C8C`). B18/Port C remains the next P0 task; B26 NC hardware-family manifest remains after it; deferred FPU instruction work stays unobserved. No duplicates or additional tasks justified. |

## High-level parent workstreams

- [#1 — NC hardware families and ROM variants](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/1)
- [#2 — SH7058 / SH-2E CPU execution and real ROM boot](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/2)
- [#3 — ECU peripherals and simulated engine I/O](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/3)

## P0 — Unblock the observed LF9VEB startup failure

Highest confidence, immediate work. **Next: B05, then B18 (PCDR)**. Implement only verified register behaviour, rerun LF9VEB, and report the next authentic blocker.

| Order | Single-pass task | Testable finish line | Depends on |
|---|---|---|---|
| **[B01](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/4)** | Capture LF9VEB reset baseline | Existing reset diagnostic; synthetic and optional local-ROM snapshot | — |
| **[B02](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/5)** | Implement PBDR output latch at `0xFFFFF738` | Real register behaviour + reset, access-width and trace tests | B01 |
| **[B03](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/6)** | Handle Port B pin reads with explicit inputs | Physical pins are not silently read as zero | B02 |
| **[B04](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/7)** | Surface precise next startup blocker | Last executed PC, opcode, access and reason in CLI/GUI | B01 |
| **[B05](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/8)** | Protect power/manual reset and NMI regression paths | Synthetic test matrix; no false `boot_complete` | B01–B04 |
| **[B18](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/21)** | Implement verified Port C data register **PCDR `0xFFFFF73E`** (8/16-bit, PC0–PC4; reserved bits read zero; physical pin values explicit) | Pass synthetic reset/width/pin tests; LF9VEB must proceed beyond the real 59-instruction PCDR write without fake pins | B05 |

## P1 — Verify ECU families, then implement observed CPU gaps

**After B05/B18, prioritise B26** (local NC1/NC2/NC3 hardware-family inventory). Implement other CPU instruction groups only when supported by an observed ROM trace or essential verified prerequisite; the rows below are an inventory, **not** a commitment to implement every group in numeric order.

| Order | Single-pass task | Testable finish line | Depends on |
|---|---|---|---|
| **[B26](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/33)** | Early NC1/NC2/NC3 ECU hardware-family and local-ROM manifest | Documented profiles, SHA-256 metadata only, unsupported variants explicitly unknown | B01; schedule after B18 |
| **[B06](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/9)** | Indexed/displacement memory MOV group | Documented encoding + read/write/exception tests | B05 |
| **[B07](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/10)** | Pre-decrement/post-increment MOV group | Correct register mutation and alias rules | B06 |
| **[B08](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/11)** | Logical AND/OR/XOR/TST opcode group | Known T-bit semantics and edge-case tests | B05 |
| **[B09](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/12)** | Compare and carry/borrow arithmetic group | Correct signed/unsigned flags and wraps | B08 |
| **[B10](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/13)** | Delayed conditional/register branch group | Taken/not-taken delay-slot tests | B05 |
| **[B11](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/14)** | Shift/rotate opcode group | Correct T-bit, sign and wrap behaviour | B08 |
| **[B12](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/15)** | SR/GBR/VBR/PR transfers | Unknown bits tracked; register tests | B05 |
| **[B16](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/19)** | One architectural exception / RTE path | Vector entry/return and saved state tests | B12 |

## P2 — Build truthful simulated hardware

Other hardware and deferred FPU work: implement only when confirmed necessary for real firmware boot or the next verified operating phase. B18/Port C has been moved to the immediate P0 queue.

| Order | Single-pass task | Testable finish line | Depends on |
|---|---|---|---|
| **[B17](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/20)** | Small peripheral-registry abstraction | Existing bus behaviour preserved, unknowns fail closed | B05 |
| **[B19](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/22)** | Deterministic instruction/cycle time | Repeatable virtual time and delay-slot accounting | B05 |
| **[B20](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/27)** | Verified watchdog register subset | Write key/initial state tested, unknowns explicit | B17, B19 |
| **[B21](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/28)** | One interrupt source dispatched to CPU | Priority/mask/vector route proven by tests | B16, B19 |
| **[B22](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/29)** | One ATU-II counter/capture channel | Deterministic timer register behaviour and events | B19, B21 |
| **[B23](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/30)** | One ADC channel reading external voltage | Explicit input, conversion/status output, missing input | B17, B19 |
| **[B24](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/31)** | Synthetic crank/cam edge fixture | Deterministic timestamps into actual capture model | B22 |
| **[B25](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/32)** | One genuine hardware command-output trace | Capture one validated output, or label as raw GPIO | B18, B19 |
| **[B13](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/16)** | Defer FPU initial state until a ROM needs it | Unknown FR/FPUL/FPSCR values remain unknown | B12; observed need |
| **[B14](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/17)** | Defer FPU transfer/conversion subset until observed | Bit-exact IEEE-754 and FPSCR tests | B13; observed need |
| **[B15](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/18)** | Defer FPU arithmetic subset until observed | Only verified FPSCR modes; documented exceptions | B14; observed need |

## P3 — Coverage and controlled interaction

Longer-horizon execution coverage and first sensor input; the early multi-ROM inventory B26 is now in P1. These are not yet idle/DFCO scenarios.

| Order | Single-pass task | Testable finish line | Depends on |
|---|---|---|---|
| **[B27](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/34)** | Sustained-execution diagnostic harness | Bounded PC coverage/loops/interrupt evidence, no fake boot | B16, B19 |
| **[B28](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/35)** | One live simulated input exposed to app | GUI/CLI feeds actual peripheral read; synthetic proof | B23, B27 |

## Intentional stop line

The currently sized backlog stops after **B28: one verified sensor value reaches running ROM instructions through an actual peripheral model**. It does **not** promise successful ECU idle, RPM sweeps, fuel-cut or ignition calculations. Once the CPU can run a credible sustained firmware loop, split the next capabilities into more one-pass tickets using real evidence:

- Verify actual NC crank/cam tooth pattern and phase; do not mistake a synthetic square wave for a validated engine signal.
- Model sufficient engine inputs for one stable operating condition, and demonstrate actual firmware reads of these inputs.
- Trace authentic injection and ignition commands through documented MCU-to-ECU output paths.
- Run bounded idle, RPM rise and closed-throttle deceleration scenarios and capture reproducible firmware decisions.
- Repeat the same scenario across verified NC1/NC2/NC3 ROMs and report **per hardware family** coverage rather than a misleading blanket compatibility claim.

These are **future milestones, not 'one-go' tickets**, until dependencies and evidence let us break them down without inventing output behaviour.

## Reference material

- [Renesas SH7058 SH-2E hardware manual](https://www.renesas.com/en/document/mah/sh-2e-sh7058-f-ztat-tm-hardware-manual), in particular sections on I/O ports, CPU instruction operation, the bus controller, timer hardware and interrupt controller.
- [Current emulator architecture](docs/ARCHITECTURE.md) and [ROM compatibility scope](docs/COMPATIBILITY.md).
- Prior emulator code: [`ecu_workbench/nc_boot.py`](ecu_workbench/nc_boot.py).
