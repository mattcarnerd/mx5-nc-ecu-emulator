"""Structured, deterministic explanations of bounded ECU reset-execution stops.

The fetched instruction that raised a stop is NOT assumed successful.
Reaching the instruction limit is NOT a missing hardware dependency.
"""
from __future__ import annotations

from typing import Any

TRACE_CONTEXT_LENGTH = 16

_STOP_CATEGORIES = {
    "unsupported_opcode": "unsupported_cpu_instruction",
    "unmodelled_peripheral": "unmodelled_hardware_register",
    "unknown_peripheral_reset_state": "unknown_hardware_state",
    "missing_input": "missing_external_input",
    "uninitialised_ram": "uninitialised_memory",
    "instruction_limit": "instruction_limit_reached",
    "unsupported_image_size": "unsupported_rom_image",
    "invalid_vectors": "invalid_rom_vectors",
    "invalid_reset_vector": "invalid_rom_vectors",
    "rom_write": "invalid_memory_access",
    "unaligned_access": "invalid_memory_access",
    "unmapped_memory": "invalid_memory_access",
    "unsupported_peripheral_mode": "unsupported_hardware_access",
    "unsupported_access_size": "unsupported_hardware_access",
    "read_only_peripheral": "invalid_hardware_access",
    "invalid_peripheral_write": "invalid_hardware_access",
    "illegal_delay_slot": "unsupported_cpu_instruction",
    "unknown_register": "unknown_cpu_state",
    "unknown_status": "unknown_cpu_state",
}


def explain_stop(
    stop: dict[str, Any], *,
    trace: list[dict[str, Any]],
    active_instruction: dict[str, Any] | None = None,
    fetch_pc: int | None = None,
) -> dict[str, Any]:
    """Report the actual attempted opcode/access plus 16 preceding instructions.

    If instruction execution fails, its trace entry is excluded from history.
    If instruction fetch fails, the requested PC is recorded but no opcode
    is fabricated. All fields are deterministic and JSON serialisable.
    """
    reason = stop.get("reason", "unknown_stop")
    category = _STOP_CATEGORIES.get(reason, "execution_stopped")
    budget_only = reason == "instruction_limit"
    failing = None if budget_only else active_instruction
    if failing is not None:
        last_is_failing = bool(trace) and trace[-1] == failing
        prior = trace[:-1] if last_is_failing else trace
        instruction_pc = failing.get("pc")
        opcode = failing.get("opcode")
    else:
        prior = trace
        instruction_pc = f"0x{fetch_pc:08X}" if fetch_pc is not None and not budget_only else None
        opcode = None

    memory = {
        key: stop[key]
        for key in ("access", "address", "width", "value")
        if key in stop
    }
    return {
        "category": category,
        "reason": reason,
        "detail": stop.get("detail", ""),
        "instruction_pc": instruction_pc,
        "opcode": opcode,
        "delay_slot": failing.get("delay_slot") if failing is not None else None,
        "memory_access": memory or None,
        "prior_instructions": prior[-TRACE_CONTEXT_LENGTH:],
        "is_dependency_blocker": not budget_only,
    }
