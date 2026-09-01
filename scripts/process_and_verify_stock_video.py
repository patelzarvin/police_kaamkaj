import os
import sys
import time
import asyncio
import cv2
import numpy as np
import datetime
from sqlalchemy import select

sys.path.insert(0, os.path.abspath("."))

from backend.database import AsyncSessionLocal, init_db
from backend.models import Camera, Detection, Watchlist, Vehicle, Alert
from ai.detection.detector import VehicleDetector
from ai.tracking.tracker import CentroidTracker
from ai.anpr.anpr_engine import ANPREngine, TemporalConsensusTracker
from stream_gateway.sentinel_client import SentinelIngestClient

def process_and_verify_stock_video():
    print("=" * 80)
    print("   GUJARAT POLICE SENTINEL -- LOCAL TEST VIDEO & SEARCH VERIFICATION")
    print("=" * 80)

    # 1. Ensure Database & Camera Asset
    asyncio.run(init_db())

    stock_cam_id = "STOCK_VIDEO_CAM"
    stock_cam_name = "Local Stock Test Video - Ahmedabad Junction"

    async def ensure_stock_camera():
        async with AsyncSessionLocal() as db:
            cam_check = await db.execute(select(Camera).where(Camera.camera_id == stock_cam_id))
            if not cam_check.scalar_one_or_none():
                stock_cam = Camera(
                    camera_id=stock_cam_id,
                    name=stock_cam_name,
                    department="Local Video Test",
                    district="Ahmedabad",
                    city="Ahmedabad",
                    latitude=23.0276,
                    longitude=72.5074,
                    address="Local Stock Video File Source",
                    stream_type="FILE",
                    codec="H264",
                    resolution="1920x1080",
                    fps=25.0,
                    status="ONLINE"
                )
                db.add(stock_cam)
                await db.commit()
                print(f"[OK] Created Stock Camera Record in Database ({stock_cam_id})")

    asyncio.run(ensure_stock_camera())

    # 2. Locate Readable Local Test Video File (Generated High-Resolution CCTV Traffic Feed)
    video_path = os.path.abspath("data/videos/test_cctv_stream.mp4")

    print(f"\n1. PROCESSING LOCAL READABLE TEST VIDEO FILE")
    print(f"   Video Source Path: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[FAIL] Cannot open local test video file {video_path}")
        sys.exit(1)

    # 3. Instantiate Real AI Pipeline Components
    detector = VehicleDetector(confidence_threshold=0.15)
    tracker = CentroidTracker()
    anpr = ANPREngine()
    consensus = TemporalConsensusTracker()

    total_frames = 0
    total_detections = 0
    valid_plates_indexed = 0
    unknown_plates_count = 0
    indexed_plates = set()

    print("\n2. EXECUTING REAL AI PIPELINE ON VIDEO FRAMES...")
    print(f"{'Frame':<6} | {'Track ID':<9} | {'Raw OCR Text':<18} | {'Consensus Plate':<18} | {'Status'}")
    print("-" * 75)

    os.makedirs("data/vehicle_crops", exist_ok=True)
    os.makedirs("data/plates", exist_ok=True)

    while cap.isOpened() and total_frames < 60:
        ret, frame = cap.read()
        if not ret or frame is None:
            break

        total_frames += 1
        h, w, _ = frame.shape
        pts_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
        if pts_ms <= 0:
            pts_ms = total_frames * 40.0 # 25 FPS frame delta

        # YOLO Vehicle Detection
        dets = detector.detect_vehicles(frame)
        if not dets:
            dets = detector._heuristic_fallback(frame)

        # Centroid Tracking
        tracked = tracker.update(dets)

        for det in tracked:
            total_detections += 1
            bbox = det["bbox"]
            v_class = det["vehicle_class"]
            det_conf = float(det["confidence"])
            track_id = det.get("track_id", 101)
            crop = det["crop"]

            # ANPREngine (Dedicated Plate Region Locator + Preprocessing + EasyOCR)
            anpr_res = anpr.process_vehicle_crop(crop)
            raw_plate = "UNKNOWN"
            raw_conf = 0.0
            is_valid = False
            plate_crop = crop

            if anpr_res:
                raw_plate = anpr_res["plate_number"]
                raw_conf = float(anpr_res["confidence"])
                is_valid = anpr_res["valid_plate"]
                plate_crop = anpr_res["plate_crop"]

            # Temporal Consensus
            consensus.add_detection(track_id, raw_plate, raw_conf, is_valid)
            plate_number, consensus_conf, consensus_valid = consensus.get_consensus_plate(track_id)

            if consensus_valid and plate_number != "UNKNOWN":
                valid_plates_indexed += 1
                indexed_plates.add(plate_number)
                status_txt = "[VALID PLATE]"
            else:
                unknown_plates_count += 1
                status_txt = "UNKNOWN (INVALID OCR)"

            # Print sample detections
            if total_detections % 10 == 1:
                print(f"#{total_frames:<5} | #{track_id:<8} | {raw_plate:<18} | {plate_number:<18} | {status_txt}")

            # Save Crops & Insert Record into Database
            det_id = f"STOCK-DET-{int(time.time()*1000)}-{total_detections}"
            img_filename = f"vehicle_{plate_number}_{det_id}.jpg"
            plate_filename = f"plate_{plate_number}_{det_id}.jpg"

            img_disk_path = os.path.join("data", "vehicle_crops", img_filename)
            plate_disk_path = os.path.join("data", "plates", plate_filename)

            cv2.imwrite(img_disk_path, crop)
            cv2.imwrite(plate_disk_path, plate_crop)

            web_img_path = f"/data/vehicle_crops/{img_filename}"
            web_plate_path = f"/data/plates/{plate_filename}"

            async def insert_detection(det_id, track_id, plate, pconf, dconf, bbox, vclass, web_img, web_plate, lat, lng, pts):
                async with AsyncSessionLocal() as db:
                    timestamp = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=(60 - total_frames))
                    d = Detection(
                        detection_id=det_id,
                        camera_id=stock_cam_id,
                        timestamp=timestamp,
                        vehicle_class=vclass,
                        track_id=track_id,
                        plate_number=plate,
                        plate_confidence=pconf,
                        detection_confidence=dconf,
                        bbox_x1=int(bbox[0]), bbox_y1=int(bbox[1]), bbox_x2=int(bbox[2]), bbox_y2=int(bbox[3]),
                        image_path=web_img,
                        plate_crop_path=web_plate,
                        latitude=lat,
                        longitude=lng
                    )
                    db.add(d)
                    await db.commit()

            asyncio.run(insert_detection(det_id, track_id, plate_number, consensus_conf, det_conf, bbox, v_class, web_img_path, web_plate_path, 23.0276, 72.5074, pts_ms))

    cap.release()

    print("\n3. STOCK VIDEO PROCESSING SUMMARY")
    print(f"   - Total Frames Processed: {total_frames}")
    print(f"   - Total Vehicle Detections Generated: {total_detections}")
    print(f"   - Valid Plates Indexed: {valid_plates_indexed}")
    print(f"   - Unknown / Invalid OCR Instances: {unknown_plates_count}")
    print(f"   - Unique Valid Plates Discovered: {list(indexed_plates)}")

    # 4. Search Verification Tests
    print("\n4. DATABASE SEARCH VERIFICATION TESTS")
    test_plate = "DL2CA27993"
    non_existent_plate = "GJ99ZZ9999"

    async def verify_search_query(plate_to_search):
        async with AsyncSessionLocal() as db:
            stmt = select(Detection, Camera.name.label("camera_name"))\
                .join(Camera, Detection.camera_id == Camera.camera_id, isouter=True)\
                .where(Detection.plate_number == plate_to_search)\
                .order_by(Detection.timestamp.asc())
            res = await db.execute(stmt)
            return res.all()

    # Test Known Plate Search
    known_results = asyncio.run(verify_search_query(test_plate))
    print(f"\n   A. Searching Known Indexed Plate '{test_plate}':")
    if known_results:
        first_row, cam_name = known_results[0]
        print(f"      [PASS] FOUND {len(known_results)} matching detection(s) in Database")
        print(f"      - Camera Source: {cam_name} ({first_row.camera_id})")
        print(f"      - Timestamp: {first_row.timestamp}")
        print(f"      - Vehicle Class: {first_row.vehicle_class}")
        print(f"      - Image Crop Path: {first_row.image_path}")
        print(f"      - Plate Crop Path: {first_row.plate_crop_path}")
        known_search_passed = True
    else:
        print(f"      [FAIL] Known plate '{test_plate}' not found in database.")
        known_search_passed = False

    # Test Unknown Plate Search
    unknown_results = asyncio.run(verify_search_query(non_existent_plate))
    print(f"\n   B. Searching Non-Existent Plate '{non_existent_plate}':")
    if not unknown_results:
        print(f"      [PASS] 0 matching detections returned for non-existent plate.")
        unknown_search_passed = True
    else:
        print(f"      [FAIL] Returned fake match for non-existent plate.")
        unknown_search_passed = False

    # 5. Sentinel Live Camera Grid Preservation Audit
    print("\n5. SENTINEL LIVE CAMERA GRID PRESERVATION AUDIT")
    sentinel_client = SentinelIngestClient("https://live.corp8.cloud")
    reachable, catalogue, _ = sentinel_client.fetch_catalogue()
    catalogue_count = len(catalogue) if (catalogue and isinstance(catalogue, list)) else 0
    print(f"   - Live Host: https://live.corp8.cloud")
    print(f"   - Catalogue Endpoint Reachable: {'YES' if reachable else 'NO'}")
    print(f"   - Cameras Discovered: {catalogue_count}")
    
    sentinel_preserved = (reachable and catalogue_count == 30)
    if sentinel_preserved:
        print("   [PASS] SENTINEL LIVE CAMERA GRID PRESERVED & FULLY FUNCTIONAL")
    else:
        print("   [FAIL] Sentinel Integration broken or modified.")

    # 6. Final Report Matrix
    print("\n" + "=" * 80)
    print("   FINAL VERIFICATION REPORT")
    print("=" * 80)

    stock_passed = (total_frames > 0 and total_detections > 0 and known_search_passed and unknown_search_passed)
    print(f"   A) LOCAL STOCK VIDEO PLATE SEARCH: {'PASS' if stock_passed else 'FAIL'}")
    print(f"   B) SENTINEL LIVE CAMERA GRID PRESERVATION: {'PASS' if sentinel_preserved else 'FAIL'}")
    print("=" * 80 + "\n")

    if not stock_passed or not sentinel_preserved:
        sys.exit(1)

if __name__ == "__main__":
    process_and_verify_stock_video()
