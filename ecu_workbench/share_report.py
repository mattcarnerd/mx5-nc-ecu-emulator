"""B32: deterministic, reduced diagnostic evidence for voluntary sharing.

Use a *whitelist* of report fields rather than copying free text or full
traces. This is not an authenticity attestation and never claims ECU boot.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from .trace_review import LF9VEB_SHA256

_HEX8 = re.compile(r"^0x[0-9A-Fa-f]{8}$")
_OPCODE = re.compile(r"^[0-9A-Fa-f]{4}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SAFE_REASON = re.compile(r"^[a-z][a-z0-9_]{0,79}$")


def _hex8(value):
    return value.upper().replace("0X", "0x") if isinstance(value, str) and _HEX8.fullmatch(value) else None


def _opcode(value):
    return value.upper() if isinstance(value, str) and _OPCODE.fullmatch(value) else None


def _memory(data):
    if not isinstance(data, dict):
        return None
    out = {}
    for key in ("address", "value"):
        v = _hex8(data.get(key))
        if v is not None:
            out[key] = v
    if data.get("access") in ("read", "write", "fetch"):
        out["access"] = data["access"]
    if type(data.get("width")) is int and data["width"] in (1, 2, 4):
        out["width"] = data["width"]
    return out or None


def make_shareable_blocker_report(diagnostic: dict) -> dict:
    """Make a small, safe-to-review JSON report from the detailed GUI/CLI run.

    The output is based on a user's locally supplied diagnostic, which may
    itself be modified. It is not proof the original ROM is authentic.
    """
    if not isinstance(diagnostic, dict):
        raise ValueError("Expected a detailed NC diagnostic object")
    image = diagnostic.get("image")
    boot = diagnostic.get("nc_boot")
    if not isinstance(image, dict) or not isinstance(boot, dict):
        raise ValueError("Detailed diagnostic must contain image and nc_boot objects")
    sha = image.get("sha256")
    if not isinstance(sha, str) or _SHA256.fullmatch(sha) is None:
        raise ValueError("Missing or invalid ROM SHA-256")
    if isinstance(boot.get("rom_sha256"), str) and boot["rom_sha256"] != sha:
        raise ValueError("ROM hash mismatch in diagnostic")
    count = boot.get("executed_instructions", 0)
    if type(count) is not int or not 0 <= count <= 100000:
        raise ValueError("Invalid attempted instruction count")
    stop = boot.get("stop")
    if not isinstance(stop, dict) or not isinstance(stop.get("reason"), str) or not _SAFE_REASON.fullmatch(stop["reason"]):
        raise ValueError("Invalid diagnostic stop")
    settings = diagnostic.get("diagnostic_settings", {})
    if not isinstance(settings, dict):
        raise ValueError("Invalid diagnostic settings")
    reset = settings.get("reset", boot.get("reset"))
    nmi = settings.get("nmi")
    if nmi is None:
        nmi = "high" if boot.get("nmi_high") is True else "low" if boot.get("nmi_high") is False else "unknown"
    limit = settings.get("max_steps")
    if reset not in ("power", "manual") or nmi not in ("high", "low", "unknown"):
        raise ValueError("Invalid reset/NMI settings")
    if limit is not None and (type(limit) is not int or not 1 <= limit <= 100000):
        raise ValueError("Invalid instruction limit")
    provided = settings.get("explicit_pin_values", None)
    if provided is not None and type(provided) is not bool:
        raise ValueError("Invalid explicit-input setting")

    accesses = boot.get("modelled_peripheral_accesses", [])
    if not isinstance(accesses, list):
        raise ValueError("Expected peripheral access list")
    port_e_writes = [a for a in accesses if isinstance(a, dict) and
                     a.get("register") == "PEDR" and a.get("access") == "write" and
                     a.get("width") == 2 and a.get("value") == 0xFFFF]
    observed_port_e_write = bool(port_e_writes)
    # B33: record the exact newly observed Port F startup write; never
    # infer the write from instruction count or from the register model.
    observed_port_f_write = any(
        isinstance(a, dict) and a.get("register") == "PFDR"
        and a.get("access") == "write" and a.get("width") == 2
        and a.get("value") == 0xFFFF for a in accesses
    )
    # B34: check an actual PGDR word write, not an inferred instruction count.
    observed_port_g_write = any(
        isinstance(a, dict) and a.get("register") == "PGDR"
        and a.get("access") == "write" and a.get("width") == 2
        and a.get("value") == 0x000F for a in accesses
    )
    observed_port_h_write = any(
        isinstance(a, dict) and a.get("register") == "PHDR"
        and a.get("access") == "write" and a.get("width") == 2
        and a.get("value") == 0xFFFF for a in accesses
    )
    same_reference = (sha == LF9VEB_SHA256 and reset == "power" and nmi == "high"
                      and limit == 300 and provided is False)
    dependency = boot.get("next_dependency")
    if not isinstance(dependency, dict):
        dependency = {}
    stop_memory = _memory(stop)
    dependency_memory = _memory(dependency.get("memory_access"))
    stopping_at_port_e = stop["reason"] == "unmodelled_peripheral" and (
        (stop_memory and stop_memory.get("address") == "0xFFFFF754") or
        (dependency_memory and dependency_memory.get("address") == "0xFFFFF754"))
    if not same_reference:
        assessment = "not_reference_scenario"
    elif observed_port_e_write:
        assessment = "port_e_write_observed_in_diagnostic"
    elif stopping_at_port_e:
        assessment = "blocked_at_historical_port_e_access"
    else:
        assessment = "port_e_write_not_confirmed"
    result = {
        "schema_version": 1,
        "kind": "nc_sh7058_shareable_blocker",
        "rom_sha256": sha,
        "reference_lf9veb_scenario": same_reference,
        "settings": {
            "reset": reset, "nmi": nmi, "max_steps": limit,
            "explicit_pin_values": provided,
        },
        "executed_instructions": count,
        "pc_at_stop": _hex8(boot.get("pc_at_stop")),
        "stop": {
            "reason": stop["reason"],
            "memory_access": stop_memory,
        },
        "next_dependency": {
            "category": dependency.get("category") if dependency.get("category") in (
                "unsupported_cpu_instruction", "unmodelled_hardware_register",
                "unknown_hardware_state", "missing_external_input",
                "uninitialised_memory", "instruction_limit_reached",
                "invalid_rom_vectors", "unsupported_rom_image",
                "invalid_memory_access", "unsupported_hardware_access",
                "invalid_hardware_access", "unknown_cpu_state",
                "execution_stopped") else None,
            "instruction_pc": _hex8(dependency.get("instruction_pc")),
            "opcode": _opcode(dependency.get("opcode")),
            "memory_access": dependency_memory,
        },
        "pedr_word_write_ffff_in_peripheral_trace": observed_port_e_write,
        "pfdr_word_write_ffff_in_peripheral_trace": observed_port_f_write,
        "pgdr_word_write_000f_in_peripheral_trace": observed_port_g_write,
        "phdr_word_write_ffff_in_peripheral_trace": observed_port_h_write,
        "assessment": assessment,
        "boot_complete": False,
        "warning": "This is a reduced diagnostic report, not ROM authenticity proof or a completed ECU boot. No ROM bytes, filenames, file paths or full instruction traces included.",
    }
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Export reduced NC ECU diagnostic evidence")
    parser.add_argument("diagnostic", type=Path, help="Detailed JSON saved by Windows app or CLI")
    parser.add_argument("--output", type=Path, help="Optional shareable JSON destination")
    args = parser.parse_args(argv)
    try:
        report = make_shareable_blocker_report(json.loads(args.diagnostic.read_text(encoding="utf-8")))
        output = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.write_text(output, encoding="utf-8")
        else:
            print(output, end="")
        return 0
    except (OSError, ValueError) as error:
        parser.exit(2, f"ERROR: {error}\n")


if __name__ == "__main__":
    main()
