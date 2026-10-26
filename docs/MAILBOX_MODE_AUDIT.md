# Prohibited mailbox control audit (B82/#89)

## Result

The autonomous milestone is **not achieved**. The declared original-hash experiment stops1057 attempts/1056 completed at PC00000E70/op81C2, a word2308 store to FFFFD104 (mailbox0 control). MBC bits10:8 are011, not documented as an operating mode. No recurring original-firmware interrupts were observed.

## Primary evidence

- [SH7058 Rev.3 manual](https://www.renesas.com/en/document/mah/sh-2e-sh7058-f-ztat-tm-hardware-manual), section16.3.2/table16.3, printed533/535: mailbox0 is receive-only, supported active mode010, and011/110 are prohibited.
- [SH7058S/SH7059 Rev.5 manual](https://www.renesas.com/en/document/mah/sh-2e-sh7059-f-ztattm-sh7058s-f-ztattm-hardware-manual), section17.3.2/table17.3, printed430/432: the same prohibition remains. Merely substituting a related chip name does not justify the command.
- [Renesas TN-SH7-A534A/J](https://www.renesas.com/ja/document/tcu/sh7058f-hcan-ii),12 October2004, page2 section1(6)(B): explicitly prohibits MBC011. This source is stronger than an inference from a missing implementation. This bounded review does not certify every silicon/lot update.
- [Pinned image provenance](ROM_PROVENANCE.md): SHA-256 bfd0965a0f51f60a951d8cd3ef8fe77e5a37fbc326ddb723edf0ede4b1640fbf matches the local original image and a public NC Flash Git blob. ROMDrop metadata declares an SH7058 tool model, not an exact physical suffix/revision or proof of OEM authenticity.

## CPU/argument audit

A local step-by-step audit confirms that the caller supplies literal mode3 in R5 before entering the mailbox helper. At the control construction, EXTU.B supplies3, SHLL8 produces0300, low-byte DLC contributes8, and a2000 constant contributes NMC:

    3 * 256 + 8 + 0x2000 = 0x2308

A generated instruction sequence in test_mailbox_mode_audit.py independently constructs this value from those numeric arguments and stops before the same prohibited write. No private instruction stream or binary is copied into the test. Existing independent extension/shift/ADD/MOV tests cover the constituent operations. This establishes the local calculation, not a full independent CPU trace comparison.

The control value decodes NMC1/MBC011/DLC8, without unsupported CCM/TTE/DART/TCT/CBE/CLE bits. Endian selection for CAN message data does not justify remapping control bits. The identified command is not a frame, reception event, successful mailbox configuration or proof the original ECU firmware is faulty.

## Reproducer and sensitivity

Declare power reset/NMI high, assumed H-UDI TRST-reset or transfer-complete, artificial phi1, explicit MCR bit6=0, synthetic reset-completion delay1 and synthetic11-recessive-bit event delay64 or256, budget100000. Both H-UDI choices and both longer delays reach the same2308 store. A short delay1 ends the configuration window too early and is rejected earlier at BCR1; it is retained as a negative scenario, not tuned away as if measured timing.

[Reduced matrix](evidence/b82-startup-matrix.json) contains19 no-completion cases and6 explicit completion cases with every assumption and attempted/completed counts. Strict reference stays188; original conditional bit6-unknown stays592; bit6=0 without completion now stops976 at an unknown-status branch. None establishes physical inputs, oscillator, CAN operation or full boot.

## Missing evidence and decision

No reviewed applicable source establishes hardware behavior for011. Continuing a faithful initialization model beyond this command requires one of:
- an applicable MCU-specific primary document/erratum or reproducible register/hardware trace explaining this command;
- independent evidence of an emulator instruction/profile error explaining why the calculated command differs from matching hardware;
- a different authorized ROM with sufficient target-profile provenance for a separate compatibility scenario.

An exact original download URL/revision may help provenance but alone cannot define undocumented mode behavior. A ROM filename, synthetic reset completion, related chip manual or longer trace is insufficient. No physical ECU purchase is prescribed. Public documentation or an independently reproducible reference can supply the evidence.

Do not silently convert011 to010, patch the image, ignore the write, declare the mailbox inactive, invent CAN acknowledgement or choose undefined readback. Raw command recording with ignored effects would be a different experiment and cannot satisfy this faithful-initialization milestone. Hardware parents#1/#2/#3 retain this gate. B82 completion is the bounded audit/reproducer, not resolution of the gate.

## B121/B122 later exploration audit

A separate optional experiment can record prohibited commands while leaving their hardware effects unknown. Even after explicit timer/RAM/pin/watchdog hypotheses, symbolic mailbox read-mask-store stops at PCC084/op2421, FFFFD104 after58713/58711 completed instructions. Known written mask F8F0/value2000 leaves unknown mask070F: exactly MBC[2:0] and DLC[3:0]. Reserved fields were eliminated by CPU masking. This is a later manifestation of the same evidence gap, not a new reset value to guess. No original-firmware IRQs were observed.

The downloaded v0.2.0-dev.189.1 Windows EXE was checksum-verified before execution and reproduces both strict188/187 and experimental58714/58713 counts. All assumptions stay attached. Generated recurring interrupt tests validate implemented mechanics only. Public source identity is already established; asking the user for CAN terminology or a physical ECU is unnecessary. A download link alone would not resolve mode011 behavior. The missing evidence is still applicable primary behavior/trace, an independent CPU/profile correction, or a separate authorized target-identified ROM.

## B123: independent public image comparison

The user requested another ROM from ROMDrop. Full LFNPEA and LF4XEC issue attachments were downloaded and identified locally; see ROM_PROVENANCE.md. Both hit MBC011 under explicit completion assumptions: LFNPEA word2308 at PCE70, LF4XEC word0308 at PCCBC. LFNPEA reproduces the later symbolic MBC/DLC store under the fully labelled timer experiment; LF4XEC reaches an unknown-T branch in its recorder-only exploration. Zero CPU IRQs in every supplied matrix case. Different images do not automatically resolve undocumented behavior, and no image is patched or substituted for the LF9VEB reference. The comparison strengthens the need for applicable behavior evidence or an independent CPU/profile correction. No full-image bytes are published.

## B124 independent semantic check

[Ghidra SLEIGH/pypcode audit](INDEPENDENT_SH2_AUDIT.md) now independently decodes and evaluates the three reached nine-instruction windows and matches864 generated vectors. Every window store and final R0 agree, including final2308/0308 to FFFFD104. This narrows the checked arithmetic/addressing issue but is not an independent full-reset trace: entry registers come from our emulator. SH7058S Rev5 uses the same control address/MBC bits and prohibition. Exact silicon remains unverified; no hardware behavior exception or mode conversion is inferred. The gate remains unresolved.

## B125 independent caller provenance

SLEIGH confirms an unconditional full-register literal3 assignment at caller PC1E2 (LF9VEB/LFNPEA) or21A (LF4XEC), requiring no incoming R5 value. Across57/57/54 observed instruction events to the low-byte consumer, no later R5 writer exists, including lifted branch delay slots. Stale incoming R5 is therefore ruled out on those paths. Branch/path selection still comes from our emulator and has not been independently executed from reset; controller011 behavior remains unknown. See the extended INDEPENDENT_SH2_AUDIT.md and reduced B125 report.

## B126 caller branch/target execution

The SLEIGH/symbolic evaluator now independently selects the same57/57/54 caller-path instruction events, including two conditional decisions and one call target per image, without forcing observed outcomes. Unknown entry bits and initial mailbox masks remain symbolic; ambiguous branches stop. Entry state before the caller still comes from our emulator. This excludes the checked caller-segment branch/target semantics as the observed discrepancy under that entry state, not earlier reset/profile mistakes or physical CAN behavior. See INDEPENDENT_SH2_AUDIT.md and evidence/b126-symbolic-caller-paths.json.

## B127 independent CPU execution from reset

SLEIGH plus symbolic state now independently selects all1057/1057/278 attempted instruction events from power-reset vectors under explicitly emulator-generated peripheral input transcripts. It validates407/407/77 I/O requests and outputs; undefined registers/RAM remain symbolic, and no observed branch outcome is forced. The same2308/2308/0308 attempted control writes result. This finds no earlier CPU-path discrepancy under those inputs. It does not establish physical input/profile correctness or defined011 behavior, and does not complete the terminal write or firmware initialization. See the extended INDEPENDENT_SH2_AUDIT.md and evidence/b127-independent-reset-replay.json.
