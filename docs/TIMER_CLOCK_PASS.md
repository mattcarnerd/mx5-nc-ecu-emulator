# Startup evidence and interrupt integration pass

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
