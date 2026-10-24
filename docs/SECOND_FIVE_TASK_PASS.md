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

## B21/#28 one explicit interval interrupt route

SH7058 hardware manual table 7.3 and section 7.2.5 assign WDT ITI vector224 (offset380) and IPRL[7:4] (IPRL at FFFFED16). The API accepts an explicitly supplied ITI request level; no overflow is generated. Requests remain asserted until the supplier deasserts them. Priority zero, SR mask and equal/lower priorities block entry. Acceptance saves the exact PC/SR frame and raises the SR interrupt mask. No acceptance occurs between branch/slot or the documented interrupt-disabled transfer and its following instruction. Unknown SR/priority and bus failures remain explicit stops; injected request history cannot be classified as reference evidence.

245 local tests pass including private integrations. [Default](evidence/b21-unknown.json) remains 188; [TRST](evidence/b21-trst-reset.json) and [serial completion](evidence/b21-transfer-complete.json) remain 225; no ITI event is injected into those runs. This verifies plumbing synthetically, not authentic timer operation. Full open-backlog review: no changes; B27 can now use the tested event/exception route; B42 still owns supplied-phi timing and #1 board reset evidence remains missing. FPU, timer/capture, ADC and engine scopes stay deferred.

## B27/#34 bounded execution harness and final review

Coverage tracks fetched/completed instructions, unique PC addresses and repeat visits, attempted/completed slots, interrupt entries and every bus failure count. Reports cap PC listings at 256 and failure histories at 100 while retaining exact totals/truncation markers. Host probes outside an executing instruction are not attributed to the previous PC. A repeated PC or instruction limit never sets boot_complete.

`ecu_workbench.execution_harness.run_execution_harness` runs the same CPU with an ordered list of explicit `{'tick': integer, 'asserted': boolean}` ITI input events. Tick units are completed instructions, not phi cycles or seconds. Event inputs are validated before execution. Both fired requests and scheduled-but-unfired events retain injection provenance; shareable/baseline reference classification excludes them. No source overflow is generated automatically. Existing CLI/GUI detailed reports include coverage without adding extra physical-input controls.

254 local tests pass with all private-ROM cases enabled. Loop, memory/CPU failure, bounded-history, event-order, interrupt/frame and provenance tests are synthetic. The private harness regression verifies coverage/count consistency and the unchanged three scenario stops. [Default](evidence/b27-unknown.json) remains 188; [TRST assumption](evidence/b27-trst-reset.json) and [serial-complete assumption](evidence/b27-transfer-complete.json) remain 225. The safe evidence files include reduced stop/provenance fields, never ROM bytes, private names/paths, coverage PC maps or full instruction traces.

Final complete open-backlog review: no further changes. #1 genuine board H-UDI history remains unresolved. B42/#49 is the next conditional timing dependency; it must accept explicit phi-cycle input rather than assuming one instruction is one hardware cycle. #2 full CPU/boot and #3 engine workstreams remain incomplete. FPU #16-18, timer/capture #29, ADC #30, crank/cam #31, outputs #32 and live sensor UI #35 retain prerequisites and evidence requirements. All five completed-task issues must link their own implementation, successful CI, Windows release and backlog-review outcome before closure. No full boot, idle, RPM or physical output claim is made.
