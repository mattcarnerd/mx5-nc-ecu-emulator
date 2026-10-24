# Unknown stack transport and CAN status pass

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

## B69/#76

B69: preserve partial operands across supported direct/indexed/displacement MOV memory transfers.

Validation: Ran 353 tests in 3.946s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b69-no-clock-unknown.json and b69-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. Supported integer MOV memory paths and register copies now transport masks consistently; unknown addresses and peripheral values still stop. Expected experimental dependency remains GSR0 at PCDB2. Other CPU/floating-point consumers remain concrete-only. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five ROM-only tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## B70/#77

B70: model GSR power-on flag subset and preserve uncertain reset/bus status.

Validation: Ran 356 tests in 3.990s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b70-no-clock-unknown.json and b70-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 356 tests pass. GSR low6 reset bits are0x0C; reserved15:6 readback is not guaranteed. After software reset/release requests dynamic flags remain unknown. Zero-readback experiment reaches974 attempts, PCDB4/op633D EXTU.W on partial GSR; no reset completion or CAN state guessed. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five ROM-only tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.

## Instruction and storage contract

Primary sources: [SH-2E software manual](https://www.renesas.com/en/document/mah/sh-2e-software-manual), section7.2.30 (MOV); [SH7058 Rev.3 hardware manual](https://www.renesas.com/en/document/mah/sh-2e-sh7058-f-ztat-tm-hardware-manual), table16.4/section16.4.3, printed549-550 (GSR). Register reset-undefined values are not initialized by the emulator.

B67 attaches one known-bit mask per RAM byte. ram_valid indicates an explicit write, not that every stored bit is known. The backing byte value is meaningful only under its mask. Partial writes invalidate only the relevant written bits; concrete byte/word/long overwrites restore their knowledge. Overlapping reads reconstruct big-endian values and masks. Unwritten reset RAM remains an explicit stop in this bounded implementation.

B68 routes MOV.B/W/L predecrement stores and postincrement loads through typed transfers. A reset-undefined source becomes a fully unknown value for transport, not a selected integer. The address must be concrete. Aliased predecrement stores retain the old pointer value; postincrement loads suppress the increment when source/destination registers match. Byte/word loads sign-extend both value and knowledge: an unknown sign bit leaves extension bits unknown. MOV leaves T unchanged.

B69 applies the same contract to supported direct, indexed and displacement integer MOV forms and register copies. It does not add unimplemented GBR/FPU/system-transfer modes. Arithmetic, extension/shift consumers not yet supporting partial bits, unknown effective addresses, branches and peripheral writes retain their guards. Concrete/raw RAM readers also reject unknown data. This is a conservative independent-bit model, not symbolic execution with cross-register correlations.

## GSR boundary reached by original firmware

B68 exposed a word GSR0 read at FFFFD002, PCDB2/op6351, at973 attempts. B70 adds GSR0/1 at FFFFD002/FFFFD802 with aligned word-only access. GSR is read-only; writes and unsupported widths are rejected.

At power reset low bits5:0 are known with value000C (reset flag bit3 and no-pending-transmission flag bit2 set). Reserved bits15:6 explicitly have no guaranteed readback and are not set to known zero. Manual prior state is unknown. After an accepted reset/release request, this command-only model conservatively invalidates dynamic status knowledge rather than guessing controller processing/completion, errors or bus state. Typed reads carry unknown bits without choosing them; full concrete reads stop. Repeated polling does not complete reset.

No new completion input is introduced in this pass. Full CAN reset processing/GSR/IRR effects, recessive-bit synchronization, mailbox RAM content and traffic remain outside the subset.

## Current reproducible evidence

- [Generated save/restore report](evidence/b71-unknown-stack-fixture.json): generated JSR function pushes reset-undefined R11/R10, replaces them, restores both masks as fully unknown, returns using known PR, restores SP and increments a call counter. No manufacturer firmware used. Source command: python -m ecu_workbench.unknown_stack_fixture.
- Integration regressions reject restored unknown values as an address, branch target, SR value or peripheral write. XOR of a register with itself can independently prove zero.
- [Current19-case matrix](evidence/b71-rom-only-matrix.json) retains all declared B66 scenario choices. Strict reference remains188/187; original H-UDI/artificial-phi1-only remains592/591; explicit bit6=1 still rejects reserved-one0041 at592/591.
- Explicit bit6=0, assumed H-UDI, artificial phi1 and10000 budget now reach974 attempts/973 completed, PC00000DB4/op633D (EXTU.W R3,R3). R3 carries unknown GSR bits; the existing extension instruction requires a concrete register. No unknown value is replaced with zero to pass this stop.
- The next bounded software scope is propagating known masks through EXTU/EXTS and then examining subsequent consumers. Preserving masks alone cannot establish CAN reset completion; that needs a separately justified model or explicit labelled completion fixture.

Run the existing matrix source CLI with --rom YOUR_LOCAL_IMAGE --nmi high --steps 10000 and preserve its assumptions. The Windows diagnostic CLI retains --experimental-mcr-bit6 0/1; no new physical profile or GUI control is claimed. Earlier matrix reports are historical evidence for their implementation revisions. No full ECU boot, measured clock or engine operation is claimed.

## B71/#78

B71: verify unknown-stack call/return and guarded consumers, publish refreshed19-case matrix.

Validation: Ran 359 tests in 4.076s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b71-no-clock-unknown.json and b71-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. 359 tests pass. All open issue bodies and backlog rows reviewed: partial EXTU/EXTS is next concrete software scope; CAN completion, board verification and engine operation stay open. Earlier strict188 and original conditional592 preserved; new experimental974 remains labelled, not full boot. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User requested these five ROM-only tasks; research outcomes do not assert hardware resolution and synthetic coverage is distinct from original firmware operation.
