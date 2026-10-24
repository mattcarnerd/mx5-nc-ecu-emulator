# ROM-only investigation pass

## B67/#74

B67: retain per-byte known-bit masks for explicit RAM transfers.

Validation: Ran 349 tests in 3.780s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b67-no-clock-unknown.json and b67-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 349 tests pass; partial RAM transport preserves overlap masks while concrete reads/peripheral writes require known bits. Updated earlier RAM-store test to the new documented transport contract; strict and ROM-only stops unchanged before B68 stack opcodes. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five ROM-only tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.
