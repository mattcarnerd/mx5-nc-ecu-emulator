# Second five-task pass - 24 October 2026

## B41/#48 CMP/EQ immediate

[Renesas SH-2E Software Manual Rev.2](https://www.renesas.com/en/document/mas/sh-2e-software-manual), section 7.2.15, defines a sign-extended 8-bit immediate equality comparison with R0 that updates T only. Added this encoding with positive/negative/zero equality and inequality tests, preservation of R0, unknown-R0 stop and branch-consumer regression. 224 local tests pass with all private-ROM cases enabled.

Original reference hash and power/NMI-high/300/no-physical-pin settings are unchanged. [Default](evidence/b41-unknown.json) stays at 188/unknown SDSR. [Assumed TRST](evidence/b41-trst-reset.json) and [assumed serial completion](evidence/b41-transfer-complete.json) both reach 225 attempts, stopping on the running-timer enable write (TCSR word A53C at FFFFEC10, instruction PC 786, opcode 2E11). Conditional hardware provenance remains explicit; no fabricated clock timing is used.

### Complete backlog review after B41

Reviewed all 16 open issue bodies and every backlog row. No existing open ticket covers running WDT timing; completed B20 was disabled programming only, so add bounded B42/#49. Select existing B19/#22 abstract clock, B16/#19 one exception/RTE path, B21/#28 one interrupt route and B27/#34 coverage harness as the four remaining requested tasks. They are documented prerequisites and coverage, not an assertion of further original-reference execution. #1 remains the authentic H-UDI board-history prerequisite. FPU #16-18, timers #29, ADC #30, engine edges/outputs #31-32 and UI #35 retain scopes/dependencies. Commit/CI/versioned EXE evidence is recorded in each issue before closure. Private ROM bytes and paths are never committed.

## B19/#22 completed-instruction clock

One abstract tick advances only after a successfully completed instruction; attempted instructions remain a separate diagnostic count. Delay slots count once; a paused pending slot resumes once; failed instruction/fetch does not gain completed time. Explicit callbacks are ordered by tick then insertion sequence. Detailed/baseline reports and GUI summaries expose the policy, pending-event count, and null CPU-cycle/seconds values. This is scheduling infrastructure, not a silicon timing estimate. No oscillator value or instruction-to-phi conversion is assumed.

230 local tests pass. [Default](evidence/b19-unknown.json) remains at 188; [TRST assumption](evidence/b19-trst-reset.json) and [serial-complete assumption](evidence/b19-transfer-complete.json) remain at 225. Running-timer stops are now classified unsupported_hardware_access without changing their PC/opcode/access/value. Full open-backlog review: no changes; B16 exception handling precedes B21 routing, B27 follows those prerequisites, B42 still needs explicit phi-cycle input, and #1 remains authentic board evidence. Deferred FPU and engine-related tasks retain their requirements.

## B16/#19 one TRAPA/RTE path

Software manual sections 7.2.48 and 7.2.65 plus SH7058 section 6.5.2 specify this bounded path. TRAPA pushes SR then next-instruction PC, fetches VBR+4*imm and jumps without a delay slot. RTE reads PC then SR and restores status before its required slot. Unknown SR stops before frame fabrication. Memory faults retain documented partial stack progress; unsupported exception families remain explicit diagnostic stops. Tests exercise the frame, vector bounds/relocation, reserved SR mask, slot legality, unknown state, partial bus failures and return-slot state.

237 local tests pass with private integrations. [Default](evidence/b16-unknown.json) remains 188; [TRST](evidence/b16-trst-reset.json) and [serial completion](evidence/b16-transfer-complete.json) remain 225. No real-ROM TRAPA/RTE execution is asserted. Complete open-backlog review: no changes; B21 now has a tested entry helper and clock prerequisite, B27 follows; B42 still owns actual running interval timing and #1 board history remains missing. FPU, ADC and engine-related work is not promoted.
