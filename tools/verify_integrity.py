"""Verify original artifacts and installed files without changing them."""

from __future__ import annotations

import base64
import csv
import hashlib
from importlib import metadata
import io
import json
from pathlib import Path, PurePosixPath
import sys
from zipfile import BadZipFile, ZipFile


ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_WHEEL = (
    "mazegenerator-00001(1)/mazegenerator-2.1.0-py3-none-any.whl"
)
VENDOR_WHEEL = "vendor/mazegenerator-2.1.0-py3-none-any.whl"


class IntegrityError(Exception):
    """Report missing, modified or inconsistent project artifacts."""


def _sha256(path: Path) -> str:
    """Read an artifact in bounded chunks and return its SHA-256 digest."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_path(relative: str) -> Path:
    """Locate original inputs beside the project or its source directory."""
    names = [relative]
    if relative.startswith("mazegenerator-00001(1)/"):
        names.append(relative.replace(
            "mazegenerator-00001(1)/", "mazegenerator-00001/", 1,
        ))
    for base in (ROOT, ROOT.parent):
        for name in names:
            candidate = base / name
            if candidate.is_file():
                return candidate
    raise IntegrityError(f"Original artifact is missing: {relative}")


def _load_manifest() -> dict[str, str]:
    """Load the original pre-development SHA-256 inventory defensively."""
    manifest_path = ROOT / "project_management/artifact_hashes.json"
    with manifest_path.open(encoding="utf-8") as source:
        raw: object = json.load(source)
    if not isinstance(raw, dict) or not raw:
        raise IntegrityError("The original artifact inventory is invalid.")
    manifest: dict[str, str] = {}
    for relative, digest in raw.items():
        if not isinstance(relative, str) or not isinstance(digest, str):
            raise IntegrityError("Artifact inventory values must be strings.")
        if (len(digest) != 64
                or any(c not in "0123456789abcdef" for c in digest)):
            raise IntegrityError(f"Invalid recorded digest: {relative}")
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT):
            raise IntegrityError("An artifact path leaves the project folder.")
        manifest[relative] = digest
    if ORIGINAL_WHEEL not in manifest:
        raise IntegrityError("The original wheel is missing from inventory.")
    return manifest


def _read_record(data: bytes) -> dict[str, tuple[str, str]]:
    """Read wheel RECORD rows as filename, digest and decimal size."""
    rows: dict[str, tuple[str, str]] = {}
    try:
        reader = csv.reader(io.StringIO(data.decode("utf-8")))
        for row in reader:
            if len(row) != 3 or row[0] in rows:
                raise IntegrityError("A dependency RECORD file is invalid.")
            rows[row[0]] = (row[1], row[2])
    except csv.Error as error:
        raise IntegrityError("A RECORD file is unreadable.") from error
    return rows


def _record_digest(data: bytes) -> str:
    """Encode a SHA-256 digest in the URL-safe form used by wheel RECORD."""
    encoded = base64.urlsafe_b64encode(hashlib.sha256(data).digest())
    return "sha256=" + encoded.decode("ascii").rstrip("=")


def _verify_installed_package(wheel: Path) -> None:
    """Compare installed original members and validate both RECORD files.

    Pip adds installer information and bytecode rows to installed RECORD.
    Those additions are permitted; every original source and metadata member
    except RECORD itself must remain byte-for-byte equal to the wheel.
    """
    distribution = metadata.distribution("mazegenerator")
    if distribution.version != "2.1.0":
        raise IntegrityError("Installed mazegenerator must be version 2.1.0.")
    with ZipFile(wheel) as archive:
        members = [
            name for name in archive.namelist() if not name.endswith("/")
        ]
        record_names = [
            name for name in members if name.endswith(".dist-info/RECORD")
        ]
        if len(record_names) != 1:
            raise IntegrityError("The assigned wheel has no unique RECORD.")
        record_name = record_names[0]
        original_record = _read_record(archive.read(record_name))
        installed_record_path = Path(
            str(distribution.locate_file(record_name))
        )
        installed_record = _read_record(installed_record_path.read_bytes())
        if installed_record.get(record_name) != ("", ""):
            raise IntegrityError("Installed RECORD has an invalid self row.")
        if set(original_record) != set(members):
            raise IntegrityError("Wheel RECORD does not list all members.")
        for name in members:
            member_path = PurePosixPath(name)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise IntegrityError("The wheel contains an unsafe path.")
            if name not in original_record:
                raise IntegrityError(f"Wheel RECORD is missing: {name}")
            if name == record_name:
                if original_record[name] != ("", ""):
                    raise IntegrityError("Wheel RECORD self row is invalid.")
                continue
            original = archive.read(name)
            expected = (_record_digest(original), str(len(original)))
            if original_record[name] != expected:
                raise IntegrityError(f"Wheel RECORD digest mismatch: {name}")
            installed_path = Path(str(distribution.locate_file(name)))
            installed = installed_path.read_bytes()
            if installed != original:
                raise IntegrityError(f"Installed file was modified: {name}")
            if installed_record.get(name) != expected:
                raise IntegrityError(f"Installed RECORD mismatch: {name}")
            if name.endswith(".py"):
                digest = hashlib.sha256(installed).hexdigest()
                print(f"OK installed SHA256 {digest} {name}")
        source_root = Path(str(distribution.locate_file("mazegenerator")))
        expected_sources = {
            name for name in members
            if name.startswith("mazegenerator/") and name.endswith(".py")
        }
        actual_sources = {
            "mazegenerator/" + path.relative_to(source_root).as_posix()
            for path in source_root.rglob("*.py")
        }
        if actual_sources != expected_sources:
            raise IntegrityError("Installed source inventory has changed.")
    print("OK installed source, metadata and RECORD match the assigned wheel.")


def verify() -> None:
    """Verify originals, the vendor copy and the installed dependency."""
    manifest = _load_manifest()
    for relative, expected in manifest.items():
        original = _artifact_path(relative)
        digest = _sha256(original)
        if digest != expected:
            raise IntegrityError(f"Original artifact changed: {relative}")
        print(f"OK original SHA256 {digest} {original}")
    vendor_digest = _sha256(ROOT / VENDOR_WHEEL)
    if vendor_digest != manifest[ORIGINAL_WHEEL]:
        raise IntegrityError("The vendor wheel differs from the original.")
    print(f"OK vendor SHA256 {vendor_digest} {VENDOR_WHEEL}")
    _verify_installed_package(_artifact_path(ORIGINAL_WHEEL))


def main() -> int:
    """Print a clear success or failure message without expected tracebacks."""
    try:
        verify()
    except (IntegrityError, OSError, ValueError, BadZipFile,
            metadata.PackageNotFoundError) as error:
        print(f"Integrity verification failed: {error}", file=sys.stderr)
        return 1
    print("Integrity verified: all original artifacts remain unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
