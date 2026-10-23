# MX-5 NC ECU Workbench

**Goal: execute any valid Mazda MX-5 NC engine-ECU ROM in a faithful virtual NC ECU.**

The target is **the NC generation (approximately 2005/2006–2015): NC1, NC2 and
NC3; 1.8L/2.0L; manual/automatic; applicable market/calibration variants; and
stock and modified engine-ECU firmware**. The emulator must not depend on
whether a particular calibration (e.g. LF9VEB) has an XML definition or a
per-ROM patch. Each supported ECU hardware family is described once, then ROMs
from that family run under the same processor/memory/peripheral model.

**This is the intended compatibility target, not a statement that every NC ROM
currently runs.** The existing v0.1 application is a ROM inspector/differ with
an experimental *partial* SH-2 instruction interpreter. Whole-firmware
execution, an accurate SH7058 model, interrupt scheduling, RAM/peripheral
emulation, CAN/diagnostics, and engine input simulation are not implemented.

## Product boundaries

- **In scope:** Mazda MX-5 NC engine ECUs and their valid full/modified firmware,
  including variations that require distinct, documented ECU hardware profiles.
- **Not a goal:** generic all-manufacturer/all-processor firmware emulation,
  transmission-controller ROMs, tune editing, ROM patching, or ECU flashing.
- **Compatibility means execution**, not simply opening the file or extracting
  its calibration ID.
- NCFlash and ROMDrop can remain separate ROM editing/flashing tools; this
  project's purpose is *emulation and repeatable offline firmware testing*.

## What works in the current development version

| Capability | Status |
| --- | --- |
| Read a local ROM, SHA-256, entropy and hex dump | Available |
| Compare factory and modified binary files | Available |
| Assess common 1 MiB NC image size | Heuristic only; **not identity validation** |
| Export JSON inspection/diff report | Available |
| Basic Windows GUI | Implemented |
| Step a few SH-2 instructions | Experimental, incomplete |
| Confirm valid NC ROM identity/checksum/hardware profile | Not implemented |
| Execute entire original/modified NC firmware | Not implemented |
| Run virtual engine sensors, timers, interrupts, CAN and diagnostics | Not implemented |
| Flash ECU or communicate with vehicle | Deliberately not included |

The loader will still *open* other binary files so that unknown NC dumps can
be inspected, but it must label them as **unrecognised** rather than promising
to emulate them.

## How we reach full NC ROM coverage

1. **ROM format & variant evidence:** catalogue ECU hardware, CPU IDs, ROM
   layouts, boot paths, RAM/peripheral maps and calibration IDs across
   NC1/NC2/NC3, 1.8/2.0, transmission and markets. Do not infer identity
   merely from a 1 MiB file length.
2. **Faithful processor:** replace the experimental interpreter with a tested
   SH-2E/SH7058 CPU execution backend; implement delay slots, exceptions,
   floating-point behaviour and a proper address space.
3. **Virtual ECU board:** model memory, timers, ADCs, crank/cam inputs,
   injector/coil outputs, CAN, watchdog, interrupts and other dependencies
   of the real ROM. Separate hardware differences from firmware IDs.
4. **Boot and operate:** start firmware using realistic reset vectors and
   defaults; simulate engine states and record actual firmware outputs.
5. **Cross-ROM acceptance:** run a reproducible boot/idle/RPM-change/decel
   suite on a representative set of legally obtained stock and modified NC
   engine ROMs. Each new ROM must either run or yield a precise documented
   missing-hardware/unsupported-format reason—not need hand-patched code.

See [Architecture](docs/ARCHITECTURE.md) and
[Compatibility](docs/COMPATIBILITY.md).

## Run the current prototype

Requires Python 3.11+ and its standard library.

```powershell
python -m ecu_workbench
python -m ecu_workbench --rom path/to/nc.bin
python -m ecu_workbench --rom stock.bin --compare modified.bin --report comparison.json
python -m unittest discover -s tests -v
```

Opt-in partial instruction stepping remains available for research only:

```powershell
python -m ecu_workbench --rom sample.bin --sh2-step --pc 0x100 --base 0x0 --steps 50
```

Windows binaries are available through GitHub releases. Old releases labelled
"universal ROM inspector" represent the earlier scope, not a working NC
emulator. The next release should reflect this revised product definition.

## Safety, copyright and privacy

- All ROM analysis takes place locally; no manufacturer ROMs are distributed.
- Do not commit proprietary ROMs, vendor definitions, VINs or security keys.
- A successful offline test never by itself proves a ROM is safe to flash.
- This project never edits/flashes vehicle firmware or connects to a car.

MIT licence. Contributions are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md).
