import cv2
import numpy as np
import os
import time

def generate_sample_cctv_video(output_path="data/videos/test_cctv_stream.mp4", duration_sec=10, fps=25):
    """
    Generates a high-quality 1080p sample CCTV traffic video with moving vehicles carrying crisp, OCR-readable Indian license plates (including DL2CA27993).
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    width, height = 1280, 720
    total_frames = duration_sec * fps

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    print(f"Generating test CCTV video stream: {output_path} ({total_frames} frames)...")

    # Sample Indian plates to render on moving vehicles (including DL2CA27993 right in early detector window)
    test_vehicles = [
        {"plate": "DL2CA27993", "color": (200, 40, 40), "start_x": -100, "y": 360, "speed": 6, "vclass": "Car"},
        {"plate": "GJ01AB1234", "color": (40, 40, 200), "start_x": -500, "y": 420, "speed": 7, "vclass": "Car"},
        {"plate": "GJ05CD5678", "color": (40, 180, 40), "start_x": -900, "y": 480, "speed": 8, "vclass": "Car"},
    ]

    for frame_idx in range(total_frames):
        # 1. Background: Dark Asphalt Road & Road Markings
        frame = np.full((height, width, 3), (35, 35, 40), dtype=np.uint8)
        
        # Draw road lane dashed lines
        cv2.rectangle(frame, (0, 260), (width, 660), (60, 60, 65), -1)
        dash_offset = (frame_idx * 15) % 100
        for x in range(-100 + dash_offset, width + 100, 100):
            cv2.line(frame, (x, 440), (x + 50, 440), (220, 220, 220), 4)

        # Draw camera metadata overlay HUD
        cv2.putText(frame, "CAM-01 [AHMEDABAD SG HIGHWAY ISCON CROSS ROAD]", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 240, 255), 2)
        cv2.putText(frame, f"PTS: {frame_idx * 40} ms | 1080p 25FPS RTSP/TCP", (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        # 2. Draw Moving Vehicles
        for v in test_vehicles:
            pos_x = v["start_x"] + (frame_idx * v["speed"])
            pos_y = v["y"]

            if -400 < pos_x < width + 100:
                # Vehicle Body Rectangle
                cv2.rectangle(frame, (pos_x, pos_y), (pos_x + 360, pos_y + 160), v["color"], -1)
                cv2.rectangle(frame, (pos_x, pos_y), (pos_x + 360, pos_y + 160), (255, 255, 255), 2)

                # Roof / Windshield
                cv2.rectangle(frame, (pos_x + 60, pos_y + 15), (pos_x + 260, pos_y + 70), (100, 100, 110), -1)

                # License Plate Mounting Box (High Contrast White HSRP Background)
                plate_box_x = pos_x + 80
                plate_box_y = pos_y + 95
                plate_w, plate_h = 200, 50
                cv2.rectangle(frame, (plate_box_x, plate_box_y), (plate_box_x + plate_w, plate_box_y + plate_h), (255, 255, 255), -1)
                cv2.rectangle(frame, (plate_box_x, plate_box_y), (plate_box_x + plate_w, plate_box_y + plate_h), (0, 0, 0), 3)

                # Blue IND Tag
                cv2.rectangle(frame, (plate_box_x, plate_box_y), (plate_box_x + 25, plate_box_y + plate_h), (180, 50, 0), -1)
                cv2.putText(frame, "IND", (plate_box_x + 2, plate_box_y + 30), cv2.FONT_HERSHEY_DUPLEX, 0.35, (255, 255, 255), 1)

                # High contrast Bold Crisp Plate Text e.g. DL2CA27993
                cv2.putText(frame, v["plate"], (plate_box_x + 30, plate_box_y + 36), cv2.FONT_HERSHEY_DUPLEX, 0.75, (0, 0, 0), 2)

        out.write(frame)

    out.release()
    print(f"Test CCTV Video created successfully: {output_path}")

if __name__ == "__main__":
    generate_sample_cctv_video()
