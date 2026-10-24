# HCAN software-reset command subset (B65/#72)

The B64 experiment reaches a concrete word1 store to MCR0 at PC7B6/op2301 only when reserved-bit6 readback is explicitly assumed0. Assuming1 produces word0041 and remains rejected. With bit6 unknown, existing conditional execution still stops592 before a concrete store is selected.

Primary source: [SH7058 Rev.3](https://www.renesas.com/en/document/mah/sh-2e-sh7058-f-ztat-tm-hardware-manual), section16.4.2 printed548 and figure16.7 printed598. Bit0 requests module reset; the controller performs internal reset processing and reports its resulting state through GSR3/IRR0. Clearing bit0 requests release and does not establish bus synchronization.

## Implemented boundary

Accept aligned MCR word commands0000 and0001 on channels0/1. Record last written command, reset-request history and current release request independently per channel. Repeated writes remain requests. All other modes and reserved-one writes stop before mutation. Documented R/W command bits can be read; bit6 remains unknown unless an explicit readback fixture is supplied.

This implements command acceptance/readback only. It does not claim completion, clear unrelated registers optimistically, schedule CAN events, synthesize GSR/IRR acknowledgement, or join the bus. The mailbox_writes map is historical command evidence, not a readable mailbox-memory model, and remains unchanged; all mailbox reads stop. Full software-reset processing and its register effects remain future work. This boundary is deliberate, not an assertion that hardware reset leaves all registers unchanged.

## Original-hash conditional result

With power reset, NMI high, no supplied physical pins, declared H-UDI TRST-reset or transfer-complete, artificial phi1 per completed instruction, explicit bit6=0, budget10000:

- 960 attempts /959 completed.
- PC000001BA, opcode2FB6 (MOV.L R11,@-R15) needs reset-undefined R11.
- Both channels recorded reset requests; no physical completion asserted.
- Bit6=1 branch still stops592 at PC7B6/op2301 writing0041.
- Strict reference remains188 at H-UDI; existing H-UDI/phi-only branch remains592 with unknown bit6.

Reduced reports: b65-bit0-trst-reset.json and corresponding transfer-complete/bit1 files in evidence/. No firmware edits or private traces are published. The next CPU work package is preserving unknown register values through stack save/restore where justified, rather than inventing R11=0.
