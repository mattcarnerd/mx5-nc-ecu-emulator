# Fourth five-task pass

## B47/#54 inactive HCAN mailbox command

Rev.3 section16.3.2/table16.3 marks MBC111 inactive, including mailbox0 (unlike active transmit modes forbidden for mailbox0). Accept only word0700/2700 at control offset4; no receive/transmit behavior is inferred. Other nonzero settings remain unsupported. NMC is recorded as a command, not a received-message event. All64 mailboxes/channels and unsupported modes tested; 278 tests pass.

Default stays188; no-clock H-UDI assumptions225. Explicit H-UDI+phi1 reaches300 instruction limit. Separate budget10000 reaches590, PC7B2/op6031 reading MCR0 FFFFD000 with unspecified reserved bit6. See evidence b47-clock1-budget10000-trst-reset.json. Budget/clock/H-UDI assumptions remain explicit and exclude reference classification. No full boot or physical timing claim.

Full backlog review: all12 open issue bodies and all rows checked. No duplicate for partial known-bit machinery; add B48/#55 as CPU dependency for this reserved-bit read. Parents1-3/FPU16-18/timer29/ADC30/crank31/output32/UI35 retain scopes and dependencies; actual board state remains unresolved. Existing CPU parent is narrowed by this child rather than replaced. Private ROM stays local.

## B48/#55 independent known-bit value primitive

Immutable32-bit values retain a known mask and canonicalize unknown storage bits without choosing a concrete value. Concretization fails unless every bit is known. Word sign extension, AND/OR/XOR and three-valued zero proof are independently tested, including exhaustive two-bit truth tables against all concrete completions and mask precision. No CPU behavior changes yet;281 tests pass. Same reduced default/no-clock and conditional10000 scenarios remain188/225/590.

Full backlog review: all current open bodies compared with B47 review; only new B48 child added, others unchanged. Add B49/#56 for the observed MOV.W MCR partial read; generic primitive is a tested dependency, not firmware progress. Parents1-3/FPU16-18/timer29/ADC30/crank31/output32/UI35 retain scopes/dependencies. No duplicate partial-load task exists. Evidence b48-no-clock-unknown.json and b48-clock1-budget10000-trst-reset.json.
