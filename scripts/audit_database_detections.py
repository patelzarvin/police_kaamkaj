import os
import sys
import asyncio
from sqlalchemy import select, func

sys.path.insert(0, os.path.abspath("."))

from backend.database import AsyncSessionLocal, init_db
from backend.models import Detection

async def audit_stock_video_detections():
    await init_db()
    async with AsyncSessionLocal() as db:
        # Total Local Video Detections
        total_stmt = select(func.count(Detection.detection_id)).where(Detection.camera_id == "STOCK_VIDEO_CAM")
        total_res = await db.execute(total_stmt)
        total_count = total_res.scalar() or 0

        # Valid Plates Found (plate_number != 'UNKNOWN')
        valid_stmt = select(func.count(Detection.detection_id)).where(
            Detection.camera_id == "STOCK_VIDEO_CAM",
            Detection.plate_number != "UNKNOWN"
        )
        valid_res = await db.execute(valid_stmt)
        valid_count = valid_res.scalar() or 0

        # Unknown OCR Records
        unknown_stmt = select(func.count(Detection.detection_id)).where(
            Detection.camera_id == "STOCK_VIDEO_CAM",
            Detection.plate_number == "UNKNOWN"
        )
        unknown_res = await db.execute(unknown_stmt)
        unknown_count = unknown_res.scalar() or 0

        # Unique Valid Plate Numbers
        unique_stmt = select(Detection.plate_number).where(
            Detection.camera_id == "STOCK_VIDEO_CAM",
            Detection.plate_number != "UNKNOWN"
        ).distinct()
        unique_res = await db.execute(unique_stmt)
        unique_plates = [r for (r,) in unique_res.all()]

        print("=" * 80)
        print("   DATABASE AUDIT -- LOCAL STOCK VIDEO DETECTIONS")
        print("=" * 80)
        print(f"TOTAL LOCAL VIDEO DETECTIONS:\n{total_count}\n")
        print(f"VALID PLATES FOUND:\n{valid_count}\n")
        print(f"UNIQUE VALID PLATE NUMBERS:\n{unique_plates}\n")
        print(f"UNKNOWN OCR RECORDS:\n{unknown_count}")
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(audit_stock_video_detections())
