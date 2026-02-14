#!/usr/bin/env python3
"""Seed the Pinecone knowledge base from a folder of medical text/PDF files.

Usage:
    python -m scripts.seed_knowledge_base /path/to/docs [--namespace medical]

Each file is read, split into ~500-token chunks with 50-token overlap,
embedded via Amazon Titan Embeddings v2, and upserted into Pinecone.
"""

import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path

import tiktoken
from PyPDF2 import PdfReader

# Ensure the app package is importable when running from /app
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.utils.embeddings import generate_embedding_sync
from app.utils.pinecone_client import upsert_vectors

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

CHUNK_SIZE = 500       # tokens
CHUNK_OVERLAP = 50     # tokens
ENCODING_NAME = "cl100k_base"  # tiktoken encoding compatible with most models


# ------------------------------------------------------------------
# File reading
# ------------------------------------------------------------------

def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def read_pdf_file(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n\n".join(pages)


def read_file(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return read_pdf_file(path)
    if ext in (".txt", ".md", ".csv", ".json"):
        return read_text_file(path)
    logger.warning("Skipping unsupported file type: %s", path)
    return ""


# ------------------------------------------------------------------
# Chunking
# ------------------------------------------------------------------

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into token-based chunks with overlap."""
    enc = tiktoken.get_encoding(ENCODING_NAME)
    tokens = enc.encode(text)

    if len(tokens) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        chunk_text = enc.decode(chunk_tokens)
        chunks.append(chunk_text)
        start += chunk_size - overlap

    return chunks


# ------------------------------------------------------------------
# Processing
# ------------------------------------------------------------------

def process_file(path: Path, namespace: str) -> list[dict]:
    """Read, chunk, embed, and return Pinecone vectors for a single file."""
    text = read_file(path)
    if not text.strip():
        logger.info("  Skipping empty file: %s", path.name)
        return []

    chunks = chunk_text(text)
    logger.info("  %s → %d chunks", path.name, len(chunks))

    vectors = []
    for i, chunk in enumerate(chunks):
        # Deterministic ID based on file + chunk index
        chunk_id = hashlib.sha256(f"{path.name}::{i}".encode()).hexdigest()[:16]

        try:
            embedding = generate_embedding_sync(chunk)
        except Exception as e:
            logger.error("  Embedding failed for chunk %d of %s: %s", i, path.name, e)
            continue

        vectors.append({
            "id": chunk_id,
            "values": embedding,
            "metadata": {
                "source_file": path.name,
                "chunk_index": i,
                "text": chunk,  # store the text for retrieval
            },
        })

    return vectors


def seed(folder: str, namespace: str = "") -> None:
    folder_path = Path(folder)
    if not folder_path.is_dir():
        logger.error("Not a directory: %s", folder)
        sys.exit(1)

    files = sorted(
        p for p in folder_path.iterdir()
        if p.is_file() and p.suffix.lower() in (".txt", ".md", ".csv", ".json", ".pdf")
    )

    if not files:
        logger.error("No supported files found in %s", folder)
        sys.exit(1)

    logger.info("Found %d files in %s", len(files), folder)

    all_vectors = []
    for path in files:
        vectors = process_file(path, namespace)
        all_vectors.extend(vectors)

    if not all_vectors:
        logger.error("No vectors generated. Nothing to upsert.")
        sys.exit(1)

    logger.info("Upserting %d vectors into Pinecone (namespace=%r)...", len(all_vectors), namespace)
    upsert_vectors(all_vectors, namespace=namespace)
    logger.info("Done. %d vectors upserted.", len(all_vectors))


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Seed the Pinecone knowledge base with medical documents."
    )
    parser.add_argument(
        "folder",
        help="Path to folder containing .txt, .md, or .pdf files",
    )
    parser.add_argument(
        "--namespace",
        default="medical",
        help="Pinecone namespace (default: medical)",
    )
    args = parser.parse_args()
    seed(args.folder, args.namespace)


if __name__ == "__main__":
    main()
