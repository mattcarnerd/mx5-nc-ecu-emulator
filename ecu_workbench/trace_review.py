"""Summarise a locally generated NC reset baseline, without needing ROM bytes.

A diagnostic report is evidence of *a particular run*, not proof of ECU boot.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .hudi import run_scenario_metadata

LF9VEB_SHA256 = "bfd0965a0f51f60a951d8cd3ef8fe77e5a37fbc326ddb723edf0ede4b1640fbf"


def summarise(report: dict) -> dict:
    if not isinstance(report, dict) or report.get("schema_version") != 1 or report.get("kind") != "nc_sh7058_reset_baseline":
        raise ValueError("Expected schema version 1 NC reset baseline")
    rom, settings, run = (report.get(k) for k in ("rom", "inputs", "result"))
    if not all(isinstance(k, dict) for k in (rom, settings, run)):
        raise ValueError("Incomplete baseline")
    sha = rom.get("sha256")
    if not isinstance(sha, str) or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
        raise ValueError("Invalid ROM SHA-256")
    count = run.get("executed_instructions")
    if type(count) is not int or count < 0:
        raise ValueError("Invalid instruction count")
    stop = run.get("stop")
    if not isinstance(stop, dict) or not isinstance(stop.get("reason"), str):
        raise ValueError("Missing stop reason")
    scenario=run_scenario_metadata(settings.get("hudi_scenario", "unknown"),settings.get("phi_cycles_per_instruction"),settings.get("adc_fixture"))
    if "hudi_scenario" in report and report["hudi_scenario"]!=scenario["hudi_scenario"]:
        raise ValueError("H-UDI scenario mismatch in baseline")
    if "phi_cycles_per_instruction" in report and report["phi_cycles_per_instruction"]!=scenario["phi_cycles_per_instruction"]:
        raise ValueError("Clock scenario mismatch in baseline")
    injected_counts=[run.get(k,0) for k in ("explicit_interrupt_requests","scheduled_interrupt_events")]
    if any(type(n) is not int or n<0 for n in injected_counts):
        raise ValueError("Invalid injected interrupt provenance")
    injected=any(injected_counts)
    if "adc_fixture" in report and report["adc_fixture"]!=scenario["adc_fixture"]:
        raise ValueError("ADC fixture mismatch in baseline")
    expected_scenario = (sha == LF9VEB_SHA256 and settings.get("reset") == "power"
                         and settings.get("nmi") == "high" and settings.get("max_steps") == 300
                         and not any(k.startswith("port_") for k in settings)
                         and not scenario["conditional_hardware_scenario"] and not injected)
    last = run.get("trace_tail")
    if not isinstance(last, list):
        raise ValueError("Invalid trace tail")
    # The original B29 diagnostic stops *before* Port E executes, at 76
    # attempted instructions. Counts alone never prove the write occurred.
    unsupported = run.get("first_unsupported_peripheral")
    next_dependency = run.get("next_dependency")
    last_access = unsupported if isinstance(unsupported, dict) else (
        next_dependency.get("memory_access") if isinstance(next_dependency, dict) else None)
    still_at_port_e = bool(isinstance(last_access, dict)
                            and last_access.get("address") == "0xFFFFF754"
                            and stop["reason"] == "unmodelled_peripheral")
    if not expected_scenario:
        assessment = "different_rom_or_settings"
    elif still_at_port_e:
        assessment = "still_blocked_on_port_e"
    elif count <= 76:
        assessment = "no_proven_progress"
    else:
        assessment = "past_previous_instruction_count_only"
    return {
        **scenario,
        "injected_interrupt_scenario":injected,
        "rom_sha256": sha,
        "known_lf9veb": sha == LF9VEB_SHA256,
        "reference_scenario": expected_scenario,
        "attempted_instructions": count,
        "stop_pc": run.get("pc_at_stop"),
        "stop_reason": stop["reason"],
        "stop_details": {k: stop.get(k) for k in ("address", "access", "width", "value", "detail") if k in stop},
        "next_dependency": next_dependency,
        "assessment": assessment,
        "boot_complete": False,
        "limitations": "A compact baseline has only 16 tail instructions and cannot prove the Port E write occurred; use full diagnostic output for the peripheral trace. Original ROM data stays local."
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Review an NC reset baseline without ROM bytes")
    parser.add_argument("baseline", type=Path, help="JSON from --baseline --report")
    parser.add_argument("--output", type=Path, help="Optional path for safe summary")
    args = parser.parse_args(argv)
    try:
        result = summarise(json.loads(args.baseline.read_text(encoding="utf-8")))
        body = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.write_text(body, encoding="utf-8")
        else:
            print(body, end="")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(2, f"ERROR: {exc}\n")


if __name__ == "__main__":
    main()
