# Ordered development backlog

> **Goal:** a virtual Mazda MX-5 NC engine ECU that executes real firmware from **any valid NC engine-ECU ROM**, regardless of calibration ID. Do not build a ROM editor/diff tool or duplicate NCFlash.

**Status at creation:** experimental SH7058 startup diagnostic only; earlier LF9VEB/NMI-high run executed 46 instructions and stopped on a write to `0xFFFFF738` (Port B data register / PBDR). This is *not* a complete boot. Actual CPU/board differences between NC ECU variants must be verified.

## Working agreement — one issue = one development pass

- Each ticket must be narrow enough for one bounded source change, synthetic unit tests, updated documentation where necessary, and GitHub CI verification. No promise that a complex firmware milestone can be finished merely by extending the instruction limit.
- **Definition of done:** implementation on `main`, new focused tests passing with the existing suite, no regressions or imaginary sensor values, clear ROM execution limitations, and a successful Windows pre-release under [Releases](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/releases).
- Synthetic fixtures must run in public CI. Optionally use `MX5_NC_TEST_ROM` for a privately held test ROM; do not commit Mazda binaries or any proprietary calibration data.
- Priority numbers express **starting order**, not an instruction to implement unnecessary CPU functions ahead of an actual observed startup blocker. After B02/B03, rerun the boot trace and bring forward the next *verified* unmet instruction or peripheral dependency.
- Research that reveals missing ECU-specific evidence is still a bounded task when it produces a documented blocker and reproducer. It is **not** a successful emulation milestone.

## High-level parent workstreams

- [#1 — NC hardware families and ROM variants](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/1)
- [#2 — SH7058 / SH-2E CPU execution and real ROM boot](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/2)
- [#3 — ECU peripherals and simulated engine I/O](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/3)

## P0 — Unblock the observed LF9VEB startup failure

Highest confidence, immediate work. Target the actual register at the recorded stop, then rerun and report the next genuine obstacle.

| Order | Single-pass task | Testable finish line | Depends on |
|---|---|---|---|
| **[B01](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/4)** | Capture LF9VEB reset baseline | Existing reset diagnostic; synthetic and optional local-ROM snapshot | — |
| **[B02](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/5)** | Implement PBDR output latch at `0xFFFFF738` | Real register behaviour + reset, access-width and trace tests | B01 |
| **[B03](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/6)** | Handle Port B pin reads with explicit inputs | Physical pins are not silently read as zero | B02 |
| **[B04](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/7)** | Surface precise next startup blocker | Last executed PC, opcode, access and reason in CLI/GUI | B01 |
| **[B05](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/8)** | Protect power/manual reset and NMI regression paths | Synthetic test matrix; no false `boot_complete` | B01–B04 |

## P1 — Fill CPU gaps in bounded opcode groups

One well-defined instruction family per task, validated against SH-2E behaviour; reorder by whichever opcode the real startup trace needs next.

| Order | Single-pass task | Testable finish line | Depends on |
|---|---|---|---|
| **[B06](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/9)** | Indexed/displacement memory MOV group | Documented encoding + read/write/exception tests | B05 |
| **[B07](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/10)** | Pre-decrement/post-increment MOV group | Correct register mutation and alias rules | B06 |
| **[B08](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/11)** | Logical AND/OR/XOR/TST opcode group | Known T-bit semantics and edge-case tests | B05 |
| **[B09](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/12)** | Compare and carry/borrow arithmetic group | Correct signed/unsigned flags and wraps | B08 |
| **[B10](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/13)** | Delayed conditional/register branch group | Taken/not-taken delay-slot tests | B05 |
| **[B11](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/14)** | Shift/rotate opcode group | Correct T-bit, sign and wrap behaviour | B08 |
| **[B12](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/15)** | SR/GBR/VBR/PR transfers | Unknown bits tracked; register tests | B05 |
| **[B13](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/16)** | FPU initial state representation | Undefined register values remain undefined | B12 |
| **[B14](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/17)** | FPU transfer/conversion subset | Raw IEEE-754 bit moves and first conversions | B13 |
| **[B15](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/18)** | FPU arithmetic subset | Supported FPSCR modes only; unsupported modes halt | B14 |
| **[B16](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/19)** | One architectural exception / RTE path | Vector entry/return and saved state tests | B12 |

## P2 — Build truthful simulated hardware

Start with registers the firmware actually uses; clocks, interrupts, sensors and outputs depend on the earlier CPU and peripheral layers.

| Order | Single-pass task | Testable finish line | Depends on |
|---|---|---|---|
| **[B17](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/20)** | Small peripheral-registry abstraction | Existing bus behaviour preserved, unknowns fail closed | B05 |
| **[B18](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/21)** | One additional observed GPIO bank | One bank only; direction/latches/external inputs | B17 |
| **[B19](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/22)** | Deterministic instruction/cycle time | Repeatable virtual time and delay-slot accounting | B05 |
| **[B20](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/27)** | Verified watchdog register subset | Write key/initial state tested, unknowns explicit | B17, B19 |
| **[B21](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/28)** | One interrupt source dispatched to CPU | Priority/mask/vector route proven by tests | B16, B19 |
| **[B22](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/29)** | One ATU-II counter/capture channel | Deterministic timer register behaviour and events | B19, B21 |
| **[B23](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/30)** | One ADC channel reading external voltage | Explicit input, conversion/status output, missing input | B17, B19 |
| **[B24](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/31)** | Synthetic crank/cam edge fixture | Deterministic timestamps into actual capture model | B22 |
| **[B25](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/32)** | One genuine hardware command-output trace | Capture one validated output, or label as raw GPIO | B18, B19 |

## P3 — Coverage and controlled interaction

A compatibility test harness and the first real input path; not yet a running idle/DFCO scenario.

| Order | Single-pass task | Testable finish line | Depends on |
|---|---|---|---|
| **[B26](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/issues/33)** | Locally held multi-ROM compatibility manifest | NC1/NC2/NC3 evidence, missing files skip, hashes only | B01 |
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
