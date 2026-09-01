from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from datetime import datetime

from backend.database import get_db
from backend.models import Detection, Camera, Watchlist
from backend.schemas import DetectionResponse, DetectionCreate

router = APIRouter(prefix="/api/detections", tags=["Detections & Analytics"])

@router.get("", response_model=List[DetectionResponse])
async def search_detections(
    plate_number: Optional[str] = Query(None, description="Search by license plate (e.g. GJ01AB1234)"),
    camera_id: Optional[str] = Query(None),
    vehicle_class: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Detection, Camera.name.label("camera_name"))\
        .join(Camera, Detection.camera_id == Camera.camera_id, isouter=True)

    if plate_number:
        clean_plate = plate_number.upper().replace(" ", "").replace("-", "")
        stmt = stmt.where(Detection.plate_number.contains(clean_plate))
    if camera_id:
        stmt = stmt.where(Detection.camera_id == camera_id)
    if vehicle_class:
        stmt = stmt.where(Detection.vehicle_class == vehicle_class)
    if start_time:
        stmt = stmt.where(Detection.timestamp >= start_time)
    if end_time:
        stmt = stmt.where(Detection.timestamp <= end_time)

    stmt = stmt.order_by(desc(Detection.timestamp)).offset(offset).limit(limit)
    result = await db.execute(stmt)
    rows = result.all()

    # Pre-fetch active watchlist items for flagging
    wl_stmt = select(Watchlist.vehicle_number, Watchlist.category).where(Watchlist.is_active == True)
    wl_res = await db.execute(wl_stmt)
    watchlist_map = {row[0]: row[1] for row in wl_res.all()}

    responses = []
    for det, cam_name in rows:
        flag = watchlist_map.get(det.plate_number)
        resp = DetectionResponse(
            detection_id=det.detection_id,
            camera_id=det.camera_id,
            source_type=getattr(det, "source_type", "SENTINEL_LIVE_CAMERA") or "SENTINEL_LIVE_CAMERA",
            timestamp=det.timestamp,
            vehicle_class=det.vehicle_class,
            track_id=det.track_id,
            plate_number=det.plate_number,
            plate_confidence=det.plate_confidence,
            detection_confidence=det.detection_confidence,
            bbox_x1=det.bbox_x1,
            bbox_y1=det.bbox_y1,
            bbox_x2=det.bbox_x2,
            bbox_y2=det.bbox_y2,
            plate_bbox_x1=getattr(det, "plate_bbox_x1", 0) or 0,
            plate_bbox_y1=getattr(det, "plate_bbox_y1", 0) or 0,
            plate_bbox_x2=getattr(det, "plate_bbox_x2", 0) or 0,
            plate_bbox_y2=getattr(det, "plate_bbox_y2", 0) or 0,
            image_path=det.image_path,
            plate_crop_path=det.plate_crop_path,
            latitude=det.latitude,
            longitude=det.longitude,
            camera_name=cam_name or det.camera_id,
            watchlist_flag=flag
        )
        responses.append(resp)
    return responses

@router.post("", response_model=DetectionResponse)
async def create_detection(det_data: DetectionCreate, db: AsyncSession = Depends(get_db)):
    det_id = f"DET-{int(datetime.now().timestamp()*1000)}"
    timestamp = det_data.timestamp or datetime.utcnow()
    new_det = Detection(
        detection_id=det_id,
        camera_id=det_data.camera_id,
        timestamp=timestamp,
        vehicle_class=det_data.vehicle_class,
        track_id=det_data.track_id,
        plate_number=det_data.plate_number.upper().replace(" ", ""),
        plate_confidence=det_data.plate_confidence,
        detection_confidence=det_data.detection_confidence,
        bbox_x1=det_data.bbox_x1,
        bbox_y1=det_data.bbox_y1,
        bbox_x2=det_data.bbox_x2,
        bbox_y2=det_data.bbox_y2,
        image_path=det_data.image_path,
        plate_crop_path=det_data.plate_crop_path,
        latitude=det_data.latitude,
        longitude=det_data.longitude
    )
    db.add(new_det)
    await db.commit()
    return new_det
