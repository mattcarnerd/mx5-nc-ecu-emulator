# ECU Workbench — format-agnostic ROM inspector and emulator research project

**Load any ROM**: open arbitrary nonempty binary files, regardless of manufacturer,
calibration ID, file extension or size. The program identifies the file by hash,
inspects it in hex, and compares it byte-by-byte with another image.

**Important:** *Loading any ROM is not the same as emulating any ROM.* Firmware
execution is processor-specific. The current optional interpreter supports
only a small subset of SuperH SH-2 integer instructions and requires an
explicit load address and program counter. Full processor, RAM, peripheral,
engine, or ECU simulation has **not** been implemented. Unsupported
instructions stop; they are never guessed.

The project started with Mazda MX-5 NC research, but the core loader and
comparison engine have **no Mazda or LF9VEB assumptions**.

## Features

| Capability | Current state |
| --- | --- |
| Open arbitrary binary images | Available |
| SHA-256, file size, entropy, ASCII and hex dump | Available |
| Compare files of different sizes | Available |
| Export inspection and comparison report to JSON | Available |
| Desktop GUI (Windows / Tkinter) | Implemented, Windows build pending CI |
| Limited SH-2 instruction stepping | Experimental; not complete CPU emulation |
| Configurable ECU profiles and memory/peripheral models | Planned |
| Emulate any manufacturer or processor | Not available |
| Read/write or flash a vehicle ECU | Not included |

## Run from Python

Python 3.11+; standard library only for running the app.

```powershell
python -m ecu_workbench
python -m ecu_workbench --rom "C:\\path\\to\\your\\own\\rom.bin"
python -m ecu_workbench --rom stock.bin --compare tuned.bin --report changes.json
```

Optional, explicitly selected limited SH-2 instruction stepping:

```powershell
python -m ecu_workbench --rom firmware.bin --sh2-step --pc 0x100 --base 0x0 --steps 50
```

To run tests:

```powershell
python -m unittest discover -s tests -v
```

The desktop application lets you inspect and compare images without using
the CLI. The project's Windows GitHub Actions build produces a downloadable
workflow artifact when the build succeeds.

## Extensibility roadmap

1. Generic, read-only file loading, hashes and comparisons — **implemented**.
2. Pluggable architecture profiles with explicit CPU/memory mappings.
3. Verified SH-2E execution engine, then additional architecture backends.
4. Configurable hardware peripheral, sensor and interrupt models.
5. Whole-firmware differential execution and reproducible tests.

## Safety, copyright and privacy

- The application **never flashes, edits or writes vehicle firmware**.
- Do not upload proprietary ECU ROMs or calibration definitions into the repository.
- ROMs are opened locally by the user; JSON reports include hashes and selected
  sample bytes, but do not embed full ROM images.
- A passing instruction test is not a certificate of safe ECU operation.

Contributions are welcome under the MIT licence. See CONTRIBUTING.md.
