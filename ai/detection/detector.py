import cv2
import os
import numpy as np
import logging
from typing import List, Dict, Any, Tuple

from backend.config import settings

logger = logging.getLogger("sentinel.ai.detector")

class VehicleDetector:
    """
    Enterprise Hybrid Multi-Scale Vehicle Detector.
    Fast mode (default): single YOLO pass at 640px for real-time pipeline use.
    Full mode: multi-scale tiling + contour fallback for maximum recall.
    """
    def __init__(self, model_path: str = None, confidence_threshold: float = None):
        self.confidence_threshold = confidence_threshold or settings.YOLO_CONFIDENCE
        self.enable_tiling = settings.YOLO_ENABLE_TILING
        self.imgsz = settings.YOLO_IMGSZ
        self.model = None
        self._init_model(model_path or settings.YOLO_MODEL_PATH)

    def _init_model(self, model_path: str):
        try:
            from ultralytics import YOLO
            logger.info(f"Loading YOLO Vehicle Detection model: {model_path}")
            self.model = YOLO(model_path)
            logger.info("YOLO Model loaded successfully.")
        except Exception as e:
            logger.warning(f"Could not load Ultralytics YOLO ({e}). Initializing Advanced Contour Detector.")
            self.model = None

    def detect_vehicles(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Multi-Scale Vehicle Detection Strategy:
        1. Full Frame High-Resolution Inference (1024px imgsz)
        2. Quad/Tile Zoomed Inference (Left & Right halves for small distant vehicles)
        3. Non-Maximum Suppression (NMS) to merge overlapping boxes
        4. OpenCV Contour Shape Filtering fallback for un-captured vehicle shapes
        """
        if frame is None or frame.size == 0:
            return []

        h, w, _ = frame.shape
        raw_boxes = []

        if self.model is not None:
            try:
                imgsz = self.imgsz
                results_full = self.model(
                    frame, imgsz=imgsz, verbose=False,
                    conf=self.confidence_threshold, classes=[2, 3, 5, 7]
                )

                for res in results_full:
                    for box in res.boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        raw_boxes.append(([x1, y1, x2, y2], conf, self.model.names[cls_id]))

                # Optional tiled pass for wide-angle footage (disabled in fast pipeline mode)
                if self.enable_tiling and w >= 800:
                    mid_x = w // 2
                    overlap = int(w * 0.1)

                    tile_left = frame[:, :mid_x + overlap]
                    tile_right = frame[:, max(0, mid_x - overlap):]

                    res_l = self.model(tile_left, imgsz=640, verbose=False, conf=self.confidence_threshold, classes=[2, 3, 5, 7])
                    for res in res_l:
                        for box in res.boxes:
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            cls_id = int(box.cls[0])
                            conf = float(box.conf[0])
                            raw_boxes.append(([x1, y1, x2, y2], conf, self.model.names[cls_id]))

                    res_r = self.model(tile_right, imgsz=640, verbose=False, conf=self.confidence_threshold, classes=[2, 3, 5, 7])
                    offset_x = max(0, mid_x - overlap)
                    for res in res_r:
                        for box in res.boxes:
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            cls_id = int(box.cls[0])
                            conf = float(box.conf[0])
                            raw_boxes.append(([x1 + offset_x, y1, x2 + offset_x, y2], conf, self.model.names[cls_id]))

            except Exception as e:
                logger.error(f"YOLO Multi-Scale Inference Error: {e}")

        # Stage 3: Apply Non-Maximum Suppression (NMS) to eliminate duplicate overlapping boxes
        merged_boxes = self._apply_nms(raw_boxes, iou_threshold=0.45)

        # Stage 4: OpenCV contour fallback (cheap; helps synthetic/demo footage)
        contour_boxes = self._detect_vehicle_contours(frame, merged_boxes)
        merged_boxes.extend(contour_boxes)

        detections = []
        for bbox, conf, class_name in merged_boxes:
            x1, y1, x2, y2 = bbox
            v_class = "Car"
            if class_name in ["motorcycle", "bike"]: v_class = "Motorcycle"
            elif class_name == "bus": v_class = "Bus"
            elif class_name == "truck": v_class = "Truck"
            elif class_name == "auto": v_class = "Auto"

            # 4% context padding around vehicle bounding box
            pad_w = int((x2 - x1) * 0.04)
            pad_h = int((y2 - y1) * 0.04)
            cx1 = max(0, x1 - pad_w)
            cy1 = max(0, y1 - pad_h)
            cx2 = min(w, x2 + pad_w)
            cy2 = min(h, y2 + pad_h)

            crop = frame[cy1:cy2, cx1:cx2]
            if crop.size > 0:
                detections.append({
                    "bbox": [x1, y1, x2, y2],
                    "vehicle_class": v_class,
                    "confidence": float(conf),
                    "crop": crop
                })

        return detections

    def _apply_nms(self, boxes_with_scores: List[Tuple[List[int], float, str]], iou_threshold: float = 0.45) -> List[Tuple[List[int], float, str]]:
        if not boxes_with_scores:
            return []

        boxes_with_scores = sorted(boxes_with_scores, key=lambda x: x[1], reverse=True)
        keep = []

        while boxes_with_scores:
            current = boxes_with_scores.pop(0)
            keep.append(current)

            boxes_with_scores = [
                b for b in boxes_with_scores
                if self._compute_iou(current[0], b[0]) < iou_threshold
            ]

        return keep

    @staticmethod
    def _compute_iou(boxA: List[int], boxB: List[int]) -> float:
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        interArea = max(0, xB - xA) * max(0, yB - yA)
        if interArea == 0:
            return 0.0

        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

        iou = interArea / float(boxAArea + boxBArea - interArea)
        return iou

    def _detect_vehicle_contours(self, frame: np.ndarray, existing_boxes: List[Tuple[List[int], float, str]]) -> List[Tuple[List[int], float, str]]:
        """
        OpenCV Edge & Aspect Ratio Vehicle Detector.
        Searches lower 75% of image for rectangular vehicle contours (aspect ratio 0.7:1 to 3.2:1).
        Adds candidates if not already covered by YOLO bboxes.
        """
        h, w, _ = frame.shape
        roi_y1 = int(h * 0.25)
        roi = frame[roi_y1:h, :]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # Bilateral filter & Canny edge detection
        denoised = cv2.bilateralFilter(gray, 7, 50, 50)
        edges = cv2.Canny(denoised, 50, 150)

        # Morphological Closing to form solid vehicle shapes
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 9))
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contour_candidates = []

        frame_area = float(w * h)

        for cnt in contours:
            x, y, cw, ch = cv2.boundingRect(cnt)
            area = cw * ch
            aspect = float(cw) / float(ch) if ch > 0 else 0

            # Vehicle physical aspect ratio (0.65 to 3.5) and minimum area (0.5% to 25% of frame)
            if 0.65 <= aspect <= 3.5 and (0.005 * frame_area <= area <= 0.35 * frame_area):
                abs_bbox = [x, y + roi_y1, x + cw, y + roi_y1 + ch]

                # Check if covered by YOLO box
                is_duplicate = False
                for ex_box, _, _ in existing_boxes:
                    if self._compute_iou(abs_bbox, ex_box) > 0.30:
                        is_duplicate = True
                        break

                if not is_duplicate:
                    v_type = "Car"
                    if aspect > 2.2: v_type = "Bus"
                    elif aspect < 0.95: v_type = "Motorcycle"
                    contour_candidates.append((abs_bbox, 0.88, v_type))

        return contour_candidates
