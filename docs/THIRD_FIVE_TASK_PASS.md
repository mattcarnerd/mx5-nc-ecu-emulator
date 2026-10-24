# Third five-task pass - 24 October 2026

## B42/#49 explicit supplied-phi interval engine

[SH7058 Rev.3 hardware manual](https://www.renesas.com/en/document/mah/sh-2e-sh7058-f-ztat-tm-hardware-manual), section 13, defines interval operation, dividers and flag access. B42 implements the supplied-cycle counter/overflow/ITI subset. No frequency is selected. Explicit fixture phase starts at zero and advances while stopped; callers order cycle packets and writes. Sub-instruction simultaneous T3 collisions are not modelled or claimed. Running watchdog reset mode is rejected.

261 local tests pass. Counter packets are checked for all eight dividers, fractional/batched input, multiple wraps, source-level assertion/clearing, stop/configuration rules and counter writes. [Default](evidence/b42-unknown.json) remains 188; [TRST](evidence/b42-trst-reset.json) and [serial-complete](evidence/b42-transfer-complete.json) assumptions without clock input remain 225. A library engine is not proof of physical elapsed time or full boot.

### Mandatory full backlog review after B42

Read all 12 open issue bodies and all backlog rows. No open duplicate covers the frontend clock integration, so add B43/#50 as the next bounded task in this requested five-task pass. It will expose explicitly conditional clock fixtures, preserving the unknown source by default. #1 actual board H-UDI/clock/phase evidence is unresolved. CPU/engine parents #2/#3 remain open; FPU #16-18, timer/capture #29, ADC #30, crank/cam #31, output #32 and sensor UI #35 retain scope/dependencies. Per-task issue evidence must link commit, successful CI, release and review before closure. Private ROM bytes/paths/full traces stay out of source and releases.

## B43/#50 explicit conditional clock integration

API/CLI/GUI accept an optional artificial phi-cycle count per completed instruction, 1..1000000. Blank/None stays unknown. A supplied policy declares zero fixture origin/phase; it is never measured CPU latency, oscillator frequency or seconds. Ordering is instruction completion, scheduled callbacks, then the phi packet. Sub-instruction T3 collisions and real instruction timing are not represented. Generated interval-source changes are distinguished from manual ITI injections. Clock/hardware conditional markers and the actual saved choice persist through detailed/baseline/shareable output and presentation, with mismatch rejection and original-reference exclusion.

268 local tests pass. GUI field/notice visually verified. [No-clock default](evidence/b43-no-clock-unknown.json) stays188; no-clock H-UDI assumptions stay225. Explicit clock fixtures [ratio1/TRST](evidence/b43-clock1-trst-reset.json), [ratio1/serial complete](evidence/b43-clock1-transfer-complete.json), [ratio512/TRST](evidence/b43-clock512-trst-reset.json) and [ratio512/serial complete](evidence/b43-clock512-transfer-complete.json) reach233: word0 to HCAN MCR_0 FFFFD000 at PC792/op2341. An unknown H-UDI still stops188 even with a clock fixture. These results are conditional scenarios, not hardware observations.

Complete open-backlog/body/row review: add B44/#51 for the newly observed reset-release command; no open duplicate exists. #1 board TRST/clock/bus evidence remains unresolved. Other FPU/timer/ADC/engine tasks retain scope/dependencies. No CAN status or bus-idle value will be invented. CI/release evidence belongs in #50 before closure.

## B44/#51 HCAN reset-release command

SH7058 table16.4/section16.4.2 identify MCR_0/1 and word-only access. This subset records only the observed zero reset-release request, with known power reset request and unknown manual prior state. It does not declare synchronization, eleven recessive bits, GSR transitions or CAN traffic. Nonzero unsupported modes fail; full MCR readback fails explicitly because reserved bit6 is not guaranteed, rather than manufacturing a word.

272 local tests pass. [Default](evidence/b44-no-clock-unknown.json) remains188; no-clock H-UDI runs remain225. Explicit [TRST+clock1](evidence/b44-clock1-trst-reset.json) and [serial-complete+clock1](evidence/b44-clock1-transfer-complete.json) reach238, next mailbox header zero at FFFFD100/PC79C/op2541. Full backlog review: add non-duplicate B45/#52 for documented mailbox initialization only; other scopes/dependencies unchanged. #1 board/CAN evidence remains unresolved.
