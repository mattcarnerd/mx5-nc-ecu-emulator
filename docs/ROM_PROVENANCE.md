# LF9VEB provenance audit (B62/#69)

Reviewed 24 October 2026. The user has a downloaded image, no matching physical ECU. User reports ROMDrop as its source; exact original download URL/revision is not available. This report identifies a public byte-identity match, not the complete acquisition chain or OEM authenticity.

## Reproducible identity

- Local full image: 1,048,576 bytes, SHA-256 `bfd0965a0f51f60a951d8cd3ef8fe77e5a37fbc326ddb723edf0ede4b1640fbf`.
- Git blob SHA-1 computed locally as SHA1(`blob <decimal-size>\0` + image): `313db489e9485659848e807d735969dc4778d0f7`.
- The pinned [NC Flash tree](https://github.com/cdufresne81/nc-flash/tree/a6d3c8027eb7e4ca882930fbc74e184891dcd376) records exactly this blob and size at examples/lf9veb.bin. No second binary was downloaded or added to this repository. This is a Git blob identity match, not an independently downloaded SHA-256 comparison.
- The pinned [ROMDrop tree](https://github.com/speepsio/romdrop/tree/647f409bf2c27e3576696bbfec412a23b191705e) contains metadata/lf9veb.xml and patches/lf9veb.patch, not a stock LF9VEB .bin at that revision. Patch presence does not prove the tested image was patched. Public availability does not establish licensing of OEM firmware.

## Metadata facts and limits

The [ROMDrop definition](https://github.com/speepsio/romdrop/blob/647f409bf2c27e3576696bbfec412a23b191705e/metadata/lf9veb.xml) declares calibration LF9VEB, identification address B8046, Mazda MX5 and memory model SH7058. Market/year/transmission fields are empty. This is a tool definition, not a physical MCU marking or board inspection.

The [NC Flash definition notice](https://github.com/cdufresne81/nc-flash/blob/a6d3c8027eb7e4ca882930fbc74e184891dcd376/examples/metadata/NOTICE.md) identifies ROMDrop as the origin of most definitions but specifically describes its LF9VEB definition as an extended derivative maintained separately. A metadata attribution is not a provenance statement for the binary itself.

## Result

Confirmed: local content identity matches the pinned NC Flash example blob; ROMDrop declares an SH7058 calibration model. Unresolved: original download chain, stock/OEM authenticity, board identity, exact silicon suffix/revision, oscillator, TRST history, external bus state and pin mapping. Retain unknown hardware-profile status. Neither repository settles the H-UDI or MCR reserved-bit question. Do not infer NC generation/engine/gearbox/market from the filename.

Next: B63 reconciles these limits with primary register documentation, then B64 introduces explicitly hypothetical readback branches. Physical validation is an open workstream, not a prerequisite for every software experiment.

## B123: additional full images from ROMDrop issue attachments (26 October2026)

The current ROMDrop master tree647f409bf2c27e3576696bbfec412a23b191705e has definitions and patch files, with no tracked full .bin/.hex images. Its README requires a separately supplied factory ROM for patching. However, public issue attachments do contain full uploaded images. Following the user request, two were downloaded locally and tested; no OEM bytes are committed here.

| Image | Public source | Archive SHA256 | Extracted1MiB image SHA256 | Target evidence |
|---|---|---|---|---|
| LFNPEA | [issue22](https://github.com/speepsio/romdrop/issues/22), [ZIP](https://github.com/speepsio/romdrop/files/11834016/SW-LFNPEA.zip) | 4d4afe35660e470757678d7ec2e155e941bd0835a7cfbfc2efc6e168ee4a67e9 | 590111ace660ef6257572dd1ec45948558a7741f3c6aa505fa432a698d1f15f7 | Uploader describes NC3 25th anniversary stock read; internal identifier SW-LFNPEA000.HEX |
| LF4XEC | [issue17](https://github.com/speepsio/romdrop/issues/17), [ZIP](https://github.com/speepsio/romdrop/files/8500563/SW-LF4XEC.zip) | 092cfc609acd08a1218fdd66cfa4146ac2f61614f649688895d9d35f289c3ffe | ca9ecd4bf0556dc66712341d303c171c220be104060e61bc4cbe32f4b4f1adcf | LF4XEC definition request; internal identifier SW-LF4XEC000.HEX; exact vehicle not independently established |

Both are distinct from LF9VEB and have different first0x2000 bytes. Uploader statements and internal identifiers are provenance evidence, not physical board/MCU-revision or OEM-authenticity verification. The unchanged LF9VEB strict reference is kept separate.

LFNPEA strict188/187 and explicit reset-completion1057/1056 reproduce the same H-UDI and MBC0112308 gates. With all timer/priorRAM/pin/ordered-stop hypotheses retained, it stops58714/58713 at mailbox store FFFFD104, PCAE88, zero CPU IRQs. LF4XEC strict151/150 stops at running watchdog enable without a supplied clock; H-UDI/phi1 stops172/171 on MCR bit6; explicit bit6/reset/bus fixture stops278/277 on MBC0110308, PCCBC. Its recorder/priorRAM/pin exploration stops14044/14043 on unknown T at PC3B0 before timer binding; zero IRQs. The later branch is only experimental and does not resolve the earlier prohibited command.

Actual checksum-verified Windows EXE v0.2.0-dev.190.1 reproduces strict and latest experimental cases for both new images. See [LFNPEA matrix](evidence/b123-lfnpea-comparison.json), [LF4XEC matrix](evidence/b123-lf4xec-comparison.json), [packaged verification](evidence/b123-packaged-comparison.json). This retrieves the requested alternate images but does not establish sustained firmware initialization or recurring original-firmware interrupts.
