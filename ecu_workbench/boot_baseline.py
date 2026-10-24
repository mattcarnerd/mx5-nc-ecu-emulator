"""Deterministic, read-only NC reset-execution snapshots.

The reports contain hashes and a short trace, never ROM bytes. A reset trace
is not evidence that an ECU boots or operates.
"""
from __future__ import annotations

from .core import ROMImage
from .nc_boot import diagnose_nc_reset
from .hudi import scenario_metadata

BASELINE_SCHEMA_VERSION = 1
TRACE_TAIL_LENGTH = 16


def capture_boot_baseline(
    rom: ROMImage, *, reset: str = "power", max_steps: int = 300,
    nmi_high: bool | None = None, hudi_scenario: str = "unknown",
    port_b_pin_values: int | None = None, port_b_pin_known_mask: int = 0xFFFF,
    port_c_pin_values: int | None = None, port_c_pin_known_mask: int = 0x001F,
    port_d_pin_values: int | None = None, port_d_pin_known_mask: int = 0xFFFF,
) -> dict:
    """Return a stable JSON-serialisable record of a bounded startup attempt.

    No wall-clock times, file paths, random values or host-specific identifiers
    are stored. Missing ECU hardware is reported, not silently emulated.
    """
    if reset not in ("power", "manual"):
        raise ValueError("reset must be 'power' or 'manual'")
    if type(nmi_high) not in (bool, type(None)):
        raise ValueError("nmi_high must be True, False or None")
    if not isinstance(max_steps, int) or not 1 <= max_steps <= 100000:
        raise ValueError("max_steps must be between 1 and 100000")

    run = diagnose_nc_reset(
        rom, reset=reset, max_steps=max_steps, nmi_high=nmi_high, hudi_scenario=hudi_scenario,
        port_b_pin_values=port_b_pin_values, port_b_pin_known_mask=port_b_pin_known_mask,
        port_c_pin_values=port_c_pin_values, port_c_pin_known_mask=port_c_pin_known_mask,
        port_d_pin_values=port_d_pin_values, port_d_pin_known_mask=port_d_pin_known_mask,
    )
    trace = run.get("trace", [])
    stop = run.get("stop", {})
    unsupported = None
    if stop.get("reason") == "unmodelled_peripheral":
        last_instruction = trace[-1] if trace else {}
        unsupported = {
            "address": stop.get("address"),
            "access": stop.get("access"),
            "width": stop.get("width"),
            "value": stop.get("value"),
            "instruction_pc": last_instruction.get("pc"),
            "opcode": last_instruction.get("opcode"),
        }

    input_settings = {"reset": reset,
                      "nmi": "unknown" if nmi_high is None else ("high" if nmi_high else "low"),
                      "max_steps": max_steps, "hudi_scenario": hudi_scenario}
    if port_b_pin_values is not None:
        input_settings["port_b_pin_values"] = f"0x{port_b_pin_values:04X}"
        input_settings["port_b_pin_known_mask"] = f"0x{port_b_pin_known_mask:04X}"

    if port_c_pin_values is not None:
        input_settings["port_c_pin_values"] = f"0x{port_c_pin_values:04X}"
        input_settings["port_c_pin_known_mask"] = f"0x{port_c_pin_known_mask:04X}"

    if port_d_pin_values is not None:
        input_settings["port_d_pin_values"] = f"0x{port_d_pin_values:04X}"
        input_settings["port_d_pin_known_mask"] = f"0x{port_d_pin_known_mask:04X}"

    return {
        "schema_version": BASELINE_SCHEMA_VERSION,
        "kind": "nc_sh7058_reset_baseline",
        "rom": {
            "sha256": rom.sha256,
            "size_bytes": rom.size,
        },
        "inputs": input_settings,
        **scenario_metadata(hudi_scenario),
        "result": {
            "reset_vectors": run.get("vectors"),
            "initial_sp": run.get("initial_sp"),
            "executed_instructions": run.get("executed_instructions", 0),
            "completed_instructions": run.get("completed_instructions", 0),
            "virtual_time": run.get("virtual_time"),
            "explicit_interrupt_requests": run.get("explicit_interrupt_requests",0),
            "scheduled_interrupt_events": run.get("scheduled_interrupt_events",0),
            "execution_coverage": run.get("execution_coverage"),
            "pc_at_stop": run.get("pc_at_stop"),
            "last_fetched_pc": run.get("last_fetched_pc"),
            "stop": stop,
            "next_dependency": run.get("next_dependency"),
            "first_unsupported_peripheral": unsupported,
            "trace_tail": trace[-TRACE_TAIL_LENGTH:],
            "boot_complete": False,
        },
        "warning": (
            "A reset trace is not a successfully booted ECU. "
            "Unknown CPU/peripheral behaviour is never assumed valid."
        ),
    }
