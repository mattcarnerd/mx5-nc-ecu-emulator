# MX-5 ECU Workbench (early prototype)

A standalone, **offline**, shareable desktop tool for testing experimental Mazda
MX-5 NC `LF9VEB` SH7058 firmware hooks. It executes **actual V7 hook instruction
bytes** using a deliberately small SH-2E instruction-subset interpreter, checks
register preservation and compares observed branch/map routing with expected
behaviour.

**Not a full ECU emulator.** It does not emulate the complete processor,
interrupts, peripherals or whole Mazda firmware. The live RAM variable meanings
have not been verified on an ECU, and passing tests do not establish flash safety.
No flashing, vehicle programming or OBD connectivity is included.

## Run locally

Requires Python 3.11 or later. No third-party packages for the app.

- GUI: `python -m ecu_workbench`
- CLI: `python -m ecu_workbench --rom path/to/your/V7.bin --rpm 4500 --pedal 0 --enabled 1 --trigger 4000 --flag 1 --trace`
- Sweep: `python -m ecu_workbench --rom path/to/your/V7.bin --sweep --report audit.json`
- Synthetic tests: `python -m unittest discover -s tests -v`

For optional integration tests, set the `MX5_V7_TEST_ROM` environment variable
to the path of a separately obtained V7 research ROM. No Mazda ROM is distributed.

## Coverage

- Requires a 1,048,576-byte LF9VEB ROM with expected V7 hook layout.
- Executes the targeted DFCO, eight spark and three fuel-map hooks, including
  a shared-pointer pass-through regression case.
- Checks routing, branch decisions and select register/stack invariants.
- Fails closed on unsupported instructions and unmapped reads.
- Exports JSON report with ROM SHA-256, without embedding the binary.

**Unverified input assumptions:** RAM `0xFFFF6DD8` (RPM),
`0xFFFF6D1C` (pedal) and `0xFFFF739C` (DFCO flag).

## Windows distribution

`.github/workflows/build-windows.yml` runs tests and builds a portable Windows
executable with PyInstaller; look under the GitHub Actions workflow artifacts.
Keep this repo free of `.bin`, `.patch`, proprietary ECU definitions and flash dumps.

## Roadmap

Replace the limited instruction engine with Ghidra's SH-2E p-code execution,
add precise memory/peripheral models, verify live RAM variables, and perform
differential tests against factory code. Workbench is a research tool only.

Reference: https://ghidra.re/ghidra_docs/GhidraClass/Debugger/B2-Emulation.html

See CONTRIBUTING.md; MIT licence.
