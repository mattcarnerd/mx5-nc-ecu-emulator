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
python -m unittest discover -s tests -v
```

The current reset diagnostic models a small subset of the SH7058 CPU,
1 MiB flash, 48 KiB RAM and selected bus, clock, interrupt and GPIO
registers. Its NMI pin defaults to **unknown** rather than inventing a
hardware state. The optional local-ROM integration test uses
`MX5_NC_TEST_ROM`, and does not ship copyrighted manufacturer ROMs.

With an independently obtained LF9VEB ROM, the prior NMI-high experiment
executed **46 startup instructions**, then stopped at an unmodelled
Port B register (`0xFFFFF738`). This is an incomplete startup trace,
**not** evidence that the firmware booted.

For the current one-pass development sequence, see the **[prioritised backlog](BACKLOG.md)** and its linked GitHub issues.

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
