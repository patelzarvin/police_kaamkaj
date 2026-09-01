from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, asc
from typing import List

from backend.database import get_db
from backend.models import Detection, Camera, Watchlist, Vehicle
from backend.schemas import VehicleJourneyResponse, JourneyStep

router = APIRouter(prefix="/api/vehicles", tags=["Vehicle Journey Reconstruction"])

@router.get("/sample-plates")
async def get_sample_detected_plates(db: AsyncSession = Depends(get_db)):
    """Fetch distinct valid plate numbers genuinely detected and stored in database."""
    stmt = select(Detection.plate_number).where(Detection.plate_number != "UNKNOWN").distinct()
    res = await db.execute(stmt)
    plates = [r for (r,) in res.all()]
    return {"sample_plates": plates}

@router.get("/{plate_number}/journey", response_model=VehicleJourneyResponse)
async def reconstruct_vehicle_journey(plate_number: str, db: AsyncSession = Depends(get_db)):
    clean_plate = plate_number.upper().replace(" ", "").replace("-", "")

    # Query chronological detections for plate
    stmt = select(Detection, Camera.name.label("camera_name"))\
        .join(Camera, Detection.camera_id == Camera.camera_id, isouter=True)\
        .where(Detection.plate_number == clean_plate)\
        .order_by(asc(Detection.timestamp))

    res = await db.execute(stmt)
    rows = res.all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No CCTV detection history found for vehicle registration number '{clean_plate}'"
        )

    # Check Watchlist Status
    wl_stmt = select(Watchlist).where(Watchlist.vehicle_number == clean_plate, Watchlist.is_active == True)
    wl_res = await db.execute(wl_stmt)
    wl_entry = wl_res.scalar_one_or_none()

    watchlist_status = wl_entry.category if wl_entry else "CLEAR"
    watchlist_category = wl_entry.category if wl_entry else None

    journey_steps: List[JourneyStep] = []
    route_coordinates: List[List[float]] = []

    for idx, (det, cam_name) in enumerate(rows, start=1):
        formatted_t = det.timestamp.strftime("%I:%M %p | %b %d, %Y")
        step = JourneyStep(
            step_number=idx,
            camera_id=det.camera_id,
            camera_name=cam_name or det.camera_id,
            timestamp=det.timestamp,
            formatted_time=formatted_t,
            latitude=det.latitude,
            longitude=det.longitude,
            plate_number=det.plate_number,
            vehicle_class=det.vehicle_class,
            plate_confidence=det.plate_confidence,
            detection_confidence=det.detection_confidence,
            image_path=det.image_path,
            plate_crop_path=det.plate_crop_path,
            watchlist_status=watchlist_status
        )
        journey_steps.append(step)
        route_coordinates.append([det.latitude, det.longitude])

    first_det = rows[0][0]
    last_det = rows[-1][0]

    return VehicleJourneyResponse(
        plate_number=clean_plate,
        vehicle_class=first_det.vehicle_class,
        total_detections=len(rows),
        first_seen=first_det.timestamp,
        last_seen=last_det.timestamp,
        watchlist_status=watchlist_status,
        watchlist_category=watchlist_category,
        journey_steps=journey_steps,
        route_coordinates=route_coordinates
    )
