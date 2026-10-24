# Fourth five-task pass

## B47/#54 inactive HCAN mailbox command

Rev.3 section16.3.2/table16.3 marks MBC111 inactive, including mailbox0 (unlike active transmit modes forbidden for mailbox0). Accept only word0700/2700 at control offset4; no receive/transmit behavior is inferred. Other nonzero settings remain unsupported. NMC is recorded as a command, not a received-message event. All64 mailboxes/channels and unsupported modes tested; 278 tests pass.

Default stays188; no-clock H-UDI assumptions225. Explicit H-UDI+phi1 reaches300 instruction limit. Separate budget10000 reaches590, PC7B2/op6031 reading MCR0 FFFFD000 with unspecified reserved bit6. See evidence b47-clock1-budget10000-trst-reset.json. Budget/clock/H-UDI assumptions remain explicit and exclude reference classification. No full boot or physical timing claim.

Full backlog review: all12 open issue bodies and all rows checked. No duplicate for partial known-bit machinery; add B48/#55 as CPU dependency for this reserved-bit read. Parents1-3/FPU16-18/timer29/ADC30/crank31/output32/UI35 retain scopes and dependencies; actual board state remains unresolved. Existing CPU parent is narrowed by this child rather than replaced. Private ROM stays local.

## B48/#55 independent known-bit value primitive

Immutable32-bit values retain a known mask and canonicalize unknown storage bits without choosing a concrete value. Concretization fails unless every bit is known. Word sign extension, AND/OR/XOR and three-valued zero proof are independently tested, including exhaustive two-bit truth tables against all concrete completions and mask precision. No CPU behavior changes yet;281 tests pass. Same reduced default/no-clock and conditional10000 scenarios remain188/225/590.

Full backlog review: all current open bodies compared with B47 review; only new B48 child added, others unchanged. Add B49/#56 for the observed MOV.W MCR partial read; generic primitive is a tested dependency, not firmware progress. Parents1-3/FPU16-18/timer29/ADC30/crank31/output32/UI35 retain scopes/dependencies. No duplicate partial-load task exists. Evidence b48-no-clock-unknown.json and b48-clock1-budget10000-trst-reset.json.

## B49/#56 partial MCR MOV.W load

CPU MOV.W @Rm,Rn can preserve known MCR bits with bit6 unknown, sign-extended correctly. Both channel command latches use maskFFBF; manual unknown prior state still fails. Concrete bus readers still fail instead of selecting bit6. Other CPU consumers reject partial registers until specifically supported; immediate overwrites restore exact values. 284 tests pass, default188/no-clock assumptions225 unchanged. Conditional10000 reaches591, OR #1,R0 at PC7B4/opCB01, preserving rather than choosing unknown readback. Evidence b49-clock1-budget10000-trst-reset.json.

Full backlog review: all open bodies refreshed/compared, all rows reviewed. Only child scope/closure evidence changed; no duplicate logical partial-value task. Add B50/#57 for observed OR and generic existing logical forms/copies. Parents1-3/FPU16-18/timer29/ADC30/crank31/output32/UI35 keep dependencies. No hardware state/full boot inferred.

## B50/#57 logical partial values

Existing register/immediate AND/OR/XOR/TST and register MOV now retain known masks. AND zero or OR one can prove bits; XOR of the same register is exact zero. TST produces an unknown T when zero cannot be proved either way, and branch consumers still stop. Other SR flags remain unchanged. Unknown reset-register None still fails. 287 tests pass, including exhaustive value primitive checks, aliasing, masking, copies and uncertain branches.

Default188/no-clock225 unchanged. Conditional10000 reaches592, PC7B6/op2301 MOV.W R0,@R3. The unknown reserved bit6 is still present after OR1; it must not be silently written as zero. Full backlog review of refreshed bodies/rows adds B51/#58 for width-aware direct stores and precise blocked-write evidence. Other issue scopes/dependencies unchanged; do not create speculative CAN behavior. Evidence b50-clock1-budget10000-trst-reset.json.

## B51/#58 width-aware direct stores and explicit hardware blocker

Direct MOV.B/W/L stores validate only the low8/16/32 bits that actually reach the bus. Unknown truncated high bits no longer block a provably exact byte/word. Unknown written bits stop before side effects, report actual address/width/access and the unknown mask, omit an invented concrete value, and count the failed access in coverage. Partial MCR read failures also retain coverage. Other load/store forms remain conservatively strict. 291 local tests pass, including private hash-checked regression, all direct store widths, RAM no-mutation, reserved-bit RMW guard and explicit firmware masking. Public CI skips only private-ROM-dependent tests.

Default300 remains188 on SDSR. Assumed H-UDI with no clock remains225 at TCSR. Explicit H-UDI+phi1/budget300 reaches the instruction limit, not boot. Separate budget10000 reaches592 attempts/591 completed at PC7B6/op2301 attempting MCR0 FFFFD000 word write. Known lower bits value0001/maskFFBF, unknown bit6. The manual requires writing reserved bit6 zero, but its read value is not guaranteed; the firmware's OR1 does not resolve it. No concrete write/reset side effect is claimed. Evidence [default](evidence/b51-no-clock-unknown.json), [conditional300](evidence/b51-clock1-trst-reset.json), [conditional10000](evidence/b51-clock1-budget10000-trst-reset.json).

Mandatory full backlog review: all14 open issue bodies refreshed/compared and every backlog row reviewed; no duplicate/new speculative hardware task added. Existing hardware research#1 now records the exact MCU revision/errata/readback evidence gate. CPU#2 and peripherals#3 remain incomplete; FPU16-18/timer29/ADC30/crank31/output32/UI35 keep scopes/dependencies. Next work must resolve the MCR evidence gate or deliberately select another existing bounded workstream. Do not silently choose reserved readback, simulated bus status or physical clock values. All five B47-B51 require per-issue commit/CI/release evidence before closure. No private ROM bytes/paths/full traces published. No full boot claimed.

Sources: [Renesas SH7058 Rev.3 hardware manual](https://www.renesas.com/en/document/mah/sh-2e-sh7058-f-ztat-tm-hardware-manual), sections16.3.2 and16.4.2; [SH-2E software manual](https://www.renesas.com/en/document/mas/sh-2e-software-manual), MOV/logical/TST instructions.
