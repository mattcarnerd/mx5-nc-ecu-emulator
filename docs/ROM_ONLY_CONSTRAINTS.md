# ROM-only startup constraints and experiment contract (B63/#70)

## Evidence reconciliation

[B62 provenance](ROM_PROVENANCE.md) supports an SH7058 tool memory model, not a verified MCU suffix/revision. It gives no new board/TRST or MCR readback observation. Therefore the [H-UDI](HUDI_STARTUP_AUDIT.md) and [HCAN](HCAN_STARTUP_AUDIT.md) evidence gates remain open. No SH7058S/SH7059 replacement profile is justified by an unrelated board or another calibration.

Primary sources rechecked:
- [SH7058 Rev.3 manual](https://www.renesas.com/en/document/mah/sh-2e-sh7058-f-ztat-tm-hardware-manual), section19.3.2/table19.2: ordinary reset does not establish SDSR; existing TRST/transfer-complete choices remain explicit scenarios.
- Same manual section16.4.2, printed542-546: MCR reserved bit6 has no guaranteed read value and requires zero on write. An experimental read-one followed by a write-one must still stop; an experiment never waives a write constraint.
- Same manual figure16.7, printed598: MCR bit0 requests software reset; reset completion/configuration status is a separate question. Mailboxes are RAM requiring initialization. Setting this bit does not establish normal CAN operation.
- [TN-SH7-A534A/J](https://www.renesas.com/ja/document/tcu/sh7058f-hcan-ii), 12 October2004: updates reset/settings flow; no new guarantee of bit6 readback identified. This limited review does not certify all silicon/lot errata.

## Explicit experimental contract

B64 adds one caller-supplied readback assumption, experimental_mcr_bit6 = null (strict default), 0 or 1. This is a constant fixture for bit6 on both HCAN channels, not a verified physical value or an inference from the ROM. Unknown command/register state remains unknown even with this bit supplied. The firmware image is not changed and no instructions/accesses are skipped.

Readback choices combine independently with existing H-UDI and artificial Pphi-per-completed-instruction settings. NMI/reset/step budget must be recorded. A supplied bit always marks the report conditional, even if execution stops before reading MCR. Reduced exports and baselines must carry the assumption, reject conflicting/missing execution provenance, and exclude it from strict reference classification.

B65 will implement only the next documented command reached by the zero branch. A software-reset request may be recorded, but processing/completion, GSR/IRR acknowledgement, mailbox RAM content and bus synchronization must not be invented. Unsupported register accesses remain stops. Both zero and one branches are tested, not just whichever advances farther.

## Development priorities without a matching ECU

1. Use provenance and the declared scenario matrix to reproduce the next software dependency.
2. Scope one register/instruction at that dependency, implement documented behavior with synthetic and original-hash regressions.
3. Keep physical-board verification, oscillator/pins, CAN traffic, NC waveforms and engine validation as open workstreams; they are not prerequisites for all software work.
4. Keep strict reference188 and existing conditional592 as separate baselines. An experimental increase is conditional execution, not resolved board evidence or full boot.

No new hardware measurements were available. Repeating the earlier audits alone cannot close these parent gates.
