"""Fetch specifically allowlisted public official PDFs for local full-text indexing.

Usage: python -m scripts.fetch_policy_sources --source all
The downloaded documents are ignored by git; catalog metadata stays shareable.
"""

import argparse
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from app.policy.kb import CATALOG_PATH, load_catalog

MAX_BYTES = 25 * 1024 * 1024
ALLOWED_HOSTS = {"www.uaelegislation.gov.ae", "ai.gov.ae"}
ALLOWED_SOURCE_IDS = {"UAE-PDPL-2021-FULL", "UAE-AI-STRATEGY-2031-FULL"}


def fetch_source(doc: dict) -> Path:
    if doc["id"] not in ALLOWED_SOURCE_IDS:
        raise ValueError("Source ID not allowlisted")
    url = doc["url"]
    if urlparse(url).scheme != "https" or urlparse(url).hostname not in ALLOWED_HOSTS:
        raise ValueError("Only known official HTTPS hosts are permitted")
    target = CATALOG_PATH.parent / "sources" / Path(doc["local_pdf"]).name
    target.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "Itqan-Policy-KB/1.0"})
    with urlopen(request, timeout=40) as response:
        if urlparse(response.geturl()).hostname not in ALLOWED_HOSTS:
            raise ValueError("Unexpected cross-domain redirect")
        content = response.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES or not content.startswith(b"%PDF-"):
        raise ValueError("Source was not a PDF or exceeds the 25 MB download limit")
    target.write_bytes(content)
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["all", *sorted(ALLOWED_SOURCE_IDS)], default="all")
    args = parser.parse_args()
    docs = [d for d in load_catalog() if d["id"] in ALLOWED_SOURCE_IDS]
    if args.source != "all":
        docs = [d for d in docs if d["id"] == args.source]
    failed = False
    for document in docs:
        try:
            print("Fetched:", fetch_source(document))
        except (HTTPError, URLError, ValueError, TimeoutError) as exc:
            failed = True
            print(f"Unavailable official source {document['id']}: {exc}. Download it manually from the listed government source if authorized.")
    if failed:
        sys.exit(1)
