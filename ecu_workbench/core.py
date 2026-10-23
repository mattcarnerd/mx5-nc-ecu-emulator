"""Read-only, format-agnostic binary image inspection. No ECU writes."""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from itertools import zip_longest
from pathlib import Path
import hashlib
import math

@dataclass(frozen=True)
class ROMImage:
    name: str
    data: bytes

    @classmethod
    def from_file(cls, path: str | Path) -> "ROMImage":
        p = Path(path)
        data = p.read_bytes()
        if not data:
            raise ValueError("ROM file is empty")
        return cls(p.name, data)

    @property
    def size(self) -> int:
        return len(self.data)

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.data).hexdigest()

    @property
    def entropy(self) -> float:
        frequencies = Counter(self.data)
        total = self.size
        return -sum((n / total) * math.log2(n / total) for n in frequencies.values())

    def inspect(self) -> dict:
        sample = self.data[:64]
        return {
            "name": self.name,
            "size_bytes": self.size,
            "sha256": self.sha256,
            "entropy_bits_per_byte": round(self.entropy, 4),
            "leading_hex": sample[:32].hex(" "),
            "leading_ascii": "".join(chr(v) if 32 <= v < 127 else "." for v in sample),
            "program_architecture": "unknown",
            "emulation_status": "not_started",
            "note": "Reading a binary does not establish ECU compatibility or flashing safety."
        }

    def hexdump(self, offset: int = 0, length: int = 256, bytes_per_row: int = 16) -> str:
        if offset < 0 or length < 0 or bytes_per_row <= 0:
            raise ValueError("Invalid hexdump arguments")
        lines = []
        for start in range(min(offset, self.size), min(offset + length, self.size), bytes_per_row):
            row = self.data[start:min(start + bytes_per_row, offset + length, self.size)]
            h = " ".join(f"{b:02X}" for b in row)
            text = "".join(chr(b) if 32 <= b < 127 else "." for b in row)
            lines.append(f"{start:08X}  {h:<{bytes_per_row * 3 - 1}}  {text}")
        return "\n".join(lines)

def compare(a: ROMImage, b: ROMImage, max_details: int = 100) -> dict:
    if max_details < 0:
        raise ValueError("max_details must be >= 0")
    examples, regions = [], []
    changed = 0
    active_start = None
    prev = 0
    for i, (x, y) in enumerate(zip_longest(a.data, b.data, fillvalue=None)):
        if x != y:
            changed += 1
            if len(examples) < max_details:
                examples.append({
                    "offset": i, "offset_hex": f"0x{i:X}",
                    "a": None if x is None else f"{x:02X}",
                    "b": None if y is None else f"{y:02X}"
                })
            if active_start is None:
                active_start = i
            prev = i
        elif active_start is not None:
            regions.append({"from": active_start, "to": prev, "bytes": prev - active_start + 1})
            active_start = None
    if active_start is not None:
        regions.append({"from": active_start, "to": prev, "bytes": prev - active_start + 1})
    return {
        "first": {"name": a.name, "size": a.size, "sha256": a.sha256},
        "second": {"name": b.name, "size": b.size, "sha256": b.sha256},
        "changed_bytes": changed,
        "changed_regions": len(regions),
        "first_changed_regions": regions[:25],
        "example_changes": examples,
        "truncated": changed > len(examples),
        "note": "Binary comparison only; calibration/firmware meaning is unknown."
    }
