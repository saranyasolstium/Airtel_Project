import queue
import threading
import numpy as np
import requests
import secrets
import base64
import time
import cv2
import re
import os
import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Tuple, Optional, Dict
from pathlib import Path
from collections import deque, defaultdict

# PaddleOCR imports
from paddleocr import PaddleOCR

from ultralytics import YOLO
from dotenv import load_dotenv

# -------------------- env/threads --------------------
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "4"
load_dotenv()

# -------------------- Singapore Plate Validation --------------------


def validate_singapore_plate(plate_text: str, is_bike: bool = False) -> Tuple[bool, str]:
    """
    Validate Singapore vehicle plate numbers.

    Singapore plate formats:
    For Cars/Trucks/Buses:
    1. Old format: SBA1234A (3 letters, 4 numbers, 1 letter)
    2. New format: SKZ1234C (3 letters, 4 numbers, 1 letter)
    3. Military: WRA1234A
    4. Classic/Historic: SBP1234A (P for classic)
    5. General: Any 6-8 alphanumeric characters

    For Motorcycles (Bikes):
    1. Standard: FB1234A (2 letters, 4 numbers, 1 letter)
    2. Newer: FX1234C (2 letters, 4 numbers, 1 letter)
    3. Can be 5-7 characters total

    Returns: (is_valid, reason)
    """
    if not plate_text:
        return False, "Empty plate"

    plate = plate_text.upper().strip()

    # Remove spaces and special characters
    plate = re.sub(r'[^A-Z0-9]', '', plate)

    if len(plate) < 2:
        return False, "Too short"

    # Bike-specific validation
    if is_bike:
        # Singapore bike plates are typically 5-7 characters
        if len(plate) < 4 or len(plate) > 7:
            return False, f"Bike plate length {len(plate)} invalid (should be 4-7)"

        # Common Singapore bike plate patterns:
        # 1. Starts with F (most common for bikes)
        # 2. Format: F?####? (F + letter + 4 digits + letter)
        # 3. Can also be: AB####, AZ####, etc.

        # Check if starts with common bike prefixes
        bike_prefixes = ['F', 'FB', 'FD', 'FE', 'FG', 'FH', 'FJ', 'FK',
                         'FL', 'FM', 'FN', 'FP', 'FQ', 'FR', 'FS', 'FT',
                         'FU', 'FV', 'FW', 'FX', 'FY', 'FZ']

        has_valid_prefix = any(plate.startswith(prefix)
                               for prefix in bike_prefixes)

        if not has_valid_prefix:
            # Check other valid bike patterns
            # Pattern: LetterLetter NumberNumberNumberNumber (e.g., AB1234)
            if len(plate) >= 5:
                if plate[0].isalpha() and plate[1].isalpha() and plate[2:].isdigit():
                    return True, "Valid bike plate (LLNNNN)"

            # Pattern: LetterLetter NumberNumberNumberNumber Letter (e.g., AB1234C)
            if len(plate) == 7:
                if (plate[0].isalpha() and plate[1].isalpha() and
                        plate[2:6].isdigit() and plate[6].isalpha()):
                    return True, "Valid bike plate (LLNNNNL)"

        # If starts with F, it's likely a valid bike plate
        if plate.startswith('F'):
            return True, "Valid bike plate (F-series)"

        # Still accept if it meets basic alphanumeric requirements
        if re.match(r'^[A-Z]{1,2}[A-Z0-9]{3,6}$', plate):
            return True, "Valid bike plate (general)"

        return False, "Invalid bike plate format"

    # Car/Truck/Bus validation
    else:
        # Singapore car plates are typically 6-8 characters
        if len(plate) < 6 or len(plate) > 10:
            return False, f"Car plate length {len(plate)} invalid (should be 6-10)"

        # Common Singapore car plate patterns:
        # 1. Starts with S (most common)
        # 2. Format: S??####? (S + 2 letters + 4 digits + optional letter)
        # 3. Can also start with other letters for special vehicles

        # Check for common Singapore car prefixes
        sg_prefixes = ['S', 'E', 'G', 'W', 'X', 'Y', 'Z']

        # Special cases
        if plate.startswith('S'):
            # Standard S-series plates
            if len(plate) >= 7:
                # Pattern: SLL####L (e.g., SBA1234A)
                if (plate[0] == 'S' and plate[1].isalpha() and plate[2].isalpha() and
                        plate[3:7].isdigit() and (len(plate) == 7 or (len(plate) == 8 and plate[7].isalpha()))):
                    return True, "Valid Singapore plate (S-series)"

        # Check for general alphanumeric pattern
        # Should have at least 2 letters and some numbers
        letters = sum(1 for c in plate if c.isalpha())
        digits = sum(1 for c in plate if c.isdigit())

        if letters >= 2 and digits >= 1:
            # Additional format checks
            if re.match(r'^[A-Z]{2,3}\d{1,4}[A-Z]?$', plate):
                return True, "Valid Singapore plate (general)"
            if re.match(r'^[A-Z]\d{1,5}[A-Z]?$', plate):
                return True, "Valid Singapore plate (single letter prefix)"
            if re.match(r'^[A-Z]{2}\d{3,4}[A-Z]?$', plate):
                return True, "Valid Singapore plate (LLNNN format)"

        # Accept general plates for now
        return True, "Accepted (general plate)"

# -------------------- PaddleOCR Configuration --------------------


class PaddleOCRWrapper:
    def __init__(self):
        print("Initializing PaddleOCR...")
        try:
            # Initialize PaddleOCR with new API (v2.8+)
            # Note: use_gpu parameter is now 'use_device'
            self.ocr = PaddleOCR(
                lang='en',  # Language
                use_angle_cls=True,  # Still works but deprecated warning
                show_log=False,  # Reduce log output
                rec_algorithm='CRNN',  # Recognition algorithm
                det_algorithm='DB'  # Detection algorithm
            )
            print("PaddleOCR initialized successfully")
        except Exception as e:
            print(f"Error initializing PaddleOCR: {e}")
            # Fallback initialization
            self.ocr = PaddleOCR(lang='en', show_log=False)
            print("PaddleOCR initialized with fallback settings")

    def read_text(self, image: np.ndarray) -> List[str]:
        """Extract text from image using PaddleOCR."""
        try:
            # Convert BGR to RGB (PaddleOCR expects RGB)
            if len(image.shape) == 3 and image.shape[2] == 3:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                rgb_image = image

            result = self.ocr.ocr(rgb_image, cls=True)
            texts = []
            if result and result[0]:
                for line in result[0]:
                    if line and len(line) >= 2:
                        text = line[1][0]
                        confidence = line[1][1]
                        if confidence > 0.5:  # Minimum confidence threshold
                            texts.append(text)
            return texts
        except Exception as e:
            print(f"PaddleOCR error: {e}")
            return []


try:
    paddle_ocr = PaddleOCRWrapper()
except Exception as e:
    print(f"Failed to initialize PaddleOCR: {e}")
    print("Falling back to simple OCR function")
    # Create a dummy OCR wrapper for fallback

    class DummyOCRWrapper:
        def read_text(self, image: np.ndarray) -> List[str]:
            print("Dummy OCR - no text detection available")
            return []
    paddle_ocr = DummyOCRWrapper()

# -------------------- files/paths --------------------
RTSP_URL = "https://api.vms.solstium.net/hls/df3e2570e7/index.m3u8"
OUTPUT_DIR = "car_captures_final"
os.makedirs(OUTPUT_DIR, exist_ok=True)

ACCEPTED_DIR = os.path.join(OUTPUT_DIR, "accepted")
os.makedirs(ACCEPTED_DIR, exist_ok=True)

# -------------------- Excel Storage for API Hits --------------------


class APIExcelStorage:
    def __init__(self, output_dir="car_captures_final"):
        self.output_dir = output_dir
        self.excel_path = os.path.join(output_dir, "api_hits.xlsx")
        self.columns = ["timestamp", "plate_number", "api_status", "http_status",
                        "response_text", "image_path", "vehicle_type", "confidence",
                        "validation_result", "is_bike"]
        self.df = pd.DataFrame(columns=self.columns)

        # Load existing data if file exists
        if os.path.exists(self.excel_path):
            self.df = pd.read_excel(self.excel_path)
            print(f"Loaded existing API hits from {self.excel_path}")
        else:
            print(f"Creating new API hits storage at {self.excel_path}")

    def add_record(self, plate_number: str, api_status: str, http_status: Optional[int] = None,
                   response_text: Optional[str] = None, image_path: Optional[str] = None,
                   vehicle_type: Optional[str] = None, confidence: Optional[float] = None,
                   validation_result: Optional[str] = None, is_bike: bool = False):
        """Add a record to the Excel file"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "plate_number": plate_number,
            "api_status": api_status,
            "http_status": http_status,
            "response_text": str(response_text)[:200] if response_text else "",
            "image_path": image_path,
            "vehicle_type": vehicle_type,
            "confidence": confidence,
            "validation_result": validation_result or "",
            "is_bike": is_bike
        }

        # Add to DataFrame
        self.df = pd.concat(
            [self.df, pd.DataFrame([record])], ignore_index=True)

        # Save to Excel
        try:
            self.df.to_excel(self.excel_path, index=False)
            print(f"Saved API hit to Excel: {plate_number} - {api_status}")
        except Exception as e:
            print(f"Error saving to Excel: {e}")

    def get_stats(self) -> Dict:
        """Get basic statistics from stored data"""
        if self.df.empty:
            return {"total_hits": 0, "successful": 0, "failed": 0, "bikes": 0, "cars": 0}

        total = len(self.df)
        successful = len(self.df[self.df["api_status"] == "success"])
        failed = total - successful
        bikes = len(self.df[self.df["is_bike"] == True])
        cars = len(self.df[self.df["is_bike"] == False])

        return {
            "total_hits": total,
            "successful": successful,
            "failed": failed,
            "bikes": bikes,
            "cars": cars,
            "last_plate": self.df.iloc[-1]["plate_number"] if total > 0 else None,
            "last_timestamp": self.df.iloc[-1]["timestamp"] if total > 0 else None
        }


api_storage = APIExcelStorage()

# -------------------- Simple Statistics --------------------


class SimpleStats:
    def __init__(self):
        self.start_time = time.time()
        self.paddle_ocr_calls = 0
        self.successful_ocr = 0
        self.failed_ocr = 0
        self.validated_plates = 0
        self.rejected_plates = 0
        self.duplicate_rejects = 0  # Track duplicate rejections
        self.vehicles_detected = defaultdict(int)
        self.plates_detected = []
        self.detected_plates_history = {}  # Track plate detection history

    def update_excel_stats(self):
        """Update statistics in Excel file"""
        stats = api_storage.get_stats()
        return f"API Hits: {stats['successful']}/{stats['total_hits']} successful, Bikes: {stats['bikes']}, Cars: {stats['cars']}"


stats = SimpleStats()

# -------------------- models ------------------------
# Skip YOLO model source check to speed up initialization
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
try:
    car_model = YOLO("yolov8n.pt")   # vehicle detector + tracker
    print("YOLO model loaded successfully")
except Exception as e:
    print(f"Error loading YOLO model: {e}")
    raise

# -------------------- tracker -----------------------
TRACKER_CFG = "bytetrack.yaml"

# -------------------- thresholds --------------------
CONFIDENCE_THRESHOLD = 0.35
PROCESS_EVERY_N_FRAMES = 2

RECONNECT_DELAY_SEC = 5
MAX_RECONNECT_ATTEMPTS = 10

# Attempt spacing
MIN_SECONDS_BETWEEN_OCR = 0.8
MAX_OCR_ATTEMPTS_PER_TRACK = 3

# geometry gates - DIFFERENT FOR BIKES
MIN_CAR_AR, MAX_CAR_AR = 1.0, 4.0
MIN_BIKE_AR, MAX_BIKE_AR = 0.5, 2.5
MIN_CAR_AREA = 1500
MIN_BIKE_AREA = 800

# Zone polygon
ZONE_POINTS = np.array([[57, 271], [496, 269], [557, 472], [
                       71, 475], [61, 273]], np.int32)

# -------------------- Image Quality Functions --------------------


def should_process_for_ocr(car_image: np.ndarray) -> bool:
    """Check if image is good enough for OCR."""
    if car_image is None or car_image.size == 0:
        return False

    # Check minimum size
    h, w = car_image.shape[:2]
    if w < 100 or h < 50:
        return False

    # Check sharpness
    if is_image_blurry(car_image, threshold=80.0):
        return False

    # Check brightness
    gray = cv2.cvtColor(car_image, cv2.COLOR_BGR2GRAY)
    brightness = np.mean(gray)
    if brightness < 40 or brightness > 200:
        return False

    return True


def sharpness_score(img_bgr: np.ndarray) -> float:
    try:
        g = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        return float(cv2.Laplacian(g, cv2.CV_64F).var())
    except Exception:
        return 0.0


def is_image_blurry(img: np.ndarray, threshold: float = 100.0) -> bool:
    """Check if image is too blurry for OCR"""
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        return laplacian_var < threshold
    except Exception:
        return True


def enhance_for_ocr(car_bgr: np.ndarray) -> np.ndarray:
    """Enhance the entire car image for better plate reading."""
    try:
        # Resize if too small but maintain aspect ratio
        h, w = car_bgr.shape[:2]
        if w < 400:
            scale = 400 / w
            new_w = 400
            new_h = int(h * scale)
            car_bgr = cv2.resize(car_bgr, (new_w, new_h),
                                 interpolation=cv2.INTER_CUBIC)

        # Apply CLAHE for better contrast
        lab = cv2.cvtColor(car_bgr, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        lab = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        # Light denoising
        enhanced = cv2.bilateralFilter(enhanced, 5, 75, 75)
        return enhanced
    except Exception:
        return car_bgr

# -------------------- PaddleOCR Functions --------------------


def read_plate_paddle_sync(car_bgr: np.ndarray, is_bike: bool = False) -> Optional[str]:
    """Extract plate text using PaddleOCR."""
    try:
        if car_bgr is None or car_bgr.size == 0:
            return None

        # Skip blurry images
        if is_image_blurry(car_bgr, threshold=150.0):
            print("Skipping blurry image for PaddleOCR")
            return None

        # Enhance the entire car image for OCR only
        car_bgr_enhanced = enhance_for_ocr(car_bgr)

        stats.paddle_ocr_calls += 1

        # Use PaddleOCR to read text
        texts = paddle_ocr.read_text(car_bgr_enhanced)

        if not texts:
            print("No text detected by PaddleOCR")
            stats.failed_ocr += 1
            return None

        print(f"PaddleOCR detected texts: {texts}")

        # Find the most likely plate number from detected texts
        best_plate = None
        best_confidence = 0
        for text in texts:
            # Clean the text
            clean_text = re.sub(r'[^A-Z0-9]', '', text.upper())

            if len(clean_text) < 4 or len(clean_text) > 10:
                continue

            # Validate with Singapore plate rules
            is_valid, reason = validate_singapore_plate(clean_text, is_bike)

            if is_valid:
                # For simplicity, take the first valid plate
                best_plate = clean_text
                print(f"Found valid plate: {best_plate} - {reason}")
                break

        if not best_plate:
            print("No valid Singapore plate found in OCR results")
            stats.failed_ocr += 1
            return None

        stats.successful_ocr += 1
        stats.validated_plates += 1
        stats.plates_detected.append({
            "plate": best_plate,
            "timestamp": datetime.now().isoformat(),
            "source": "paddle",
            "is_bike": is_bike,
            "validation": reason
        })

        vehicle_type = "motorcycle" if is_bike else "vehicle"
        print(f"PaddleOCR successful: {best_plate} ({vehicle_type})")
        return best_plate

    except Exception as e:
        print(f"PaddleOCR error: {e}")
        stats.failed_ocr += 1
        return None

# -------------------- Duplicate Detection Prevention --------------------


def is_duplicate_plate(plate_text: str, is_bike: bool = False, cooldown_seconds: int = 30) -> Tuple[bool, str]:
    """
    Check if a plate was detected recently to prevent duplicates.

    Args:
        plate_text: The plate number to check
        is_bike: Whether it's a bike plate
        cooldown_seconds: Time to wait before allowing same plate again

    Returns:
        Tuple of (is_duplicate, reason)
    """
    if not plate_text:
        return False, "Empty plate"

    plate_text = plate_text.upper().strip()

    # Check plate history
    if plate_text in stats.detected_plates_history:
        last_seen = stats.detected_plates_history[plate_text]
        time_since = time.time() - last_seen

        if time_since < cooldown_seconds:
            stats.duplicate_rejects += 1
            return True, f"Duplicate plate detected. Last seen {time_since:.1f} seconds ago (cooldown: {cooldown_seconds}s)"

    # Update history
    stats.detected_plates_history[plate_text] = time.time()

    # Clean old entries (older than 1 hour)
    current_time = time.time()
    stats.detected_plates_history = {
        plate: timestamp for plate, timestamp in stats.detected_plates_history.items()
        if current_time - timestamp < 3600
    }

    return False, "New plate detected"


# -------------------- API push --------------------
API_URL = "https://visitormanagement.solstium.net/security_monitoring/api/admin/store_feed"


def push_api_base64(img64: str, plate: Optional[str], is_bike: bool = False):
    try:
        # Check for duplicate plate
        if plate and plate != "UNKNOWN":
            is_duplicate, reason = is_duplicate_plate(plate, is_bike)
            if is_duplicate:
                print(f"Skipping API push (duplicate): {reason}")

                # Log duplicate in Excel
                api_storage.add_record(
                    plate_number=plate,
                    api_status="rejected_duplicate",
                    http_status=None,
                    response_text=reason,
                    vehicle_type="motorcycle" if is_bike else "car",
                    is_bike=is_bike
                )
                return False

        # Modify object classification based on vehicle type
        vehicle_class = "motorcycle" if is_bike else "car/truck"
        payload = {
            "_id": secrets.token_hex(8),
            "object_classification": f"Singapore {vehicle_class}, p:88.0%",
            "type": "license_plate",
            "uiType": "license_plate",
            "time": int(time.time() * 1000),
            "feedName": "Visitor Lane",
            "feedId": "",
            "locationId": "26f697c540f2015daf77f4a",
            "locationName": "Skywood",
            "license_plate_number": (plate or "UNKNOWN"),
            "timezone": "Skywood",
            "image_base64": img64,
            "vehicle_type": "motorcycle" if is_bike else "car"
        }
        r = requests.post(API_URL, json=payload, timeout=15)
        print(f"API: {r.status_code} {r.text[:120]}")

        if r.status_code == 200:
            # Store in Excel
            api_storage.add_record(
                plate_number=plate or "UNKNOWN",
                api_status="success",
                http_status=r.status_code,
                response_text=r.text[:200],
                vehicle_type="motorcycle" if is_bike else "car",
                is_bike=is_bike
            )
            return True
        else:
            # Store failure in Excel
            api_storage.add_record(
                plate_number=plate or "UNKNOWN",
                api_status="failed",
                http_status=r.status_code,
                response_text=r.text[:200],
                vehicle_type="motorcycle" if is_bike else "car",
                is_bike=is_bike
            )
            return False

    except Exception as e:
        print(f"API push error: {e}")
        # Store error in Excel
        api_storage.add_record(
            plate_number=plate or "UNKNOWN",
            api_status="error",
            http_status=None,
            response_text=str(e)[:200],
            vehicle_type="motorcycle" if is_bike else "car",
            is_bike=is_bike
        )
        return False


# -------------------- Combined image functions --------------------
BANNER_BGR = (43, 22, 10)


def make_combined_image_from_car(car_image: np.ndarray, plate_text: Optional[str], is_bike: bool = False) -> Optional[Tuple[np.ndarray, str]]:
    """Create combined image from the ORIGINAL car image (not enhanced)."""
    if car_image is None or car_image.size == 0:
        return None, None

    # Use ORIGINAL image for display (not enhanced)
    display_image = car_image.copy()

    h = display_image.shape[0]
    banner_w = int(max(260, 0.65 * h))
    banner = np.full((h, banner_w, 3), BANNER_BGR, dtype=np.uint8)

    txt = (plate_text or "").strip() or "UNKNOWN"
    full_text = f"{txt}"

    font = cv2.FONT_HERSHEY_SIMPLEX

    # auto-scale text
    margin = int(0.12 * h)
    max_w = banner_w - 2 * margin
    max_h = h - 2 * margin

    lo, hi = 0.5, 9.0
    best_scale = lo
    while hi - lo > 0.02:
        mid = (lo + hi) / 2.0
        (tw, th), _ = cv2.getTextSize(full_text, font, mid, 8)
        if tw <= max_w and th <= max_h:
            best_scale = mid
            lo = mid
        else:
            hi = mid

    (tw, th), _ = cv2.getTextSize(full_text, font, best_scale, 8)
    tx = (banner_w - tw) // 2
    ty = (h + th) // 2 - int(0.05 * h)

    cv2.putText(banner, full_text, (tx, ty), font,
                best_scale, (0, 0, 0), 18, cv2.LINE_AA)
    cv2.putText(banner, full_text, (tx, ty), font, best_scale,
                (25, 25, 25), 12, cv2.LINE_AA)
    cv2.putText(banner, full_text, (tx, ty), font, best_scale,
                (230, 210, 60), 6, cv2.LINE_AA)
    cv2.putText(banner, full_text, (tx, ty), font, best_scale,
                (255, 240, 120), 2, cv2.LINE_AA)

    combined = np.hstack([display_image, banner])

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_txt = re.sub(r"[^A-Za-z0-9]+", "", txt)
    out_path = os.path.join(
        ACCEPTED_DIR, f"combined_{ts}_{'BIKE' if is_bike else 'CAR'}_{safe_txt or 'UNKNOWN'}.jpg")
    cv2.imwrite(out_path, combined, [cv2.IMWRITE_JPEG_QUALITY, 95])

    return combined, out_path


def push_combined_from_car_image(car_image: np.ndarray, plate_text: Optional[str], is_bike: bool = False):
    """Push combined image using the ORIGINAL car image."""
    if not plate_text or plate_text == "UNREADABLE":
        print("Skipping API push: No valid plate text")
        return None

    # Validate with Singapore plate rules
    is_valid, reason = validate_singapore_plate(plate_text, is_bike)

    if not is_valid:
        print(
            f"Skipping API push: Invalid Singapore plate: {plate_text} - {reason}")

        # Log rejected plate
        api_storage.add_record(
            plate_number=plate_text,
            api_status="rejected_invalid",
            http_status=None,
            response_text=reason,
            image_path=None,
            vehicle_type="motorcycle" if is_bike else "car",
            validation_result=reason,
            is_bike=is_bike
        )
        stats.rejected_plates += 1
        return None

    # Create and push the image with ORIGINAL car image
    combined, out_path = make_combined_image_from_car(
        car_image, plate_text, is_bike)
    if combined is None:
        return None

    ok, buf = cv2.imencode(".jpg", combined, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if not ok:
        return out_path

    img64 = base64.b64encode(buf.tobytes()).decode("utf-8")
    success = push_api_base64(img64, plate_text, is_bike)

    if success:
        print(
            f"API push successful for plate: {plate_text} ({'BIKE' if is_bike else 'CAR'})")
    else:
        print(
            f"API push failed for plate: {plate_text} ({'BIKE' if is_bike else 'CAR'})")

    return out_path


def log_failed_attempt(plate_text: str, reason: str, is_bike: bool = False):
    """Log failed attempts to Excel."""
    try:
        # Log to Excel only (no image saving)
        api_storage.add_record(
            plate_number=plate_text or "NO_PLATE",
            api_status=f"rejected_{reason}",
            http_status=None,
            response_text=reason,
            image_path=None,
            vehicle_type="motorcycle" if is_bike else "car",
            is_bike=is_bike
        )

        print(
            f"Logged failed attempt: {reason} - {plate_text} ({'BIKE' if is_bike else 'CAR'})")
    except Exception as e:
        print(f"Error logging failed attempt: {e}")

# -------------------- Preview Window Functions --------------------


class PreviewWindow:
    def __init__(self, window_name="Vehicle Detection Preview"):
        self.window_name = window_name
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 1280, 720)

        # Status text positions
        self.status_y = 30
        self.line_height = 30

    def update(self, frame, stats_text, detection_info=None):
        """Update the preview window with current frame and status."""
        display_frame = frame.copy()

        # Draw zone polygon
        cv2.polylines(display_frame, [ZONE_POINTS], True, (0, 255, 0), 2)

        # Draw statistics overlay
        y = self.status_y
        for line in stats_text.split('\n'):
            cv2.putText(display_frame, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 255, 0), 2)
            y += self.line_height

        # Draw detection info if available
        if detection_info:
            info_y = y + 20
            for key, value in detection_info.items():
                text = f"{key}: {value}"
                cv2.putText(display_frame, text, (10, info_y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
                info_y += 20

        # Show frame
        cv2.imshow(self.window_name, display_frame)

    def close(self):
        cv2.destroyWindow(self.window_name)


# -------------------- OCR queue --------------------
ocr_queue = queue.Queue()
ocr_results = {}
ocr_lock = threading.Lock()
ocr_thread = None
stop_ocr_thread = False


def ocr_worker():
    global stop_ocr_thread
    while not stop_ocr_thread:
        try:
            job = ocr_queue.get(timeout=1.0)
            if job is None:
                continue

            tid, car_image, bbox, is_bike = job
            print(
                f"OCR worker: track {tid} | car={car_image.shape} | bike={is_bike}")

            plate_text = read_plate_paddle_sync(car_image, is_bike)

            with ocr_lock:
                ocr_results[tid] = {
                    "text": plate_text,
                    "timestamp": time.time(),
                    "bbox": bbox,
                    "car_image": car_image.copy(),  # Store ORIGINAL image
                    "is_bike": is_bike
                }

            print(
                f"OCR result track {tid}: {plate_text} ({'BIKE' if is_bike else 'CAR'})")
            ocr_queue.task_done()

        except queue.Empty:
            continue
        except Exception as e:
            print(f"OCR worker error: {e}")
            continue


def start_ocr_worker():
    global ocr_thread, stop_ocr_thread
    stop_ocr_thread = False
    ocr_thread = threading.Thread(target=ocr_worker, daemon=True)
    ocr_thread.start()
    print("OCR worker thread started (PaddleOCR - car images)")


def stop_ocr_worker():
    global stop_ocr_thread
    stop_ocr_thread = True
    if ocr_thread and ocr_thread.is_alive():
        ocr_thread.join(timeout=2.0)
    print("OCR worker thread stopped")

# -------------------- Track memory --------------------


@dataclass
class CarCandidate:
    image: np.ndarray  # Entire car image (ORIGINAL)
    conf: float        # Vehicle detection confidence
    sharp: float       # Sharpness score
    ts: float          # Timestamp


@dataclass
class TrackMem:
    last_seen: float
    bbox: Tuple[int, int, int, int]
    posted: bool
    in_zone: bool
    ocr_attempts: int
    last_ocr_time: float
    final_plate: Optional[str]
    candidates: List[CarCandidate]
    paddle_done: bool
    best_candidate_image: Optional[np.ndarray] = None
    is_bike: bool = False


tracks: Dict[int, TrackMem] = {}


def pick_best_candidate(cands: List[CarCandidate]) -> Optional[CarCandidate]:
    if not cands:
        return None

    # Filter out blurry images first
    non_blurry = []
    for c in cands:
        if not is_image_blurry(c.image, threshold=100.0):
            non_blurry.append(c)

    if not non_blurry:
        # If all are blurry, use the least blurry
        non_blurry = cands

    # Score based on detection confidence, image sharpness, and recency
    best = None
    best_score = -1e9
    for c in non_blurry:
        # Higher weight for sharpness and confidence
        score = (c.conf * 150.0) + (c.sharp / 10.0) + \
            (time.time() - c.ts) * -0.1
        if score > best_score:
            best_score = score
            best = c

    return best

# -------------------- Utils --------------------


def open_stream():
    """Open video stream (RTSP or HLS)."""
    try:
        # Try to open as regular video capture first
        cap = cv2.VideoCapture(RTSP_URL)

        # For HLS streams, we might need to set some properties
        if "m3u8" in RTSP_URL or "hls" in RTSP_URL:
            # Try different backends for HLS
            cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)

        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FPS, 15)

        # Try to read a frame to verify connection
        ret, frame = cap.read()
        if ret and frame is not None:
            print(f"Stream opened successfully. Frame size: {frame.shape}")
            return cap
        else:
            print("Warning: Could not read frame from stream")
            return cap
    except Exception as e:
        print(f"Error opening stream: {e}")
        return None


def restart(cap):
    print("Restarting stream...")
    if cap is not None:
        cap.release()
    time.sleep(RECONNECT_DELAY_SEC)
    return open_stream()


def zone_contains(cx, cy) -> bool:
    return cv2.pointPolygonTest(ZONE_POINTS, (float(cx), float(cy)), False) >= 0


# -------------------- main loop --------------------
print(f"Starting tracker + PaddleOCR (Async) | Vehicle Detection System")
print("Passing entire car images to PaddleOCR (no plate cropping)")
print("Only saving combined images for successful API pushes")
print("Singapore plate validation enabled")
print(f"API hits stored in Excel: {api_storage.excel_path}")
print("Duplicate detection prevention: 30 seconds cooldown")

# Start OCR worker thread
start_ocr_worker()

# Initialize preview window
preview = PreviewWindow()

# Open stream
cap = open_stream()
if cap is None or not cap.isOpened():
    print("Cannot open stream")
    stop_ocr_worker()
    preview.close()
    raise SystemExit(1)

frame_idx = 0
captures = 0
retries = 0

try:
    while True:
        ok, frame = cap.read()
        if not ok or frame is None or frame.size == 0:
            retries += 1
            if retries >= MAX_RECONNECT_ATTEMPTS:
                cap = restart(cap)
                retries = 0
            time.sleep(0.1)  # Slightly longer delay on error
            continue

        retries = 0
        frame_idx += 1

        # ---- OCR results back from worker ----
        with ocr_lock:
            done_ids = list(ocr_results.keys())
            for tid in done_ids:
                res = ocr_results.pop(tid, None)
                if not res:
                    continue
                if tid not in tracks:
                    continue
                T = tracks[tid]
                if T.posted:
                    continue

                plate_text = res["text"]
                car_image = res.get("car_image")  # ORIGINAL image
                is_bike = res.get("is_bike", False)

                if plate_text:
                    T.final_plate = plate_text
                    print(
                        f"Track {tid} final plate: {plate_text} ({'BIKE' if is_bike else 'CAR'})")

                    if T.in_zone and not T.posted:
                        # Validate with Singapore plate rules
                        is_valid, reason = validate_singapore_plate(
                            plate_text, is_bike)

                        if is_valid:
                            # Check for duplicate plate
                            is_duplicate, dup_reason = is_duplicate_plate(
                                plate_text, is_bike)

                            if not is_duplicate:
                                if car_image is not None:
                                    push_combined_from_car_image(
                                        car_image, T.final_plate, is_bike)
                                elif T.best_candidate_image is not None:
                                    push_combined_from_car_image(
                                        T.best_candidate_image, T.final_plate, is_bike)

                                captures += 1
                                T.posted = True
                                print(
                                    f"Posted track {tid} plate={T.final_plate} ({'BIKE' if is_bike else 'CAR'})")
                            else:
                                # Log duplicate detection
                                log_failed_attempt(
                                    plate_text, f"duplicate: {dup_reason}", is_bike)
                                print(
                                    f"Skipping duplicate plate: {plate_text}")

                        else:
                            # Log why it failed
                            log_failed_attempt(plate_text, reason, is_bike)

                        T.paddle_done = True
                        T.ocr_attempts = MAX_OCR_ATTEMPTS_PER_TRACK
                else:
                    T.paddle_done = True

        # ---- Detect/track every N frames ----
        if frame_idx % PROCESS_EVERY_N_FRAMES == 0:
            try:
                tr = car_model.track(
                    frame,
                    conf=CONFIDENCE_THRESHOLD,
                    persist=True,
                    verbose=False,
                    tracker=TRACKER_CFG,
                    classes=[2, 3, 5, 7],
                )

                if tr and len(tr):
                    r = tr[0]
                    if r.boxes is not None and hasattr(r.boxes, "id") and r.boxes.id is not None:
                        ids = r.boxes.id.int().cpu().tolist()
                        xyxy = r.boxes.xyxy.int().cpu().tolist()
                        confs = r.boxes.conf.cpu().tolist()
                        classes_list = r.boxes.cls.int().cpu().tolist()

                        for (tid, (x1, y1, x2, y2), c, class_id) in zip(ids, xyxy, confs, classes_list):
                            ar = (x2 - x1) / max(1, (y2 - y1))
                            area = (x2 - x1) * (y2 - y1)

                            is_bike = (class_id == 3)

                            # Update vehicle statistics
                            if is_bike:
                                stats.vehicles_detected["bike"] += 1
                                if ar < MIN_BIKE_AR or ar > MAX_BIKE_AR or area < MIN_BIKE_AREA:
                                    continue
                            else:
                                vehicle_type = {2: "car", 5: "bus", 7: "truck"}.get(
                                    class_id, "vehicle")
                                stats.vehicles_detected[vehicle_type] += 1
                                if ar < MIN_CAR_AR or ar > MAX_CAR_AR or area < MIN_CAR_AREA:
                                    continue

                            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
                            in_zone = zone_contains(cx, cy)

                            now = time.time()
                            if tid not in tracks:
                                tracks[tid] = TrackMem(
                                    last_seen=now,
                                    bbox=(x1, y1, x2, y2),
                                    posted=False,
                                    in_zone=False,
                                    ocr_attempts=0,
                                    last_ocr_time=0.0,
                                    final_plate=None,
                                    candidates=[],
                                    paddle_done=False,
                                    best_candidate_image=None,
                                    is_bike=is_bike
                                )

                            T = tracks[tid]
                            T.last_seen = now
                            T.bbox = (x1, y1, x2, y2)
                            T.in_zone = in_zone
                            T.is_bike = is_bike

                            if T.posted:
                                continue

                            if T.final_plate and T.in_zone:
                                # Check for duplicate plate
                                is_duplicate, dup_reason = is_duplicate_plate(
                                    T.final_plate, T.is_bike)

                                if not is_duplicate:
                                    if T.best_candidate_image is not None:
                                        push_combined_from_car_image(
                                            T.best_candidate_image, T.final_plate, T.is_bike)
                                    captures += 1
                                    T.posted = True
                                    print(
                                        f"Posted track {tid} plate={T.final_plate} ({'BIKE' if T.is_bike else 'CAR'})")
                                else:
                                    print(
                                        f"Skipping duplicate plate: {T.final_plate}")
                                continue

                            # ---- Collect car images when in zone ----
                            if in_zone and (not T.posted) and (T.ocr_attempts < MAX_OCR_ATTEMPTS_PER_TRACK):
                                if time.time() - T.last_ocr_time >= MIN_SECONDS_BETWEEN_OCR:
                                    car_roi = frame[y1:y2, x1:x2]
                                    if car_roi is not None and car_roi.size > 0:
                                        # Quality check
                                        if should_process_for_ocr(car_roi):
                                            sharp = sharpness_score(car_roi)
                                            vehicle_type = "bike" if is_bike else "car"

                                            T.candidates.append(CarCandidate(
                                                image=car_roi.copy(),  # ORIGINAL image
                                                conf=c,
                                                sharp=sharp,
                                                ts=time.time()
                                            ))

                                            T.ocr_attempts += 1
                                            T.last_ocr_time = time.time()
                                            print(
                                                f"{vehicle_type.upper()} image collected for track {tid} | conf={c:.2f} sharp={sharp:.0f}")
                                        else:
                                            print(
                                                f"Skipping low-quality image for track {tid}")

                            # ---- When enough candidates collected, do ONE PaddleOCR call ----
                            if in_zone and (not T.posted) and (not T.paddle_done):
                                if len(T.candidates) >= 2 or T.ocr_attempts >= MAX_OCR_ATTEMPTS_PER_TRACK:
                                    best = pick_best_candidate(T.candidates)
                                    if best is not None:
                                        T.best_candidate_image = best.image.copy()

                                        ocr_queue.put(
                                            (tid, best.image, (x1, y1, x2, y2), T.is_bike))
                                        T.paddle_done = True
                                        vehicle_type = "bike" if T.is_bike else "car"
                                        print(
                                            f"Submitted ONE PaddleOCR for track {tid} ({vehicle_type})")
            except Exception as e:
                print(f"Error in detection/tracking: {e}")

        # ---- Update Preview Window ----
        # Prepare stats text for display
        stats_text = f"Frame: {frame_idx} | Captures: {captures}"
        stats_text += f"\nPaddleOCR calls: {stats.paddle_ocr_calls}"
        stats_text += f"\nSuccessful OCR: {stats.successful_ocr} | Failed: {stats.failed_ocr}"
        stats_text += f"\nDuplicates rejected: {stats.duplicate_rejects}"
        stats_text += f"\nActive tracks: {len(tracks)}"

        # Show vehicle counts
        vehicle_counts = ", ".join(
            [f"{k}: {v}" for k, v in stats.vehicles_detected.items()])
        stats_text += f"\nVehicles: {vehicle_counts}"

        # Show API stats
        api_stats = api_storage.get_stats()
        stats_text += f"\nAPI: {api_stats['successful']}/{api_stats['total_hits']} success"

        # Prepare detection info
        detection_info = {}
        if tracks:
            active_in_zone = sum(1 for t in tracks.values() if t.in_zone)
            detection_info["Active in zone"] = active_in_zone

            # Show last successful plate if any
            if stats.plates_detected:
                last_plate = stats.plates_detected[-1]
                detection_info["Last plate"] = f"{last_plate['plate']} ({'BIKE' if last_plate['is_bike'] else 'CAR'})"

        # Update preview window
        preview.update(frame, stats_text, detection_info)

        # Check for ESC key press to exit
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC key
            print("ESC pressed, exiting...")
            break

        # cleanup old tracks
        now = time.time()
        dead = [tid for tid, T in tracks.items() if now - T.last_seen > 30]
        for tid in dead:
            tracks.pop(tid, None)

except KeyboardInterrupt:
    print("\nKeyboard interrupt detected, shutting down...")
except Exception as e:
    print(f"Unexpected error in main loop: {e}")
finally:
    print("Cleaning up resources...")
    stop_ocr_worker()
    if cap is not None:
        cap.release()
    preview.close()

    # Save final Excel
    try:
        api_storage.df.to_excel(api_storage.excel_path, index=False)
        print(f"Final data saved to {api_storage.excel_path}")
    except Exception as e:
        print(f"Error saving final Excel: {e}")

    print("\n" + "="*50)
    print("FINAL STATISTICS:")
    print("="*50)
    print(f"Runtime: {time.time() - stats.start_time:.1f} seconds")
    print(f"Total captures: {captures}")
    print(f"PaddleOCR calls: {stats.paddle_ocr_calls}")
    print(f"Successful OCR: {stats.successful_ocr}")
    print(f"Failed OCR: {stats.failed_ocr}")
    print(f"Validated plates: {stats.validated_plates}")
    print(f"Rejected plates: {stats.rejected_plates}")
    print(f"Duplicates rejected: {stats.duplicate_rejects}")
    print(f"Vehicles detected: {dict(stats.vehicles_detected)}")

    api_stats = api_storage.get_stats()
    print(
        f"API Hits in Excel: {api_stats['successful']}/{api_stats['total_hits']} successful")
    print(f"Bikes detected: {api_stats['bikes']}")
    print(f"Cars detected: {api_stats['cars']}")
    print(f"Excel file: {api_storage.excel_path}")
    print("="*50)
    print("Done.")
