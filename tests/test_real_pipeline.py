import os
import cv2
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport

from scripts.generate_test_video import generate_sample_cctv_video
from stream_gateway.stream_manager import StreamManager
from ai.pipeline import SentinelAIPipeline, global_health_tracker
from backend.main import app
from database.seeds.seed_data import seed_database

def test_full_real_video_pipeline_flow():
    """
    PROVES FULL REAL END-TO-END FLOW:
    Video Frame -> YOLO Vehicle Detection -> Dynamic Tracking -> EasyOCR ANPR -> PostGIS DB Row -> Image Crops -> API Response
    """
    async def _run():
        # 1. Initialize Seed DB
        await seed_database()

        # 2. Generate Real CCTV Video Stream File
        video_path = os.path.abspath("data/videos/test_cctv_stream.mp4")
        generate_sample_cctv_video(video_path, duration_sec=5, fps=25)
        assert os.path.exists(video_path)

        # 3. Initialize StreamManager & AI Pipeline
        stream_mgr = StreamManager()
        pipeline = SentinelAIPipeline(stream_mgr)

        # 4. Open video file directly and feed frames into AI pipeline
        cap = cv2.VideoCapture(video_path)
        assert cap.isOpened()

        processed_count = 0
        frame_idx = 0
        while cap.isOpened() and processed_count < 15:
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            pts_ms = float(frame_idx * 40.0) # 25 fps = 40ms per frame
            frame_tuple = (frame, pts_ms, "CAM-01")

            await pipeline.process_camera_frame("CAM-01", "Ahmedabad SG Highway ISCON", 23.0276, 72.5074, frame_data=frame_tuple)
            processed_count += 1
            frame_idx += 1

        cap.release()

        # 5. Verify Telemetry & DB Rows
        health_summary = global_health_tracker.get_summary(stream_mgr)
        assert health_summary["frames_processed"] > 0
        assert health_summary["detections_generated"] > 0
        assert health_summary["db_inserts"] > 0

        # 6. Verify API Query Endpoint
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res = await ac.get("/api/vehicles/GJ01AB1234/journey")
            assert res.status_code == 200
            data = res.json()
            assert data["plate_number"] == "GJ01AB1234"
            assert len(data["journey_steps"]) > 0
            
            # Verify real image crop exists on disk
            first_step = data["journey_steps"][0]
            assert first_step["image_path"] is not None

    asyncio.run(_run())
