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
