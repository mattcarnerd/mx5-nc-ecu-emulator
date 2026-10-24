# Second five-task pass - 24 October 2026

## B41/#48 CMP/EQ immediate

[Renesas SH-2E Software Manual Rev.2](https://www.renesas.com/en/document/mas/sh-2e-software-manual), section 7.2.15, defines a sign-extended 8-bit immediate equality comparison with R0 that updates T only. Added this encoding with positive/negative/zero equality and inequality tests, preservation of R0, unknown-R0 stop and branch-consumer regression. 224 local tests pass with all private-ROM cases enabled.

Original reference hash and power/NMI-high/300/no-physical-pin settings are unchanged. [Default](evidence/b41-unknown.json) stays at 188/unknown SDSR. [Assumed TRST](evidence/b41-trst-reset.json) and [assumed serial completion](evidence/b41-transfer-complete.json) both reach 225 attempts, stopping on the running-timer enable write (TCSR word A53C at FFFFEC10, instruction PC 786, opcode 2E11). Conditional hardware provenance remains explicit; no fabricated clock timing is used.

### Complete backlog review after B41

Reviewed all 16 open issue bodies and every backlog row. No existing open ticket covers running WDT timing; completed B20 was disabled programming only, so add bounded B42/#49. Select existing B19/#22 abstract clock, B16/#19 one exception/RTE path, B21/#28 one interrupt route and B27/#34 coverage harness as the four remaining requested tasks. They are documented prerequisites and coverage, not an assertion of further original-reference execution. #1 remains the authentic H-UDI board-history prerequisite. FPU #16-18, timers #29, ADC #30, engine edges/outputs #31-32 and UI #35 retain scopes/dependencies. Commit/CI/versioned EXE evidence is recorded in each issue before closure. Private ROM bytes and paths are never committed.
