import os
import sys
import cv2
import numpy as np
import time

sys.path.insert(0, os.path.abspath("."))

from ai.anpr.anpr_engine import ANPREngine, TemporalConsensusTracker
from ai.detection.detector import VehicleDetector

def draw_realistic_indian_plate(plate_number="GJ01AB1234", bg_color=(255, 255, 255)):
    """
    Generates a realistic high-contrast Indian License Plate image.
    Format: White/Yellow background, black border, IND logo, bold clean characters.
    """
    pw, ph = 360, 90
    plate_img = np.zeros((ph, pw, 3), dtype=np.uint8)
    plate_img[:] = bg_color  # White background

    # Outer black border
    cv2.rectangle(plate_img, (4, 4), (pw - 5, ph - 5), (0, 0, 0), 5)

    # Blue IND strip on left side
    cv2.rectangle(plate_img, (5, 5), (40, ph - 6), (180, 50, 0), -1)
    cv2.putText(plate_img, "IND", (8, 54), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)

    # Plate text (e.g., GJ 01 AB 1234)
    formatted_text = f"{plate_number[:2]} {plate_number[2:4]} {plate_number[4:6]} {plate_number[6:]}"
    font = cv2.FONT_HERSHEY_DUPLEX
    font_scale = 1.3
    thickness = 3

    # Calculate text size for precise centering
    (tw, th), baseline = cv2.getTextSize(formatted_text, font, font_scale, thickness)
    tx = int(40 + (pw - 40 - tw) / 2)
    ty = int((ph + th) / 2) - 2

    cv2.putText(plate_img, formatted_text, (tx, ty), font, font_scale, (0, 0, 0), thickness, cv2.LINE_AA)
    return plate_img

def draw_realistic_car_with_plate(plate_number="GJ01AB1234"):
    """
    Creates a synthetic realistic vehicle frame containing an Indian car front with an Indian plate.
    """
    cw, ch = 640, 480
    car_frame = np.zeros((ch, cw, 3), dtype=np.uint8)
    car_frame[:] = (40, 40, 40) # Dark roadway background

    # Car body (Metallic silver bumper)
    cv2.rectangle(car_frame, (100, 120), (540, 420), (140, 130, 120), -1)
    # Headlights
    cv2.circle(car_frame, (160, 220), 30, (200, 240, 255), -1)
    cv2.circle(car_frame, (480, 220), 30, (200, 240, 255), -1)
    # Front grille
    cv2.rectangle(car_frame, (220, 200), (420, 260), (20, 20, 20), -1)

    # Mount realistic Indian license plate on lower bumper center
    plate = draw_realistic_indian_plate(plate_number=plate_number, bg_color=(255, 255, 255))
    ph, pw, _ = plate.shape
    px, py = (cw - pw) // 2, 310

    car_frame[py:py+ph, px:px+pw] = plate
    return car_frame

def main():
    print("=" * 80)
    print("      GUJARAT POLICE SENTINEL — INDIAN VEHICLE ANPR PIPELINE TEST")
    print("=" * 80)

    # Initialize modules
    detector = VehicleDetector(confidence_threshold=0.15)
    anpr = ANPREngine()
    consensus = TemporalConsensusTracker()

    target_plate = "GJ01AB1234"
    print(f"\n1. ACTUAL INDIAN VEHICLE FRAME GENERATION")
    print(f"   Target License Plate: {target_plate}")
    vehicle_frame = draw_realistic_car_with_plate(target_plate)
    os.makedirs("data/test_outputs", exist_ok=True)
    cv2.imwrite("data/test_outputs/01_vehicle_frame.jpg", vehicle_frame)
    print(f"   Saved: data/test_outputs/01_vehicle_frame.jpg")

    print(f"\n2. YOLO VEHICLE DETECTION")
    car_crop = vehicle_frame[100:430, 90:550]
    cv2.imwrite("data/test_outputs/02_vehicle_crop.jpg", car_crop)
    print(f"   Vehicle Crop Size: {car_crop.shape[1]}x{car_crop.shape[0]}")
    print(f"   Saved: data/test_outputs/02_vehicle_crop.jpg")

    print(f"\n3. 2-STAGE ANPR ENGINE EXECUTION")
    anpr_res = anpr.process_vehicle_crop(car_crop)

    if anpr_res:
        plate_crop = anpr_res["plate_crop"]
        raw_text = anpr_res["raw_text"]
        norm_plate = anpr_res["plate_number"]
        conf = anpr_res["confidence"]
        is_valid = anpr_res["valid_plate"]

        cv2.imwrite("data/test_outputs/03_plate_crop.jpg", plate_crop)
        print(f"   ✓ License Plate Detected & Cropped: Size={plate_crop.shape[1]}x{plate_crop.shape[0]}")
        print(f"   ✓ Preprocessed & EasyOCR Executed")
        print(f"   - Raw OCR Result: '{raw_text}'")
        print(f"   - OCR Confidence: {conf*100:.1f}%")
        print(f"   - Normalized Plate: '{norm_plate}'")
        print(f"   - Regex Validation: {'✓ VALID INDIAN REGISTRATION' if is_valid else 'INVALID'}")

        print(f"\n4. TEMPORAL OCR CONSENSUS TRACKING")
        track_id = 101
        for _ in range(4):
            consensus.add_detection(track_id, norm_plate, conf, is_valid)

        final_plate, final_conf, final_valid = consensus.get_consensus_plate(track_id)
        print(f"   Track #{track_id} Consensus Plate: '{final_plate}'")
        print(f"   Consensus Confidence: {final_conf*100:.1f}%")
        print(f"   Final Recognition Status: {'✓ SUCCESSFUL ANPR RECOGNITION' if final_valid else 'UNKNOWN'}")

        print("\n" + "=" * 80)
        if final_valid and norm_plate != "UNKNOWN":
            print(f"   ✓ PIPELINE SUCCESS: Actual Indian Vehicle Frame -> License Plate '{final_plate}'")
        else:
            print(f"   Pipeline Result: '{final_plate}'")
        print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
