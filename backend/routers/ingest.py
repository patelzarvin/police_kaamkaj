from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any

from backend.database import get_db
from backend.models import Camera

router = APIRouter(prefix="/api", tags=["Sentinel Ingest Contract"])

@router.get("/ingest", response_model=List[Dict[str, Any]])
async def get_sentinel_camera_catalog(db: AsyncSession = Depends(get_db)):
    """
    Official Sentinel Sandbox Ingestion Catalogue Endpoint Contract.
    Returns every camera with its id, location, codec, live status, stream properties, and all three URLs:
    - RTSP: rtsp://<host>:8554/stream/<id>
    - WebRTC (WHEP): http://<host>:8889/stream/<id>/whep
    - HLS: http://<host>/live/stream/<id>/index.m3u8
    """
    stmt = select(Camera)
    result = await db.execute(stmt)
    cameras = result.scalars().all()

    catalog = []
    for cam in cameras:
        cam_key = cam.camera_id.lower().replace("-", "")
        catalog.append({
            "id": cam.camera_id,
            "name": cam.name,
            "location": {
                "lat": cam.latitude,
                "lng": cam.longitude,
                "city": cam.city,
                "district": cam.district,
                "address": cam.address
            },
            "codec": cam.codec or "H264",
            "live": cam.status.upper() == "ONLINE",
            "rtsp_url": cam.rtsp_url or f"rtsp://localhost:8554/stream/{cam_key}",
            "whep_url": cam.webrtc_url or f"http://localhost:8889/stream/{cam_key}/whep",
            "hls_url": cam.hls_url or f"http://localhost:8000/live/stream/{cam_key}/index.m3u8",
            "stream_properties": {
                "resolution": cam.resolution or "1920x1080",
                "declared_fps": cam.fps or 25,
                "transport": "tcp",
                "depayloader": "rtph264depay" if (cam.codec or "H264").upper() == "H264" else "rtph265depay",
                "pts_monotonic": True,
                "reconnect_exponential_backoff": True
            }
        })
    return catalog
