from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional

from backend.config import settings
from stream_gateway.stream_manager import StreamManager
from backend.models import Camera

router = APIRouter(prefix="/api/sentinel", tags=["Sentinel Live Sandbox Integration"])

class CredentialsRequest(BaseModel):
    username: Optional[str] = ""
    password: Optional[str] = ""
    auth_token: Optional[str] = ""
    sentinel_host: Optional[str] = "https://live.corp8.cloud"

@router.get("/status")
async def get_sentinel_live_status():
    """
    Requirement 15: Backend health/status endpoint for Sentinel Sandbox Integration.
    Shows catalogue reachability, cameras discovered, live cameras, connected streams, frames received, and auth/connection errors.
    """
    from backend.main import stream_manager
    status = stream_manager.get_sentinel_status()
    return status

@router.post("/credentials")
async def update_sentinel_credentials(creds: CredentialsRequest):
    """
    Requirement 17: Single configuration point to update Sentinel Sandbox credentials.
    Updates in-memory settings and triggers a re-fetch of authorized live camera streams.
    """
    if creds.username:
        settings.SENTINEL_USERNAME = creds.username
    if creds.password:
        settings.SENTINEL_PASSWORD = creds.password
    if creds.auth_token:
        settings.SENTINEL_AUTH_TOKEN = creds.auth_token
    if creds.sentinel_host:
        settings.SENTINEL_HOST = creds.sentinel_host

    from backend.main import stream_manager
    cams = stream_manager.refresh_sentinel_catalogue()

    return {
        "status": "SUCCESS",
        "message": "Sentinel Sandbox credentials updated.",
        "sentinel_host": settings.SENTINEL_HOST,
        "cameras_discovered": len(cams)
    }
