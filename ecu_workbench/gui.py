"""Windows desktop front-end for executing NC ECU reset diagnostics.

This is a diagnostic runner, not an engine simulator. All hardware inputs
must be explicit; missing peripherals halt execution instead of faking results.
"""
from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .core import ROMImage
from .nc_boot import diagnose_nc_reset
from .boot_presenter import present_reset_diagnostic
from .nc_rom import assess_nc_rom


class Workbench(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MX-5 NC ECU Emulator — experimental boot")
        self.geometry("1000x710")
        self.minsize(740, 540)
        self.rom: ROMImage | None = None
        self.report: dict | None = None
        self.reset = tk.StringVar(value="power")
        self.nmi = tk.StringVar(value="unknown")
        self.steps = tk.StringVar(value="300")
        self.port_b_pins = tk.StringVar(value="")
        self.port_b_mask = tk.StringVar(value="0xFFFF")
        self.filename = tk.StringVar(value="No ROM loaded")
        self.status = tk.StringVar(value="Load an NC engine ECU ROM to begin.")
        self._build_ui()

    def _build_ui(self):
        panel = ttk.Frame(self, padding=16)
        panel.pack(fill="both", expand=True)
        ttk.Label(panel, text="MX-5 NC Virtual ECU", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(
            panel,
            text="Boot real NC firmware from its reset vector. Full engine simulation is not implemented.",
        ).pack(anchor="w", pady=(2, 12))

        file_row = ttk.Frame(panel)
        file_row.pack(fill="x", pady=(0, 10))
        ttk.Button(file_row, text="Load NC ROM…", command=self.load_rom).pack(side="left")
        ttk.Label(file_row, textvariable=self.filename).pack(side="left", padx=(12, 0))
        ttk.Button(file_row, text="Save diagnostic JSON…", command=self.save_report).pack(side="right")

        hardware = ttk.LabelFrame(panel, text="Virtual hardware settings", padding=10)
        hardware.pack(fill="x", pady=(0, 8))
        ttk.Label(hardware, text="Reset").pack(side="left")
        ttk.Combobox(
            hardware, textvariable=self.reset, values=("power", "manual"),
            state="readonly", width=9,
        ).pack(side="left", padx=(5, 14))
        ttk.Label(hardware, text="NMI pin").pack(side="left")
        ttk.Combobox(
            hardware, textvariable=self.nmi, values=("unknown", "high", "low"),
            state="readonly", width=10,
        ).pack(side="left", padx=(5, 14))
        ttk.Label(hardware, text="Max instructions").pack(side="left")
        ttk.Entry(hardware, textvariable=self.steps, width=9).pack(side="left", padx=(5, 14))
        self.run_button = ttk.Button(
            hardware, text="Run startup diagnostic", command=self.run_boot,
        )
        self.run_button.pack(side="right")
        self.run_button.state(["disabled"])

        pin_controls = ttk.Frame(panel)
        pin_controls.pack(fill="x", pady=(0, 8))
        ttk.Label(pin_controls, text="Port B physical pins (hex; blank = unknown)").pack(side="left")
        ttk.Entry(pin_controls, textvariable=self.port_b_pins, width=12).pack(side="left", padx=(5, 12))
        ttk.Label(pin_controls, text="Known-bit mask").pack(side="left")
        ttk.Entry(pin_controls, textvariable=self.port_b_mask, width=12).pack(side="left", padx=5)

        ttk.Label(
            panel, textvariable=self.status, font=("Segoe UI", 11, "bold"),
            wraplength=900,
        ).pack(fill="x", anchor="w", pady=(6, 9))

        tabs = ttk.Notebook(panel)
        tabs.pack(fill="both", expand=True)
        self.summary = self._tab(tabs, "Boot status")
        self.blocker = self._tab(tabs, "Next dependency")
        self.trace = self._tab(tabs, "Firmware instruction trace")
        self.peripherals = self._tab(tabs, "Hardware accesses")
        self._set(self.blocker, "Load a ROM and run the diagnostic to identify a blocker.")
        self._set(
            self.summary,
            "This tool executes the ROM's actual instructions from its reset vector.\n\n"
            "The emulator currently supports only a small portion of the SH7058 CPU and "
            "virtual peripherals. It stops on unknown hardware instead of guessing.\n\n"
            "Until a full firmware main loop and engine-input model run successfully, "
            "this is NOT a booted or operational ECU.",
        )

    def _tab(self, tabs, title):
        tab = ttk.Frame(tabs)
        tabs.add(tab, text=title)
        tab.rowconfigure(0, weight=1)
        tab.columnconfigure(0, weight=1)
        display = tk.Text(tab, wrap="none", font=("Consolas", 10))
        yscroll = ttk.Scrollbar(tab, orient="vertical", command=display.yview)
        display.configure(yscrollcommand=yscroll.set)
        display.grid(row=0, column=0, sticky="nsew", padx=(4, 0), pady=4)
        yscroll.grid(row=0, column=1, sticky="ns", pady=4)
        return display

    @staticmethod
    def _set(output, content):
        output.configure(state="normal")
        output.delete("1.0", "end")
        output.insert("1.0", content)
        output.configure(state="disabled")

    def load_rom(self):
        path = filedialog.askopenfilename(
            title="Load an NC engine ECU ROM",
            filetypes=(("ROM files", "*.bin *.rom *.hex"), ("All files", "*.*")),
        )
        if not path:
            return
        try:
            image = ROMImage.from_file(path)
            assessment = assess_nc_rom(image)
            self.rom = image
            self.report = None
            self.filename.set(image.name)
            self.status.set("ROM loaded — firmware not running.")
            self.run_button.state(["!disabled"])
            self._set(
                self.summary,
                f"File: {image.name}\n"
                f"Size: {image.size:,} bytes\n"
                f"SHA-256: {image.sha256}\n"
                f"ROM screening: {assessment.status}\n\n"
                f"{assessment.explanation}\n\n"
                "Click Run startup diagnostic to execute from the ROM's reset vector.\n"
                "A plausible ROM size is not proof that the image is a valid NC ROM.",
            )
            self._set(self.trace, "No execution trace yet.")
            self._set(self.blocker, "No startup diagnostic yet.")
            self._set(self.peripherals, "No simulated peripheral accesses yet.")
        except (OSError, ValueError) as exc:
            messagebox.showerror("Cannot load ROM", str(exc))

    def run_boot(self):
        if self.rom is None:
            messagebox.showinfo("Load a ROM", "Select an NC ECU ROM first.")
            return
        try:
            maximum = int(self.steps.get())
            if not 1 <= maximum <= 100000:
                raise ValueError("Maximum instructions must be between 1 and 100000")
            result = diagnose_nc_reset(
                self.rom,
                reset=self.reset.get(),
                nmi_high={"unknown": None, "high": True, "low": False}[self.nmi.get()],
                max_steps=maximum,
                port_b_pin_values=(int(self.port_b_pins.get(), 0) if self.port_b_pins.get().strip() else None),
                port_b_pin_known_mask=int(self.port_b_mask.get(), 0),
            )
            self.report = {
                "image": self.rom.inspect(),
                "nc_rom_assessment": assess_nc_rom(self.rom).as_dict(),
                "nc_boot": result,
            }
            presentation = present_reset_diagnostic(result)
            self.status.set(presentation["status"])
            self._set(self.summary, json.dumps(presentation["summary"], indent=2))
            dependency = presentation["dependency"]
            if dependency is not None:
                self._set(
                    self.blocker,
                    presentation["dependency_title"] + "\n\n" + json.dumps(dependency, indent=2),
                )
            else:
                self._set(self.blocker, presentation["dependency_title"] + "\n\nNo further details.")
            self._set(self.trace, presentation["trace_text"])
            self._set(self.peripherals, json.dumps(presentation["peripherals"], indent=2))
        except (KeyError, ValueError) as exc:
            messagebox.showerror("Invalid diagnostic settings", str(exc))

    def save_report(self):
        if self.report is None:
            messagebox.showinfo("No diagnostic", "Run a startup diagnostic first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=(("JSON reports", "*.json"),),
        )
        if not path:
            return
        try:
            Path(path).write_text(json.dumps(self.report, indent=2) + "\n", encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Cannot save report", str(exc))


def start():
    Workbench().mainloop()
