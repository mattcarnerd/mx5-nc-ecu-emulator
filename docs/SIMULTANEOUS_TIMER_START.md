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
