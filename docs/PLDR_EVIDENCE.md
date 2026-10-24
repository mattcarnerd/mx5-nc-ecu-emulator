# B38: Port L data latch evidence

## Supplied diagnostic

The reduced user report is preserved in [evidence](evidence/lf9veb-pldr-blocker.json).
It reports SHA-256 `bfd0965a0f51f60a951d8cd3ef8fe77e5a37fbc326ddb723edf0ede4b1640fbf`,
power reset, NMI high, 300 steps and no explicit pin values. Its 129 attempted
instructions and successful PEDR/PFDR/PGDR/PHDR/PJDR/PKDR trace flags supersede
the previous 117-attempt PKDR stop. The next unmodelled operation is a 2-byte
write of `0x3FFF` to `0xFFFFF75E`, opcode `2031` (MOV.W R3,@R0), instruction
PC `0x00000D18`, stop PC `0x00000D1A`. This is user-supplied diagnostic evidence,
not independent ROM authenticity proof. No ROM bytes or full trace are available.

## Primary register source and bounded semantics

[Renesas SH7058 Hardware Manual Rev.3.00, September 2004](https://www.renesas.com/en/document/mah/sh-2e-sh7058-f-ztat-tm-hardware-manual),
§22.12.1–22.12.2, Tables 22.21 and 22.22, printed pages 828–830
(PDF indices 870–872 in the current Renesas copy) identifies PLDR at this address.

- Byte and aligned word accesses; big-endian byte lanes.
- Bits 13–0 hold data. Bits 15–14 read zero; software must write them zero.
  The emulator rejects reserved-one writes without mutation or success trace;
  it does not guess silicon behaviour outside the documented write contract.
- PLIOR bit zero selects physical pin readback; bit one selects data latch
  readback. Table 22.22 applies this read rule even with alternate pin functions.
  Writes update the latch regardless of direction and do not invent input levels.
- Ordinary power-on reset clears the latch. The manual excludes watchdog
  power-on reset and also specifies hardware-standby initialization. Neither
  WDT reset nor standby transitions are exposed by this bounded model.
  A new manual-reset diagnostic has no supplied pre-reset latch state, so its
  bits remain unknown until written; no retained zero value is fabricated.
- Physical outputs, alternate signals and PLPR are outside this issue.

PLIOR and Port L configuration latches already existed. This pass adds only
PLDR routing, the data model, focused regression tests and a trace-derived
shareable export flag. Existing broad PFC configuration handling is unchanged.

## Mandatory review of the complete open backlog

Reviewed all 19 issues open before B38 was created, including their full bodies
and every row in BACKLOG.md. No PLDR duplicate exists; add B38/#45 as P0 after
B37/#44. The new report confirms the prior PKDR implementation was exercised
under the stated original-reference settings. It provides no post-PLDR evidence.

| Issues / tasks reviewed | Decision and reason |
|---|---|
| #1 hardware variants; #2 CPU/boot; #3 peripheral scenarios | Keep open: board-family proof, full CPU execution and engine scenarios remain incomplete. |
| #13/B10 branches; #14/B11 shifts; #15/B12 control transfers | No changes: PLDR is the observed blocker; no evidence promotes another opcode group. |
| #16/B13 FPU state; #17/B14 transfers/conversion; #18/B15 arithmetic | No changes: retain evidence-driven ordering and FPU-state dependency. |
| #19/B16 exceptions | No changes: control state and verified exception path remain prerequisites. |
| #22/B19 virtual time; #27/B20 watchdog | No changes: no new observed timing or watchdog accesses. |
| #28/B21 interrupt; #29/B22 timer; #30/B23 ADC | No changes: retain exception/time dependencies and require observed register use. |
| #31/B24 crank/cam; #32/B25 outputs | No changes: retain timer and physical-mapping requirements; no invented ECU signals. |
| #34/B27 harness; #35/B28 sensor UI | No changes: retain execution/input prerequisites; no full-boot inference. |

No other reprioritization, splits or duplicate tickets are justified. Optional
private-ROM regression remains available but cannot run here because no ROM
was supplied. After the versioned Windows release, rerun the original ROM
with the same settings and inspect the next real stop. Do not infer it from
synthetic fixtures. Commit, successful CI, release and this review outcome
must be linked in #45 before closure.
