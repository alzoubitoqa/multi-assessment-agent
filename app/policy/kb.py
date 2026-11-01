"""Policy KB with labelled seed summaries and optional official PDF ingestion."""

import json
import re
from pathlib import Path
from config import CHROMA_DIR, DATA_DIR

CATALOG_PATH = DATA_DIR / "policies" / "catalog.json"
POLICY_COLLECTION = "official_policy_sources"


def load_catalog(catalog_path: Path = CATALOG_PATH) -> list[dict]:
    documents = json.loads(catalog_path.read_text(encoding="utf-8"))
    required = {"id", "title", "jurisdiction", "reference", "url", "text",
                "source_kind", "binding_level"}
    ids = set()
    for document in documents:
        missing = required.difference(document)
        if missing:
            raise ValueError(f"Policy record missing fields: {sorted(missing)}")
        if document["id"] in ids or not document["url"].startswith("https://"):
            raise ValueError(f"Duplicate policy ID or invalid URL: {document['id']}")
        ids.add(document["id"])
    return documents


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def _lexical_search(query: str, documents: list[dict], limit: int) -> list[dict]:
    tokens = _tokens(query) - {"a", "an", "the", "of", "to", "for", "in", "and", "what", "should"}
    ranked = []
    for doc in documents:
        content = _tokens(doc["text"] + " " + doc["title"])
        topics = _tokens(" ".join(doc.get("topics", [])))
        score = len(tokens & content) + 3 * len(tokens & topics)
        if score:
            ranked.append((score, doc))
    ranked.sort(key=lambda entry: (-entry[0], entry[1]["id"]))
    return [{**item, "retrieval_mode": "lexical"} for _, item in ranked[:limit]]


def search_policies(query: str, jurisdiction: str = "UAE", limit: int = 4,
                    use_vector: bool = True) -> list[dict]:
    """Retrieve provenance-bearing evidence; never assume a law automatically applies."""
    docs = [doc for doc in load_catalog()
            if doc["jurisdiction"] in {jurisdiction, "GLOBAL"}
            and not doc.get("comparison_only")]
    if not use_vector:
        return _lexical_search(query, [d for d in docs if d["source_kind"] != "catalog_metadata"], limit)
    try:
        import chromadb
        collection = chromadb.PersistentClient(path=str(CHROMA_DIR)).get_or_create_collection(POLICY_COLLECTION)
        if collection.count() == 0:
            return _lexical_search(query, [d for d in docs if d["source_kind"] != "catalog_metadata"], limit)
        from app.ingestion.embedder import _model
        result = collection.query(query_embeddings=[_model.encode([query]).tolist()[0]],
                                  n_results=min(collection.count(), max(limit * 5, limit)))
        by_id = {doc["id"]: doc for doc in docs}
        found = []
        for record_id, metadata, snippet in zip(result["ids"][0], result["metadatas"][0], result["documents"][0]):
            policy_id = metadata["policy_id"]
            if metadata["source_kind"] == "catalog_metadata":
                continue
            if policy_id in by_id:
                found.append({**by_id[policy_id], "text": snippet, "record_id": record_id,
                              "retrieval_mode": "vector", "source_kind": metadata["source_kind"],
                              "page_number": metadata.get("page_number", 0)})
        return found[:limit] or _lexical_search(
            query, [d for d in docs if d["source_kind"] != "catalog_metadata"], limit
        )
    except (ImportError, RuntimeError, OSError):
        return _lexical_search(query, [d for d in docs if d["source_kind"] != "catalog_metadata"], limit)


def search_global_examples(query: str, limit: int = 3) -> list[dict]:
    """Comparative international/foreign examples, never automatic UAE obligations."""
    docs = [doc for doc in load_catalog() if doc.get("comparison_only")]
    return _lexical_search(query + " global comparison education", docs, limit)


def index_policy_documents(include_local_pdfs: bool = True) -> dict:
    """Vectorize summaries and optional PDFs provided at data/policies/sources/.

    To index an official document, add `local_pdf` to the catalog record and
    place that PDF in sources/. The app does not auto-download legal material.
    """
    import chromadb
    from app.ingestion.embedder import _model
    from app.ingestion.splitter import split_pages

    collection = chromadb.PersistentClient(path=str(CHROMA_DIR)).get_or_create_collection(POLICY_COLLECTION)
    rows, missing_pdfs = [], []
    for doc in load_catalog():
        if doc["source_kind"] == "curated_summary":
            rows.append((doc["id"] + "-summary", doc["text"], doc, 0, "curated_summary"))
        file_name = doc.get("local_pdf")
        if not include_local_pdfs or not file_name:
            continue
        path = CATALOG_PATH.parent / "sources" / Path(file_name).name
        if not path.is_file():
            missing_pdfs.append(str(path))
            continue
        from app.ingestion.loader import load_pdf
        for chunk in split_pages(load_pdf(path)):
            rows.append((doc["id"] + "-" + chunk["chunk_id"], chunk["text"],
                         doc, chunk["page_number"], "official_pdf"))
    for i in range(0, len(rows), 64):
        batch = rows[i:i + 64]
        collection.upsert(
            ids=[r[0] for r in batch], documents=[r[1] for r in batch],
            embeddings=_model.encode([r[1] for r in batch], show_progress_bar=False).tolist(),
            metadatas=[{"policy_id": r[2]["id"], "jurisdiction": r[2]["jurisdiction"],
                        "source_url": r[2]["url"], "reference": r[2]["reference"],
                        "source_kind": r[4], "page_number": r[3]} for r in batch],
        )
    return {"records_indexed": len(rows), "missing_pdfs": missing_pdfs,
            "collection": POLICY_COLLECTION}
