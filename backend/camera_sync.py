"""Sync Sentinel camera catalogue into the database on startup."""
import logging
from sqlalchemy import select

from backend.database import AsyncSessionLocal
from backend.models import Camera
from backend.integrations.sentinel import SentinelCatalogClient

logger = logging.getLogger("sentinel.camera_sync")


async def sync_sentinel_catalog_to_db() -> int:
    client = SentinelCatalogClient()
    catalog = client.fetch_cameras()
    if not catalog:
        return 0

    added = 0
    async with AsyncSessionLocal() as db:
        for cam in catalog:
            cid = cam["camera_id"]
            existing = await db.execute(select(Camera).where(Camera.camera_id == cid))
            if existing.scalar_one_or_none():
                continue
            db.add(Camera(
                camera_id=cid,
                name=cam.get("name", cid),
                department="Home Department",
                district=cam.get("district", "Ahmedabad"),
                city=cam.get("city", "Ahmedabad"),
                latitude=float(cam.get("latitude", 23.0225)),
                longitude=float(cam.get("longitude", 72.5714)),
                address=cam.get("address", cam.get("name", cid)),
                stream_type="RTSP",
                rtsp_url=cam.get("rtsp_url"),
                hls_url=cam.get("hls_url"),
                webrtc_url=cam.get("webrtc_url"),
                codec=cam.get("codec", "H264"),
                resolution=cam.get("resolution", "1920x1080"),
                fps=float(cam.get("fps", 25.0)),
                status=cam.get("status", "ONLINE"),
            ))
            added += 1
        await db.commit()

    logger.info("Sentinel catalog sync complete: %s new cameras in registry", added)
    return added
