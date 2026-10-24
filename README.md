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
**59 instructions** and then stopped at Port C PCDR `0xFFFFF73E`.
With **B18**, the ROM advanced to **67 attempted instructions** and stopped
at Port D PDDR `0xFFFFF746`. With **B29**, it passes Port D and reaches
**76 attempted instructions**, stopping at Port E PEDR `0xFFFFF754`.
None of these stages is a completed ECU boot.

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

### B03 — Port B external input simulation

Renesas SH7058 Rev 3.00, §§22.3.1–22.3.3: **PBDR** (`0xFFFFF738`)
combines input-mode physical pin readings with output-mode stored latch values.
**PBPR** (`0xFFFFF782`) is a read-only register that always returns the
physical Port B pin levels, even when output latches contain other values.
Both registers permit 8-bit or 16-bit accesses.

**No pin levels are supplied by default.** Unsupported reads stop as
`missing_input`. For offline research, pass explicitly chosen 16-bit
physical levels and optionally specify which individual bits are known:

```powershell
python -m ecu_workbench --rom original.bin --nmi high --port-b-pins 0x12A5 --port-b-known-mask 0x00FF --steps 300
```

A known-bit mask of `0x00FF` means PB7–PB0 are supplied; PB15–PB8
remain unknown. Hex values are **synthetic test inputs**, not a claim about
Mazda's actual ECU wiring. The desktop app exposes the same inputs.
The original LF9VEB power-on / NMI-high startup still reaches the
unmodelled **Port C data register at `0xFFFFF73E` after 59 instructions**:
this work makes input handling accurate; it does not artificially progress
firmware boot. NMI is the *separate* non-maskable interrupt input monitored
through ICR bit 15 (NMIL); default interrupt-edge selection is falling edge.

## B04 — precise firmware startup blockers

The main JSON diagnostic and the desktop **Next dependency** tab now report:

- Category of stop: unsupported CPU instruction, unmodelled hardware,
  required external pin level, uninitialised RAM, invalid ROM/vector, or
  instruction budget reached. These are deliberately distinct.
- **Failing instruction address**, **fetched opcode** and delay-slot flag,
  independently of the CPU's **PC at stop**, which may have advanced.
- Attempted memory access direction (`read`/`write`/`fetch`), address,
  size and written value when the bus supplies that information.
- The **16 instructions preceding the failing instruction**, excluding
  the attempted failing instruction itself. For an instruction-fetch
  failure there is no invented opcode.
- `is_dependency_blocker: false` when the instruction limit is reached,
  rather than claiming the ECU booted or inventing missing hardware.

The compact `--baseline` JSON also includes `result.next_dependency`.
Existing `pc_at_stop`, raw `stop` and `trace` fields remain for compatibility.

For the unmodified LF9VEB ROM (power-on reset, NMI high), B04 reports
**opcode `2201` at instruction PC `0x00000C8C`**, a 16-bit write of
`0x001F` to unmodelled Port C data register `0xFFFFF73E`.
The existing 59-instruction startup stop remains unchanged. This reporting
improvement does **not** implement Port C or complete ECU boot.

## B05 — reset and NMI regression safety

The synthetic regression matrix runs both **power-on** and **manual reset**
with NMI **unknown / high / low** (six combinations), preserving each reset
vector and stack pointer. Tests verify the two different ICR blockers:
unknown **physical NMI** input after power-on reset is `missing_input`,
whereas **undefined ICR control state after manual reset** is
`unknown_peripheral_reset_state` even when the NMI pin was supplied.
Known NMI input never implies other reset-preserved hardware bits are known.

A new pure, tkinter-independent `present_reset_diagnostic()` function drives
the Windows GUI's status, summary, dependency and trace panels. Its output
always says **ECU boot NOT verified**: a bounded instruction run, an invalid
image or even an optimistic source field cannot turn the current partial CPU
interpreter into a booted ECU. The displayed count means **attempted/fetched**
instructions, not necessarily successfully completed ones.

The regression suite includes an optional real-ROM matrix, enabled by
`MX5_NC_TEST_ROM`. It records only hashes and diagnostic values; the OEM
ROM is never stored in GitHub. Original LF9VEB with power-on reset,
300-instruction limit remains: unknown NMI -> 23 (`missing_input`),
high -> 59 (Port C PCDR `0xFFFFF73E`), low -> 300
(`instruction_limit`). These results are **not ECU boots**.

## B18 — Port C PCDR (SH7058 Rev 3.00)

PCDR (`0xFFFFF73E`) implements PC4..PC0 as a 16-bit data register
with 8- and 16-bit access. Power-on reset clears the data latch;
manual reset preserves unknown previous state until initialised.
Bits 15..5 always read zero and must be written zero.

Reads follow Renesas Table 22.6: PCIOR=0 returns **physical pin state**
and requires explicit input values; PCIOR=1 returns the **stored data latch**.
Serial alternate-function routing is not simulated. Writes do not imply
the physical vehicle pin has changed.

To provide optional simulated inputs, use `--port-c-pins 0x15` and
`--port-c-known-mask 0x1F` on the CLI, or the Port C fields in the
Windows application. By default all external Port C pin levels are unknown.

Original LF9VEB, power reset, NMI high, 300-instruction maximum:
**67 attempted instructions**, stopping on `MOV.W R1,@R0` (opcode
`2011`, instruction address `0x00000C9C`) writing `0x3EFF` to
unmodelled **Port D PDDR** at `0xFFFFF746`. This remains a reset
diagnostic, not a working ECU. The next priority is B29/Port D.

Source: [Renesas SH7058 hardware manual](https://www.renesas.com/en/document/mah/sh-2e-sh7058-f-ztat-tm-hardware-manual),
§22.4 (tables 22.5–22.6).

## B29 — Port D PDDR and PDPR

Renesas SH7058 Rev 3.00 §22.5 (Tables 22.7–22.8) defines the
**Port D data register** at `0xFFFFF746` and the separate
**Port D physical pin register** at `0xFFFFF784`. Both support
8- and 16-bit accesses. PDDR contains 14 meaningful bits (PD13..PD0);
reserved bits 15 and 14 always read zero and must be written zero.

The emulator tracks the data latch separately from explicitly supplied physical
pin levels. With PDIOR=0, PDDR reads the physical pin; with PDIOR=1 it reads
the stored latch. PDPR always reads physical levels. An unprovided input
remains unknown and causes an explicit diagnostic, never a made-up zero.
Both manual-reset uncertainty and big-endian high/low byte accesses are tested.
Timer and HCAN alternate-function pin driving is not simulated.

Example optional input:

```powershell
python -m ecu_workbench --rom original.bin --nmi high --port-d-pins 0x1234 --port-d-known-mask 0x3FFF --steps 300
```

Original LF9VEB (SHA-256 `bfd0965a0f51f60a951d8cd3ef8fe77e5a37fbc326ddb723edf0ede4b1640fbf`)
with power reset, NMI high and no invented physical levels now reaches
**76 attempted instructions** before stopping at opcode `2151`
(`MOV.W R5,@R1`) at instruction address `0x00000CAE`.
It attempts a 16-bit write of `0xFFFF` to **Port E PEDR**
`0xFFFFF754`. This is only a reset diagnostic, not a booted ECU.

Next observed hardware item: **B30 — Port E PEDR**. The NC1/NC2/NC3
hardware-family manifest (B26) follows; GPIO/peripheral refactoring
(B17) is moved forward to avoid piling up separate ad hoc handlers.

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

## B31 — capture the first real blocker after Port E (local ROM only)

The original LF9VEB binary is not included in this repository. On a Windows
computer holding your **own** full ROM image, from the source checkout run:

```powershell
python -m ecu_workbench --rom "C:\\ROMs\\LF9VEB.bin" --reset power --nmi high --steps 300 --baseline --report baseline.json
python -m ecu_workbench.trace_review baseline.json --output review.json
python -m ecu_workbench --rom "C:\\ROMs\\LF9VEB.bin" --reset power --nmi high --steps 300 --report detailed.json
```

The baseline and review contain ROM hashes, execution state, and a short
instruction trace; `detailed.json` additionally contains a peripheral trace
to confirm that the original `PEDR` word write was actually executed.
Inspect reports before sharing: diagnostics can contain firmware-derived
addresses, values and calibration-identifying metadata, though **not a copy
of the ROM**. Do **not** commit any original manufacturer ROM or private
files. If you're sharing evidence, the `review.json` summary is safest.

Previously observed before B30: 76 attempted instructions; stop at
`0x00000CAE` on `MOV.W` to `PEDR 0xFFFFF754` with `0xFFFF`.
Since B30 modelled that register, its next real stop is **unknown until a
local ROM diagnostic is run**. Instruction-count increases alone do not
demonstrate a completed boot, nor conclusively prove a particular write.

## B32 — Share the next startup blocker directly from the Windows EXE

In the [latest Windows prerelease](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/releases),
open **MX5-NC-ECU-Emulator.exe**, load your locally held NC ROM, select
**Reset: power**, **NMI pin: high**, and **Max instructions: 300**,
leave all optional physical pin inputs blank, and run the startup diagnostic.
Then choose **Save shareable blocker JSON…** and share that small file to
review the next instruction or unmodelled register.

The new report is derived **from the diagnostic you actually ran**, so
changing the GUI settings after running does not silently change its label.
It whitelists only the ROM SHA-256, settings, attempted count, stop PC,
stop opcode/address/access and whether a 16-bit `0xFFFF` write to `PEDR`
was present in the recorded peripheral accesses. It **does not** include
the ROM bytes, ROM filename, local path, complete instruction trace or
unrestricted error text. It still contains a ROM hash and some firmware-derived
addresses/opcodes, so inspect the file before sharing externally.

For Python users, the equivalent standalone command is:

```powershell
python -m ecu_workbench.share_report detailed.json --output shareable-blocker.json
```

The **existing** Save diagnostic JSON command still exports the fuller trace
for private debugging. A verified original LF9VEB image has SHA-256
`bfd0965a0f51f60a951d8cd3ef8fe77e5a37fbc326ddb723edf0ede4b1640fbf`.
The report distinguishes that known hash and the original power/NMI-high
300-instruction test from other combinations, but does not attest to the
image's authenticity or claim firmware booted. The post-Port-E stopping point
remains unknown until the original ROM is run locally.

## B33 — Port F startup register found from user diagnostic

A user-generated shareable report from a **different SHA-256** to the
reference LF9VEB image reached **83 attempted instructions** after recording
the expected Port E write. It stopped on the 16-bit write `0xFFFF` to
**PFDR `0xFFFFF74E`**, opcode `2351`, PC `0x00000CBC`.
The SH7058 Rev.3 hardware manual, §§22.7.1–22.7.2, confirms Port F.
This build implements its data latch and read semantics, but not actual
physical pins or POD output drivers. CI tests **do not** establish how far
this original user ROM will run until that ROM is tested again locally.

To find the next real blocker, download the **latest** Windows executable,
load the **same** ROM, select power-on reset, NMI high and 300 instructions,
leave unmeasured physical pin inputs blank, and run the startup diagnostic.
Then use **Save shareable blocker JSON…** again. The report now carries a
`pfdr_word_write_ffff_in_peripheral_trace` field, which is true only if
the 16-bit `0xFFFF` PFDR write was actually recorded during execution.
Do not infer execution from instruction counts alone. A different SHA-256
is a different image, not a verified original LF9VEB regression.

## B34 — original LF9VEB Port G startup blocker

The local original-reference LF9VEB report (SHA-256
`bfd0965a0f51f60a951d8cd3ef8fe77e5a37fbc326ddb723edf0ede4b1640fbf`)
now reaches **94 attempted instructions** with Port E and F writes confirmed.
The next stop is a 16-bit write of `0x000F` to **Port G PGDR
`0xFFFFF764`**, opcode `2131` at PC `0x00000CD2`. B34 implements
Renesas SH7058 Rev.3 §22.8: PG3–PG0 latch and direction-dependent
readback; reserved bits 15–4 read zero and nonzero writes fail explicitly.
Physical pin values and alternate functions are not invented.

Use the latest Windows EXE, **Power** reset, **NMI high**, **300**
instructions, physical pin fields blank, then **Save shareable blocker JSON…**
again. Its `pgdr_word_write_000f_in_peripheral_trace` value is true
only when the actual PGDR write is recorded. A synthetic pass cannot reveal
the next authentic post-PGDR stop; a new local ROM run is required.

## B35 — Original-reference LF9VEB reaches Port H

The local reference-hash LF9VEB diagnostic (power reset, NMI high, 300
instructions, pin values unknown) reported **101 attempted instructions**.
It confirmed the Port E, F and G writes, then stopped attempting a 16-bit
`0xFFFF` write at `0xFFFFF72C` — SH7058 **PHDR**, instruction PC
`0x00000CE0`, opcode `2351`.

B35 models the documented 16-bit Port H data latch (Renesas SH7058
Rev.3 §22.9), power-on reset, manual-reset unknown state and
direction-dependent readback. It never assumes physical Port H pin inputs,
POD drive or external memory-bus behaviour. The shareable JSON now
includes `phdr_word_write_ffff_in_peripheral_trace`, derived only from
the executed peripheral trace.

Rerun the **same original ROM** using the newest Windows prerelease with
**Power**, **NMI high**, **300 instructions**, and physical pin values left
blank. Export another shareable blocker report. No post-PHDR firmware stop
is known until that local test.

## B36 — original-reference LF9VEB reaches Port J

With the original-reference LF9VEB image, power reset, NMI high, 300
instructions and unspecified physical inputs, the local diagnostic now
reports **108 attempted instructions**. Port E, F, G and H writes were
observed before the first stop at **PJDR 0xFFFFF76C**, a 16-bit
`0xFFFF` store (opcode `2151` at `0x00000CEE`).

The SH7058 Rev.3 manual §22.10 (Table 22.17) confirms PJDR is a 16-bit
port data latch supporting aligned byte/word accesses; output-pin reads
use the latch and input-pin reads need explicit pin levels. This build
models those software-visible semantics without inventing physical pin
levels or alternate-function electrical signals. The separately
documented read-only PJPR input register is **not yet modelled**.

To discover the next *real* firmware blocker, use the newest Windows EXE,
load the same original-reference ROM, select **Power reset**, **NMI high**,
**300 instructions**, and leave unmeasured pins blank. After executing,
choose **Save shareable blocker JSON…**. The new
`pjdr_word_write_ffff_in_peripheral_trace` key confirms the PJDR write
only if present in the peripheral trace.
