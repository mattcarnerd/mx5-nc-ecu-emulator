# Five-task CPU and startup pass - 24 October 2026

Primary source: [Renesas SH-2E Software Manual Rev.2](https://www.renesas.com/en/document/mas/sh-2e-software-manual), section 2.2 and instruction descriptions 7.2.26/27/58/59. SH7058 SR implements M/Q/I/S/T (mask 0x3F3); reserved bits read zero. This target has no SH-4 user/supervisor mode bit. MACH/MACL and FPU transfer forms remain unsupported.

B12/#15 adds SR/GBR/VBR/PR register and memory forms, CLRT/SETT, current SR-known-bit reporting and unknown-source stops. Predecrement stack stores update the pointer before a bus fault; loads increment only after a successful read. A synthetic test reproduces 4F22, verifies stored PR bytes and checks unknown-state/fault cases.

All 191 tests pass locally with the user-provided original-reference ROM. The public CI suite uses synthetic fixtures; private integration cases skip there. The local ROM is never copied into source or release assets. Its redacted post-B12 report is [here](evidence/lf9veb-after-b12.json): 157 attempts, next RSTCSR write. No full boot is claimed.

## Review after B12

Reviewed all 19 open issues and every backlog row. #1-3 parent scopes remain open. Promote existing B20/#27 to P0 for the observed RSTCSR access; no duplicate. B10/#13, B11/#14 and B16/#19 remain bounded coverage tasks requested in this five-task pass. B19/#22 virtual time is displaced from this pass by B20. FPU #16-18, timing #22, interrupts #28, timer #29, ADC #30, crank/cam #31, outputs #32, harness #34 and sensor UI #35 have no new evidence justifying other scope/dependency changes. Each issue records its own successful CI and Windows release before closure.
