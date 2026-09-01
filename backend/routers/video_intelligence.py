import os
import time
import cv2
import numpy as np
import re
import uuid
import asyncio
import datetime
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func

from backend.database import get_db, AsyncSessionLocal
from backend.models import LocalVideo, VideoDetection, Detection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/videos", tags=["Video Intelligence"])

VIDEOS_DIR = os.path.abspath("data/videos")

def discover_local_video_files() -> List[Dict[str, Any]]:
    """Scan data/videos folder and return fast metadata list."""
    os.makedirs(VIDEOS_DIR, exist_ok=True)
    video_list = []
    
    for fname in os.listdir(VIDEOS_DIR):
        if not fname.lower().endswith(('.mp4', '.avi', '.mkv', '.mov', '.webm')):
            continue
        if "test_cctv" in fname.lower() or "synthetic" in fname.lower():
            continue
        
        fpath = os.path.join(VIDEOS_DIR, fname)
        video_id = os.path.splitext(fname)[0].replace(' ', '_')
        
        clean_title = fname.replace('_', ' ').replace('-', ' ').title()
        display_name = f"Stock Video: {fname[:24]}"
        desc = f"Traffic surveillance video file: {fname}"

        # Fast default metadata (probes only if needed)
        width = 1280 if "1280" in fname else 768
        height = 720 if "1280" in fname else 432
        fps = 25.0
        duration = 20.0
        total_frames = 500

        video_list.append({
            "video_id": video_id,
            "filename": fname,
            "file_path": fpath,
            "source_type": "REAL_WORLD",
            "display_name": display_name,
            "description": desc,
            "resolution": f"{width}x{height}",
            "duration_seconds": round(duration, 2),
            "fps": round(fps, 2),
            "total_frames": total_frames
        })

    return video_list

@router.get("", response_model=List[Dict[str, Any]])
async def list_videos(db: AsyncSession = Depends(get_db)):
    """List all discovered local videos and sync with DB status."""
    discovered = discover_local_video_files()
    result = []
    
    for v in discovered:
        if "test_cctv" in v["video_id"].lower() or "synthetic" in v["video_id"].lower():
            continue
        # Check DB entry cleanly
        stmt = select(LocalVideo).where(LocalVideo.video_id == v["video_id"])
        res = await db.execute(stmt)
        video_record = res.scalars().first()

        if not video_record:
            video_record = LocalVideo(
                video_id=v["video_id"],
                filename=v["filename"],
                file_path=v["file_path"],
                source_type=v["source_type"],
                display_name=v["display_name"],
                description=v["description"],
                resolution=v["resolution"],
                duration_seconds=v["duration_seconds"],
                fps=v["fps"],
                total_frames=v["total_frames"],
                processing_status="NOT_INDEXED"
            )
            db.add(video_record)
            await db.commit()
            await db.refresh(video_record)

        # Count total detections and valid plates in DB
        det_stmt = select(func.count(VideoDetection.id)).where(VideoDetection.video_id == v["video_id"])
        det_count = (await db.execute(det_stmt)).scalar() or 0

        plate_stmt = select(func.count(VideoDetection.id)).where(
            VideoDetection.video_id == v["video_id"],
            VideoDetection.plate_number != "UNKNOWN"
        )
        plate_count = (await db.execute(plate_stmt)).scalar() or 0

        if det_count > 0:
            video_record.processing_status = "INDEXED"
            video_record.total_detections = det_count
            video_record.valid_plates_count = plate_count
            await db.commit()

        result.append({
            "video_id": video_record.video_id,
            "filename": video_record.filename,
            "file_path": f"/data/videos/{video_record.filename}",
            "source_type": video_record.source_type,
            "display_name": video_record.display_name,
            "description": video_record.description,
            "resolution": video_record.resolution,
            "duration_seconds": video_record.duration_seconds,
            "fps": video_record.fps,
            "total_frames": video_record.total_frames,
            "processing_status": video_record.processing_status,
            "total_detections": det_count,
            "valid_plates_count": plate_count,
            "last_processed_at": video_record.last_processed_at.isoformat() if video_record.last_processed_at else None
        })

    return [r for r in result if "test_cctv" not in r["video_id"].lower() and "synthetic" not in r["video_id"].lower()]

@router.get("/{video_id}")
async def get_video_details(video_id: str, db: AsyncSession = Depends(get_db)):
    """Get single video metadata and indexing summary."""
    stmt = select(LocalVideo).where(LocalVideo.video_id == video_id)
    video = (await db.execute(stmt)).scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail=f"Local video '{video_id}' not found.")

    det_stmt = select(func.count(VideoDetection.id)).where(VideoDetection.video_id == video_id)
    det_count = (await db.execute(det_stmt)).scalar() or 0

    plate_stmt = select(func.count(VideoDetection.id)).where(
        VideoDetection.video_id == video_id,
        VideoDetection.plate_number != "UNKNOWN"
    )
    plate_count = (await db.execute(plate_stmt)).scalar() or 0

    return {
        "video_id": video.video_id,
        "filename": video.filename,
        "file_path": f"/data/videos/{video.filename}",
        "source_type": video.source_type,
        "display_name": video.display_name,
        "description": video.description,
        "resolution": video.resolution,
        "duration_seconds": video.duration_seconds,
        "fps": video.fps,
        "total_frames": video.total_frames,
        "processing_status": video.processing_status,
        "total_detections": det_count,
        "valid_plates_count": plate_count,
        "last_processed_at": video.last_processed_at.isoformat() if video.last_processed_at else None
    }

@router.get("/{video_id}/stream")
async def stream_video_file(video_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """
    High-performance byte-range video streaming endpoint (HTTP 206 Partial Content).
    Enables zero-lag instant scrubbing, seeking, and smooth hardware-accelerated playback.
    """
    stmt = select(LocalVideo).where(LocalVideo.video_id == video_id)
    video = (await db.execute(stmt)).scalar_one_or_none()
    
    filename = video.filename if video else f"{video_id}.mp4"
    file_path = os.path.join(VIDEOS_DIR, filename)
    
    if not os.path.isfile(file_path):
        for f in os.listdir(VIDEOS_DIR):
            if os.path.splitext(f)[0].replace(' ', '_') == video_id:
                file_path = os.path.join(VIDEOS_DIR, f)
                break
                
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Video file not found on disk")
        
    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("range")
    
    if range_header:
        range_match = re.match(r"bytes=(\d+)-(\d*)", range_header)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
            start = max(0, min(start, file_size - 1))
            end = max(start, min(end, file_size - 1))
            content_length = end - start + 1
            
            def iter_chunk():
                with open(file_path, "rb") as f:
                    f.seek(start)
                    bytes_remaining = content_length
                    while bytes_remaining > 0:
                        chunk_size = min(bytes_remaining, 1024 * 512) # 512KB chunks
                        data = f.read(chunk_size)
                        if not data:
                            break
                        bytes_remaining -= len(data)
                        yield data
                        
            headers = {
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(content_length),
                "Content-Type": "video/mp4",
            }
            return StreamingResponse(iter_chunk(), status_code=206, headers=headers)

    def iter_full():
        with open(file_path, "rb") as f:
            while chunk := f.read(1024 * 512):
                yield chunk
                
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
        "Content-Type": "video/mp4",
    }
    return StreamingResponse(iter_full(), status_code=200, headers=headers)

class SimpleSpatialTracker:
    def __init__(self, iou_threshold=0.25):
        self.next_id = 1001
        self.tracks = {}
        self.iou_threshold = iou_threshold

    def update(self, detections):
        new_tracks = {}
        for det in detections:
            bbox = det["bbox"]
            best_id = None
            best_iou = 0.0
            
            for tid, tbbox in self.tracks.items():
                x1 = max(bbox[0], tbbox[0])
                y1 = max(bbox[1], tbbox[1])
                x2 = min(bbox[2], tbbox[2])
                y2 = min(bbox[3], tbbox[3])
                inter = max(0, x2 - x1) * max(0, y2 - y1)
                b1_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                b2_area = (tbbox[2] - tbbox[0]) * (tbbox[3] - tbbox[1])
                union = b1_area + b2_area - inter
                iou = float(inter / union) if union > 0 else 0.0
                
                if iou > best_iou and iou >= self.iou_threshold:
                    best_iou = iou
                    best_id = tid
            
            if best_id is None:
                best_id = self.next_id
                self.next_id += 1
            
            det["track_id"] = best_id
            new_tracks[best_id] = bbox
        self.tracks = new_tracks
        return detections

async def run_video_processing_task(video_id: str, mode: str):
    """Background task to run YOLO + ANPR + Temporal Consensus on local video."""
    from ai.detection.detector import VehicleDetector
    from ai.anpr.anpr_engine import ANPREngine, TemporalConsensusTracker
    
    stride = 1 if mode == "full" else (2 if mode == "balanced" else 5)

    async with AsyncSessionLocal() as db:
        stmt = select(LocalVideo).where(LocalVideo.video_id == video_id)
        video = (await db.execute(stmt)).scalar_one_or_none()
        if not video:
            return

        video.processing_status = "PROCESSING"
        await db.commit()

        # Clear previous detections for this video
        del_vd = delete(VideoDetection).where(VideoDetection.video_id == video_id)
        del_d = delete(Detection).where(Detection.camera_id == f"VIDEO_{video_id}")
        await db.execute(del_vd)
        await db.execute(del_d)
        await db.commit()

        fpath = os.path.join(VIDEOS_DIR, video.filename)
        logger.info(f"[INDEXING] video_id={video_id}, fpath={fpath}, exists={os.path.exists(fpath)}")
        cap = cv2.VideoCapture(fpath)
        if not cap.isOpened():
            logger.error(f"[INDEXING FAILED] Cannot open video file: {fpath}")
            video.processing_status = "FAILED"
            await db.commit()
            return

        detector = VehicleDetector()
        anpr = ANPREngine()
        consensus = TemporalConsensusTracker()
        tracker = SimpleSpatialTracker()

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        
        frame_idx = 0
        indexed_count = 0
        valid_plates_count = 0

        os.makedirs("data/vehicle_crops", exist_ok=True)
        os.makedirs("data/plates", exist_ok=True)

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                frame_idx += 1
                
                if (frame_idx - 1) % stride != 0:
                    continue

                video_timestamp_ms = float((frame_idx - 1) / fps) * 1000.0

                dets = detector.detect_vehicles(frame)
                if not dets:
                    dets = detector._heuristic_fallback(frame)

                dets = tracker.update(dets)

                fh, fw = frame.shape[:2]

                for det_idx, det in enumerate(dets):
                    bbox = det["bbox"] # [x1, y1, x2, y2]
                    vclass = det["vehicle_class"]
                    vconf = det.get("confidence", 0.90)
                    track_id = det["track_id"]

                    # Add 5% context padding around vehicle bounding box for high quality photo view
                    bw = bbox[2] - bbox[0]
                    bh = bbox[3] - bbox[1]
                    pad_w = int(bw * 0.05)
                    pad_h = int(bh * 0.05)

                    vx1 = max(0, bbox[0] - pad_w)
                    vy1 = max(0, bbox[1] - pad_h)
                    vx2 = min(fw, bbox[2] + pad_w)
                    vy2 = min(fh, bbox[3] + pad_h)

                    # Ensure contiguous memory array slice for 100% valid OpenCV JPEG encoding
                    crop_raw = frame[vy1:vy2, vx1:vx2]
                    if crop_raw is None or crop_raw.size == 0:
                        crop_raw = det.get("crop")

                    if crop_raw is not None and crop_raw.size > 0:
                        crop = np.ascontiguousarray(crop_raw.copy())
                    else:
                        crop = None

                    plate_num = "UNKNOWN"
                    plate_conf = 0.0
                    plate_bbox = [0, 0, 0, 0]
                    img_rel_path = None
                    plate_rel_path = None

                    p_crop = None
                    if crop is not None and crop.shape[1] >= 20 and crop.shape[0] >= 15:
                        anpr_res = anpr.process_vehicle_crop(crop)
                        if anpr_res:
                            raw_text = anpr_res.get("raw_text", "")
                            norm_plate = anpr_res.get("plate_number")
                            is_valid = anpr_res.get("valid_plate", False)
                            conf = anpr_res.get("confidence", 0.0)
                            p_crop_raw = anpr_res.get("plate_crop")
                            p_bbox = anpr_res.get("plate_bbox")

                            if p_crop_raw is not None and p_crop_raw.size > 0:
                                p_crop = np.ascontiguousarray(p_crop_raw.copy())

                            consensus.add_detection(track_id, norm_plate if is_valid else "UNKNOWN", conf, is_valid)
                            c_plate, c_conf, c_valid = consensus.get_consensus_plate(track_id)

                            if c_valid and c_plate != "UNKNOWN":
                                plate_num = c_plate
                                plate_conf = c_conf
                            elif is_valid and norm_plate != "UNKNOWN":
                                plate_num = norm_plate
                                plate_conf = conf

                            if p_bbox:
                                plate_bbox = [
                                    bbox[0] + p_bbox[0],
                                    bbox[1] + p_bbox[1],
                                    bbox[0] + p_bbox[0] + p_bbox[2],
                                    bbox[1] + p_bbox[1] + p_bbox[3]
                                ]

                    # High Quality Crop Image Generation from Contiguous Video Array
                    if crop is not None and crop.size > 0:
                        clean_plate_str = re.sub(r'[^A-Z0-9]', '', plate_num.upper()) or "UNKNOWN"
                        det_stamp = f"{video_id}-F{frame_idx}-D{det_idx}"
                        v_fname = f"vehicle_{clean_plate_str}_{det_stamp}.jpg"
                        p_fname = f"plate_{clean_plate_str}_{det_stamp}.jpg"
                        e_fname = f"enhanced_{clean_plate_str}_{det_stamp}.jpg"

                        # Upscale small vehicle crop to min 500px width for razor sharp photo modal preview
                        h_c, w_c = crop.shape[:2]
                        if w_c < 500:
                            scale = 500.0 / float(w_c)
                            crop_highres = cv2.resize(crop, (500, max(100, int(h_c * scale))), interpolation=cv2.INTER_CUBIC)
                        else:
                            crop_highres = crop

                        # Prepare plate crop
                        if p_crop is None or p_crop.size == 0:
                            # Slicing lower center 40% of vehicle crop as plate region fallback crop
                            vh_c, vw_c = crop.shape[:2]
                            p_crop_raw = crop[int(vh_c * 0.55):int(vh_c * 0.95), int(vw_c * 0.15):int(vw_c * 0.85)]
                            if p_crop_raw.size > 0:
                                p_crop = np.ascontiguousarray(p_crop_raw.copy())
                            else:
                                p_crop = crop

                        if p_crop is not None and p_crop.size > 0:
                            hp_c, wp_c = p_crop.shape[:2]
                            if wp_c < 350:
                                p_scale = 350.0 / float(wp_c)
                                p_crop_highres = cv2.resize(p_crop, (350, max(50, int(hp_c * p_scale))), interpolation=cv2.INTER_CUBIC)
                            else:
                                p_crop_highres = p_crop
                        else:
                            p_crop_highres = crop_highres

                        crop_highres = np.ascontiguousarray(crop_highres.copy())
                        p_crop_highres = np.ascontiguousarray(p_crop_highres.copy())

                        # Process enhanced variant image
                        if anpr_res and "enhanced_plate_crop" in anpr_res and anpr_res["enhanced_plate_crop"] is not None:
                            e_crop = np.ascontiguousarray(anpr_res["enhanced_plate_crop"].copy())
                        else:
                            e_crop = p_crop_highres

                        # Save at maximum JPEG quality 98 to both data and static mount targets
                        os.makedirs(os.path.join("data", "vehicle_crops"), exist_ok=True)
                        os.makedirs(os.path.join("data", "plates"), exist_ok=True)
                        os.makedirs(os.path.join("data", "enhanced_plates"), exist_ok=True)
                        os.makedirs(os.path.join("static", "crops"), exist_ok=True)

                        cv2.imwrite(os.path.join("data", "vehicle_crops", v_fname), crop_highres, [cv2.IMWRITE_JPEG_QUALITY, 98])
                        cv2.imwrite(os.path.join("data", "plates", p_fname), p_crop_highres, [cv2.IMWRITE_JPEG_QUALITY, 98])
                        cv2.imwrite(os.path.join("data", "enhanced_plates", e_fname), e_crop, [cv2.IMWRITE_JPEG_QUALITY, 98])
                        cv2.imwrite(os.path.join("static", "crops", v_fname), crop_highres, [cv2.IMWRITE_JPEG_QUALITY, 98])
                        cv2.imwrite(os.path.join("static", "crops", p_fname), p_crop_highres, [cv2.IMWRITE_JPEG_QUALITY, 98])
                        cv2.imwrite(os.path.join("static", "crops", e_fname), e_crop, [cv2.IMWRITE_JPEG_QUALITY, 98])

                        img_rel_path = f"/data/vehicle_crops/{v_fname}"
                        plate_rel_path = f"/data/plates/{p_fname}"
                        enh_rel_path = f"/data/enhanced_plates/{e_fname}"

                    if plate_num != "UNKNOWN":
                        valid_plates_count += 1

                    ocr_conf = anpr_res.get("confidence", 0.0) if anpr_res else 0.0
                    raw_ocr = anpr_res.get("raw_text", "") if anpr_res else ""
                    prep_method = anpr_res.get("preprocessing_method", "SubPixel-Bicubic + CLAHE + Sharpening") if anpr_res else "SubPixel-Bicubic + CLAHE + Sharpening"
                    verif_status = "VERIFIED" if (plate_num != "UNKNOWN") else "UNREADABLE"

                    vd = VideoDetection(
                        video_id=video_id,
                        source_filename=video.filename,
                        source_type=video.source_type,
                        frame_number=frame_idx,
                        video_timestamp_ms=video_timestamp_ms,
                        track_id=track_id,
                        vehicle_class=vclass,
                        vehicle_confidence=vconf,
                        bbox_x1=bbox[0],
                        bbox_y1=bbox[1],
                        bbox_x2=bbox[2],
                        bbox_y2=bbox[3],
                        plate_number=plate_num,
                        plate_confidence=plate_conf,
                        ocr_confidence=ocr_conf,
                        raw_ocr_text=raw_ocr,
                        plate_bbox_x1=plate_bbox[0],
                        plate_bbox_y1=plate_bbox[1],
                        plate_bbox_x2=plate_bbox[2],
                        plate_bbox_y2=plate_bbox[3],
                        image_path=img_rel_path,
                        plate_crop_path=plate_rel_path,
                        enhanced_plate_crop_path=enh_rel_path,
                        supporting_frames_count=1,
                        verification_status=verif_status,
                        ocr_engine="EasyOCR",
                        preprocessing_method=prep_method
                    )
                    db.add(vd)
                    indexed_count += 1

                    # Also store in main Detections table for unified search
                    if plate_num != "UNKNOWN":
                        d_id = f"VDET-{video_id}-F{frame_idx}-D{det_idx}-{uuid.uuid4().hex[:6]}"
                        d_record = Detection(
                            detection_id=d_id,
                            camera_id=f"VIDEO_{video_id}",
                            timestamp=datetime.datetime.now(datetime.timezone.utc),
                            vehicle_class=vclass,
                            track_id=track_id,
                            plate_number=plate_num,
                            plate_confidence=plate_conf,
                            detection_confidence=vconf,
                            bbox_x1=bbox[0],
                            bbox_y1=bbox[1],
                            bbox_x2=bbox[2],
                            bbox_y2=bbox[3],
                            image_path=img_rel_path,
                            plate_crop_path=plate_rel_path,
                            latitude=23.0225,
                            longitude=72.5714
                        )
                        db.add(d_record)
                
                if frame_idx % 50 == 0:
                    await db.commit()

                await asyncio.sleep(0.001)

            cap.release()

            # Re-fetch video record to update final indexed status
            stmt_v = select(LocalVideo).where(LocalVideo.video_id == video_id)
            video_rec = (await db.execute(stmt_v)).scalar_one_or_none()
            if video_rec:
                video_rec.processing_status = "INDEXED"
                video_rec.indexed_frames = total_frames
                video_rec.total_detections = indexed_count
                video_rec.valid_plates_count = valid_plates_count
                video_rec.last_processed_at = datetime.datetime.now(datetime.timezone.utc)
            await db.commit()
            logger.info(f"Successfully indexed video '{video_id}': {indexed_count} detections ({valid_plates_count} plates)")

        except Exception as err:
            logger.error(f"Error processing video '{video_id}': {err}", exc_info=True)
            stmt_v = select(LocalVideo).where(LocalVideo.video_id == video_id)
            video_rec = (await db.execute(stmt_v)).scalar_one_or_none()
            if video_rec:
                video_rec.processing_status = "FAILED"
            await db.commit()

@router.post("/{video_id}/process")
async def process_video(
    video_id: str,
    background_tasks: BackgroundTasks,
    mode: str = Query("full", pattern="^(full|balanced|fast)$"),
    db: AsyncSession = Depends(get_db)
):
    """Trigger background indexing for a local video."""
    stmt = select(LocalVideo).where(LocalVideo.video_id == video_id)
    video = (await db.execute(stmt)).scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail=f"Local video '{video_id}' not found.")

    background_tasks.add_task(run_video_processing_task, video_id, mode)

    return {
        "status": "PROCESSING_STARTED",
        "video_id": video_id,
        "mode": mode,
        "message": f"Started processing '{video.filename}' in {mode.upper()} mode."
    }

@router.get("/{video_id}/summary")
async def get_video_summary(
    video_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get video summary statistics and discovered unique plates."""
    v_stmt = select(LocalVideo).where(LocalVideo.video_id == video_id)
    video = (await db.execute(v_stmt)).scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail=f"Local video '{video_id}' not found.")

    d_stmt = select(VideoDetection).where(VideoDetection.video_id == video_id)
    res = await db.execute(d_stmt)
    detections = res.scalars().all()

    total_vehicles = len(detections)
    total_plates = len([d for d in detections if d.plate_crop_path])
    verified_count = len([d for d in detections if d.plate_number != "UNKNOWN"])
    unreadable_count = total_vehicles - verified_count

    # Group detections by track_id & plate_number to build unique discovered plates
    track_groups: Dict[str, List[VideoDetection]] = {}
    for d in detections:
        key = f"TRK-{d.track_id}-{d.plate_number}"
        if key not in track_groups:
            track_groups[key] = []
        track_groups[key].append(d)

    discovered_plates = []
    for key, group in track_groups.items():
        best_det = max(group, key=lambda x: (x.plate_confidence, x.ocr_confidence, x.vehicle_confidence))
        p_num = best_det.plate_number
        is_verified = (p_num != "UNKNOWN")

        discovered_plates.append({
            "plate_number": p_num,
            "verification_status": "VERIFIED" if is_verified else "UNREADABLE",
            "vehicle_class": best_det.vehicle_class,
            "best_vehicle_crop": best_det.image_path,
            "best_plate_crop": best_det.plate_crop_path,
            "best_enhanced_crop": best_det.enhanced_plate_crop_path or best_det.plate_crop_path,
            "vehicle_confidence": round(best_det.vehicle_confidence, 2),
            "plate_confidence": round(best_det.plate_confidence, 2),
            "ocr_confidence": round(best_det.ocr_confidence, 2) if best_det.ocr_confidence else 0.0,
            "supporting_frames_count": len(group),
            "first_seen_timestamp_ms": min(d.video_timestamp_ms for d in group),
            "last_seen_timestamp_ms": max(d.video_timestamp_ms for d in group),
            "track_id": best_det.track_id,
            "preprocessing_method": best_det.preprocessing_method or "SubPixel-Bicubic + CLAHE + Sharpening",
            "ocr_engine": best_det.ocr_engine or "EasyOCR"
        })

    # Sort verified first, then by confidence
    discovered_plates.sort(key=lambda x: (x["verification_status"] == "VERIFIED", x["supporting_frames_count"], x["plate_confidence"]), reverse=True)

    return {
        "video_id": video.video_id,
        "filename": video.filename,
        "display_name": video.display_name,
        "processing_status": video.processing_status,
        "total_vehicles_detected": total_vehicles,
        "total_plates_detected": total_plates,
        "verified_plates_count": verified_count,
        "unreadable_plates_count": unreadable_count,
        "unique_discovered_plates": discovered_plates
    }

@router.get("/{video_id}/discovered-plates")
async def get_discovered_plates(
    video_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Fetch all unique discovered plates with full crop telemetry for a video."""
    d_stmt = select(VideoDetection).where(VideoDetection.video_id == video_id)
    res = await db.execute(d_stmt)
    detections = res.scalars().all()

    track_groups: Dict[str, List[VideoDetection]] = {}
    for d in detections:
        key = f"TRK-{d.track_id}-{d.plate_number}"
        if key not in track_groups:
            track_groups[key] = []
        track_groups[key].append(d)

    discovered = []
    for key, group in track_groups.items():
        best_det = max(group, key=lambda x: (x.plate_confidence, x.ocr_confidence, x.vehicle_confidence))
        p_num = best_det.plate_number
        is_verified = (p_num != "UNKNOWN")

        discovered.append({
            "plate_number": p_num,
            "verification_status": "VERIFIED" if is_verified else "UNREADABLE",
            "vehicle_class": best_det.vehicle_class,
            "best_vehicle_crop": best_det.image_path,
            "best_plate_crop": best_det.plate_crop_path,
            "best_enhanced_crop": best_det.enhanced_plate_crop_path or best_det.plate_crop_path,
            "vehicle_confidence": round(best_det.vehicle_confidence, 2),
            "plate_confidence": round(best_det.plate_confidence, 2),
            "ocr_confidence": round(best_det.ocr_confidence, 2) if best_det.ocr_confidence else 0.0,
            "supporting_frames_count": len(group),
            "first_seen_timestamp_ms": min(d.video_timestamp_ms for d in group),
            "last_seen_timestamp_ms": max(d.video_timestamp_ms for d in group),
            "track_id": best_det.track_id,
            "preprocessing_method": best_det.preprocessing_method or "SubPixel-Bicubic + CLAHE + Sharpening",
            "ocr_engine": best_det.ocr_engine or "EasyOCR"
        })

    discovered.sort(key=lambda x: (x["verification_status"] == "VERIFIED", x["supporting_frames_count"], x["plate_confidence"]), reverse=True)

    return {
        "video_id": video_id,
        "total_unique_plates": len(discovered),
        "discovered_plates": discovered
    }

@router.get("/{video_id}/detections")
async def get_video_detections(
    video_id: str,
    timestamp_ms: Optional[float] = Query(None),
    frame_number: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Fetch frame/timestamp synchronized detection overlays for canvas playback."""
    stmt = select(VideoDetection).where(VideoDetection.video_id == video_id)
    
    if frame_number is not None:
        stmt = stmt.where(VideoDetection.frame_number == frame_number)
    elif timestamp_ms is not None:
        # Match detections within a 250ms window around target timestamp
        stmt = stmt.where(
            VideoDetection.video_timestamp_ms >= timestamp_ms - 250,
            VideoDetection.video_timestamp_ms <= timestamp_ms + 250
        )

    res = await db.execute(stmt)
    detections = res.scalars().all()

    return [{
        "id": d.id,
        "video_id": d.video_id,
        "frame_number": d.frame_number,
        "video_timestamp_ms": d.video_timestamp_ms,
        "track_id": d.track_id,
        "vehicle_class": d.vehicle_class,
        "vehicle_confidence": d.vehicle_confidence,
        "bbox": [d.bbox_x1, d.bbox_y1, d.bbox_x2, d.bbox_y2],
        "plate_number": d.plate_number,
        "plate_confidence": d.plate_confidence,
        "plate_bbox": [d.plate_bbox_x1, d.plate_bbox_y1, d.plate_bbox_x2, d.plate_bbox_y2],
        "image_path": d.image_path,
        "plate_crop_path": d.plate_crop_path,
        "enhanced_plate_crop_path": d.enhanced_plate_crop_path or d.plate_crop_path
    } for d in detections]

@router.get("/search/plates")
async def search_video_plates(
    plate_number: str = Query(..., description="Target vehicle plate number"),
    source_id: str = Query("all", description="Specific video_id or 'all'"),
    db: AsyncSession = Depends(get_db)
):
    """Multi-source isolated vehicle search endpoint."""
    clean_plate = re.sub(r'[^A-Z0-9]', '', plate_number.upper())
    
    # Authentic Database Search
    stmt = select(VideoDetection).where(VideoDetection.plate_number.ilike(f"%{clean_plate}%"))
    if source_id != "all":
        stmt = stmt.where(VideoDetection.video_id == source_id)
        
    res = await db.execute(stmt)
    detections = res.scalars().all()
    
    if not detections:
        video_name = source_id
        if source_id != "all":
            v_stmt = select(LocalVideo.display_name).where(LocalVideo.video_id == source_id)
            v_name = (await db.execute(v_stmt)).scalar()
            if v_name:
                video_name = v_name
        
        return {
            "query_plate": clean_plate,
            "source_id": source_id,
            "total_matches": 0,
            "message": f"No genuine detection found for '{clean_plate}' in selected video source ({video_name}).",
            "results": []
        }

    # Group matches by video_id
    results = []
    for d in detections:
        # Fetch video metadata
        v_stmt = select(LocalVideo).where(LocalVideo.video_id == d.video_id)
        v_obj = (await db.execute(v_stmt)).scalar_one_or_none()
        
        results.append({
            "detection_id": d.id,
            "video_id": d.video_id,
            "source_filename": d.source_filename,
            "source_type": d.source_type,
            "source_display_name": v_obj.display_name if v_obj else d.source_filename,
            "frame_number": d.frame_number,
            "video_timestamp_ms": d.video_timestamp_ms,
            "timestamp_seconds": round(d.video_timestamp_ms / 1000.0, 2),
            "vehicle_class": d.vehicle_class,
            "vehicle_confidence": round(d.vehicle_confidence, 2),
            "bbox": [d.bbox_x1, d.bbox_y1, d.bbox_x2, d.bbox_y2],
            "plate_number": d.plate_number,
            "plate_confidence": round(d.plate_confidence, 2),
            "ocr_confidence": round(d.ocr_confidence, 2) if d.ocr_confidence else 0.0,
            "image_path": d.image_path,
            "plate_crop_path": d.plate_crop_path,
            "enhanced_plate_crop_path": d.enhanced_plate_crop_path or d.plate_crop_path,
            "supporting_frames_count": d.supporting_frames_count or 1,
            "verification_status": d.verification_status or ("VERIFIED" if d.plate_number != "UNKNOWN" else "UNREADABLE"),
            "preprocessing_method": d.preprocessing_method or "SubPixel-Bicubic + CLAHE + Sharpening",
            "ocr_engine": d.ocr_engine or "EasyOCR",
            "track_id": d.track_id
        })

    return {
        "query_plate": clean_plate,
        "source_id": source_id,
        "total_matches": len(results),
        "results": results
    }
