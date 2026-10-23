"""Non-authoritative Mazda MX-5 NC ROM *candidate* screening.

File structure is not enough to prove an image belongs to an NC ECU or can
execute on a particular ECU. Future identity/checksum checks will be separate.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from .core import ROMImage

STANDARD_USER_FLASH_SIZE = 0x100000  # Common ROMDrop/NCFlash full-flash images

@dataclass(frozen=True)
class NCROMAssessment:
    status: str
    image_size: int
    probable_layout: str
    confirmed_nc_rom: bool
    firmware_emulation_supported: bool
    explanation: str
    next_checks: tuple[str, ...]

    def as_dict(self) -> dict:
        return asdict(self)

def assess_nc_rom(rom: ROMImage) -> NCROMAssessment:
    checks = (
        "Verify ROM/container layout and calibration identity against independent evidence",
        "Verify checksums using the correct NC ECU variant and image format",
        "Identify ECU hardware profile and memory map",
        "Demonstrate boot and peripheral behaviour in a validated execution engine",
    )
    if rom.size != STANDARD_USER_FLASH_SIZE:
        return NCROMAssessment(
            status="unrecognised_layout",
            image_size=rom.size,
            probable_layout="unknown",
            confirmed_nc_rom=False,
            firmware_emulation_supported=False,
            explanation=(
                "Not the usual 1 MiB NC engine-ECU full-flash size. This is not "
                "proof the data is invalid; partial dumps or other formats may differ."
            ),
            next_checks=checks,
        )
    if not any(b != 0 for b in rom.data) or not any(b != 0xFF for b in rom.data):
        return NCROMAssessment(
            status="empty_or_erased",
            image_size=rom.size,
            probable_layout="1MiB",
            confirmed_nc_rom=False,
            firmware_emulation_supported=False,
            explanation="All-zero or all-0xFF image; not executable firmware.",
            next_checks=checks,
        )
    return NCROMAssessment(
        status="plausible_size_only",
        image_size=rom.size,
        probable_layout="1MiB",
        confirmed_nc_rom=False,
        firmware_emulation_supported=False,
        explanation=(
            "Size is consistent with common 1 MiB MX-5 NC ECU images; content "
            "identity, checksum, processor compatibility and emulation are NOT "
            "verified. An unrelated 1 MiB file receives the same result."
        ),
        next_checks=checks,
    )
