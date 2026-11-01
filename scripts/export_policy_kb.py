"""Export a portable, source-attributed ITU education-policy knowledge base.

From the repository root:
    python -B -m scripts.export_policy_kb --output ../ITQAN_Policy_KB \
        --zip ../ITQAN_ITU_Policy_Knowledge_Base.zip

This is an offline export. It neither uploads data nor claims ITU Lab access.
"""

import argparse
import csv
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from app.policy.kb import CATALOG_PATH, POLICY_COLLECTION, load_catalog


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CODE_FILES = (
    "config.py",
    "requirements-kb.txt",
    "app/__init__.py",
    "app/policy/__init__.py",
    "app/policy/kb.py",
    "app/ingestion/__init__.py",
    "app/ingestion/loader.py",
    "app/ingestion/splitter.py",
    "app/ingestion/embedder.py",
    "scripts/__init__.py",
    "scripts/fetch_policy_sources.py",
    "scripts/ingest_policies.py",
    "scripts/export_policy_kb.py",
)
PROVENANCE_FIELDS = (
    "id", "title", "authority", "jurisdiction", "document_type", "reference",
    "source_kind", "binding_level", "comparison_only", "url", "local_pdf",
    "local_pdf_included",
)


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _copy_relative(src: Path, destination: Path, relative_path: Path) -> None:
    target = destination / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, target)


def _base_record(doc: dict) -> dict:
    return {
        "policy_id": doc["id"],
        "title": doc["title"],
        "authority": doc.get("authority", ""),
        "jurisdiction": doc["jurisdiction"],
        "document_type": doc.get("document_type", ""),
        "reference": doc["reference"],
        "source_url": doc["url"],
        "binding_level": doc["binding_level"],
        "comparison_only": bool(doc.get("comparison_only", False)),
        "topics": doc.get("topics", []),
    }


def export_knowledge_base(output: Path, archive: Path | None = None,
                          include_pdfs: bool = True) -> dict:
    """Write portable JSONL, provenance, included PDF sources, and a manifest.

    JSONL chunk IDs agree with app.policy.kb.index_policy_documents so source
    citations remain reviewable when the vector index is rebuilt locally.
    """
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    documents = load_catalog()
    _copy_relative(CATALOG_PATH, output, Path("data/policies/catalog.json"))

    for relative in CODE_FILES:
        source = PROJECT_ROOT / relative
        if source.is_file():
            _copy_relative(source, output, Path(relative))
    _copy_relative(PROJECT_ROOT / "docs/KNOWLEDGE_BASE_SUBMISSION.md", output,
                   Path("README_KNOWLEDGE_BASE.md"))

    records = []
    for document in documents:
        if document["source_kind"] == "curated_summary":
            records.append({
                **_base_record(document),
                "record_id": f"{document['id']}-summary",
                "source_kind": "curated_summary",
                "page_number": None,
                "text": document["text"],
            })

    official_sources = []
    missing_pdfs = []
    provenance = []
    for document in documents:
        filename = document.get("local_pdf", "")
        source = CATALOG_PATH.parent / "sources" / Path(filename).name if filename else None
        available = bool(include_pdfs and source and source.is_file())
        provenance.append({key: document.get(key, "") for key in PROVENANCE_FIELDS}
                          | {"local_pdf_included": available})
        if not filename or not include_pdfs:
            continue
        if not available:
            missing_pdfs.append({"id": document["id"], "filename": filename,
                                 "official_url": document["url"]})
            continue
        assert source is not None
        with source.open("rb") as handle:
            if handle.read(5) != b"%PDF-":
                raise ValueError(f"Invalid PDF header: {source}")

        from app.ingestion.loader import load_pdf
        from app.ingestion.splitter import split_pages

        pages = load_pdf(source)
        chunks = split_pages(pages)
        for chunk in chunks:
            records.append({
                **_base_record(document),
                "record_id": f"{document['id']}-{chunk['chunk_id']}",
                "source_kind": "official_pdf",
                "page_number": chunk["page_number"],
                "source_filename": filename,
                "text": chunk["text"],
            })
        _copy_relative(source, output, Path("data/policies/sources") / filename)
        official_sources.append({
            "id": document["id"],
            "filename": filename,
            "official_url": document["url"],
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "size_bytes": source.stat().st_size,
            "text_pages": len(pages),
            "text_chunks": len(chunks),
        })

    records_path = output / "data/policies/exports/records.jsonl"
    records_path.parent.mkdir(parents=True, exist_ok=True)
    with records_path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    provenance_path = output / "data/policies/exports/provenance.csv"
    with provenance_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PROVENANCE_FIELDS)
        writer.writeheader()
        writer.writerows(provenance)

    manifest = {
        "title": "ITQAN education policy knowledge base - portable export",
        "exported_at_utc": datetime.now(timezone.utc).isoformat(),
        "catalog_records": len(documents),
        "curated_summary_records": sum(d["source_kind"] == "curated_summary" for d in documents),
        "metadata_only_records": sum(d["source_kind"] == "catalog_metadata" for d in documents),
        "indexable_text_records": len(records),
        "official_pdf_text_records": sum(r["source_kind"] == "official_pdf" for r in records),
        "official_sources_included": official_sources,
        "missing_official_pdfs": missing_pdfs,
        "local_vector_collection": POLICY_COLLECTION,
        "embedding_model": "all-MiniLM-L6-v2 (configurable via EMBEDDING_MODEL)",
        "vector_index_included": False,
        "itu_distributed_kb_uploaded": False,
        "itu_integration_status": "not integrated; ITU AI for Good Lab access and ingestion interface required",
        "legal_applicability": "not determined automatically; verify jurisdiction, scope and updates",
    }
    _write_json(output / "data/policies/exports/manifest.json", manifest)

    if archive is not None:
        archive = archive.resolve()
        if archive.is_relative_to(output):
            raise ValueError("ZIP must be outside the exported directory")
        archive.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED,
                             compresslevel=6) as zip_file:
            for file_path in sorted(output.rglob("*")):
                if file_path.is_file():
                    zip_file.write(file_path, Path("ITQAN_Policy_Knowledge_Base") /
                                   file_path.relative_to(output))
        manifest["zip_path"] = str(archive)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True,
                        help="Directory for the portable KB (outside the repository recommended)")
    parser.add_argument("--zip", type=Path, default=None, help="Optional submission ZIP path")
    parser.add_argument("--no-pdfs", action="store_true",
                        help="Create a small metadata/summary-only export")
    options = parser.parse_args()
    result = export_knowledge_base(options.output, options.zip,
                                   include_pdfs=not options.no_pdfs)
    print(json.dumps(result, ensure_ascii=False, indent=2))
