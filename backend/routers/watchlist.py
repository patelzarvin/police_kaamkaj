from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from backend.database import get_db
from backend.models import Watchlist
from backend.schemas import WatchlistResponse, WatchlistCreate

router = APIRouter(prefix="/api/watchlist", tags=["Watchlist Management"])

@router.get("", response_model=List[WatchlistResponse])
async def list_watchlist(db: AsyncSession = Depends(get_db)):
    stmt = select(Watchlist).where(Watchlist.is_active == True).order_by(Watchlist.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("", response_model=WatchlistResponse)
async def add_to_watchlist(entry: WatchlistCreate, db: AsyncSession = Depends(get_db)):
    clean_plate = entry.vehicle_number.upper().replace(" ", "").replace("-", "")

    existing = await db.execute(select(Watchlist).where(Watchlist.vehicle_number == clean_plate, Watchlist.is_active == True))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Vehicle already on active watchlist")

    new_wl = Watchlist(
        vehicle_number=clean_plate,
        category=entry.category,
        priority=entry.priority,
        reason=entry.reason,
        added_by="COMMAND_CENTER",
        is_active=True
    )
    db.add(new_wl)
    await db.commit()
    await db.refresh(new_wl)
    return new_wl

@router.delete("/{watchlist_id}")
async def remove_from_watchlist(watchlist_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Watchlist).where(Watchlist.id == watchlist_id)
    res = await db.execute(stmt)
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist entry not found")
    item.is_active = False
    await db.commit()
    return {"status": "success", "message": f"Watchlist entry {watchlist_id} deactivated"}
