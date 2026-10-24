# Startup evidence and interrupt integration pass

## B52/#59

Audit H-UDI startup evidence and preserve unresolved board state (B52)
Primary manuals distinguish ordinary reset from TRST and related MCU variants; current image/trace is not board identity or pin history. Report lists exact reproducer, evidence limits and minimum missing observations. Existing H-UDI/default/conditional tests rerun; no source behavior/default change justified.

Validation: Ran 312 tests in 2.484s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b52-no-clock-unknown.json and b52-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. B52 research scope complete; hardware1 gate remains unresolved. B53 CAN audit next, B54/B55 verified vector routes then B56 integration. No duplicate broad research issue. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five bounded tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B53/#60

Audit HCAN constraints without fabricating reserved readback (B53)
Reviewed Rev.3 reserved-bit/mailbox rules, product technical-update listing and TN-SH7-A534A/J with its earlier-manual scope. No applicable reserved-bit waiver established. Retain existing unknown-mask store stop and inactive2700 caveat; document profile/conformance question and missing MCU/read-write evidence. Existing partial-value/no-side-effect regressions rerun; no firmware patch or guessed CAN state.

Validation: Ran 312 tests in 2.567s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b53-no-clock-unknown.json and b53-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. B53 research complete with unresolved evidence gate; parents1-3 stay open. B54 ATU source route then B55 ADC and B56 integrated fixture are independent synthetic implementation work. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five bounded tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B54/#61

Deliver ATU IMI1A through CPU interrupt arbitration (B54)
Rev.3 table7.3: vector96/offset180 and IPRD FFFFED06[7:4]. Module IMF1A/IME1A generates held request; acceptance preserves flag. Highest supported configured priority wins, equal priorities use table order; ITI preserved. Masks/zero priority, delayed slots, transfer inhibition, read1/write0 ISR acknowledgement, RTE, held-source reentry and unknown states tested. Active IMI1B route still fails explicitly rather than disappear.

Validation: Ran 316 tests in 2.568s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b54-no-clock-unknown.json and b54-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. B54 implemented; B55 adds ADI0 vector190/IPRJ[11:8], then B56 integration. B52/B53 evidence gates remain open under parents despite completed research. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five bounded tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.
