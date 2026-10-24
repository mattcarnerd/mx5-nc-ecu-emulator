# Timer clock and dual capture pass

## B57/#64

Deliver second capture interrupt IMI1B to CPU (B57)
Existing GR1B capture now uses vector97/offset184 and shared IPRD[7:4]. Independent flag clearing, same-priority A-before-B, firmware ISR register read/acknowledgement/RTE verified. No physical waveform or original boot assertion.

Validation: Ran 326 tests in 2.767s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b57-no-clock-unknown.json and b57-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. B57 closes existing capture-route gap. B58 overflow, B59 internal clock packets, B60 external edges and B61 integration are explicit requested child scopes; hardware gates unchanged. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five bounded tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B58/#65

Model ATU1A overflow and CPU OVI1A delivery (B58)
Rev.3 TSR1A/TIER1A bit8 and table7.3 vector104/IPRE[15:12]. Explicit counter packets set held overflow with read1/write0 clear; modulo16 wrap and aggregated occurrence count/first-last ticks remain exact. Compare/overflow first-event order is chronological within a packet, with no CPU execution invented inside it. Firmware ISR acknowledgement/RTE and priority tested.

Validation: Ran 329 tests in 2.733s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b58-no-clock-unknown.json and b58-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. B58 overflow prerequisite complete. B59 internal supplied clocks and B60 external selected edges follow; B61 integrates dual captures through rollover. Hardware gates remain unchanged. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five bounded tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B59/#66

B59: model PSCR1 and internal clock division from explicitly supplied zero-phase Pphi packets.

Validation: Ran 331 tests in 3.135s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b59-no-clock-unknown.json and b59-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. All 192 divider combinations checked; supplied fixture phase is explicit, clock frequency and physical timing remain unknown. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five bounded tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B60/#67

B60: count explicitly supplied TCLKA/TCLKB edges with TCR1A edge selection.

Validation: Ran 333 tests in 3.078s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b60-no-clock-unknown.json and b60-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. Both sources and all four edge selections tested; first level establishes a baseline, unselected pins cannot advance the counter. TI10 and AGCKM remain unsupported. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five bounded tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.


## Register semantics and fixture contract

Primary source: [Renesas SH7058 hardware manual Rev.3](https://www.renesas.com/en/document/mah/sh-2e-sh7058-f-ztat-tm-hardware-manual), table7.3 (printed108), table11.3 (printed209), sections11.2.2-11.2.6 (printed234-262).

- PSCR1 at FFFFF404 uses byte access, bits4:0 divide supplied Pphi by value+1; bits7:5 must be zero. TCR1A at FFFFF45D uses byte access: CKSEL0..5 selects the first-stage clock divided by1,2,4,8,16,32. Bits7:6 must be zero.
- CKSEL6 selects TCLKA;7 selects TCLKB. CKEG bits5:4 select rising, falling, both, disabled for values0,1,2,3. TI10/AGCKM remain unsupported. Internal selections with nonzero CKEG are outside this bounded implementation.
- TSR1A OVF1A bit8 is set on TCNT1A FFFF-to-0000 rollover. GR1A/GR1B capture flags are bits0/1; TIER1A enables corresponding requests. Flags require read-one/write-zero acknowledgement. OVI1A uses vector104, IPRE bits15:12; IMI1A/B use vectors96/97, IPRD bits7:4. TCNT1B sharing vector104 is not modelled.
- All fixture clock APIs are opt-in. Internal packets require an explicitly declared zero phase. The divider continues through supplied cycles while the counter is stopped. Changing clock configuration after binding or while running stops explicitly. First external level establishes a baseline; no edge is inferred from an unknown prior level. Raw selected ticks, internal packets and external levels cannot be mixed.
- Clock packets are atomic peripheral advancement, not instruction execution. Multiple wraps are aggregated with occurrence count and first/last selected-clock timestamps; held flags do not count interrupts per wrap. No oscillator frequency, instruction-cycle ratio or physical synchronization delay is inferred.

## Reproduce generated firmware integration

Run either command from the repository:

```
python -m ecu_workbench.dual_capture_fixture --clock-source internal
python -m ecu_workbench.dual_capture_fixture --clock-source external
```

The generated program configures PSCR1=1, internal TCR1A=1 (divide4 overall) or external TCR1A=6 (TCLKA rising), TCNT1A=FFFE, rising capture on both channels, and three enabled requests. Explicit packets at completed-instruction ticks100/180 advance1/2 selected counter ticks. These are scheduling fixtures, not physical time.

Actual generated SH-2 handlers read captures, acknowledge their own flags, increment separate counters and return using RTE. Both clock-source reports require captures FFFF/0001, handler counts1/1/1, vector order96/104/97 (overflow priority6 above capture priority5), cleared flags, restored stack and return to the generated idle loop. Insufficient budget must fail the fixture. Reports are [internal](evidence/b61-dual-internal.json) and [external](evidence/b61-dual-external.json). The source CLI is an integration diagnostic; no new GUI control is claimed. Versioned Windows releases include the updated core.

## B61/#68

B61: verify both capture handlers and overflow across rollover using generated SH-2 firmware and both explicit clock sources.

Validation: Ran 335 tests in 3.463s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b61-no-clock-unknown.json and b61-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. All five child scopes reviewed against remaining work packages. Dual captures, overflow priority, independent acknowledgement, RTE and deterministic repeated reports verified; startup hardware gates remain unresolved. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five bounded tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.
