# Five-task CPU and startup pass - 24 October 2026

Primary source: [Renesas SH-2E Software Manual Rev.2](https://www.renesas.com/en/document/mas/sh-2e-software-manual), section 2.2 and instruction descriptions 7.2.26/27/58/59. SH7058 SR implements M/Q/I/S/T (mask 0x3F3); reserved bits read zero. This target has no SH-4 user/supervisor mode bit. MACH/MACL and FPU transfer forms remain unsupported.

B12/#15 adds SR/GBR/VBR/PR register and memory forms, CLRT/SETT, current SR-known-bit reporting and unknown-source stops. Predecrement stack stores update the pointer before a bus fault; loads increment only after a successful read. A synthetic test reproduces 4F22, verifies stored PR bytes and checks unknown-state/fault cases.

All 191 tests pass locally with the user-provided original-reference ROM. The public CI suite uses synthetic fixtures; private integration cases skip there. The local ROM is never copied into source or release assets. Its redacted post-B12 report is [here](evidence/lf9veb-after-b12.json): 157 attempts, next RSTCSR write. No full boot is claimed.

## Review after B12

Reviewed all 19 open issues and every backlog row. #1-3 parent scopes remain open. Promote existing B20/#27 to P0 for the observed RSTCSR access; no duplicate. B10/#13, B11/#14 and B16/#19 remain bounded coverage tasks requested in this five-task pass. B19/#22 virtual time is displaced from this pass by B20. FPU #16-18, timing #22, interrupts #28, timer #29, ADC #30, crank/cam #31, outputs #32, harness #34 and sensor UI #35 have no new evidence justifying other scope/dependency changes. Each issue records its own successful CI and Windows release before closure.

## B20 watchdog initialization and review

SH7058 Rev.3 section 13.2.3/13.2.4 specifies RSTCSR word writes at EC12 and byte reads at EC13. Implement keyed control/flag writes, read-before-clear and reserved-one readback. TCNT programming at EC10 was then observed. Disabled TCSR programming and byte readback have synthetic coverage; no TCSR write is observed in the authentic trace before the current stop. Enabling counting stops explicitly because clock-driven watchdog operation is outside this task. Invalid-key/reserved encodings stop outside the supported write contract; no undocumented silicon effect is guessed. Manual-reset retained values remain unknown.

197 tests pass locally. [Post-B20 redacted evidence](evidence/lf9veb-after-b20.json) reaches 175 attempts, unsupported SHLL8 R6 at D90. Review of all 18 open issues and complete backlog promotes existing B11/#14 to P0; no duplicate or other scope/dependency changes. FPU, timing, interrupts, ADC, engine signals and broader board support remain deferred. The five tasks are now B12, B20, B11, B10 and B16, with priorities reconsidered on every authentic rerun.

## B11 shifts/rotates and review

Software manual sections 7.2.44-47 and 7.2.51-56 define fixed shifts and rotations. Added SHLL/SHAL/SHLR/SHAR, shifts by 2/8/16 and ROTL/ROTR/ROTCL/ROTCR with explicit incoming T for carry rotation. Multi-bit shifts preserve T. Tests cover zero/sign/wrap and unknown states.

200 local tests pass. [Post-B11 evidence](evidence/lf9veb-after-b11.json) reaches 188 attempts: SDSR word read at FFFFF7C2, instruction PC EF8, opcode 6321. Reviewed all remaining open issues and complete backlog; no H-UDI task exists, so add one bounded P0 SDSR issue. Do not substitute the TRST-only initial value for missing reset history. B16 is displaced from this five-task pass by this real blocker; B10 remains independent coverage. No other priority/dependency changes.

## B39 H-UDI status and review

SH7058 Rev.3 table 19.2 and section 19.3.2 specify SDSR reserved readback 0x0B00 and the independent SDTRF flag. Neither power nor manual reset initializes this register. Implement byte/word access with unknown flag by default; explicit synthetic TRST and serial-complete events demonstrate known-state readback. CPU writes can set the flag; no spontaneous debugger or serial activity is generated. Combined long access through SDIR/SDSR is outside this subset.

204 tests pass with private integration enabled. [Post-B39 evidence](evidence/lf9veb-after-b39.json) remains at 188 attempts with unknown_peripheral_reset_state instead of unmodelled_peripheral. This is a more precise blocker, not further firmware execution. Reviewed the entire remaining backlog: track verified board TRST/serial-history evidence under existing #1, no duplicate research ticket. B10 is the fifth requested task; all other priorities/dependencies unchanged. No fabricated physical state is used.

## B10 delayed branches and final review

Software manual sections 7.2.4-12 define conditional delayed and register-relative branches. Added BT/S/BF/S/BRAF/BSRF. A not-taken conditional has no delay-slot instruction; the next instruction executes normally. Taken branches capture their destination before the slot, BSRF saves PC+4 to PR, and a branch in a slot fails before link mutation. The runner retains a pending destination if the step limit ends before a required slot, so a later bounded run resumes correctly.

212 tests pass with every private-ROM integration case enabled; public CI runs the same suite with private-ROM cases skipped. [Final redacted reference evidence](evidence/lf9veb-after-b10.json) still reports 188 attempts and unknown SDSR state at EF8/6321/F7C2. B10 has not been demonstrated to advance this reference trace.

Final full backlog review: no changes beyond existing #1 evidence work for H-UDI TRST/serial history. Parent #2 CPU/boot and #3 engine scenarios remain open. B16/#19 exceptions, B19/#22 timing, B13-15/#16-18 FPU, B21/#28 interrupts, B22/#29 timers, B23/#30 ADC, B24/#31 crank/cam, B25/#32 outputs, B27/#34 harness and B28/#35 UI retain their evidence/dependency requirements. No new speculative task is introduced. B12, B20, B11, B39 and B10 each require successful CI and a Windows release linked in their issue before closure.

## Reproduction and limits

Use the same legally held original-reference ROM with power reset, NMI high, 300 instructions, and physical pins unspecified. Public reports contain only reduced whitelisted diagnostics; manufacturer ROM bytes, names, private paths and full traces are not committed. H-UDI is deliberately unknown until supported by explicit reset/serial history. Do not substitute a synthetic TRST event for evidence of real ECU wiring or claim full boot from instruction counts.

An optional exact-hash reference regression additionally verifies successful PLDR/RSTCSR/TCNT writes, execution of the original PR stack-save instruction and the precise known H-UDI stop when still at 188 attempts. Future genuine progress may exceed that baseline without failing an obsolete exact-count assertion.

Authentic-trace clarification: before the current 188-attempt stop, RSTCSR and TCNT writes are observed; TCSR programming support is synthetic-only. No TCSR write or running watchdog is claimed.
