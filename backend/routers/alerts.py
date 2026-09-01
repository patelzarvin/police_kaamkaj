from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional

from backend.database import get_db
from backend.models import Alert, Camera
from backend.schemas import AlertResponse

router = APIRouter(prefix="/api/alerts", tags=["Alert Engine"])

@router.get("", response_model=List[AlertResponse])
async def list_alerts(
    status: Optional[str] = Query(None, description="UNREAD, READ, ACKNOWLEDGED, DISPATCHED"),
    priority: Optional[str] = Query(None),
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Alert, Camera.name.label("camera_name"))\
        .join(Camera, Alert.camera_id == Camera.camera_id, isouter=True)

    if status:
        stmt = stmt.where(Alert.status == status)
    if priority:
        stmt = stmt.where(Alert.priority == priority)

    stmt = stmt.order_by(desc(Alert.timestamp)).limit(limit)
    result = await db.execute(stmt)
    rows = result.all()

    alerts = []
    for alert, cam_name in rows:
        resp = AlertResponse(
            id=alert.id,
            detection_id=alert.detection_id,
            watchlist_id=alert.watchlist_id,
            timestamp=alert.timestamp,
            camera_id=alert.camera_id,
            vehicle_number=alert.vehicle_number,
            alert_category=alert.alert_category,
            priority=alert.priority,
            status=alert.status,
            notes=alert.notes,
            location_name=alert.location_name,
            latitude=alert.latitude,
            longitude=alert.longitude,
            camera_name=cam_name or alert.camera_id
        )
        alerts.append(resp)
    return alerts

@router.patch("/{alert_id}/status")
async def update_alert_status(alert_id: int, status: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Alert).where(Alert.id == alert_id)
    res = await db.execute(stmt)
    alert = res.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = status.upper()
    await db.commit()
    return {"status": "success", "alert_id": alert_id, "new_status": alert.status}
