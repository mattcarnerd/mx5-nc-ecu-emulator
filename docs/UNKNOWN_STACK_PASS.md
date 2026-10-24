# ROM-only investigation pass

## B67/#74

B67: retain per-byte known-bit masks for explicit RAM transfers.

Validation: Ran 349 tests in 3.780s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b67-no-clock-unknown.json and b67-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 349 tests pass; partial RAM transport preserves overlap masks while concrete reads/peripheral writes require known bits. Updated earlier RAM-store test to the new documented transport contract; strict and ROM-only stops unchanged before B68 stack opcodes. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five ROM-only tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B68/#75

B68: preserve reset-undefined values through stack MOV save and restore.

Validation: Ran 351 tests in 3.836s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b68-no-clock-unknown.json and b68-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 351 tests pass. Zero-readback experiment now reaches973 attempts at GSR0 word read FFFFD002, PCDB2/op6351. No register initialized artificially; raw RAM/peripheral/control guards remain. B70 will be narrowed to GSR reset-status uncertainty after B69. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five ROM-only tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.
