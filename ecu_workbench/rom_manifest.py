"""B26 local-only NC ROM inventory; metadata is never ROM verification.

Input JSON: {"entries":[{"path":"local.bin","family":"NC2","calibration_id":"...",
"provenance":"ECU sticker","hardware_profile":"unknown"}]}. File paths are
resolved relative to the JSON file and never included in the report.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

FAMILIES = {"NC1", "NC2", "NC3", "unknown"}
STATUSES = {"not_available", "candidate", "verified_profile", "boot_trace_tested"}

def inventory(document: dict, *, base: Path) -> dict:
    if not isinstance(document, dict) or not isinstance(document.get("entries"), list):
        raise ValueError("manifest requires an entries array")
    seen = set()
    output = []
    for index, item in enumerate(document["entries"]):
        if not isinstance(item, dict):
            raise ValueError(f"entry {index} must be an object")
        family = item.get("family", "unknown")
        if family not in FAMILIES:
            raise ValueError(f"entry {index}: invalid NC family")
        profile = item.get("hardware_profile", "unknown")
        if not isinstance(profile, str) or not profile.strip():
            raise ValueError(f"entry {index}: invalid hardware profile")
        provenance = item.get("provenance")
        if provenance is not None and (not isinstance(provenance, str) or not provenance.strip()):
            raise ValueError(f"entry {index}: invalid provenance")
        calibration = item.get("calibration_id")
        if calibration is not None and (not isinstance(calibration, str) or not calibration.strip()):
            raise ValueError(f"entry {index}: invalid calibration ID")
        # Neither a filename, declared family nor a plausible size verifies hardware.
        path = item.get("path")
        if path is not None and (not isinstance(path, str) or not path.strip()):
            raise ValueError(f"entry {index}: invalid path")
        source = base / path if path else None
        present = bool(source and source.is_file())
        digest = None
        size = None
        if present:
            data = source.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            size = len(data)
            if digest in seen:
                raise ValueError(f"entry {index}: duplicate ROM SHA-256")
            seen.add(digest)
        evidence = item.get("hardware_evidence")
        if evidence is not None and (not isinstance(evidence, str) or not evidence.strip()):
            raise ValueError(f"entry {index}: invalid hardware evidence")
        traced = item.get("boot_trace_tested", False)
        if type(traced) is not bool:
            raise ValueError(f"entry {index}: boot_trace_tested must be boolean")
        verified = profile != "unknown" and bool(evidence)
        if traced and not verified:
            raise ValueError(f"entry {index}: boot trace requires verified hardware profile and evidence")
        if traced and not present:
            raise ValueError(f"entry {index}: boot trace requires locally available ROM")
        status = ("not_available" if not present else
                  "boot_trace_tested" if traced else
                  "verified_profile" if verified else "candidate")
        output.append({
            "entry": index+1, "family": family,
            "calibration_id": calibration if provenance else None,
            "calibration_provenance": provenance if calibration else None,
            "hardware_profile": profile if verified else "unknown",
            "hardware_evidence": evidence if verified else None,
            "sha256": digest, "size_bytes": size, "status": status,
            "boot_complete": False,
        })
    return {"schema_version":1,"entries":output,
            "warning":"Inventory metadata is not ROM authenticity validation or ECU boot proof."}

def main(argv=None):
    parser=argparse.ArgumentParser(description="Local NC ROM metadata inventory (read-only)")
    parser.add_argument("manifest",type=Path,help="Local JSON input; never committed")
    parser.add_argument("--output",type=Path,help="Optional report destination; omit for stdout")
    args=parser.parse_args(argv)
    result=inventory(json.loads(args.manifest.read_text(encoding="utf-8")),base=args.manifest.resolve().parent)
    report=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if args.output:
        args.output.write_text(report,encoding="utf-8")
    else:
        print(report,end="")

if __name__=="__main__":
    main()
