import sys
import os
sys.path.insert(0, os.path.abspath("."))

import asyncio
import logging
from sqlalchemy import select
from backend.database import AsyncSessionLocal, engine, Base
from backend.models import LocalVideo, VideoDetection
from backend.routers.video_intelligence import run_video_processing_task, get_video_summary, search_video_plates

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_generic_anpr")

async def run_pipeline_test():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    target_video_id = "gettyimages-1164849900-640_adpp"
    logger.info(f"=== STEP 1: Processing real local traffic video '{target_video_id}' ===")
    
    await run_video_processing_task(target_video_id, mode="full")
    logger.info("Processing complete!")

    async with AsyncSessionLocal() as db:
        logger.info("=== STEP 2: Fetching Video Summary & Automatically Discovered Plates ===")
        summary = await get_video_summary(target_video_id, db=db)
        
        logger.info(f"Video Display Name: {summary['display_name']}")
        logger.info(f"Total Vehicles Detected: {summary['total_vehicles_detected']}")
        logger.info(f"Total Plates Cropped: {summary['total_plates_detected']}")
        logger.info(f"Verified Plates Count: {summary['verified_plates_count']}")
        logger.info(f"Unreadable Plates Count: {summary['unreadable_plates_count']}")
        
        discovered = summary['unique_discovered_plates']
        logger.info(f"Automatically Discovered Unique Plates ({len(discovered)} total):")
        for idx, item in enumerate(discovered, 1):
            logger.info(f"  [{idx}] Plate: {item['plate_number']} | Status: {item['verification_status']} | Track ID: #{item['track_id']} | Support: {item['supporting_frames_count']} frames | Vehicle Crop: {item['best_vehicle_crop']} | Plate Crop: {item['best_plate_crop']}")

        assert len(discovered) > 0, "Pipeline failed: No plate records found!"

        logger.info("=== STEP 3: Picking ONE automatically discovered plate for isolated video search ===")
        # Find first verified plate or unreadable plate candidate
        picked_item = discovered[0]
        target_plate = picked_item['plate_number']
        logger.info(f"Selected Discovered Target Plate: '{target_plate}'")

        if target_plate != "UNKNOWN":
            search_res = await search_video_plates(plate_number=target_plate, source_id=target_video_id, db=db)
            logger.info(f"Search Query Results for '{target_plate}': Total Matches = {search_res['total_matches']}")
            assert search_res['total_matches'] > 0, f"Search failed for discovered plate {target_plate}"
            first_match = search_res['results'][0]
            logger.info(f"Match Vehicle Crop Path: {first_match['image_path']}")
            logger.info(f"Match Plate Crop Path: {first_match['plate_crop_path']}")
            logger.info(f"Match Enhanced Crop Path: {first_match['enhanced_plate_crop_path']}")
            logger.info(f"Match Verification Status: {first_match['verification_status']}")
            assert first_match['image_path'] is not None, "Vehicle crop path missing!"
            assert first_match['plate_crop_path'] is not None, "Plate crop path missing!"
        else:
            logger.info(f"Discovered UNREADABLE plate candidate (Track #{picked_item['track_id']}). Crop paths stored cleanly.")

    logger.info("=== EMPIRICAL PIPELINE TEST SUCCESSFUL! ===")

if __name__ == "__main__":
    asyncio.run(run_pipeline_test())
