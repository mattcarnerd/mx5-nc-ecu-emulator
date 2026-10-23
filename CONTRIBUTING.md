# Contributing to the MX-5 NC ECU emulator

Our goal is to run **any valid Mazda MX-5 NC engine ECU ROM** against a virtual
NC ECU, irrespective of calibration ID. This is *not* a general-purpose
multi-brand ECU emulation project.

Priority contributions: verified NC ECU hardware/CPU research (NC1/NC2/NC3),
ROM-format identification, SH7058/SH-2E instruction tests, peripheral/interrupt
models, synthetic and legally reusable test vectors, deterministic engine
scenario fixtures, bug reports and regression harnesses.

Keep ECU hardware profiles independent of individual calibration IDs.
Do **not** implement separate ignition, fuel, throttle or DFCO logic for
different ROMs: the goal is to run the actual firmware instructions.

Please do not commit copyrighted ECU firmware, proprietary definitions,
VINs or security access keys. Record a ROM hash and hardware details instead
of uploading ROM contents. No flashing capability belongs in this project.

Passing the emulator's tests does not establish roadworthiness or flashing safety.
