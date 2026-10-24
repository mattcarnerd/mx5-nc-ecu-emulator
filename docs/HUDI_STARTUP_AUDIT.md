# B52 H-UDI startup evidence audit

Outcome: **hardware state remains unresolved; no startup value selected**.

| Evidence | What it establishes | What it cannot establish |
|---|---|---|
| SH7058 Rev.3 section19.3.2/table19.2 | SDSR reset domain is TRST, not ordinary reset; TRST fixture has SDTRF1 | Actual NC board TRST history |
| SH7058S/SH7059 Rev.5 differences table | Related parts have different SDSR fixed-bit patterns/reset details | That this ECU contains either related part |
| Local original-hash firmware regression | Default power/NMI-high/300/no pins stops188, PC EF8/op6321/SDSR FFFFF7C2 | MCU package marking, wiring, debug activity or physical voltage/time |
| Explicit TRST/transfer-complete scenarios | Testable software paths under declared input history | Authentic board startup behavior |

Sources: [SH7058 Rev.3](https://www.renesas.com/en/document/mah/sh-2e-sh7058-f-ztat-tm-hardware-manual), section19.3.2, printed701; [SH7058S/SH7059 Rev.5](https://www.renesas.com/en/document/mah/sh-2e-sh7059-f-ztattm-sh7058s-f-ztattm-hardware-manual), differences table. Do not import one part's reset values into another profile.

## Reproducer and minimum missing evidence

Use the authorized original image locally, power reset, NMI high,300 steps, no explicit pins, H-UDI unknown and no artificial phi ratio. CLI:

    python -m ecu_workbench --rom YOUR_LOCAL_IMAGE --reset power --nmi high --steps 300

Reduced evidence is stored in b52-no-clock-unknown.json. The private image is identified by SHA-256 bfd0965a0f51f60a951d8cd3ef8fe77e5a37fbc326ddb723edf0ede4b1640fbf; bytes/paths/full traces are not published.

To replace unknown with an observed profile, obtain a legible MCU/board identity, relevant schematic or continuity evidence for TRST/reset circuitry, and a reproducible record of TRST/debug/serial history through the relevant startup. A readback observation must include those conditions and its acquisition method. This audit has no such board evidence; a matching firmware hash or conditional execution result cannot substitute for it. Do not prescribe a physical level from this report.

Existing fail-closed H-UDI/reset/provenance tests are rerun; no redundant behavior change or new default is justified. Parent hardware issue#1 remains open. Research task completion means the evidence gate/reproducer is documented, not that the gate has been resolved.
