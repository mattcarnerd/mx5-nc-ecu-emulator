# Architecture: one virtual NC ECU, many ROMs

## Non-negotiable design principle

The simulated hardware executes **real firmware instructions taken from the
user's ROM**. No hard-coded replacements of ignition/DFCO/fuelling behaviour,
no dependency on a particular calibration identifier, and no emulator patches
to individual ROM binaries merely to make them pass tests.

## Layers

1. **ROM image and identity** — open/inspect arbitrary file containers, validate
   supported NC full-flash layouts, identify ROM/ECU variant, verify checksums
   (read-only). Identity must use documented patterns/cross-checks, never just
   the file name or size. Reject or clearly flag unknown formats.
2. **Physical ECU profile** — model board-specific CPU variant, address ranges,
   RAM, flash, persistent data, interrupts, peripherals, clocks and wiring.
   Profiles apply to ECU hardware families, **not** individual calibration IDs.
3. **Instruction engine** — independently validated SH-2E-compatible CPU with
   correct exceptions, registers, FP, memory accesses, branch delay slots and
   timing where required.
4. **Virtual peripherals** — hardware registers and interrupt sources for
   timers/capture, ADC, crank/cam signals, watchdog, CAN, GPIO, etc. Missing
   hardware must produce a meaningful stop, never a fabricated success.
5. **Plant/input scenarios** — reproducible engine/sensor stimuli (RPM, pedal,
   coolant, temperatures, manifold pressure, throttle, lambda, etc.) plus
   vehicle-network inputs. Observe commanded injections/ignition and fault
   states. Physical combustion and acoustic afterfire are outside a basic
   firmware emulator.
6. **Regression harness** — run the same scenarios on multiple OEM/modified
   NC ROMs; compare outputs and identify unsupported hardware dependencies,
   crashes, uninitialised reads and timeouts.

## B17 peripheral data-register routing

`ecu_workbench/peripheral_router.py` provides an explicit address registry for
already implemented Port B/C/D/E data and physical-pin registers. Each
two-byte register covers its word address and the individual high/low byte
addresses, consistent with the SH7058 big-endian bus. There is no default
zero-valued register: unregistered accesses fall through to the existing
`unmodelled_peripheral` stop.

The router delegates actual read/write semantics to the existing B/C/D/E
handlers (including Port D/E classes), preserving reset-known masks, pin
direction/mux caveats, read-only physical-pin registers, reserved bits and
diagnostic traces. It checks documented invalid 32-bit access **before** the
bus alignment check, retaining existing error categories and details. It
does not drive pins or simulate new hardware. Synthetic routing tests run
alongside the original reset and peripheral suites.

The **only** supported firmware phase is the limited reset diagnostic. No
locally held LF9VEB binary is included in this repository, so the current
post-Port-E genuine ROM stop remains unverified.

## Boot acceptance criteria

A ROM is *emulated* only when we can demonstrate, with recorded traces:
- Correct reset vector and memory mapping for the selected hardware profile.
- Execution past boot checks, into a sustained main loop/interrupt scheduling.
- Consistent sensor-driven operating behaviour without unmodelled reads/writes.
- Observable firmware outputs under idle, rev-up and closed-throttle decel.
- Deterministic replay and explicit unsupported-hardware errors.

A 1 MiB file loading, a ROM ID match, a successful checksumming step or a
single hook function passing tests do **not** meet these criteria.

## ROM support policy

- Candidate: plausible NC image size/layout; identity not verified.
- Identified: corroborated NC calibration and ECU hardware family.
- Booting: reaches an observable post-reset execution phase in the simulator.
- Functional: passes documented simulated engine scenarios.
- Regression-verified: passes shared cases against a reference hardware/trace
  corpus and has known limitations recorded.

No blanket "supports all NC ROMs" badge until these levels are attained across
the intended variant matrix.

## Research references

- ROMDrop: https://github.com/speepsio/romdrop
- NCFlash: https://github.com/cdufresne81/nc-flash
- Prior reverse-engineering study:
  https://github.com/shifty35/NC-MX5-Unbrick

References are for studying hardware/protocol/ROM variants, not copying
copyrighted ROM binaries or code without licence clearance.
