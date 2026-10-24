# ROM-only investigation pass

## B62/#69

B62: pin LF9VEB public blob identity and separate ROMDrop metadata from hardware evidence.

Validation: Ran 335 tests in 2.821s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b62-no-clock-unknown.json and b62-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. ROM-only path selected from user context. No matching ECU available; provenance match does not resolve silicon or reset gates. Review keeps existing parents and five bounded children, no duplicate broad hardware task. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five ROM-only tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B63/#70

B63: reconcile public ROM identity with startup constraints and define opt-in ROM-only experiments.

Validation: Ran 335 tests in 2.781s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b63-no-clock-unknown.json and b63-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. No new evidence resolves actual TRST history, silicon revision or reserved readback. Backlog separates physical evidence gates from executable software scenarios. B64/B65/B66 remain bounded; no duplicated physical research. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five ROM-only tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.
