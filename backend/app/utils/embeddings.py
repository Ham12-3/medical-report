import json
import logging

from app.utils.bedrock_client import get_bedrock_client, invoke_model_with_retry

logger = logging.getLogger(__name__)

TITAN_EMBED_MODEL_ID = "amazon.titan-embed-text-v2:0"
EMBEDDING_DIMENSION = 1024  # Titan v2 default


async def generate_embedding(text: str) -> list[float]:
    """Generate an embedding vector using Amazon Titan Embeddings v2.

    Uses the Bedrock InvokeModel API with retry logic for transient errors.
    """
    client = get_bedrock_client()

    body = json.dumps({
        "inputText": text,
        "dimensions": EMBEDDING_DIMENSION,
        "normalize": True,
    })

    response = await invoke_model_with_retry(
        client,
        model_id=TITAN_EMBED_MODEL_ID,
        content_type="application/json",
        accept="application/json",
        body=body,
    )

    result = json.loads(response["body"].read())
    return result["embedding"]


def generate_embedding_sync(text: str) -> list[float]:
    """Synchronous version of generate_embedding for use in CLI scripts."""
    client = get_bedrock_client()

    body = json.dumps({
        "inputText": text,
        "dimensions": EMBEDDING_DIMENSION,
        "normalize": True,
    })

    response = client.invoke_model(
        modelId=TITAN_EMBED_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=body,
    )

    result = json.loads(response["body"].read())
    return result["embedding"]


async def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts.

    Titan Embeddings v2 doesn't support native batching, so we call
    one at a time.
    """
    embeddings = []
    for i, text in enumerate(texts):
        try:
            emb = await generate_embedding(text)
            embeddings.append(emb)
        except Exception as e:
            logger.error("Embedding failed for chunk %d: %s", i, e)
            # Append zero vector so indices stay aligned
            embeddings.append([0.0] * EMBEDDING_DIMENSION)
    return embeddings
