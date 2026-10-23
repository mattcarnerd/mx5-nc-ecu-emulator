"""Read-only Tkinter interface for any binary ROM.

This GUI does not flash ECUs, edit ROMs, or assume a processor architecture.
"""
from __future__ import annotations

import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from .core import ROMImage, compare
from .nc_rom import assess_nc_rom
from .sh2 import SH2Subset
from .nc_boot import diagnose_nc_reset


class Workbench(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MX-5 NC ECU Workbench — ROM inspection")
        self.geometry("1000x760")
        self.minsize(740, 560)
        self.rom: ROMImage | None = None
        self.other: ROMImage | None = None
        self.report: dict | None = None
        self.offset = tk.StringVar(value="0x0")
        self.pc = tk.StringVar(value="0x0")
        self.base = tk.StringVar(value="0x0")
        self.steps = tk.StringVar(value="100")
        self.nmi_setting = tk.StringVar(value="unknown")
        self.reset_setting = tk.StringVar(value="power")
        self._layout()

    def _layout(self):
        root = ttk.Frame(self, padding=15)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="ECU Workbench", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(
            root,
            text="Target: any valid MX-5 NC ECU ROM. Current version inspects ROMs; full NC ECU emulation is not yet available.",
        ).pack(anchor="w", pady=(2, 10))

        toolbar = ttk.Frame(root)
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="Open ROM…", command=self.open_rom).pack(side="left")
        ttk.Button(toolbar, text="Compare with ROM…", command=self.open_comparison).pack(side="left", padx=8)
        ttk.Button(toolbar, text="Save JSON report…", command=self.save_report).pack(side="right")

        tabs = ttk.Notebook(root)
        tabs.pack(fill="both", expand=True, pady=(12, 0))
        inspect_frame = ttk.Frame(tabs, padding=12)
        cpu_frame = ttk.Frame(tabs, padding=12)
        tabs.add(inspect_frame, text="Inspect / Compare")
        tabs.add(cpu_frame, text="Experimental CPU test")

        row = ttk.Frame(inspect_frame)
        row.pack(fill="x", pady=(0, 8))
        ttk.Label(row, text="Hex offset").pack(side="left")
        ttk.Entry(row, textvariable=self.offset, width=14).pack(side="left", padx=(6, 8))
        ttk.Button(row, text="Show 256 bytes", command=self.inspect).pack(side="left")
        self.details = self._text(inspect_frame)
        self._display(
            self.details,
            "Open an MX-5 NC engine ECU ROM, or an unknown binary for preliminary inspection.\n\n"
            "The program will show the byte count, SHA-256, entropy and hex view. "
            "Use Compare with ROM for a byte-level diff.\n\n"
            "Opening a ROM is NOT equivalent to emulating its ECU or validating a calibration."
        )

        cpu_controls = ttk.Frame(cpu_frame)
        cpu_controls.pack(fill="x", pady=(0, 8))
        for name, variable in (
            ("Start PC", self.pc),
            ("ROM base address", self.base),
            ("Max steps", self.steps),
        ):
            ttk.Label(cpu_controls, text=name).pack(side="left", padx=(8, 4))
            ttk.Entry(cpu_controls, textvariable=variable, width=12).pack(side="left")
        ttk.Button(cpu_controls, text="Step", command=self.step).pack(side="left", padx=8)
        ttk.Label(
            cpu_frame,
            text="Limited SH-2 instruction subset ONLY. Does not model a full ECU, RAM, peripherals or interrupts.\n"
                 "Unsupported instructions halt. You must supply a valid PC and ROM load address."
        ).pack(anchor="w", pady=(0, 8))
        boot_row = ttk.Frame(cpu_frame)
        boot_row.pack(fill="x", pady=(2, 8))
        ttk.Label(boot_row, text="NC reset:").pack(side="left")
        ttk.Combobox(boot_row, textvariable=self.reset_setting, values=("power", "manual"), state="readonly", width=9).pack(side="left", padx=4)
        ttk.Label(boot_row, text="Simulated NMI pin:").pack(side="left", padx=(8, 0))
        ttk.Combobox(boot_row, textvariable=self.nmi_setting, values=("unknown", "high", "low"), state="readonly", width=10).pack(side="left", padx=4)
        ttk.Button(boot_row, text="Diagnose NC startup", command=self.run_nc_boot).pack(side="left", padx=8)
        self.cpu_output = self._text(cpu_frame)

    def _text(self, parent):
        holder = ttk.Frame(parent)
        holder.pack(fill="both", expand=True)
        text = tk.Text(holder, wrap="none", font=("Consolas", 10))
        sy = ttk.Scrollbar(holder, orient="vertical", command=text.yview)
        sx = ttk.Scrollbar(holder, orient="horizontal", command=text.xview)
        text.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        text.grid(row=0, column=0, sticky="nsew")
        sy.grid(row=0, column=1, sticky="ns")
        sx.grid(row=1, column=0, sticky="ew")
        holder.rowconfigure(0, weight=1)
        holder.columnconfigure(0, weight=1)
        return text

    @staticmethod
    def _display(box, value: str):
        box.delete("1.0", "end")
        box.insert("1.0", value)

    def open_rom(self):
        path = filedialog.askopenfilename(filetypes=[("All files", "*.*")])
        if not path:
            return
        try:
            image = ROMImage.from_file(path)
            self.rom = image
            self.other = None
            self.inspect()
        except (OSError, ValueError) as exc:
            messagebox.showerror("Open ROM failed", str(exc))

    def open_comparison(self):
        if self.rom is None:
            messagebox.showinfo("Load first ROM", "Open a ROM before selecting a comparison.")
            return
        path = filedialog.askopenfilename(filetypes=[("All files", "*.*")])
        if not path:
            return
        try:
            self.other = ROMImage.from_file(path)
            self.inspect()
        except (OSError, ValueError) as exc:
            messagebox.showerror("Open comparison failed", str(exc))

    def inspect(self):
        if self.rom is None:
            return
        try:
            position = int(self.offset.get(), 0)
            self.report = {"image": self.rom.inspect(), "nc_rom_assessment": assess_nc_rom(self.rom).as_dict()}
            if self.other is not None:
                self.report["comparison"] = compare(self.rom, self.other)
            self._display(
                self.details,
                json.dumps(self.report, indent=2) + "\n\nHEX DUMP\n"
                + self.rom.hexdump(position, 256),
            )
        except ValueError as exc:
            messagebox.showerror("Invalid offset", str(exc))

    def step(self):
        if self.rom is None:
            messagebox.showinfo("Load ROM", "Open a ROM before running instruction tests.")
            return
        try:
            result = SH2Subset(
                self.rom, int(self.pc.get(), 0), int(self.base.get(), 0)
            ).run(int(self.steps.get()))
            if self.report is None:
                self.report = {}
            self.report["sh2_subset"] = result
            self._display(self.cpu_output, json.dumps(result, indent=2))
        except ValueError as exc:
            messagebox.showerror("Invalid CPU test settings", str(exc))

    def run_nc_boot(self):
        if self.rom is None:
            messagebox.showinfo("Load ROM", "Open an NC engine ECU ROM first.")
            return
        try:
            result = diagnose_nc_reset(
                self.rom, reset=self.reset_setting.get(),
                max_steps=int(self.steps.get()),
                nmi_high={"unknown": None, "high": True, "low": False}[self.nmi_setting.get()])
            if self.report is None:
                self.report = {}
            self.report["nc_boot"] = result
            self._display(self.cpu_output, json.dumps(result, indent=2))
        except (KeyError, ValueError) as exc:
            messagebox.showerror("Boot diagnostic", str(exc))

    def save_report(self):
        if not self.report:
            messagebox.showinfo("No report", "Inspect or test a ROM first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON reports", "*.json")]
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump(self.report, fh, indent=2)
            except OSError as exc:
                messagebox.showerror("Save failed", str(exc))


def start():
    Workbench().mainloop()
