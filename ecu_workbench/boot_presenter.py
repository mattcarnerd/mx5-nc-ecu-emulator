"""Pure, headless presentation of a bounded SH7058 reset diagnostic.

This module does not import tkinter. Neither a clean instruction-limit stop nor
an invalid input is evidence that Mazda firmware successfully booted.
"""
from __future__ import annotations

from typing import Any
from .hudi import run_scenario_metadata


def present_reset_diagnostic(report: dict[str, Any]) -> dict[str, Any]:
    """Produce deterministic UI status/sections from a reset diagnostic.

    This frontend currently runs only a partial SH7058 interpreter. It cannot
    label a virtual ECU as booted, even if a caller accidentally supplies
    boot_complete=True. Supporting verified boots will require a separate
    evidence-bearing result model in a future milestone.
    """
    stop = report.get("stop") or {}
    dependency = report.get("next_dependency") or {}
    reason = stop.get("reason", "unknown")
    count = report.get("executed_instructions", 0)
    budget = reason == "instruction_limit"
    status = f"Stopped: {reason} — {count} attempted instructions; ECU boot NOT verified."
    scenario=run_scenario_metadata(report.get("hudi_scenario", "unknown"),report.get("phi_cycles_per_instruction"),report.get("adc_fixture"))
    if scenario["conditional_hardware_scenario"]:
        status="Conditional hardware scenario — " + status
    if report.get("explicit_interrupt_requests",0) or report.get("scheduled_interrupt_events",0):
        status="Injected interrupt scenario — " + status
    if report.get("explicit_peripheral_inputs",0) or report.get("scheduled_peripheral_events",0):
        status="Explicit peripheral fixture — " + status
    summary = {
        **scenario,
        "boot_complete": False,
        "phase": "reset_diagnostic_only",
        "attempted_instructions": count,
        "completed_instructions": report.get("completed_instructions"),
        "virtual_time": report.get("virtual_time"),
        "execution_coverage": report.get("execution_coverage"),
        "scheduled_interrupt_events": report.get("scheduled_interrupt_events",0),
        "explicit_peripheral_inputs":report.get("explicit_peripheral_inputs",0),
        "scheduled_peripheral_events":report.get("scheduled_peripheral_events",0),
        "interrupt_entries": report.get("interrupt_entries",0),
        "explicit_interrupt_requests": report.get("explicit_interrupt_requests",0),
        "reset": report.get("reset"),
        "nmi_high": report.get("nmi_high"),
        "port_b_explicit_pins": report.get("port_b_explicit_pins"),
        "port_c_explicit_pins": report.get("port_c_explicit_pins"),
        "port_d_explicit_pins": report.get("port_d_explicit_pins"),
        "reset_vectors": report.get("vectors"),
        "pc_at_stop": report.get("pc_at_stop"),
        "stop_reason": stop,
        "next_dependency": dependency or None,
        "modelled_peripheral_access_count": len(report.get("modelled_peripheral_accesses") or []),
        "warning": "Only reset-vector instruction execution is simulated; ECU boot NOT verified.",
    }
    trace = report.get("trace") or []
    trace_text = "\n".join(
        f"{step.get('pc', '?')}    {step.get('opcode', '?')}  "
        f"{'[delay slot]' if step.get('delay_slot') else ''}"
        for step in trace
    ) or "No instructions fetched."
    return {
        "status": status,
        "summary": summary,
        "dependency_title": (
            "Instruction budget reached — not a successful boot or hardware failure:"
            if budget else "Execution stopped — next dependency or invalid input:"
        ),
        "dependency": dependency or None,
        "trace_text": trace_text,
        "peripherals": report.get("modelled_peripheral_accesses") or [],
    }
