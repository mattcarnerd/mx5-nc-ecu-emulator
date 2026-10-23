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

## Task completion and backlog review

For each GitHub issue completed in a development pass:

- Implement the bounded functionality and unit tests; retain optional local-ROM regression tests.
- Rerun the current real-ROM reset trace where locally available, and inspect the precise new instruction/hardware blocker.
- **Review the complete open backlog every single time**: change priority/dependencies, narrow or split an issue, add new tickets for actual gaps, and avoid duplicate issues. Note explicitly when no changes are justified.
- Record the review decision in [BACKLOG.md](BACKLOG.md), keeping that file's order aligned with GitHub issue titles and priorities.
- Verify that automated tests passed and a new Windows EXE was published under [Releases](https://github.com/mattcarnerd/mx5-nc-ecu-emulator/releases).
- Link commit, CI, release and the backlog review outcome in the issue **before marking it complete**.

This review happens in the same development pass as each finished task; it
must not rely on the user asking for a separate review. See the
[mandatory post-task process and decision log](BACKLOG.md).
