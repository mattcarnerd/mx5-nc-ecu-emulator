# MX-5 NC ECU Emulator

**Goal: run any valid Mazda MX-5 NC engine ECU ROM on a virtual ECU.**

The target is the NC generation (NC1/NC2/NC3, 1.8/2.0 MZR, manual/automatic
and relevant market variants). Our emulator models ECU **hardware**, rather
than writing special-case execution logic for each calibration ID. Ultimately
a user should load a valid NC ROM, start the virtual ECU, simulate engine
inputs and observe real firmware decisions.

> **Current state:** A read-only, experimental SH7058 reset-vector diagnostic
> executes a limited number of original ROM instructions before stopping at
> unsupported opcodes or unmodelled hardware. **This is not a fully booting
> or operational ECU**, and no simulated idle/acceleration/deceleration outputs
> are available yet.

## Focus: firmware execution, not ROM editing

- **Included:** load a locally held NC ROM, identify plausible size (not a
  validation), read reset vectors, execute real startup instructions, stop
  safely on missing hardware, inspect startup traces and export a diagnostic.
- **Planned:** complete SH-2E CPU implementation; NC ECU memory/peripheral
  models; deterministic sensor inputs; full boot/main-loop operation; simulated
  injector, ignition, throttle and diagnostics outputs.
- **Not included:** ROM comparison, map editing, binary patching, flashing or
  connection to an actual ECU. Use **NCFlash** for ROM editing/comparison.

## Current startup screen

Load NC ROM → set power/manual reset and NMI input → **Run startup diagnostic**.
The app reports the actual firmware stop point, number of executed
instructions, reset-vector state and observed peripheral accesses. A run that
hits the instruction limit **is not** considered a successful ECU boot.

## Run

Python 3.11+ is required when running from source (no third-party runtime
packages). Windows binaries are built by GitHub Actions.

```powershell
python -m ecu_workbench
python -m ecu_workbench --rom original.bin --reset power --steps 300
python -m ecu_workbench --rom original.bin --reset power --nmi high --steps 300 --report boot.json
python -m ecu_workbench --rom original.bin --baseline --reset power --nmi high --steps 300 --report baseline.json
python -m unittest discover -s tests -v
```

The current reset diagnostic models a small subset of the SH7058 CPU,
1 MiB flash, 48 KiB RAM and selected bus, clock, interrupt and GPIO
registers. Its NMI pin defaults to **unknown** rather than inventing a
hardware state. The optional local-ROM integration test uses
`MX5_NC_TEST_ROM`, and does not ship copyrighted manufacturer ROMs.

With an independently obtained LF9VEB ROM, **B01** executed 46 startup
instructions and stopped at PBDR `0xFFFFF738`. With **B02** PBDR
register-latch support, the same power reset / NMI-high test executes
**59 instructions** and then stops at the still-unmodelled Port C data
register (PCDR) `0xFFFFF73E`. Neither run constitutes a booted ECU.

For the current one-pass development sequence, see the **[prioritised backlog](BACKLOG.md)** and its linked GitHub issues.

## B01 — reproducible reset baseline

Use `--baseline` to save a small deterministic JSON snapshot containing the
ROM SHA-256, image size, reset/NMI settings, instruction count, stop PC,
stop reason, last 16 executed instructions and first unsupported peripheral
access if one was encountered. It includes **no ROM bytes or file path**.
Identical firmware and input settings yield identical baseline JSON.

```powershell
python -m ecu_workbench --rom "C:\\path\\to\\lf9veb.bin" --baseline --reset power --nmi high --steps 300 --report baseline.json
```

Optional private-ROM integration check: set `MX5_NC_TEST_ROM` to a local ROM
path before running the unit tests. On the locally held original LF9VEB ROM
(SHA-256 `bfd0965a0f51f60a951d8cd3ef8fe77e5a37fbc326ddb723edf0ede4b1640fbf`),
power reset at 300 maximum steps produces:

| Simulated NMI | Instructions | Stop reason | PC at stop |
| --- | ---: | --- | --- |
| unknown | 23 | `missing_input`, ICR NMI read `0xFFFFED18` | `0x00000C4A` |
| high | 46 | `unmodelled_peripheral`, Port B write `0xFFFFF738` | `0x00000C74` |
| low | 300 | `instruction_limit` while NMI polling | `0x00000C4C` |

These are **reset-execution diagnostics, not completed ECU boots**. Future
changes to the instruction engine must be compared against this baseline.

## B02 — SH7058 Port B data register

The [Renesas SH7058 Rev 3.00 hardware manual](https://www.renesas.com/en/document/mah/sh-2e-sh7058-f-ztat-tm-hardware-manual)
sections **22.3.1–22.3.2**, tables 22.3 and 22.4, defines
`PBDR` at `0xFFFFF738`, 8- and 16-bit access, and a power-on
reset value of `0x0000`. Port B is little-known outside the ECU;
the CPU and bus accesses here use **big-endian** byte order.

The emulator now tracks the PBDR latch and the known bits after
power-on or manual reset, supports separate upper/lower byte writes,
and logs all supported writes without pretending to drive a vehicle pin.
Reading PBDR bits with `PBIOR` set to input requires **external pin
levels**, which B03 will model. Such reads fail with `missing_input`,
not an invented zero or arbitrary pin value. Wrong access widths fail
explicitly. `PBPR` and external circuitry remain unmodelled.

With LF9VEB, NMI explicitly high and a 300-instruction cap:
**B01 46 instructions -> B02 59 instructions**, next stop is an
unmodelled 16-bit PCDR write `0xFFFFF73E`. This is still *partial
firmware startup*, not a functional virtual ECU.

## Engineering priorities

1. Model the missing Port B hardware input/output behaviour with verified
   evidence, extend instruction coverage and advance past early startup.
2. Implement a validated SH-2E processor core (FP, interrupts, exceptions,
   delay slots and correct memory mapping).
3. Simulate the necessary ECU peripherals, timed events and engine signals.
4. Reach sustained ECU firmware execution and observable injection/ignition
   outputs; verify across multiple NC hardware/ROM variants.
5. Create a repeatable scenario suite for idle, acceleration, deceleration
   and fault handling without patching individual ROMs.

See [architecture](docs/ARCHITECTURE.md) and
[NC compatibility](docs/COMPATIBILITY.md) for the evidence-backed roadmap.

## Distribution and safety

**[Download the latest Windows EXE from GitHub Releases](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/releases)**.
Open the newest development pre-release, expand **Assets**, then click
`MX5-NC-ECU-Emulator.exe` for a direct download (or the Windows ZIP).
**You do not need to use the Actions / Artifacts page.**

Every successful push to `main` automatically builds and publishes a
uniquely versioned Windows development pre-release with the EXE, ZIP and
SHA-256 checksum file. Pull requests run tests without publishing a release.
Earlier releases were ROM viewer prototypes; the current code deliberately
removes comparison.
No factory or modified ROM binaries are included in this repository.
A successful diagnostic cannot establish flash safety or roadworthiness.
The application does not communicate with vehicles or write ECU firmware.

MIT licence. See CONTRIBUTING.md.
