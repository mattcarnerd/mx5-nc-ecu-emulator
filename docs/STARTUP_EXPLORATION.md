# Startup investigation with explicit hypotheses

This tool explores code after unresolved hardware gates. It does not validate ECU initialization or CAN operation. Strict diagnostic defaults remain unchanged. CAN commands with unsupported/prohibited mailbox modes are recorded without applying their unknown effects. Reset-status isolation preserves only a supplied reset-completion bit. Neither policy establishes correct CAN behavior.

Run from the repository with an authorized local ROM:

```powershell
python -m ecu_workbench.startup_exploration --rom <local-ROM> --prior-ram-word 0 --phi-cycles-per-instruction 16 --port-b-pins 0 --report exploration.json
```

The caller must choose the prior32-bit word at FFFFBFFC and artificial phi cycles per completed instruction. RAM has no assumed power-reset content. Optional Port B pins are hypothetical fixed inputs, not measured signals. NMI high, assumed H-UDI TRST, MCR bit6=0, artificial CAN completion delays1/64 and command-recording/status-isolation policies are explicitly retained in the exploration envelope. Omit Port B pins to retain unknown external levels. No ROM bytes, filename, path or full trace are emitted.

The separate `nc-ecu-startup-exploration-v1` envelope is rejected by the reset-baseline reviewer. Preserve its assumptions when sharing. Its nested reduced diagnostic does not alone describe prior RAM; never detach it. Initialization and recurring-interrupt verification stay false until independently established. Recent-PC frequency is only a bounded recent trace sample, not a proof of a permanent loop.

B93 matrix: prior words0/FFFFFFFF with phi1 complete100000 instructions without a watchdog overflow or IRQ. Phi4/16/64 with unknown Port B reach the external-pin read FFFFF738 at PC4B6 after33032/8552/2432 completed instructions respectively. Phi16 with Port B0 orFFFF reaches a byte write FFFFF708=1 at PCC3C4 after58524 completed instructions, seven watchdog overflows, zero CPU IRQ entries. The timer overflow is polled during this startup path; it is not evidence of recurring interrupts. See evidence/b93-exploration-matrix.json. No variant is a physical hardware profile.

B95 adds optional `--port-c-pins` (PC4..0) and `--port-d-pins` (16-bit physical input fixture), both unknown when omitted. Exact values remain in the outer assumptions. With prior RAM0/phi16/PC0 and paired PB/PD0 orFFFF, both runs reach MOVT R0 opcode0029 at PCC3D2 after58531 completed instructions. These input choices exercise paths; neither is a real ECU profile. See evidence/b95-exploration.json.

The Windows executable exposes the same separate investigation through `MX5-NC-ECU-Emulator.exe --explore-startup` followed by the arguments above. This route emits the exploration envelope, never a reset baseline. CI runs the actual packaged executable against a generated ROM on both ordinary diagnostic and exploration routes and verifies retained assumptions.

## Optional startup timer clock investigation (B117)

Additional arguments explicitly choose an artificial peripheral Pphi ratio and the three ambiguous channel10 initial candidates:

```powershell
python -m ecu_workbench.startup_exploration --rom <local-ROM> --prior-ram-word 0 --phi-cycles-per-instruction 16 --port-b-pins 0 --port-c-pins 0 --port-d-pins 0 --startup-timer-p-phi 16 --channel10-initial-a 1 --channel10-initial-c 1 --channel10-initial-f 1 --experimental-channel10-wrap16 --report timer-exploration.json
```

Omit the timer arguments to retain the earlier simultaneous-start stop. All three candidate values are required when choosing startup timers. Omitting the final experimental-wrap flag retains the default stop on zero reload. The same arguments work after the EXE's `--explore-startup` option. These are declared hypotheses and model policies, not measured clock rates/reset contents or a verified hardware profile.

The peripheral clock binds with zero phase at the first nonzero TSTR1 write, after firmware setup. Scheduled packets run after each completed instruction before the existing watchdog phi packet. This event ordering and old-state-Pphi correction order are retained in the envelope, alongside candidate values, zero-reload policy, binding tick, completed packet count and clock report. Unsupported start modes are validated before clock binding/scheduling. A rejected clock packet leaves all timer counters/events untouched; the CPU instruction that preceded it can already have completed.

The B117 matrix contains four source-ROM runs. With PB/PD0 (orFFFF), candidates1/1/1 and Pphi16, unspecified zero reload stops after58669 (58667) completed instructions before applying any timer packet. The experimental-wrap16 policy applies one packet and then stops on TSTR2 FFFFF400 byteFF at PCBED4,58670 (58668) attempts and58669 (58667) completed. Zero original-firmware IRQs are observed in every case. See evidence/b117-timer-exploration.json. Windows CI executes generated NOP and first-start ROMs through the actual EXE and validates both provenance and lazy binding.
