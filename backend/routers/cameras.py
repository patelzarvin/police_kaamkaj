import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from backend.database import get_db
from backend.models import Camera, CameraHealth
from backend.schemas import CameraResponse, CameraHealthResponse
from backend.config import settings
from backend.demo_mode import RENDER_DEMO_MODE
from database.seeds.seed_data import CAMERAS_DATA

router = APIRouter(prefix="/api/cameras", tags=["Camera Registry"])

from backend.integrations.sentinel import SentinelCatalogClient

catalog_client = SentinelCatalogClient()


def _get_frame_jpeg(camera_id: str) -> bytes:
    if RENDER_DEMO_MODE:
        from backend.demo_frames import placeholder_jpeg
        return placeholder_jpeg(camera_id)
    from ai.pipeline import global_health_tracker
    return global_health_tracker.get_latest_frame_jpeg(camera_id)

@router.get("", response_model=List[CameraResponse])
async def list_cameras(
    department: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Camera)
    if department:
        stmt = stmt.where(Camera.department == department)
    if status:
        stmt = stmt.where(Camera.status == status)
    if district:
        stmt = stmt.where(Camera.district == district)

    result = await db.execute(stmt)
    cams = result.scalars().all()

    # If DB is empty, seed demo Gujarat Police cameras (not the full 30-camera Sentinel grid)
    if not cams:
        for cam_data in CAMERAS_DATA:
            db.add(Camera(**cam_data))
        await db.commit()
        result = await db.execute(stmt)
        cams = result.scalars().all()

    return cams

@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera_detail(camera_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Camera).where(Camera.camera_id == camera_id)
    result = await db.execute(stmt)
    cam = result.scalar_one_or_none()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    return cam

@router.get("/{camera_id}/stream")
async def get_camera_mjpeg_stream(camera_id: str):
    """
    Streams real-time MJPEG live camera feed with YOLO vehicle bounding boxes & ANPR badges.
    """
    async def mjpeg_generator():
        while True:
            jpeg_bytes = _get_frame_jpeg(camera_id)
            if jpeg_bytes:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n')
            await asyncio.sleep(0.1)  # ~10 FPS — lighter on CPU/bandwidth for web clients

    return StreamingResponse(mjpeg_generator(), media_type="multipart/x-mixed-replace; boundary=frame")

@router.get("/{camera_id}/frame")
async def get_camera_latest_frame(camera_id: str):
    """
    Returns the latest single live JPEG frame decoded by the AI stream worker.
    Always returns a valid JPEG image (with smooth dark fallback) to prevent UI flickering.
    """
    jpeg_bytes = _get_frame_jpeg(camera_id)
    return Response(
        content=jpeg_bytes,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=2", "X-Accel-Buffering": "no"},
    )

@router.get("/{camera_id}/health", response_model=List[CameraHealthResponse])
async def get_camera_health_history(camera_id: str, limit: int = 50, db: AsyncSession = Depends(get_db)):
    stmt = select(CameraHealth).where(CameraHealth.camera_id == camera_id).order_by(CameraHealth.recorded_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("", response_model=CameraResponse)
async def onboard_camera(camera_data: CameraResponse, db: AsyncSession = Depends(get_db)):
    cam_check = await db.execute(select(Camera).where(Camera.camera_id == camera_data.camera_id))
    if cam_check.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Camera ID already exists")

    new_cam = Camera(**camera_data.dict())
    db.add(new_cam)
    await db.commit()
    await db.refresh(new_cam)
    return new_cam
