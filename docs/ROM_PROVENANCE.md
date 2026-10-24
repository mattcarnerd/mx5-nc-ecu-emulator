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
