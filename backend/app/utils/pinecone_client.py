import logging

from pinecone import Pinecone

from app.config import settings

logger = logging.getLogger(__name__)

_client: Pinecone | None = None


def get_pinecone_client() -> Pinecone:
    global _client
    if _client is None:
        _client = Pinecone(api_key=settings.pinecone_api_key)
    return _client


def get_pinecone_index():
    """Return a handle to the configured Pinecone index."""
    pc = get_pinecone_client()
    return pc.Index(settings.pinecone_index_name)


def query_pinecone(
    vector: list[float],
    top_k: int = 3,
    namespace: str = "",
    include_metadata: bool = True,
) -> list[dict]:
    """Query the Pinecone index and return matches.

    Returns a list of dicts with keys: id, score, metadata.
    """
    index = get_pinecone_index()
    result = index.query(
        vector=vector,
        top_k=top_k,
        namespace=namespace,
        include_metadata=include_metadata,
    )
    matches = []
    for m in result.get("matches", []):
        matches.append({
            "id": m["id"],
            "score": m["score"],
            "metadata": m.get("metadata", {}),
        })
    return matches


def upsert_vectors(
    vectors: list[dict],
    namespace: str = "",
    batch_size: int = 100,
) -> None:
    """Upsert vectors into the Pinecone index.

    Each vector dict should have: id, values, metadata.
    """
    index = get_pinecone_index()
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i : i + batch_size]
        index.upsert(vectors=batch, namespace=namespace)
        logger.info("Upserted batch %d–%d", i, i + len(batch))
