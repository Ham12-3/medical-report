import asyncio
import logging
import random
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)

PRIMARY_MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
FALLBACK_VISION_MODEL_ID = "amazon.nova-pro-v1:0"

# Retry configuration
MAX_RETRIES = 3
BASE_DELAY = 1.0  # seconds
MAX_DELAY = 30.0  # seconds

# Error codes that are retryable
RETRYABLE_ERROR_CODES = {
    "ThrottlingException",
    "TooManyRequestsException",
    "ServiceUnavailableException",
    "ModelTimeoutException",
    "ModelStreamErrorException",
    "InternalServerException",
}


def get_bedrock_client():
    if settings.demo_mode:
        return None
    return boto3.client(
        "bedrock-runtime",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


def _is_retryable(error: ClientError) -> bool:
    """Check if a Bedrock error is retryable."""
    error_code = error.response.get("Error", {}).get("Code", "")
    return error_code in RETRYABLE_ERROR_CODES


def _get_error_message(error: ClientError) -> str:
    """Extract a user-friendly error message from a Bedrock ClientError."""
    error_code = error.response.get("Error", {}).get("Code", "")
    error_msg = error.response.get("Error", {}).get("Message", str(error))

    if error_code == "ThrottlingException":
        return "Service is temporarily rate-limited. Please try again in a moment."
    if error_code in ("ModelTimeoutException", "ModelStreamErrorException"):
        return "The AI model timed out processing your request. Please try again."
    if error_code == "AccessDeniedException":
        return "Access denied to the AI model. Please check AWS credentials and model access."
    if error_code == "ValidationException":
        return f"Invalid request to AI model: {error_msg}"
    if error_code == "ResourceNotFoundException":
        return "The AI model is not available in the configured region."
    return f"AI service error ({error_code}): {error_msg}"


async def _retry_with_backoff(func, *args, max_retries: int = MAX_RETRIES, **kwargs):
    """Execute a synchronous boto3 call with exponential backoff retry.

    Only retries on transient/throttling errors. Raises immediately on
    non-retryable errors like AccessDenied or ValidationException.
    """
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except ClientError as e:
            last_error = e
            error_code = e.response.get("Error", {}).get("Code", "")

            if not _is_retryable(e):
                logger.error(
                    "Non-retryable Bedrock error (attempt %d/%d): [%s] %s",
                    attempt + 1, max_retries + 1, error_code, e,
                )
                raise

            if attempt < max_retries:
                delay = min(BASE_DELAY * (2 ** attempt) + random.uniform(0, 1), MAX_DELAY)
                logger.warning(
                    "Retryable Bedrock error (attempt %d/%d): [%s] %s — retrying in %.1fs",
                    attempt + 1, max_retries + 1, error_code, e, delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "Bedrock call failed after %d attempts: [%s] %s",
                    max_retries + 1, error_code, e,
                )

    raise last_error


def _build_text_message(text: str) -> dict:
    return {
        "role": "user",
        "content": [{"text": text}],
    }


def _build_multimodal_message(text: str, image_bytes: bytes, media_type: str) -> dict:
    return {
        "role": "user",
        "content": [
            {
                "image": {
                    "format": media_type.split("/")[-1],
                    "source": {"bytes": image_bytes},
                },
            },
            {"text": text},
        ],
    }


async def converse_with_retry(
    client,
    model_id: str,
    messages: list,
    system: list,
    inference_config: dict,
) -> dict:
    """Call client.converse() with retry logic for transient errors."""
    return await _retry_with_backoff(
        client.converse,
        modelId=model_id,
        messages=messages,
        system=system,
        inferenceConfig=inference_config,
    )


async def invoke_model_with_retry(
    client,
    model_id: str,
    content_type: str,
    accept: str,
    body: str,
) -> dict:
    """Call client.invoke_model() with retry logic for transient errors."""
    return await _retry_with_backoff(
        client.invoke_model,
        modelId=model_id,
        contentType=content_type,
        accept=accept,
        body=body,
    )


async def invoke_bedrock(
    prompt: str,
    system_prompt: Optional[str] = None,
    image_bytes: Optional[bytes] = None,
    media_type: str = "image/jpeg",
    max_tokens: int = 4096,
    temperature: float = 0.3,
) -> str:
    """Call the Bedrock Converse API with text-only or multimodal input.

    Uses Claude Sonnet 4.5 as the primary model. Falls back to Amazon Nova Pro
    for vision tasks if the primary model fails.

    Includes retry logic with exponential backoff for transient errors.
    """
    client = get_bedrock_client()

    if image_bytes:
        message = _build_multimodal_message(prompt, image_bytes, media_type)
    else:
        message = _build_text_message(prompt)

    system = [{"text": system_prompt}] if system_prompt else []
    inference_config = {"maxTokens": max_tokens, "temperature": temperature}

    # Try primary model first
    model_id = PRIMARY_MODEL_ID
    try:
        response = await converse_with_retry(
            client, model_id, [message], system, inference_config
        )
        return _extract_text(response)
    except ClientError as e:
        logger.warning("Primary model (%s) failed: %s", model_id, e)
        if not image_bytes:
            raise

    # Fallback to Nova Pro for vision tasks
    model_id = FALLBACK_VISION_MODEL_ID
    logger.info("Falling back to vision model: %s", model_id)
    try:
        response = await converse_with_retry(
            client, model_id, [message], system, inference_config
        )
        return _extract_text(response)
    except ClientError as e:
        logger.error("Fallback vision model (%s) also failed: %s", model_id, e)
        raise


def _extract_text(response: dict) -> str:
    output = response.get("output", {})
    message = output.get("message", {})
    content = message.get("content", [])
    parts = [block["text"] for block in content if "text" in block]
    return "\n".join(parts)
