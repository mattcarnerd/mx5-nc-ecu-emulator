"""CLI for binary inspection and opt-in limited SuperH instruction stepping."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .core import ROMImage, compare
from .nc_rom import assess_nc_rom
from .sh2 import SH2Subset

def main(argv=None):
    parser = argparse.ArgumentParser(description="Mazda MX-5 NC engine ECU Workbench (NC ROM emulation under development)")
    parser.add_argument("--rom", required=True, help="Any nonempty binary file")
    parser.add_argument("--compare", help="A second binary to compare")
    parser.add_argument("--hex-offset", type=lambda x:int(x,0), default=0)
    parser.add_argument("--hex-length", type=lambda x:int(x,0), default=128)
    parser.add_argument("--sh2-step", action="store_true", help="Opt-in partial SH-2 interpreter")
    parser.add_argument("--pc", type=lambda x:int(x,0))
    parser.add_argument("--base", type=lambda x:int(x,0), default=0)
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--report", help="Write JSON report to this path")
    args = parser.parse_args(argv)
    try:
        rom = ROMImage.from_file(args.rom)
        result = {"image": rom.inspect(), "nc_rom_assessment": assess_nc_rom(rom).as_dict(), "hexdump": rom.hexdump(args.hex_offset, min(args.hex_length,4096))}
        if args.compare:
            result["comparison"] = compare(rom, ROMImage.from_file(args.compare))
        if args.sh2_step:
            if args.pc is None:
                parser.error("--sh2-step requires --pc (use --base for ROM mapping)")
            result["sh2_subset"] = SH2Subset(rom,args.pc,args.base).run(args.steps)
        output = json.dumps(result,indent=2)
        if args.report:
            Path(args.report).write_text(output+"\n",encoding="utf-8")
        print(output)
        return 0
    except (OSError,ValueError) as ex:
        parser.exit(2,f"ERROR: {ex}\n")
