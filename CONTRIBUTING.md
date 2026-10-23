# Contributing to the MX-5 NC ECU Emulator

**One virtual NC ECU, any valid NC engine-ECU ROM.** Do not hard-code
calibration IDs or modify ROMs simply to pass emulator tests.

Contributions we need most:
- Evidence-backed NC hardware register, CPU and board documentation.
- Tested SH7058 / SH-2E instruction coverage and reset/exception semantics.
- Carefully specified ECU peripheral, interrupt and sensor models.
- Repeatable reset/boot/idle/RPM/deceleration fixtures and traces.

ROM comparison, map editing, ROM patching and flashing belong in NCFlash or
other specialist tools, not this emulator.

Only contribute legally reusable code and synthetic fixtures. Do not commit
OEM ROMs, vendor definitions, VINs, security keys or proprietary calibration
data. A simulation passing does not certify a ROM for use on a real vehicle.
