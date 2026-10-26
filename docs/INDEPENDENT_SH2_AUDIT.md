# Independent SH instruction and HCAN profile audit (B124/#131)

## Result

The checked instruction semantics match. This does not resolve hardware behavior for prohibited MBC011 and does not prove the entire CPU or firmware startup correct. No execution guard or physical default was relaxed.

Pinned external engine: [pypcode4.0.1](https://github.com/angr/pypcode), Python bindings to Ghidra SLEIGH. Language `SuperH:BE:32:SH-2` (the relevant integer subset, not an assertion that every SH-2E/FPU instruction is covered). Compiled language SHA256 e69e099854e5b6c9e8f4d6b2deae1c038f87abfbc99484ca733e84cbdb897390. See [engine usage documentation](https://docs.angr.io/projects/pypcode/en/latest/guide.html).

## What was independently checked

The external decoder identifies the generated EXTU.B, SHLL8, ADD and MOV.W scaled-displacement forms. Its translated semantics are evaluated with a small generic byte-addressed p-code interpreter. Unsupported operations, unsupplied register bytes, partial decoding and loads outside the explicitly supplied ROM fail; there are no zero defaults for missing state. Register alias bytes and stores use big-endian order. This interpreter is an audit tool, not a full reference CPU or CAN controller.

864 generated vectors compare this SLEIGH semantic path with the emulator: all8 mode values, DLC operands0/8/15/255, R3 constants0/2000/FFFFFF00 (including32-bit wrap), three RAM bases and displacements0/2/15. High garbage in source registers tests byte extraction; memory readback tests word width and ordering; T stays unknown/unchanged. The generated programs contain no copied OEM instruction stream.

Actual local ROM windows are independently decoded/lifted from the authorized images, with entry registers captured from the emulator's declared conditional run. Every store in each window and final R0 match:

| Image | Straight-line window | Instructions | Stores compared | Final address / word |
|---|---|---|---|---|
| LF9VEB | E60 through E70 |9|1| FFFFD104 /2308 |
| LFNPEA | E60 through E70 |9|1| FFFFD104 /2308 |
| LF4XEC | CAC through CBC |9|3| FFFFD104 /0308 |

The LF4XEC window includes two earlier identifier stores; these are compared as well, rather than mistakenly treating them as a semantic discrepancy. No private instruction listing, ROM bytes, full trace or local path appears in the [reduced report](evidence/b124-independent-sh2-audit.json).

Important limitation: entry state is supplied by our emulator. This is not an independent reset-to-stop trace and does not independently validate all earlier control flow, caller arguments, reset assumptions, instruction timing or board profile. The selected nine-instruction windows and generated vectors narrow the arithmetic/decoding question; they do not certify the whole CPU.

## Primary hardware comparison

- [SH7058 Rev.3](https://www.renesas.com/en/document/mah/sh-2e-sh7058-f-ztat-tm-hardware-manual),16.3.2/table16.3, printed533/535: MBC occupies bits10:8,011/110 prohibited; mailbox0 is receive-only.
- [SH7058S/SH7059 Rev.5](https://www.renesas.com/en/document/mah/sh-2e-sh7059-f-ztattm-sh7058s-f-ztattm-hardware-manual),17.3.2, printed430 (PDF page526): same MBC bits and prohibition. Register appendix printed868 (PDF page964) places mailbox0 control at FFFFD104/105. A related chip name does not change the checked interpretation.
- [TN-SH7-A534A/J](https://www.renesas.com/ja/document/tcu/sh7058f-hcan-ii),12October2004, printedpage2,1(6)(B), explicitly prohibits011. Its front page identifies HD64F7058/HD64F7058B and all SH7058 lots. This does not identify the actual physical chip used with any supplied ROM.

No reviewed source establishes an applicable alternative register layout or defined011 behavior for these images. Exact physical suffix/revision remains unverified; tool metadata and filenames do not establish it. This bounded review does not certify every variant or silicon erratum. No mode011-to010 mapping, command-shadow readback or fabricated CAN completion was introduced.

## Reproduction and next evidence

Install audit-only dependencies separately from the application:

```text
python -m pip install -r requirements-audit.txt
python tools/audit_sh2_sleigh.py --synthetic --output independent-audit.json
python tools/audit_sh2_sleigh.py --rom PATH_TO_AUTHORIZED_ROM --output local-audit.json
```

The local-ROM command accepts only the three reviewed image hashes/windows. Outputs contain hashes, assumptions, window addresses and derived control stores, not ROM bytes or filesystem paths. Public CI installs the pinned dependency and requires the generated audit before the test suite; the Windows application does not import this dependency.

Next evidence needed: an independent reset/caller trace demonstrating an earlier CPU/profile discrepancy, or applicable controller behavior evidence explaining011. The audit has not selected between those possibilities. Original-firmware sustained initialization and recurring interrupts remain unverified; generated recurring interrupt tests remain a separate result.

## B125/#132 caller argument provenance extension

The earlier nine-instruction replay used entry registers from our emulator. A second check now starts at each actual caller literal: LF9VEB/LFNPEA PC1E2 and LF4XEC PC21A. The external SLEIGH translation is exactly a constant3 copy to the whole R5 register, requiring no prior register seed. It then examines every p-code register destination on the observed path to the R5-byte consumer (E64 or CB4), including writes in branch delay slots. Opaque/unreviewed operations and alternate address spaces reject the proof.

| Image | Caller literal | Consumer | Observed instruction events before consumer | Intervening R5 writers |
|---|---|---|---|---|
| LF9VEB |1E2|E64|57|0|
| LFNPEA |1E2|E64|57|0|
| LF4XEC |21A|CB4|54|0|

Thus stale reset/prior R5 contents cannot explain the mode3 value on these observed paths. This is a seed-free literal/noninterference check, not an independent execution of branch decisions: path addresses still come from the local emulator, and no interrupts occurred during the measured run. It does not establish why the caller path was chosen, certify earlier reset control flow, or define prohibited-mode hardware behavior. No guard/default is relaxed.

Generated cases verify preserved literals, unrelated writes and a branch with a benign delay slot. Negative cases reject a different literal, subsequent R5 write, delay-slot overwrite and opaque operation. Regression coverage also rejects an idempotent R5 rewrite: observing no value change is not substituted for independently inspecting register destinations.

Use `--caller` with the previous audit command. CI requires generated caller checks in addition to the existing864 arithmetic/addressing vectors. The local three-ROM report is [b125-independent-caller-audit.json](evidence/b125-independent-caller-audit.json), containing only hashes, assumptions, boundary PCs, counts and conclusions. No raw instruction stream is published.

## B126/#133 independent caller-path execution

Pinned z3-solver5.3.2.0 now supplies symbolic bitvectors for unsupplied register/RAM bytes and partial entry-state masks. A bounded generic SLEIGH executor calculates arithmetic, comparisons, branches, call targets and branch delay-slot effects. It never asserts the observed branch outcome as a solver constraint. If a branch condition, target or memory address is not uniquely determined, the audit stops rather than selecting a model value. Uninitialised lift temporaries and unsupported operations also stop. [Z3 bitvector semantics](https://github.com/Z3Prover/z3/blob/master/examples/python/tutorial/html/guide-examples.htm) distinguish unsigned comparisons/logical shifts from signed operations.

For each image, independent execution begins at the caller literal with the other entry registers/RAM supplied by our emulator snapshot; R5 is unseeded and assigned by the actual code. Unknown bits remain symbolic. The four mailbox interrupt mask words are symbolic software latches, initially unconstrained; no mask reset value or CAN traffic is invented. Other hardware loads reject; mailbox writes are intents only and do not supply receive data or prohibited-mode behavior.

The independently selected instruction events match57/57/54 for LF9VEB/LFNPEA/LF4XEC. Each includes two conditional decisions and one call target. This extends B125 beyond merely examining a supplied path. Generated positive cases exercise both conditional outcomes and a delayed indirect call whose slot overwrites the source register. Negative cases reject an unresolved symbolic branch, an incorrect observed path and unsupported hardware input. Tests also cover signed/unsigned comparison, zero masking of unknown values and symbolic unwritten RAM.

Reproduce with `--path` in addition to `--synthetic --caller`. CI requires all generated checks. [Reduced three-ROM results](evidence/b126-symbolic-caller-paths.json) retain the entry-snapshot limitation and scenario assumptions. This is independently evaluated caller control flow conditional on that entry snapshot, not an independent reset-to-caller or hardware trace. The earlier reset path and physical011 behavior remain unresolved; no runtime default/guard changed and no initialization milestone is claimed.

## B127/#134 reset-to-CAN CPU replay

The independent SLEIGH/symbolic CPU now starts at the actual power-reset vector, with SP from the second vector word and the documented known SR mask F0. Other register bits and unwritten RAM remain symbolic; no caller snapshot or guessed register/RAM values are supplied. It derives branches, direct/indirect targets, calls and delay-slot effects itself. The full instruction-event list is compared after execution, never used to constrain branch choices.

Peripheral inputs come from an explicitly labelled **emulator-generated I/O transcript**, not hardware. The reference requests must match address, width and access order. Read values keep only the supplied known bits; unknown bits become fresh symbolic input. Output values must independently satisfy the recorded known bits; mismatches or unresolved values reject the audit. RAM/ROM are handled independently, with read-only ROM and symbolic unwritten RAM. The reference stops on the final attempted peripheral store rather than applying an invented controller effect. The full transcript and instruction stream stay local/in memory; only counts and the terminal control access are published.

| Image | Attempted instruction events matched | Conditional decisions | Calls | Peripheral accesses matched | Final attempted word |
|---|---|---|---|---|---|
| LF9VEB |1057|70|12|407|2308 at FFFFD104|
| LFNPEA |1057|70|12|407|2308 at FFFFD104|
| LF4XEC |278|4|8|77|0308 at FFFFD104|

This is stronger CPU-path evidence than B124/B125 entry-window checks: under these explicit peripheral inputs, no earlier CPU path/arithmetic/addressing discrepancy was found from reset to the disputed write. It is still not independent physical peripheral/profile validation, instruction timing validation, successful completion of the prohibited write, sustained initialization or recurring firmware IRQ evidence. The final control-store event is attempted, not completed. The normal emulator's guard remains intact.

Generated programs test both input-driven branch outcomes, terminal writes and rejection of wrong output value, width, input address/order, exhausted input, and unknown branch input. An expected final output cannot force an ambiguous earlier branch: the reference stops when that ambiguity is encountered. CI requires these generated reset replays alongside the earlier audits. Local private-ROM regressions are skipped in public CI.

Use `--reset-replay` with the existing audit command. [Reduced three-image results](evidence/b127-independent-reset-replay.json) contain hashes, assumptions, counts, terminal access and explicit input-source limitations, with no OEM bytes, raw trace, local paths or full peripheral transcript.

The remaining practical gate is applicable controller/profile evidence explaining the prohibited command under actual hardware inputs. These checks provide no justification to convert011 to010, invent reserved-bit readback, patch firmware or claim boot. An independent hardware or applicable primary reference can still reveal that our supplied peripheral/profile assumptions differ from the target.
