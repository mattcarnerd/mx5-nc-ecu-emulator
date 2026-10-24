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

## B33 — observed Port F PFDR register

A user-generated **non-reference** NC ROM diagnostic (SHA-256
`8a54527361db7d813b2c758f0a8b326575c5850e46159de135177b1edb44d0e2`)
confirmed the Port E `0xFFFF` write and then stopped after 83 attempted
instructions at SH7058 `PFDR 0xFFFFF74E`. Attempted opcode `2351` at
`0x00000CBC` requested a 16-bit `0xFFFF` write. The SHA-256 **differs**
from the previous original LF9VEB reference hash; this report is not proof
that the original LF9VEB has the same next stop.

`ecu_workbench/port_f.py` models the documented SH7058 Rev.3 §22.7
8/16-bit Port F data latch, power-on zero and preserved unknown manual-reset
state. The register is handled by the peripheral router. `PFIOR`
controls whether read values reflect output latches or **explicitly provided**
external pin levels; missing input levels cause a diagnostic stop. POD
can tri-state PF0–PF4, but POD, alternate pins, and physical port outputs
remain **unmodelled**. The write succeeding does not establish any
physical output event or completed ECU boot.

Renesas reference: https://www.renesas.com/en/document/mah/sh-2e-sh7058-f-ztat-tm-hardware-manual
(sections 22.7.1–22.7.2, tables 22.11–22.12).

## B34 — Port G from original-reference LF9VEB

The original-reference LF9VEB hash report confirms **94 attempted instructions**
with Port E and F word writes performed, followed by an **unmodelled**
`PGDR 0xFFFFF764` word write `0x000F` (opcode `2131` at PC `0x00000CD2`).
Renesas SH7058 Rev.3 §22.8, Tables 22.13–22.14, specifies just four
implemented bits PG3..PG0. Bits 15..4 read as zero and must be written
zero. The Port G model implements only the output data latch, explicit
physical input readback and fail-closed uninitialised reset state. It
does **not** emulate pin drivers or alternate function behaviour. Synthetic
CPU opcode tests do not establish a successful original firmware boot.

## B35 — Port H PHDR from the original-reference ROM

The original-reference LF9VEB shareable report advanced to **101
attempted instructions**, with Port E/F/G writes observed, then attempted
`MOV.W R5,@R3` (opcode `2351`) at `0x00000CE0`: 16-bit `0xFFFF`
write to `PHDR 0xFFFFF72C`. Renesas SH7058 Rev 3.00 §22.9
(Tables 22.15–22.16) documents a full 16-bit 8/16-bit R/W port latch,
power-on zero, and readback governed by `PHIOR` plus physical pin input.
POD affects real high-impedance outputs but is not a simulated pin driver.
Synthetic tests exercise endian accesses, manual reset, mixed input/output
and actual opcode `2351` stores. No completed ROM boot is inferred.

## B36 — Port J PJDR found by original-reference LF9VEB

After Port H support, the same reference-hash LF9VEB report reached
**108 attempted instructions**, confirming prior Port E/F/G/H word
writes. The first new unmodelled access is `PJDR 0xFFFFF76C`:
opcode `2151` at instruction PC `0x00000CEE` attempts a 16-bit
`0xFFFF` write.

Renesas SH7058 Rev.3 §22.10, Tables 22.17–22.18, specifies a
16-bit data latch, 8/16-bit reads/writes, power-on zero, and PJIOR
direction-dependent software readback. `ecu_workbench/port_j.py`
implements this behaviour fail-closed for unknown physical inputs
and manual-reset state. No physical pin outputs, alternate functions,
or separate read-only PJPR input register are emulated. Synthetic
opcode `2151` tests do not constitute a complete firmware boot.

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
