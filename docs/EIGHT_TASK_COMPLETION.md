# Eight requested bounded tasks

## B13/#16

Implement SH-2E FPU reset state and system register transfers (B13)
Software manual2.6/4.2/7.3.16-17: FR/FPUL unknown, FPSCR reset40001; writable18C60, fixed DN/RM retained. LDS/STS direct and stack forms commit base changes only after successful access. No SH-4 banks or precision mode invented.

Validation: Ran 294 tests in 2.298s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b13-no-clock-unknown.json and b13-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. B13 enables B14, which enables B15. Timer/ADC/input/output tasks retain dependencies. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User explicitly requested these eight bounded features; synthetic coverage is distinguished from observed firmware use.

## B14/#17

Implement raw FPU transfers and bounded conversion instructions (B14)
FMOV raw32 register/direct/indexed/predecrement/postincrement forms preserve every bit including NaNs; FLDI0/1, FLDS/FSTS, FLOAT/FTRC added. Integer conversion uses exact rational binary32 truncation, fixed SH-2E DN flushing; unsupported NaN/infinity/out-of-range/enabled exception modes fail before destination update. Stack addressing changes only on successful access.

Validation: Ran 297 tests in 2.517s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b14-no-clock-unknown.json and b14-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. B14 enables B15 arithmetic; timer and ADC remain next independent scopes. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User explicitly requested these eight bounded features; synthetic coverage is distinguished from observed firmware use.

## B15/#18

Implement bounded SH-2E floating arithmetic (B15)
FADD/FSUB/FMUL/FDIV use exact rational intermediates and binary32 truncation without host-double rounding. Signed zero and fixed DN flush supported; cause V/Z cleared on successful finite operation, sticky flags retained. NaN/infinity/divide-zero/overflow and enabled exceptions explicitly stop atomically rather than invent FPU exceptions.

Validation: Ran 299 tests in 2.488s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b15-no-clock-unknown.json and b15-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. Three requested FPU subsets implemented; full FPU remains outside scope. B22 timer precedes B24 waveform; B23 ADC precedes B28 UI. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User explicitly requested these eight bounded features; synthetic coverage is distinguished from observed firmware use.

## B22/#29

Implement bounded ATU-II channel1A counter/capture/compare path (B22)
Rev.3 table11.3/11.2.1/4/5/6: TCNT1A/GR1A, byte TSTR1/TIOR1A/TCR1A and word TSR1A/TIER1A. Explicit selected-counter-clock packets,16-bit wrap, GR1A edge/compare, read1/write0 flag clear and module interrupt request events. Other channels/modes rejected. No oscillator/prescaler ratio, CPU interrupt vector or physical output invented; CPU dispatch of this additional source remains future parent scope.

Validation: Ran 302 tests in 2.603s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b22-no-clock-unknown.json and b22-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. B22 enables B24 synthetic waveform capture. ADC B23 enables B28 sensor UI. No new issue needed for completed bounded source-level interrupt event scope. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User explicitly requested these eight bounded features; synthetic coverage is distinguished from observed firmware use.

## B23/#30

Implement one AN0 ADC conversion fixture (B23)
Rev.3 section17: ADDR0 left-aligned10-bit, ADCSR0 ADF/ADIE single AN0 and ADCR0 software ADST, known power reset versus unknown manual state. Explicit voltage/reference required, no assumed5V; ideal transfer floor1024 ratio/clamp1023 is fixture quantization, not measured analog accuracy. Explicit completion event and start-time sample policy, no physical latency guessed. Read1/write0 ADF, cancellation token and module interrupt request tested. Other ADC modes rejected.

Validation: Ran 305 tests in 2.400s

OK

Default300/no-clock H-UDI and explicitly labelled conditional10000 scenarios rerun; see evidence/b23-no-clock-unknown.json and b23-clock1-budget10000-trst-reset.json. Counts do not imply boot.

Mandatory full backlog review: all open issue bodies refreshed/compared and all backlog rows reviewed. B23 enables B28 explicit sensor controls and synthetic firmware-read proof. B24 depends on existing B22 capture path; B25 can label only raw GPIO pending board mapping. Physical H-UDI/CAN evidence gates in#1 and broad parents#2/#3 remain open. No duplicate task added; no physical inputs or timing guessed. User explicitly requested these eight bounded features; synthetic coverage is distinguished from observed firmware use.
