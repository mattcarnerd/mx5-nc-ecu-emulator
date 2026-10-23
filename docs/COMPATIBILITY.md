# MX-5 NC engine-ECU compatibility target

This document describes the *target*, not verified emulator support.

| Dimension | Target |
| --- | --- |
| Model | Mazda MX-5/Miata NC (NC1, NC2, NC3), ~2005/06–2015 |
| Engines | Stock 1.8 and 2.0 MZR variants |
| Transmissions | Manual and automatic engine ECU firmware |
| Regions | UK/EU, North America, Japan and other NC markets |
| Software | Factory/updated and modified firmware |
| Formats | Full ECU ROM images first; additional documented formats later |
| Hardware | NC Denso ECU variants; identify actual processor and board family |
| Outside scope | ND/NA/NB, other Mazda vehicles, TCM firmware, ECU flashing |

## Valid ROM vs plausible file

Many NC engine-ECU image workflows use a **1,048,576-byte image**, and
SH7058 Denso hardware is reported for multiple NC variants. Neither fact
proves *every* NC ROM has the same layout or that any particular file is
genuine. The prototype labels such files `plausible_size_only`; it **does not
claim validation or support for firmware execution**.

In future, ROM identification must use independent ECU family evidence,
verified header/ID metadata, segment mappings and checksums. Modified ROMs
may intentionally differ from factory hashes, so checks cannot simply be an
allowlist of stock SHA-256 values.

## Coverage matrix to be populated from evidence

| Family | Calibration IDs | CPU/board | ROM layout | Boot tested | Functional |
| --- | --- | --- | --- | --- | --- |
| NC1 1.8 / manual | To catalogue | To verify | To verify | No | No |
| NC1 2.0 / manual | To catalogue | To verify | To verify | No | No |
| NC1 2.0 / automatic | To catalogue | To verify | To verify | No | No |
| NC2 1.8 / manual | To catalogue | To verify | To verify | No | No |
| NC2 2.0 / manual | To catalogue | To verify | To verify | No | No |
| NC2 2.0 / automatic | To catalogue | To verify | To verify | No | No |
| NC3 1.8 / manual | To catalogue | To verify | To verify | No | No |
| NC3 2.0 / manual | To catalogue | To verify | To verify | No | No |
| NC3 2.0 / automatic | To catalogue | To verify | To verify | No | No |

The table is a planning matrix, not a claim every combination exists in every
market. Verify models, ECU family changes and ROM formats before expanding.

## Sources used to set the initial research direction

- ROMDrop: https://github.com/speepsio/romdrop — NC1/NC2/NC3 scope
- NCFlash: https://github.com/cdufresne81/nc-flash — multi-ROM
  detection and calibration-definition collection
- Example Denso SH7058 / 1 MiB NC calibration:
  https://www.mazdaecu.eu/mazda-mx-5/mazda-mx-5-nc/2008-2.0-mzr-a-t-stage5-lffe/

Repository must not contain any third-party stock ROM image.

## B26 — local ROM evidence inventory

Create a **local** JSON file (not in Git) such as `private-roms.json`:

```json
{
  "entries": [
    {"path": "roms/my-ecu.bin", "family": "unknown", "hardware_profile": "unknown"},
    {"path": "roms/nc2.bin", "family": "NC2", "calibration_id": "example-id",
     "provenance": "ECU sticker + readout notes",
     "hardware_profile": "SH7058", "hardware_evidence": "physical board inspection"}
  ]
}
```

Run `python -m ecu_workbench.rom_manifest private-roms.json --output inventory.json`.
The command reads local files, calculates SHA-256, and exports **only metadata**:
family, trace/provenance claims, hash, byte count, and status; no paths or firmware
bytes appear in the report. Missing files report `not_available`; present files
without verified board evidence report `candidate`. A `verified_profile`
requires a named hardware profile **and** explicit hardware evidence.
`boot_trace_tested` is an **assertion from the operator** needing both that
evidence and the original local file; it never asserts a completed boot.

Neither a SHA-256 hash, calibration ID, filename nor 1 MiB file length
verifies hardware. Treat any manually declared identity or trace evidence as
unverified until independently checked. The CLI is an **inventory tool**, not
a firmware validator. Keep private input paths and output files out of Git.
The first supported scenario remains the single independently held LF9VEB
reset trace; NC1/NC2/NC3 hardware coverage is **still unknown**.
