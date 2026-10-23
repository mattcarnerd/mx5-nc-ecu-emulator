"""Execute a bounded NC ROM reset-vector diagnostic. No ROM comparisons."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import ROMImage
from .nc_boot import diagnose_nc_reset
from .boot_baseline import capture_boot_baseline
from .nc_rom import assess_nc_rom


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="MX-5 NC ECU Emulator — experimental reset/boot diagnostic"
    )
    parser.add_argument("--rom", required=True, help="Local NC engine-ECU ROM image")
    parser.add_argument("--reset", choices=("power", "manual"), default="power")
    parser.add_argument("--nmi", choices=("unknown", "high", "low"), default="unknown",
                        help="Simulated NMI pin; unknown fails closed")
    parser.add_argument("--port-b-pins", type=lambda s: int(s, 0),
                        help="Explicit 16-bit physical Port B levels, e.g. 0x1234; omitted means unknown")
    parser.add_argument("--port-b-known-mask", type=lambda s: int(s, 0), default=0xFFFF,
                        help="Mask of Port B pin levels explicitly known (default: 0xFFFF if supplied)")
    parser.add_argument("--port-c-pins", type=lambda s: int(s,0),
                        help="Physical PC4..PC0 pin levels (hex); omit to leave unknown")
    parser.add_argument("--port-c-known-mask", type=lambda s: int(s,0), default=0x001F,
                        help="Known PC4..PC0 physical pin bits, default 0x001F if provided")
    parser.add_argument("--port-d-pins", type=lambda s: int(s,0),
                        help="Explicit 16-bit Port D physical register levels (omit for unknown)")
    parser.add_argument("--port-d-known-mask", type=lambda s: int(s,0), default=0xFFFF,
                        help="Known Port D physical bit mask (default 0xFFFF if supplied)")
    parser.add_argument("--steps", type=int, default=300,
                        help="Maximum number of real instructions to execute (1..100000)")
    parser.add_argument("--report", help="Save diagnostic JSON at this location")
    parser.add_argument("--baseline", action="store_true",
                        help="Emit deterministic compact reset baseline JSON (instead of detailed diagnostics)")
    args = parser.parse_args(argv)

    if not 1 <= args.steps <= 100000:
        parser.error("--steps must be between 1 and 100000")

    try:
        image = ROMImage.from_file(args.rom)
        pin = {"unknown": None, "high": True, "low": False}[args.nmi]
        if args.baseline:
            result = capture_boot_baseline(
                image, reset=args.reset, max_steps=args.steps, nmi_high=pin,
                port_b_pin_values=args.port_b_pins, port_b_pin_known_mask=args.port_b_known_mask,
                port_c_pin_values=args.port_c_pins, port_c_pin_known_mask=args.port_c_known_mask,
                port_d_pin_values=args.port_d_pins, port_d_pin_known_mask=args.port_d_known_mask,
            )
        else:
            result = {
                "image": image.inspect(),
                "nc_rom_assessment": assess_nc_rom(image).as_dict(),
                "nc_boot": diagnose_nc_reset(
                    image, reset=args.reset, max_steps=args.steps, nmi_high=pin,
                    port_b_pin_values=args.port_b_pins, port_b_pin_known_mask=args.port_b_known_mask,
                    port_c_pin_values=args.port_c_pins, port_c_pin_known_mask=args.port_c_known_mask,
                    port_d_pin_values=args.port_d_pins, port_d_pin_known_mask=args.port_d_known_mask,
                ),
            }
        output = json.dumps(result, indent=2)
        if args.report:
            Path(args.report).write_text(output + "\n", encoding="utf-8")
        print(output)
        return 0
    except (OSError, ValueError) as exc:
        parser.exit(2, f"ERROR: {exc}\n")
