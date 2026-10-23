"""Explicit 16-bit register routing for the SH7058 NC reset diagnostic.

B17: this layer ONLY dispatches already-modelled port data registers. It does
not turn unrecognised peripheral addresses into successful reads/writes, infer
pin levels or alter the underlying per-port reset/width semantics.

Routes are registered per byte (big-endian upper/lower byte), while the
register implementation retains responsibility for widths, reset-known bits,
pin directions, and traces.
"""
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass(frozen=True)
class RegisterRoute:
    name: str
    base: int
    read: Callable[[int, int], int]
    write: Callable[[int, int, int], None]


class PeripheralRouter:
    """Small fail-closed registry for data registers with byte/word access.

    A missing address returns the unique `UNHANDLED` marker so the bus can
    continue to its other existing handlers and, ultimately, report an
    unmodelled peripheral. The router NEVER invents a fallback value.
    """

    UNHANDLED = object()

    def __init__(self):
        self._by_byte = {}
        self._by_base = {}

    def add_word(self, *, name: str, base: int, read: Callable,
                 write: Callable) -> None:
        if not isinstance(name, str) or not name or type(base) is not int or base & 1:
            raise ValueError("Register name must be set and base word-aligned")
        if not callable(read) or not callable(write):
            raise TypeError("Register handlers must be callable")
        if base in self._by_byte or base + 1 in self._by_byte:
            raise ValueError(f"Overlapping peripheral register at 0x{base:08X}")
        route = RegisterRoute(name, base, read, write)
        self._by_byte[base] = route
        self._by_byte[base + 1] = route
        self._by_base[base] = route

    def guard_32bit(self, address: int, width: int, *, access: str,
                    value: Optional[int] = None) -> None:
        """Preserve historical Port B/C/D/E width stops ahead of alignment.

        For base addresses that are only 2-byte aligned (PCDR/PDDR/PBPR),
        the legacy bus reported unsupported_access_size for a 4-byte access
        instead of unaligned_access. Delegate to the original register code.
        """
        if width != 4:
            return
        route = self._by_base.get(address)
        if route is None:
            return
        if access == "read":
            route.read(address, width)
        elif access == "write":
            route.write(address, width, value)
        else:
            raise ValueError("Unknown peripheral access mode")
        raise AssertionError(f"{route.name} unexpectedly accepted a 32-bit access")

    def read(self, address: int, width: int):
        route = self._by_byte.get(address)
        return self.UNHANDLED if route is None else route.read(address, width)

    def write(self, address: int, width: int, value: int):
        route = self._by_byte.get(address)
        if route is None:
            return self.UNHANDLED
        return route.write(address, width, value)
