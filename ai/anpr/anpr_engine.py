import re
import cv2
import time
import numpy as np
import logging
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger("sentinel.ai.anpr")

class ANPREngine:
    """
    Enterprise Automatic Number Plate Recognition (ANPR) & OCR Engine.
    
    Pipeline Stages:
    1. License Plate Localization (Sobel Morphological & Aspect Ratio Filtering)
    2. Plate Crop Extraction
    3. Image Preprocessing (Upscaling, CLAHE, Bilateral Denoising, Otsu Binarization)
    4. EasyOCR Execution with Alphanumeric Whitelist
    5. Strict Indian Registration Plate Normalization & Pattern Validation
    """
    def __init__(self, ocr_engine: str = "easyocr"):
        self.reader = None
        self._init_ocr(ocr_engine)

    def _init_ocr(self, ocr_engine: str):
        try:
            import easyocr
            from backend.config import settings
            logger.info("Initializing EasyOCR Engine for Indian License Plates (Alphanumeric Whitelist)...")
            self.reader = easyocr.Reader(['en'], gpu=settings.ENABLE_GPU, verbose=False)
            logger.info("EasyOCR initialized successfully.")
        except Exception as e:
            logger.warning(f"EasyOCR initialization deferred ({e}).")
            self.reader = None

    def detect_plate_region(self, vehicle_crop: np.ndarray) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
        """
        Stage 1 & 2: Dedicated Multi-Candidate License Plate Detector.
        Combines Sobel edge gradients, adaptive thresholding, and contour aspect-ratio
        filtering (typical Indian plate aspect ratio 2.2:1 to 6.5:1) to locate tight plate crops.
        """
        if vehicle_crop is None or vehicle_crop.size == 0:
            return vehicle_crop, (0, 0, 0, 0)

        vh, vw, _ = vehicle_crop.shape

        # Search primarily in lower 65% of vehicle crop where plates are mounted
        roi_y1 = int(vh * 0.35)
        roi = vehicle_crop[roi_y1:vh, :]

        if roi.size == 0:
            roi = vehicle_crop
            roi_y1 = 0

        rh, rw, _ = roi.shape

        # 1. Grayscale & Edge Detection
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # Sobel Horizontal Gradient to highlight vertical plate boundaries
        grad_x = cv2.Sobel(gray, cv2.CV_8U, 1, 0, ksize=3)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 3))
        morph = cv2.morphologyEx(grad_x, cv2.MORPH_CLOSE, kernel)
        _, thresh_otsu = cv2.threshold(morph, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Adaptive Thresholding candidate pass
        thresh_adapt = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 19, 9
        )
        kernel_adapt = cv2.getStructuringElement(cv2.MORPH_RECT, (13, 3))
        morph_adapt = cv2.morphologyEx(thresh_adapt, cv2.MORPH_CLOSE, kernel_adapt)

        best_bbox = None
        best_score = 0.0

        for thresh_img in [thresh_otsu, morph_adapt]:
            contours, _ = cv2.findContours(thresh_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                if h == 0 or w == 0:
                    continue

                aspect_ratio = float(w) / float(h)
                area = w * h
                roi_area = rw * rh

                # Indian standard plate aspect ratio: 2.2 to 6.5, area: 0.4% to 30% of ROI
                if 2.0 <= aspect_ratio <= 7.0 and (0.004 * roi_area <= area <= 0.35 * roi_area):
                    score = 1.0 - abs(aspect_ratio - 4.0) / 4.0
                    if score > best_score:
                        best_score = score
                        best_bbox = (x, y + roi_y1, w, h)

        if best_bbox is not None:
            px, py, pw, ph = best_bbox
            # Add subtle margin (3px) around plate bbox
            px_m = max(0, px - 3)
            py_m = max(0, py - 3)
            pw_m = min(vw - px_m, pw + 6)
            ph_m = min(vh - py_m, ph + 6)
            plate_crop = vehicle_crop[py_m:py_m + ph_m, px_m:px_m + pw_m]
            if plate_crop.size > 0:
                return plate_crop, (px_m, py_m, pw_m, ph_m)

        # Fallback Crop: Lower center 50% of vehicle crop
        fallback_y1 = int(vh * 0.45)
        fallback_y2 = int(vh * 0.95)
        fallback_x1 = int(vw * 0.10)
        fallback_x2 = int(vw * 0.90)
        
        fallback_crop = vehicle_crop[fallback_y1:fallback_y2, fallback_x1:fallback_x2]
        fallback_bbox = (fallback_x1, fallback_y1, fallback_x2 - fallback_x1, fallback_y2 - fallback_y1)
        
        return fallback_crop, fallback_bbox

    def preprocess_plate_image(self, plate_crop: np.ndarray) -> Tuple[np.ndarray, np.ndarray, str]:
        """
        Stage 3: OpenCV Sub-Pixel Zoom & Multi-Variant Pixel Enhancement Pipeline for License Plate OCR.
        Generates enhanced plate crop (Sub-Pixel Bicubic Zoom, Sharpening, CLAHE, Bilateral Denoising)
        and binarized threshold variant for robust character recognition.
        """
        if plate_crop is None or plate_crop.size == 0:
            return plate_crop, plate_crop, "None"

        h, w = plate_crop.shape[:2]

        # 1. OpenCV Sub-Pixel Bicubic Zooming to min 480px width for max detail
        scale = max(1.5, 480.0 / float(w)) if w > 0 else 2.0
        new_w = int(w * scale)
        new_h = max(60, int(h * scale))
        zoomed = cv2.resize(plate_crop, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

        # 2. Grayscale Conversion
        gray = cv2.cvtColor(zoomed, cv2.COLOR_BGR2GRAY) if len(zoomed.shape) == 3 else zoomed

        # 3. Unsharp Masking Filter (Sharpen blurred plate text)
        gaussian_blur = cv2.GaussianBlur(gray, (0, 0), 3.0)
        sharpened = cv2.addWeighted(gray, 1.6, gaussian_blur, -0.6, 0)

        # 4. CLAHE Contrast Enhancement (Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(sharpened)

        # 5. Bilateral Denoising Filter (Noise reduction with edge preservation)
        denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)

        # Convert enhanced grayscale back to 3-channel BGR for crop output storage
        enhanced_bgr = cv2.cvtColor(denoised, cv2.COLOR_GRAY2BGR)

        method_name = "SubPixel-Bicubic + CLAHE + Sharpening + Bilateral"
        return denoised, enhanced_bgr, method_name

    def process_vehicle_crop(self, vehicle_crop: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Full Multi-Pass ANPR Processing Pipeline:
        Vehicle Crop -> Candidate Detection -> Preprocessing -> EasyOCR -> Normalization & Validation.
        Uses dual-pass OCR (localized plate crop + lower vehicle ROI) to maximize recall on real video.
        """
        if vehicle_crop is None or vehicle_crop.size == 0:
            return None

        # Stage 1: Primary Candidate Plate Crop Detection
        plate_crop, plate_bbox = self.detect_plate_region(vehicle_crop)
        preprocessed, enhanced_plate_crop, method_used = self.preprocess_plate_image(plate_crop)

        raw_text = ""
        confidence = 0.0
        normalized_plate = None

        if self.reader is not None:
            try:
                results = self.reader.readtext(
                    preprocessed,
                    allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- ',
                    detail=1
                )
                text_blocks = []
                conf_scores = []
                for (bbox, text, prob) in results:
                    if prob > 0.15:
                        text_blocks.append(text)
                        conf_scores.append(prob)
                if text_blocks:
                    raw_text = " ".join(text_blocks)
                    confidence = float(np.mean(conf_scores))
                    normalized_plate = self.normalize_plate(raw_text)
            except Exception as e:
                logger.error(f"EasyOCR Error: {e}")

        # Secondary Pass: If primary crop failed to yield valid plate, run OCR on lower vehicle ROI
        if not normalized_plate and self.reader is not None:
            vh, vw = vehicle_crop.shape[:2]
            roi_y1 = int(vh * 0.45)
            roi_y2 = int(vh * 0.95)
            roi_x1 = int(vw * 0.05)
            roi_x2 = int(vw * 0.95)
            roi_crop = vehicle_crop[roi_y1:roi_y2, roi_x1:roi_x2]

            if roi_crop.size > 0:
                roi_prep, roi_enh, sec_method = self.preprocess_plate_image(roi_crop)
                try:
                    sec_results = self.reader.readtext(
                        roi_prep,
                        allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- ',
                        detail=1
                    )
                    sec_blocks = []
                    sec_confs = []
                    for (bbox, text, prob) in sec_results:
                        if prob > 0.15:
                            sec_blocks.append(text)
                            sec_confs.append(prob)
                    if sec_blocks:
                        sec_raw = " ".join(sec_blocks)
                        sec_norm = self.normalize_plate(sec_raw)
                        if sec_norm:
                            normalized_plate = sec_norm
                            raw_text = sec_raw
                            confidence = float(np.mean(sec_confs))
                            plate_crop = roi_crop
                            enhanced_plate_crop = roi_enh
                            method_used = f"ROI Fallback ({sec_method})"
                            plate_bbox = (roi_x1, roi_y1, roi_x2 - roi_x1, roi_y2 - roi_y1)
                except Exception as e:
                    logger.error(f"Secondary EasyOCR Error: {e}")

        if not normalized_plate or confidence < 0.25:
            return {
                "plate_number": "UNKNOWN",
                "raw_text": raw_text if raw_text else "N/A",
                "confidence": confidence,
                "valid_plate": False,
                "plate_crop": plate_crop,
                "enhanced_plate_crop": enhanced_plate_crop,
                "plate_bbox": plate_bbox,
                "preprocessing_method": method_used,
                "ocr_engine": "EasyOCR"
            }

        return {
            "plate_number": normalized_plate,
            "raw_text": raw_text,
            "confidence": confidence,
            "valid_plate": True,
            "plate_crop": plate_crop,
            "enhanced_plate_crop": enhanced_plate_crop,
            "plate_bbox": plate_bbox,
            "preprocessing_method": method_used,
            "ocr_engine": "EasyOCR"
        }

    @staticmethod
    def normalize_plate(raw_text: str) -> Optional[str]:
        """
        Stage 5: Normalize and Validate Indian Standard Registration Plates.
        Formats: "GJ01AB1234", "DL2CA27993", "DL02CA27993", "MH12DE5678".
        Applies character confusion repairs based on character position in Indian registration schema.
        
        Returns:
            Normalized plate string (e.g. "DL2CA27993") if valid, else None.
        """
        if not raw_text:
            return None

        # Split raw_text into tokens by space/newline to handle multi-line/multi-block OCR outputs
        tokens = [t.strip() for t in re.split(r'[\s\n\r,]+', raw_text) if t.strip()]
        # Also include the full joined string as a fallback token
        clean_full = re.sub(r'[^A-Z0-9]', '', raw_text.upper())
        if clean_full and clean_full not in tokens:
            tokens.append(clean_full)

        for token in tokens:
            clean_text = re.sub(r'[^A-Z0-9]', '', token.upper())

            # Strip leading IND / ID logo artifact printed on standard Indian plates
            if clean_text.startswith("IND") and len(clean_text) > 3:
                clean_text = clean_text[3:]
            elif clean_text.startswith("ID") and len(clean_text) > 2:
                clean_text = clean_text[2:]

            if len(clean_text) < 7 or len(clean_text) > 12:
                continue

            # Repair 6 -> G at start of state code e.g. 6J -> GJ
            if clean_text.startswith("6J"):
                clean_text = "G" + clean_text[1:]

            # Direct regex check on clean_text first
            match = re.search(r'^([A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{3,5})$', clean_text)
            if match:
                return match.group(1)

            # Repair 6 -> G / 0 -> O at start of state code
            if clean_text.startswith("6J"):
                clean_text = "G" + clean_text[1:]

            # State part: first 2 letters
            state_part = clean_text[0:2].replace('0', 'O').replace('1', 'I').replace('8', 'B').replace('5', 'S').replace('6', 'G')

            rest = clean_text[2:]
            if len(rest) < 4:
                continue

            # Try 3, 4, and 5-digit tail serial numbers
            for num_len in [4, 3, 5]:
                if len(rest) < num_len:
                    continue
                num_part = rest[-num_len:].replace('O', '0').replace('I', '1').replace('Z', '2').replace('S', '5').replace('B', '8').replace('G', '6')
                middle = rest[:-num_len]

                # Separate middle into district digits and series letters
                dist_chars = []
                series_chars = []
                for i, ch in enumerate(middle):
                    if i < 2 and (ch.isdigit() or ch in ['Z', 'O', 'I', 'B', 'S', 'G']):
                        dist_chars.append(ch.replace('Z', '2').replace('O', '0').replace('I', '1').replace('B', '8').replace('S', '5').replace('G', '6'))
                    else:
                        series_chars.append(ch.replace('0', 'O').replace('1', 'I').replace('8', 'B').replace('5', 'S').replace('4', 'A').replace('6', 'G'))

                dist_str = "".join(dist_chars)
                series_str = "".join(series_chars)

                candidate = f"{state_part}{dist_str}{series_str}{num_part}"
                match = re.search(r'^([A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{3,5})$', candidate)
                if match:
                    return match.group(1)

            # High-Recall Pattern Matcher for standard Indian plates (e.g., DL11CC2957, GJ01AB1234)
            fallback_match = re.search(r'([A-Z]{2}[0-9IZOBSG]{1,2}[A-Z40156]{1,3}[0-9IZOBSG]{3,4})', clean_text)
            if fallback_match:
                raw_cand = fallback_match.group(1)
                st = raw_cand[:2].replace('0', 'O').replace('1', 'I').replace('8', 'B').replace('5', 'S').replace('6', 'G')
                r = raw_cand[2:]
                tail_num = r[-4:].replace('O', '0').replace('I', '1').replace('Z', '2').replace('S', '5').replace('B', '8').replace('G', '6')
                mid = r[:-4]
                d_c = "".join([c.replace('Z', '2').replace('O', '0').replace('I', '1').replace('B', '8').replace('S', '5').replace('G', '6') for c in mid[:2] if c.isalnum()])
                s_c = "".join([c.replace('0', 'O').replace('1', 'I').replace('8', 'B').replace('5', 'S').replace('4', 'A').replace('6', 'G') for c in mid[2:] if c.isalnum()])
                res_cand = f"{st}{d_c}{s_c}{tail_num}"
                if len(res_cand) >= 7 and len(res_cand) <= 12:
                    return res_cand

        return None


class TemporalConsensusTracker:
    """
    Stage 6: Temporal OCR Consensus Tracker across consecutive video frames for the same track_id.
    Uses Weighted Majority Voting / Confidence Aggregation over a sliding frame window.
    """
    def __init__(self, max_history: int = 15):
        self.max_history = max_history
        self.track_history: Dict[int, List[Dict[str, Any]]] = {}

    def add_detection(self, track_id: int, plate_number: str, confidence: float, valid_plate: bool):
        """Add an OCR detection for a specific track_id."""
        if track_id not in self.track_history:
            self.track_history[track_id] = []

        history = self.track_history[track_id]
        history.append({
            "plate_number": plate_number,
            "confidence": confidence,
            "valid_plate": valid_plate,
            "timestamp": time.time()
        })

        if len(history) > self.max_history:
            history.pop(0)

    def get_consensus_plate(self, track_id: int) -> Tuple[str, float, bool]:
        """
        Compute weighted majority voting consensus plate for track_id.
        Returns (consensus_plate_number, aggregate_confidence, is_valid).
        """
        history = self.track_history.get(track_id, [])
        if not history:
            return "UNKNOWN", 0.0, False

        # Filter for valid plate readings
        valid_readings = [h for h in history if h["valid_plate"] and h["plate_number"] != "UNKNOWN"]

        if not valid_readings:
            best_raw = max(history, key=lambda x: x["confidence"])
            return best_raw["plate_number"], best_raw["confidence"], False

        if len(valid_readings) == 1:
            single = valid_readings[0]
            if single["confidence"] < 0.55:
                return "UNKNOWN", single["confidence"], False

        # Weighted Voting Score per candidate plate
        plate_scores: Dict[str, float] = {}
        plate_counts: Dict[str, int] = {}
        total_weight = 0.0

        current_t = time.time()
        for idx, item in enumerate(valid_readings):
            plate = item["plate_number"]
            conf = item["confidence"]
            # Recency weighting
            age_sec = max(0.1, current_t - item["timestamp"])
            weight = conf * (1.0 / (1.0 + 0.1 * age_sec))

            plate_scores[plate] = plate_scores.get(plate, 0.0) + weight
            plate_counts[plate] = plate_counts.get(plate, 0) + 1
            total_weight += weight

        # Pick candidate with highest weighted voting score
        best_plate = max(plate_scores, key=plate_scores.get)
        best_score = plate_scores[best_plate]
        avg_conf = float(best_score / float(plate_counts[best_plate]))

        return best_plate, min(0.99, avg_conf), True
