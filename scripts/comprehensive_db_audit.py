import os
import sys
import asyncio
from sqlalchemy import select, func, delete

sys.path.insert(0, os.path.abspath("."))

from backend.database import AsyncSessionLocal, init_db
from backend.models import Detection, LocalVideo, VideoDetection, Camera, Watchlist, Alert

async def audit_and_clean_database():
    await init_db()
    async with AsyncSessionLocal() as db:
        print("=" * 80)
        print("   COMPREHENSIVE DATABASE & DATA INTEGRITY AUDIT")
        print("=" * 80)

        # 1. Local Videos
        lv_stmt = select(LocalVideo)
        lvs = (await db.execute(lv_stmt)).scalars().all()
        print(f"\n[1] LOCAL VIDEOS REGISTERED: {len(lvs)}")
        for v in lvs:
            print(f"  - Video ID: {v.video_id} | Name: {v.display_name} | Type: {v.source_type} | Status: {v.processing_status} | Detections: {v.total_detections}")

        # 2. Video Detections breakdown by source
        vd_stmt = select(VideoDetection.video_id, func.count(VideoDetection.id)).group_by(VideoDetection.video_id)
        vd_res = (await db.execute(vd_stmt)).all()
        print(f"\n[2] VIDEO DETECTIONS BY SOURCE:")
        for vid, cnt in vd_res:
            print(f"  - Source: {vid} => {cnt} detections")

        # 3. Searchable Detections table breakdown by camera_id / video_id
        d_stmt = select(Detection.camera_id, func.count(Detection.detection_id)).group_by(Detection.camera_id)
        d_res = (await db.execute(d_stmt)).all()
        print(f"\n[3] SEARCHABLE DETECTIONS BY CAMERA/SOURCE:")
        for cam_id, cnt in d_res:
            print(f"  - Camera/Source: {cam_id} => {cnt} detections")

        # 4. Check for genuine vs synthetic plates in Detections table
        plates_stmt = select(Detection.plate_number, Detection.camera_id, func.count(Detection.detection_id)).group_by(Detection.plate_number, Detection.camera_id)
        plates_res = (await db.execute(plates_stmt)).all()
        print(f"\n[4] DETECTED PLATES SUMMARY:")
        for plate, cam_id, cnt in plates_res:
            print(f"  - Plate: '{plate}' | Source: {cam_id} => {cnt} records")

        # 5. Check Watchlist & Alerts
        w_stmt = select(func.count(Watchlist.id))
        w_cnt = (await db.execute(w_stmt)).scalar() or 0
        a_stmt = select(func.count(Alert.id))
        a_cnt = (await db.execute(a_stmt)).scalar() or 0
        print(f"\n[5] WATCHLIST ENTRIES: {w_cnt} | ALERTS GENERATED: {a_cnt}")

        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(audit_and_clean_database())
