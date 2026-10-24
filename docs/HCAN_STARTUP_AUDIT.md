# B53 HCAN startup constraints audit

Outcome: **no evidence-backed waiver for the unknown reserved write; preserve the stop**. This is an emulator-profile/conformance question, not proof that the real ECU firmware or hardware is defective.

## Primary sources checked

- [SH7058 Rev.3 hardware manual](https://www.renesas.com/en/document/mah/sh-2e-sh7058-f-ztat-tm-hardware-manual): section16.4.2, bit6 is unspecified on reads and requires zero on writes; section16.3.1 requires non-MBC settings cleared for inactive mailboxes. Table16.3 defines MBC111 inactive.
- [Renesas TN-SH7-A534A/J](https://www.renesas.com/ja/document/tcu/sh7058f-hcan-ii),12 October2004: applies to HD64F7058/HD64F7058B, references earlier provisional/Rev.2 documentation and covers HCAN usage/reset/cancellation restrictions. The reviewed update does not provide an MCR bit6 readback guarantee or permission to preserve an arbitrary read value on write. Its illustrative flow does not override its own prohibition on starting the HCAN timer.
- [SH7058 product documentation listing](https://www.renesas.com/en/products/sh7058): consulted for technical updates. This bounded search is not an exhaustive silicon/lot errata certification; no claim that no other update exists.

## Reproducer and conclusions

Original hash regression with power reset/NMI high/no pins, explicitly assumed TRST or transfer-complete H-UDI, artificial phi1 and separate10000 budget reaches592 attempts/591 completed. PC7B6/op2301 attempts a word store to FFFFD000. The prior MCR load yields low known maskFFBF/value0000; OR1 produces known value0001 while bit6 remains unknown. Existing tests confirm no concrete value, write event or reset side effect is fabricated. A synthetic explicit AND mask resolves the bit, but changing the private firmware is not an emulator fix.

    python -m ecu_workbench --rom YOUR_LOCAL_IMAGE --reset power --nmi high --steps 10000 --hudi-scenario trst-reset --phi-cycles-per-instruction 1

Reduced reports b53-clock1-budget10000-trst-reset.json and transfer-complete counterpart preserve these assumptions; default300 remains188 at H-UDI. Earlier observed2700 mailbox commands have NMC1/MBC111; their trace records the unused-mailbox initialization caveat. They are command observations, not validated CAN operation. No GSR transitions, recessive-bit detection, CAN traffic or physical clock values follow from these results.

Next evidence: verify the actual MCU/board revision and applicable documentation, then acquire or cite justified MCR read/write behavior under that profile, or identify an independently proven CPU/profile error. Search results for related devices cannot establish applicability. Until then, keep both the MCR unknown mask and mailbox caveat. Parent#1/#2/#3 remain open. Research completion documents the unresolved gate and its negative regression tests; it does not advance firmware past it.
