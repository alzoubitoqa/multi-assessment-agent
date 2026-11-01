"""Package all git-tracked project code and optional official UAE law PDF.

Usage: python -m scripts.package_submission
The archive intentionally omits .env credentials, databases, Chroma indexes and
virtual environments. It includes the report and reproducible Windows guide.
"""

import argparse
import hashlib
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT.parent / "Itqan_ITU_Complete_Update_2026-11-01.zip"
ARCHIVE_ROOT = "micro-assessment-agent"
OPTIONAL_SOURCE = Path("data/policies/sources/UAE_PDPL_2021.pdf")


def package(output: Path, include_official_pdf: bool = True) -> dict:
    output = output.resolve()
    tracked = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, check=True,
                             capture_output=True).stdout
    paths = [Path(name.decode("utf-8")) for name in tracked.split(b"\0") if name]
    excludes = {".env", "data/sessions.db"}
    files = []
    for relative in paths:
        if str(relative) in excludes or relative.suffix in {".db", ".sqlite", ".pyc"}:
            continue
        if (ROOT / relative).is_file():
            files.append(relative)
    if include_official_pdf and (ROOT / OPTIONAL_SOURCE).is_file():
        files.append(OPTIONAL_SOURCE)
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
        for relative in sorted(set(files)):
            archive.write(ROOT / relative, arcname=f"{ARCHIVE_ROOT}/{relative.as_posix()}")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    return {"archive": str(output), "files": len(set(files)),
            "size_bytes": output.stat().st_size, "sha256": digest,
            "official_pdf_included": OPTIONAL_SOURCE in files}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--without-local-pdf", action="store_true")
    args = parser.parse_args()
    for key, value in package(args.output, not args.without_local_pdf).items():
        print(f"{key}: {value}")
