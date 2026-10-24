# B40: explicit conditional H-UDI startup scenarios

[Renesas SH7058 Hardware Manual Rev.3](https://www.renesas.com/en/document/mah/sh-2e-sh7058-f-ztat-tm-hardware-manual), table 19.2, section 19.3.2 and status conditions in figure 19.5 distinguish TRST initialization, CPU flag setting and serial completion. B39 already models these events. B40 exposes explicit initial-state assumptions through API/CLI/GUI; it does not implement a TAP state machine or establish actual board reset history.

## Choices and provenance

- `unknown` (default): no H-UDI reset/serial history supplied; SDTRF stays unknown.
- `trst-reset`: assume a preceding TRST initialization; SDTRF starts one.
- `transfer-complete`: assume a preceding serial completion; SDTRF starts zero.

Both assumptions are conditional simulation scenarios. The choice is validated, stored with the executed diagnostic and propagated into GUI status/summary and detailed/baseline/shareable JSON. Exports derive the conditional marker from the validated choice and reject contradictory run/settings metadata. Changing the selector after running cannot relabel the saved result. Legacy reports without the field mean unknown; existing original-reference comparisons remain usable. Assumed runs never satisfy reference-scenario classification even with matching SHA/reset/NMI/steps/no pins.

## Private-ROM comparison

Original SHA-256: `bfd0965a0f51f60a951d8cd3ef8fe77e5a37fbc326ddb723edf0ede4b1640fbf`. All three use power reset, NMI high, 300 maximum instructions and no specified physical pins.

| Choice | Attempts | Stop | Reduced evidence |
|---|---:|---|---|
| unknown | 188 | unknown_peripheral_reset_state; word SDSR read FFFFF7C2; PC EF8, opcode 6321 | [default](evidence/lf9veb-hudi-unknown.json) |
| trst-reset | 212 | unsupported_opcode; PC F0C, opcode 880B | [conditional TRST](evidence/lf9veb-hudi-trst-reset.json) |
| transfer-complete | 212 | unsupported_opcode; PC F0C, opcode 880B | [conditional completion](evidence/lf9veb-hudi-transfer-complete.json) |

The default reference stop is unchanged. Neither conditional result establishes that a real ECU used that state. No ROM bytes, filenames, private paths or full instruction traces are included in these whitelisted evidence files. Boot remains false throughout.

## Validation

221 local tests pass with all private-ROM integration cases enabled. New coverage exercises both reset kinds, defaults/invalid choices, deterministic API output including invalid images, CLI detailed/baseline paths, baseline review classification, shareable provenance and redaction, contradictory metadata rejection, headless GUI choice snapshotting and the original-hash three-scenario comparison. Public CI skips private-ROM tests. The source GUI dropdown was visually checked with all three readable choices and its assumption notice. Windows build/release/commit links are recorded in #47 before closure.

## Mandatory full backlog review

Read every open issue body (#1-3, #16-19, #22, #28-32, #34-35) and every backlog row; no open duplicate covers scenario selection, so B40/#47 is a distinct frontend/provenance task following B39.

- #1 remains the immediate prerequisite for authentic H-UDI/TRST/serial-history evidence; selectable assumptions do not resolve it.
- #2 CPU/boot and #3 engine scenarios remain incomplete. Add B41/#48 for the precise immediate CMP/EQ opcode observed only under explicit assumptions. Completed B09/#12 covered register compares/carry, not this immediate encoding. Label B41 P1 conditional coverage, not a verified next default-reference blocker.
- B13-15/#16-18 FPU, B16/#19 exceptions and B19/#22 time retain their dependencies.
- B21-25/#28-32 interrupts/timer/ADC/crank-cam/outputs and B27-28/#34-35 harness/UI retain current scopes and priorities. No invented engine signals or speculative hardware family is promoted.

No other changes are justified. Next authentic evidence work remains #1; B41 is an optional bounded coverage task with explicit conditional provenance.
