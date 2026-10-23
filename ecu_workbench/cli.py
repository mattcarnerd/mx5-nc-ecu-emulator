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
            )
        else:
            result = {
                "image": image.inspect(),
                "nc_rom_assessment": assess_nc_rom(image).as_dict(),
                "nc_boot": diagnose_nc_reset(
                    image, reset=args.reset, max_steps=args.steps, nmi_high=pin,
                ),
            }
        output = json.dumps(result, indent=2)
        if args.report:
            Path(args.report).write_text(output + "\n", encoding="utf-8")
        print(output)
        return 0
    except (OSError, ValueError) as exc:
        parser.exit(2, f"ERROR: {exc}\n")
