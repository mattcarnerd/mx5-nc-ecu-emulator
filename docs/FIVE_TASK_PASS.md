# Five-task CPU and startup pass - 24 October 2026

Primary source: [Renesas SH-2E Software Manual Rev.2](https://www.renesas.com/en/document/mas/sh-2e-software-manual), section 2.2 and instruction descriptions 7.2.26/27/58/59. SH7058 SR implements M/Q/I/S/T (mask 0x3F3); reserved bits read zero. This target has no SH-4 user/supervisor mode bit. MACH/MACL and FPU transfer forms remain unsupported.

B12/#15 adds SR/GBR/VBR/PR register and memory forms, CLRT/SETT, current SR-known-bit reporting and unknown-source stops. Predecrement stack stores update the pointer before a bus fault; loads increment only after a successful read. A synthetic test reproduces 4F22, verifies stored PR bytes and checks unknown-state/fault cases.

All 191 tests pass locally with the user-provided original-reference ROM. The public CI suite uses synthetic fixtures; private integration cases skip there. The local ROM is never copied into source or release assets. Its redacted post-B12 report is [here](evidence/lf9veb-after-b12.json): 157 attempts, next RSTCSR write. No full boot is claimed.

## Review after B12

Reviewed all 19 open issues and every backlog row. #1-3 parent scopes remain open. Promote existing B20/#27 to P0 for the observed RSTCSR access; no duplicate. B10/#13, B11/#14 and B16/#19 remain bounded coverage tasks requested in this five-task pass. B19/#22 virtual time is displaced from this pass by B20. FPU #16-18, timing #22, interrupts #28, timer #29, ADC #30, crank/cam #31, outputs #32, harness #34 and sensor UI #35 have no new evidence justifying other scope/dependency changes. Each issue records its own successful CI and Windows release before closure.

## B20 watchdog initialization and review

SH7058 Rev.3 section 13.2.3/13.2.4 specifies RSTCSR word writes at EC12 and byte reads at EC13. Implement keyed control/flag writes, read-before-clear and reserved-one readback. TCNT/TCSR programming at EC10 was then observed; include disabled programming and byte readback. Enabling counting stops explicitly because clock-driven watchdog operation is outside this task. Invalid-key/reserved encodings stop outside the supported write contract; no undocumented silicon effect is guessed. Manual-reset retained values remain unknown.

197 tests pass locally. [Post-B20 redacted evidence](evidence/lf9veb-after-b20.json) reaches 175 attempts, unsupported SHLL8 R6 at D90. Review of all 18 open issues and complete backlog promotes existing B11/#14 to P0; no duplicate or other scope/dependency changes. FPU, timing, interrupts, ADC, engine signals and broader board support remain deferred. The five tasks are now B12, B20, B11, B10 and B16, with priorities reconsidered on every authentic rerun.
