# TSTR1 FF runtime audit (B112)

Reviewed26 October2026 against Renesas SH7058 hardware manual Rev3 sections11.2.1-3,11.2.7,11.2.15 and11.2.26, and table7.3. Primary source: https://www.renesas.com/en/document/mah/sh-2e-sh7058-f-ztat-tm-hardware-manual .

The explicit investigation reaches TSTR1 FFFFF401 byteFF at PCBED2/op2340. This is a simultaneous start request, not a configuration latch that may be accepted without consequences. Strict defaults remain at the earlier H-UDI gate; CAN recording/reset isolation/prior RAM0/phi16/PC0 and PB/PD0 orFFFF are hypotheses, not an ECU profile. This checkpoint observes zero original-firmware interrupts.

| Startbit | Requested counters | Required behavior before supporting the complete request |
|---|---|---|
|0|32-bit TCNT0|PSCR1 divided Pphi; overflow; bit6-13 interval transitions; ITVRR flags/ADC requests; read-before-zero status clears|
|1|TCNT1A|Existing bounded clock/compare/capture model, explicitly bound clock source/phase; broader GR1C-H/clear-trigger behavior as reached|
|2|TCNT2A|Own counter, PSCR1/TCR2A, eight GR comparisons/captures, overflow and source routing|
|3|TCNT1B andTCNT2B|Both counters, individual TCRs, OCR1/OCR2 comparisons, channel8 start/terminate dependencies|
|4-6|TCNT3/4/5|Individual TCRs; compare/capture/reset and selected mode; overflow/source routing|
|7|Channel10 group|PSCR4;32-bit TCNT10A, reload/correction10C-F and10G; TI10/AGCK/AGCKM and clear/compare/capture dependencies|

Channel10 is not a single free-running counter. TCNT10B counts external TI10 independently of STR10; section11.2.1 also excludes10H from the stop control. Do not equate every channel10 clock to supplied CPU phi. The manual's channel10 register diagrams contain initial-value inconsistencies; per-register text/table values need explicit review before runtime semantics are added.

Existing artificial phi-per-instruction drives the watchdog. It does not silently provide a measured peripheral Pphi frequency, ATU phase, TI10 levels or tooth/engine waveform. Existing ATU1A begin_clock_fixture/advance_phi_cycles is a separately declared Pphi packet source and phase. A future firmware-run fixture must preserve that provenance and ordering, permit firmware configuration before binding, and reject unmodelled clock changes after binding.

Next bounded packages: (1)TCNT0 explicit-Pphi counting with module interval/overflow flags and clear semantics; (2)table7.3 CPU delivery for shared ITV vector80/IPRC7:4 and OVI0 vector92/IPRD11:8, including generated recurring-handler tests; (3)individual remaining timer runtimes/clock/trigger interactions, then simultaneous-start regression. Those packages do not by themselves resolve CAN, external pins, sustained original-firmware initialization or hardware validation. There is no fixed task-count estimate.

B112 retains the rejectedFF value in reduced evidence and verifies no timer register, clock tick, interrupt or completed instruction is fabricated on rejection. Do not skip the write, maskFF to02, freeze newly started counters, patch firmware, or equate repeated PCs with initialization.

## B113-B114 follow-up

TCNT0 now has a separately bound zero-phase Pphi packet runtime and PSCR1 division, modulo32 counting, bit6-13 interval flags and overflow, plus read-before-zero status clears. Shared interval vector80/IPRC7:4 and OVI0 vector92/IPRD11:8 are delivered through the CPU. Generated handlers verify three recurring interval entries, acknowledgement/RTE/stack/SR restoration, overflow-before-shared priority, mask/disable/held request and branch delay slots. ADC triggers, capture enables and simultaneous starts remain explicit stops. No original-ROM interrupt or initialization milestone has been established. The next runtime packages are the other counters and channel10 interactions; generated recurring interrupts do not substitute for those original-firmware requirements.

## B115 bounded upcounter-bank follow-up

An optional `begin_upcounter_bank_clock_fixture(phase=0)` now binds a declared shared Pphi packet domain for TCNT0, existing1A and independent1B/2A/2B/3/4/5 internal-clock counts. TSTR1 values0..7F are supported in that API fixture; bit7/channel10 and FF remain rejected. PSCR1 and each TCR divider determine counts with an explicit zero global phase. Subsequent clock changes, external-clock selections and active counter writes remain unsupported.

The bank validates the entire packet before applying counts. It stops before an unimplemented OCR/GR compare or counter overflow, including GR1C-H events absent from the existing1A subset. Remaining comparator values are documented power-resetFFFF because CPU writes to those registers still stop; manual prior values remain unknown. No compare flag, counter clear, pulse or interrupt is silently dropped. This is counting only up to the next unmodelled event, not full runtime support for those timer groups. Counter0 IRQs and1A's existing bounded events remain supported. Channel8 must be proven quiescent so an accepted1A compare cannot start an unsupported downcounter.

Original-firmware evidence remains the TSTR1 FF stop. The new module is tested with generated scenarios, and is not automatically bound by the source-ROM exploration tool.
