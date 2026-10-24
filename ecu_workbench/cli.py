"""Execute a bounded NC ROM reset-vector diagnostic. No ROM comparisons."""
from __future__ import annotations
from .sensor_fixture import adc_fields

import argparse
import json
from pathlib import Path

from .core import ROMImage
from .nc_boot import diagnose_nc_reset
from .boot_baseline import capture_boot_baseline
from .nc_rom import assess_nc_rom
from .hudi import HUDI_SCENARIOS


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="MX-5 NC ECU Emulator — experimental reset/boot diagnostic"
    )
    parser.add_argument("--rom", required=True, help="Local NC engine-ECU ROM image")
    parser.add_argument("--reset", choices=("power", "manual"), default="power")
    parser.add_argument("--nmi", choices=("unknown", "high", "low"), default="unknown",
                        help="Simulated NMI pin; unknown fails closed")
    parser.add_argument("--hudi-scenario", choices=HUDI_SCENARIOS, default="unknown",
                        help="Conditional simulation only: assume TRST reset or transfer complete; default unknown")
    parser.add_argument("--phi-cycles-per-instruction", type=int,
                        help="Conditional artificial phi cycles per completed instruction (1..1000000); omitted means unknown")
    parser.add_argument("--experimental-mcr-bit6",type=int,choices=(0,1),
                        help="Experimental constant reserved-bit6 readback on both HCAN channels; not verified hardware. Omit for unknown.")
    parser.add_argument("--hcan-reset-completion-ticks",type=int,help="Explicit synthetic reset-completion delay; not physical timing")
    parser.add_argument("--hcan-recessive-bus-ticks",type=int,help="Explicit synthetic11-recessive-bit input delay; not physical timing")
    parser.add_argument("--experimental-record-can-commands",action="store_true",help="Record unresolved mailbox writes without applying their effects; CAN feedback remains unknown")
    parser.add_argument("--experimental-isolate-can-reset-status",action="store_true",help="With CAN command recording, isolate only the reset-status bit supplied by completion inputs")
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
    parser.add_argument("--an0-voltage",help="Explicit ideal AN0 voltage")
    parser.add_argument("--adc-reference-voltage",help="Explicit analog reference voltage")
    parser.add_argument("--adc-completion-ticks",type=int,help="Artificial completion delay in completed instructions; all three AN0 fields required")
    args = parser.parse_args(argv)

    if not 1 <= args.steps <= 100000:
        parser.error("--steps must be between 1 and 100000")

    if args.experimental_isolate_can_reset_status and not args.experimental_record_can_commands:
        parser.error('Reset-status isolation requires --experimental-record-can-commands')

    try:
        hcan_fixture=({'reset_completion_ticks':args.hcan_reset_completion_ticks,'recessive_bus_ticks':args.hcan_recessive_bus_ticks}
                      if args.hcan_reset_completion_ticks is not None or args.hcan_recessive_bus_ticks is not None or args.experimental_record_can_commands else None)
        if args.experimental_record_can_commands:hcan_fixture['defer_mailbox_effects']=True
        if args.experimental_isolate_can_reset_status:hcan_fixture['preserve_supplied_reset_status']=True
        adc_fixture=adc_fields(args.an0_voltage,args.adc_reference_voltage,args.adc_completion_ticks)
        image = ROMImage.from_file(args.rom)
        pin = {"unknown": None, "high": True, "low": False}[args.nmi]
        if args.baseline:
            result = capture_boot_baseline(
                image, reset=args.reset, max_steps=args.steps, nmi_high=pin, hudi_scenario=args.hudi_scenario,
                phi_cycles_per_instruction=args.phi_cycles_per_instruction, adc_fixture=adc_fixture, experimental_mcr_bit6=args.experimental_mcr_bit6, hcan_fixture=hcan_fixture,
                port_b_pin_values=args.port_b_pins, port_b_pin_known_mask=args.port_b_known_mask,
                port_c_pin_values=args.port_c_pins, port_c_pin_known_mask=args.port_c_known_mask,
                port_d_pin_values=args.port_d_pins, port_d_pin_known_mask=args.port_d_known_mask,
            )
        else:
            result = {
                "image": image.inspect(),
                "diagnostic_settings": {
                    "reset": args.reset, "nmi": args.nmi, "max_steps": args.steps,
                    "hudi_scenario": args.hudi_scenario,
                    "phi_cycles_per_instruction": args.phi_cycles_per_instruction, "adc_fixture":adc_fixture,
                    "experimental_mcr_bit6":args.experimental_mcr_bit6, "hcan_fixture":hcan_fixture,
                    "explicit_pin_values": any(v is not None for v in
                        (args.port_b_pins, args.port_c_pins, args.port_d_pins)),
                },
                "nc_rom_assessment": assess_nc_rom(image).as_dict(),
                "nc_boot": diagnose_nc_reset(
                    image, reset=args.reset, max_steps=args.steps, nmi_high=pin, hudi_scenario=args.hudi_scenario,
                phi_cycles_per_instruction=args.phi_cycles_per_instruction, adc_fixture=adc_fixture, experimental_mcr_bit6=args.experimental_mcr_bit6, hcan_fixture=hcan_fixture,
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
