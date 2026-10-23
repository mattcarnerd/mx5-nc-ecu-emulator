"""ROM image loader for the MX-5 NC emulator.

Loading a file never implies the ROM is valid for a Mazda ECU.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib


@dataclass(frozen=True)
class ROMImage:
    name: str
    data: bytes

    @classmethod
    def from_file(cls, path: str | Path) -> "ROMImage":
        p = Path(path)
        raw = p.read_bytes()
        if not raw:
            raise ValueError("ROM file is empty")
        return cls(p.name, raw)

    @property
    def size(self) -> int:
        return len(self.data)

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.data).hexdigest()

    def inspect(self) -> dict:
        return {
            "name": self.name,
            "size_bytes": self.size,
            "sha256": self.sha256,
            "format_verified": False,
            "firmware_emulated": False,
            "note": "File loading alone does not validate or emulate this ECU ROM."
        }
