# Third five-task pass - 24 October 2026

## B42/#49 explicit supplied-phi interval engine

[SH7058 Rev.3 hardware manual](https://www.renesas.com/en/document/mah/sh-2e-sh7058-f-ztat-tm-hardware-manual), section 13, defines interval operation, dividers and flag access. B42 implements the supplied-cycle counter/overflow/ITI subset. No frequency is selected. Explicit fixture phase starts at zero and advances while stopped; callers order cycle packets and writes. Sub-instruction simultaneous T3 collisions are not modelled or claimed. Running watchdog reset mode is rejected.

261 local tests pass. Counter packets are checked for all eight dividers, fractional/batched input, multiple wraps, source-level assertion/clearing, stop/configuration rules and counter writes. [Default](evidence/b42-unknown.json) remains 188; [TRST](evidence/b42-trst-reset.json) and [serial-complete](evidence/b42-transfer-complete.json) assumptions without clock input remain 225. A library engine is not proof of physical elapsed time or full boot.

### Mandatory full backlog review after B42

Read all 12 open issue bodies and all backlog rows. No open duplicate covers the frontend clock integration, so add B43/#50 as the next bounded task in this requested five-task pass. It will expose explicitly conditional clock fixtures, preserving the unknown source by default. #1 actual board H-UDI/clock/phase evidence is unresolved. CPU/engine parents #2/#3 remain open; FPU #16-18, timer/capture #29, ADC #30, crank/cam #31, output #32 and sensor UI #35 retain scope/dependencies. Per-task issue evidence must link commit, successful CI, release and review before closure. Private ROM bytes/paths/full traces stay out of source and releases.
