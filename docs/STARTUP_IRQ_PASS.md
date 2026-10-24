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

## B55/#62

Deliver ADC ADI0 completion through CPU interrupt arbitration (B55)
Rev.3 table7.3 ADI0 vector190/offset2F8, IPRJ FFFFED12[11:8]. ADF+ADIE is held until firmware clears ADF via read1/write0 or disables ADIE. Synthetic firmware starts conversion, ISR reads supplied AN0 result, acknowledges and returns; changing voltage changes ISR/main results. Priority/mask/disable/unknown state and simultaneous ATU/ADC/ITI order tested. Artificial completion delay remains explicit.

Validation: Ran 319 tests in 2.647s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b55-no-clock-unknown.json and b55-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. B54/B55 routes implemented; only IMI1A/ADI0/ITI supported. B56 combines actual synthetic firmware configuration, explicit capture/conversion events and raw output. Hardware evidence gates stay unresolved. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five bounded tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B56 integration fixture usage and finish line

From the source checkout:

    python -m ecu_workbench.integration_fixture --voltage 1 --reference 5 --adc-delay 8 --capture-delay 2 --capture-counter-ticks 17

All numeric values here are explicit synthetic inputs, not measurements. The source CLI generates its own program; manufacturer firmware is not used. The Windows GUI release contains the CPU/peripheral implementation and existing startup/AN0 controls; this fixture has a separate source CLI, not a new GUI button.

Firmware configures priorities, direction/latch, capture enable and ADC interrupt/start. IMI1A and ADI0 handlers read the actual peripheral registers, acknowledge their flags, preserve scratch registers on the emulated stack and return through RTE/slot. ADC6 can pre-empt ATU5; simultaneous requests select ADC6 first. The ADC handler derives a raw PortC latch command from the supplied conversion word; this is a synthetic transformation, not fuel/ignition logic.

The ordered log uses one sequence number and completed-instruction tick domain. Selected-counter ticks retain separate named fields. Events cover ADC start/completion, explicit capture input, capture result, CPU entry/return and raw latch writes, with active ISR context. Events are capped256; no physical durations or ECU actuator mapping are inferred. Counts and an instruction limit alone cannot pass the fixture: both handlers must run once, clear their requests, restore the stack and return to the generated main fixture.

[Explicit nested case](evidence/b56-integration-nested.json) and [simultaneous case](evidence/b56-integration-simultaneous.json) are reproducible public evidence. Tests also change voltage1 to4 and capture packet17 to123, verifying ADC count204 to819, captured register values and ADC-handler GPIO19 to12. These are supplied ideal fixtures, not fabricated board values. A too-short budget reports fixture_passed false.

Direct ADC input and ATU clock/pin API calls are counted. Declared peripheral events are counted even if the budget ends before firing. Detailed/baseline/shareable/presenter/reviewer paths retain this provenance and exclude such runs from original reference classification. No original-ROM boot progress is claimed by this generated program.

B52/B53 research reports leave the physical H-UDI/CAN gates unresolved; B54/B55 implement IMI1A/ADI0 only. Other interrupt sources, clock/profile verification and full firmware/engine operation stay open under parents1-3.

## B56/#63

Exercise generated capture ADC and GPIO firmware through interrupts (B56)
Generated source ROM configures peripherals and priorities; ISR instructions capture/read, acknowledge, preserve scratch registers, emit raw GPIO and return. Explicit selected-clock/capture/voltage/reference/completion delays remain fixtures. Ordered bounded log proves nested and simultaneous priority cases; changed inputs alter actual reads/output commands; too-short budget fails. Input/scheduled-event provenance excludes reference classification even before events fire. No manufacturer firmware, NC pattern or engine claim.

Validation: Ran 324 tests in 2.688s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b56-no-clock-unknown.json and b56-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. All five requested bounded tasks completed in scope, subject to final CI/release. Research1/2 retain unresolved evidence under parent1; IMI1A/ADI0 routes and integration implemented. Other sources and physical/engine work remain open; no speculative duplicate issue added. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five bounded tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.
