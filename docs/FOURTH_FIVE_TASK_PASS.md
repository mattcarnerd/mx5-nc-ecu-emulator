# Fourth five-task pass

## B47/#54 inactive HCAN mailbox command

Rev.3 section16.3.2/table16.3 marks MBC111 inactive, including mailbox0 (unlike active transmit modes forbidden for mailbox0). Accept only word0700/2700 at control offset4; no receive/transmit behavior is inferred. Other nonzero settings remain unsupported. NMC is recorded as a command, not a received-message event. All64 mailboxes/channels and unsupported modes tested; 278 tests pass.

Default stays188; no-clock H-UDI assumptions225. Explicit H-UDI+phi1 reaches300 instruction limit. Separate budget10000 reaches590, PC7B2/op6031 reading MCR0 FFFFD000 with unspecified reserved bit6. See evidence b47-clock1-budget10000-trst-reset.json. Budget/clock/H-UDI assumptions remain explicit and exclude reference classification. No full boot or physical timing claim.

Full backlog review: all12 open issue bodies and all rows checked. No duplicate for partial known-bit machinery; add B48/#55 as CPU dependency for this reserved-bit read. Parents1-3/FPU16-18/timer29/ADC30/crank31/output32/UI35 retain scopes and dependencies; actual board state remains unresolved. Existing CPU parent is narrowed by this child rather than replaced. Private ROM stays local.
