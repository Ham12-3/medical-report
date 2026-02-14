"""WebSocket endpoint for real-time pipeline status streaming."""

import logging
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.agents.orchestrator import run_pipeline
from app.database import async_session
from app.models.report import Report
from app.utils.auth import decode_access_token

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/reports/{report_id}")
async def websocket_pipeline(websocket: WebSocket, report_id: UUID):
    """Stream pipeline status updates over WebSocket.

    Authentication is done via a ``token`` query parameter containing
    a valid JWT.  Once authenticated the pipeline runs and each agent
    step sends a JSON message of the form::

        {"type": "status", "step": "<name>", "status": "<in_progress|complete|...>"}

    On completion a ``pipeline_complete`` message is sent, followed by
    the WebSocket being closed.
    """
    await websocket.accept()

    # --- Authenticate via query parameter ---
    token = websocket.query_params.get("token")
    if not token:
        await websocket.send_json(
            {"type": "error", "detail": "Authentication required — pass ?token=<jwt>"}
        )
        await websocket.close()
        return

    try:
        payload = decode_access_token(token)
        user_id = payload["sub"]
    except Exception:
        await websocket.send_json({"type": "error", "detail": "Invalid token"})
        await websocket.close()
        return

    # --- Run pipeline inside a fresh DB session ---
    async with async_session() as db:
        # Verify the report belongs to the authenticated user
        result = await db.execute(
            select(Report).where(
                Report.id == report_id,
                Report.user_id == UUID(user_id),
            )
        )
        report = result.scalar_one_or_none()
        if not report:
            await websocket.send_json(
                {"type": "error", "detail": "Report not found"}
            )
            await websocket.close()
            return

        if not report.image_url:
            await websocket.send_json(
                {"type": "error", "detail": "Report has no uploaded image"}
            )
            await websocket.close()
            return

        # Callback that pushes updates to the WebSocket client
        async def status_callback(step: str, status: str) -> None:
            try:
                await websocket.send_json(
                    {"type": "status", "step": step, "status": status}
                )
            except Exception:
                pass  # Client may have disconnected

        try:
            await websocket.send_json(
                {"type": "pipeline_started", "report_id": str(report_id)}
            )

            pipeline_result = await run_pipeline(
                report_id=str(report_id),
                db=db,
                status_callback=status_callback,
            )

            # Reload to get final persisted state
            await db.refresh(report)

            await websocket.send_json(
                {
                    "type": "pipeline_complete",
                    "report_id": str(report_id),
                    "status": report.status,
                    "has_findings": pipeline_result.get("has_findings", True),
                    "safety_passed": pipeline_result.get("safety_passed"),
                    "retry_count": pipeline_result.get("retry_count", 0),
                }
            )
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected for report %s", report_id)
        except Exception as e:
            logger.error("Pipeline failed for report %s: %s", report_id, e)
            try:
                await websocket.send_json(
                    {"type": "error", "detail": str(e)}
                )
            except Exception:
                pass
        finally:
            try:
                await websocket.close()
            except Exception:
                pass
