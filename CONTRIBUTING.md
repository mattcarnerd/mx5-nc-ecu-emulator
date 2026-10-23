# Contributing to ECU Workbench

The goal is to support **any binary file for inspection**, with optional
processor-specific emulators and verified ECU profiles.

Good contributions include architecture decoders, synthetic test fixtures,
static analysis, RAM/peripheral models, UI improvements and regression tests.
Keep processor-specific assumptions isolated, never hard-code a Mazda
calibration ID into the universal loader.

Please do not commit copyrighted firmware, factory ROMs, proprietary XML
definitions, client vehicle data or firmware dumps. Use synthetic binaries
in unit tests. Passing a simulation does not prove hardware compatibility,
and ECU flashing is not part of this repository.
