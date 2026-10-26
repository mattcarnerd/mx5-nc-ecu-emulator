# Independent SH instruction and HCAN profile audit (B124/#131)

## Result

The checked instruction semantics match. This does not resolve hardware behavior for prohibited MBC011 and does not prove the entire CPU or firmware startup correct. No execution guard or physical default was relaxed.

Pinned external engine: [pypcode4.0.1](https://github.com/angr/pypcode), Python bindings to Ghidra SLEIGH. Language `SuperH:BE:32:SH-2` (the relevant integer subset, not an assertion that every SH-2E/FPU instruction is covered). Compiled language SHA256 e69e099854e5b6c9e8f4d6b2deae1c038f87abfbc99484ca733e84cbdb897390. See [engine usage documentation](https://docs.angr.io/projects/pypcode/en/latest/guide.html).

## What was independently checked

The external decoder identifies the generated EXTU.B, SHLL8, ADD and MOV.W scaled-displacement forms. Its translated semantics are evaluated with a small generic byte-addressed p-code interpreter. Unsupported operations, unsupplied register bytes, partial decoding and loads outside the explicitly supplied ROM fail; there are no zero defaults for missing state. Register alias bytes and stores use big-endian order. This interpreter is an audit tool, not a full reference CPU or CAN controller.

864 generated vectors compare this SLEIGH semantic path with the emulator: all8 mode values, DLC operands0/8/15/255, R3 constants0/2000/FFFFFF00 (including32-bit wrap), three RAM bases and displacements0/2/15. High garbage in source registers tests byte extraction; memory readback tests word width and ordering; T stays unknown/unchanged. The generated programs contain no copied OEM instruction stream.

Actual local ROM windows are independently decoded/lifted from the authorized images, with entry registers captured from the emulator's declared conditional run. Every store in each window and final R0 match:

| Image | Straight-line window | Instructions | Stores compared | Final address / word |
|---|---|---|---|---|
| LF9VEB | E60 through E70 |9|1| FFFFD104 /2308 |
| LFNPEA | E60 through E70 |9|1| FFFFD104 /2308 |
| LF4XEC | CAC through CBC |9|3| FFFFD104 /0308 |

The LF4XEC window includes two earlier identifier stores; these are compared as well, rather than mistakenly treating them as a semantic discrepancy. No private instruction listing, ROM bytes, full trace or local path appears in the [reduced report](evidence/b124-independent-sh2-audit.json).

Important limitation: entry state is supplied by our emulator. This is not an independent reset-to-stop trace and does not independently validate all earlier control flow, caller arguments, reset assumptions, instruction timing or board profile. The selected nine-instruction windows and generated vectors narrow the arithmetic/decoding question; they do not certify the whole CPU.

## Primary hardware comparison

- [SH7058 Rev.3](https://www.renesas.com/en/document/mah/sh-2e-sh7058-f-ztat-tm-hardware-manual),16.3.2/table16.3, printed533/535: MBC occupies bits10:8,011/110 prohibited; mailbox0 is receive-only.
- [SH7058S/SH7059 Rev.5](https://www.renesas.com/en/document/mah/sh-2e-sh7059-f-ztattm-sh7058s-f-ztattm-hardware-manual),17.3.2, printed430 (PDF page526): same MBC bits and prohibition. Register appendix printed868 (PDF page964) places mailbox0 control at FFFFD104/105. A related chip name does not change the checked interpretation.
- [TN-SH7-A534A/J](https://www.renesas.com/ja/document/tcu/sh7058f-hcan-ii),12October2004, printedpage2,1(6)(B), explicitly prohibits011. Its front page identifies HD64F7058/HD64F7058B and all SH7058 lots. This does not identify the actual physical chip used with any supplied ROM.

No reviewed source establishes an applicable alternative register layout or defined011 behavior for these images. Exact physical suffix/revision remains unverified; tool metadata and filenames do not establish it. This bounded review does not certify every variant or silicon erratum. No mode011-to010 mapping, command-shadow readback or fabricated CAN completion was introduced.

## Reproduction and next evidence

Install audit-only dependencies separately from the application:

```text
python -m pip install -r requirements-audit.txt
python tools/audit_sh2_sleigh.py --synthetic --output independent-audit.json
python tools/audit_sh2_sleigh.py --rom PATH_TO_AUTHORIZED_ROM --output local-audit.json
```

The local-ROM command accepts only the three reviewed image hashes/windows. Outputs contain hashes, assumptions, window addresses and derived control stores, not ROM bytes or filesystem paths. Public CI installs the pinned dependency and requires the generated audit before the test suite; the Windows application does not import this dependency.

Next evidence needed: an independent reset/caller trace demonstrating an earlier CPU/profile discrepancy, or applicable controller behavior evidence explaining011. The audit has not selected between those possibilities. Original-firmware sustained initialization and recurring interrupts remain unverified; generated recurring interrupt tests remain a separate result.
