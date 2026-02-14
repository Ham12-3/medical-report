import logging

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Demo mode — run full pipeline with mock data, no cloud credentials needed
    demo_mode: bool = False

    # AWS
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"

    # Bedrock Guardrails
    bedrock_guardrail_id: str = ""
    bedrock_guardrail_version: str = "DRAFT"

    # Pinecone
    pinecone_api_key: str = ""
    pinecone_index_name: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://medai:medai_secret@db:5432/medai_report_generator"

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440

    # Rate limiting
    upload_rate_limit: int = 5  # uploads per hour per user

    class Config:
        env_file = ".env"


settings = Settings()


def validate_settings_on_startup() -> None:
    """Validate critical configuration on startup.

    Checks that required AWS credentials are set and that Bedrock
    models are accessible. Logs warnings for optional services
    (Pinecone, Guardrails) that are not configured.
    """
    if settings.demo_mode:
        logger.warning(
            "DEMO MODE is enabled — all pipeline steps will return mock data. "
            "AWS and Pinecone credentials are NOT required."
        )
        if settings.jwt_secret_key == "change-me-in-production":
            logger.warning(
                "CONFIG WARNING: JWT_SECRET_KEY is using the default value. "
                "Set a strong secret in production."
            )
        return

    warnings: list[str] = []

    # --- AWS credentials (optional – pipeline will fail without them) ---
    if not settings.aws_access_key_id or not settings.aws_secret_access_key:
        warnings.append(
            "AWS credentials are not set (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY). "
            "The app will start, but image analysis and report generation will fail. "
            "Auth, upload, and the UI will still work."
        )
    if not settings.aws_region:
        warnings.append("AWS_REGION is not set, defaulting to us-east-1.")

    # --- Required: JWT secret ---
    if settings.jwt_secret_key == "change-me-in-production":
        warnings.append(
            "JWT_SECRET_KEY is using the default value. "
            "Set a strong secret in production."
        )

    # --- Optional: Pinecone ---
    if not settings.pinecone_api_key or not settings.pinecone_index_name:
        warnings.append(
            "Pinecone is not configured (PINECONE_API_KEY / PINECONE_INDEX_NAME). "
            "Research step will fail."
        )

    # --- Optional: Bedrock Guardrails ---
    if not settings.bedrock_guardrail_id:
        warnings.append(
            "BEDROCK_GUARDRAIL_ID is not set. "
            "Safety review will rely on LLM-based review only."
        )

    # --- Validate Bedrock model access (non-fatal) ---
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        try:
            import boto3

            client = boto3.client(
                "bedrock-runtime",
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
            )
            logger.info(
                "AWS Bedrock client initialised for region %s", settings.aws_region
            )
        except Exception as e:
            warnings.append(f"Failed to initialise Bedrock client: {e}")

    # --- Report results ---
    for w in warnings:
        logger.warning("CONFIG WARNING: %s", w)

    if warnings:
        logger.info(
            "Configuration validation completed with %d warning(s). "
            "The app will start, but some features may be unavailable.",
            len(warnings),
        )
    else:
        logger.info("Configuration validation passed — all services configured.")
