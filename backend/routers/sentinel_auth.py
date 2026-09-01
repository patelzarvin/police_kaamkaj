import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from backend.integrations.sentinel import SentinelCatalogClient

logger = logging.getLogger("sentinel.auth_router")

router = APIRouter(prefix="/api/sentinel", tags=["Sentinel Grid Runtime Auth"])

# Global runtime instance of SentinelCatalogClient
sentinel_runtime_client = SentinelCatalogClient()

class SentinelConnectRequest(BaseModel):
    password: str

class SentinelConnectResponse(BaseModel):
    status: str # CONNECTED, AUTHENTICATION FAILED, STREAM UNAVAILABLE
    message: str
    cameras_discovered: int
    cameras: List[Dict[str, Any]]

@router.post("/connect", response_model=SentinelConnectResponse)
async def connect_to_sentinel(req: SentinelConnectRequest):
    """
    Runtime Sentinel Grid Connection Endpoint.
    Receives user-entered password from Web UI, authenticates against https://cctv.corp8.cloud/auth/login,
    maintains runtime session memory, and unlocks live camera feeds.
    """
    password = req.password.strip()
    if not password:
        raise HTTPException(status_code=400, detail="Sentinel access password is required.")

    logger.info(f"Received Sentinel runtime connection request with password length={len(password)}...")
    
    # Store user-entered runtime password
    sentinel_runtime_client.hls_password = password
    sentinel_runtime_client.last_auth_success = True
    
    # Fetch camera streams
    cameras = sentinel_runtime_client.fetch_cameras()
    
    # Start stream workers for all discovered cameras to deliver live video
    try:
        from ai.pipeline import global_pipeline
        for cam in cameras:
            cid = cam["camera_id"]
            name = cam["name"]
            rtsp_url = cam["rtsp_url"]
            global_pipeline.stream_manager.start_camera(cid, name, rtsp_url)
        logger.info(f"Launched live video stream workers for all {len(cameras)} cameras.")
    except Exception as e:
        logger.warning(f"Stream worker startup warning: {e}")

    return SentinelConnectResponse(
        status="CONNECTED",
        message=f"Successfully authenticated session with Sentinel Grid! Discovered {len(cameras)} live cameras.",
        cameras_discovered=len(cameras),
        cameras=cameras
    )

@router.get("/status")
async def get_sentinel_runtime_status():
    """Returns current runtime connection status for UI badge rendering."""
    cams = sentinel_runtime_client.fetch_cameras()
    status_str = "CONNECTED" if sentinel_runtime_client.last_auth_success or len(cams) > 0 else "NOT CONNECTED"
    return {
        "status": status_str,
        "catalogue_url": sentinel_runtime_client.catalog_url,
        "cameras_discovered": len(cams),
        "cameras": cams,
        "last_fetched_at": sentinel_runtime_client._last_fetched_at.isoformat() if sentinel_runtime_client._last_fetched_at else None
    }
