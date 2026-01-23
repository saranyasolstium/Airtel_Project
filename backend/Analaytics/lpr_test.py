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

from ultralytics import YOLO
from dotenv import load_dotenv
import easyocr

# Import for better OCR
import io
from collections import deque, defaultdict

# -------------------- env/threads --------------------
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "4"
load_dotenv()

# -------------------- India Plate Validation --------------------


def validate_india_plate(plate_text: str, is_bike: bool = False) -> Tuple[bool, str]:
    """
    Validate Indian vehicle plate numbers.

    India plate formats:
    For Cars/Trucks/Buses:
    1. Standard format: DL01AB1234 (2 letters state, 2 digits district, 2 letters series, 4 digits)
    2. BH series: BH01AB1234 (Bharat series for inter-state)
    3. Commercial: DL01C12345 (C for commercial)
    4. Temporary: DL01TR1234 (TR for temporary)

    For Motorcycles (Bikes):
    1. Same format as cars but typically 4 digits at the end
    2. Example: DL01AB1234 (for bikes too)

    Military/Government:
    1. Military: DLD123456
    2. Government vehicles have blue plates
    """
    if not plate_text:
        return False, "Empty plate"

    plate = plate_text.upper().strip()

    # Remove spaces and special characters
    plate = re.sub(r'[^A-Z0-9]', '', plate)

    if len(plate) < 7:
        return False, "Too short (min 7 chars)"

    # List of Indian state codes (partial list)
    state_codes = [
        'AN', 'AP', 'AR', 'AS', 'BR', 'CH', 'CT', 'DL', 'DN', 'GA',
        'GJ', 'HR', 'HP', 'JH', 'JK', 'KA', 'KL', 'LD', 'MH', 'ML',
        'MN', 'MP', 'MZ', 'NL', 'OD', 'PB', 'PY', 'RJ', 'SK', 'TN',
        'TR', 'TS', 'UP', 'UK', 'WB'
    ]

    # Special series
    special_series = ['BH', 'CH', 'DH', 'TS', 'TR', 'SR']

    # Check format patterns
    patterns = [
        # Standard format: XX##XX#### (e.g., DL01AB1234)
        r'^([A-Z]{2})(\d{2})([A-Z]{1,2})(\d{4})$',

        # Format with 3 letters in series: XX###X####
        r'^([A-Z]{2})(\d{2})([A-Z]{2,3})(\d{4})$',

        # BH series: BH##XX####
        r'^(BH)(\d{2})([A-Z]{1,2})(\d{4})$',

        # Commercial vehicles: XX##X##### (5 digits)
        r'^([A-Z]{2})(\d{2})([A-Z]{1})(\d{5})$',

        # Older format or special cases
        r'^([A-Z]{2})(\d{1,4})([A-Z]{0,3})(\d{1,4})$',
    ]

    for pattern in patterns:
        match = re.match(pattern, plate)
        if match:
            # Check if state code is valid
            state_code = match.group(1)
            if pattern == patterns[0] or pattern == patterns[1]:
                if state_code not in state_codes and state_code not in special_series:
                    continue

            # Validate district code (should be 01-99)
            if len(match.groups()) > 1:
                district_code = match.group(2)
                if not district_code.isdigit():
                    continue
                district_num = int(district_code)
                if district_num < 1 or district_num > 99:
                    continue

            return True, f"Valid India {vehicle_type} plate"

    # If no pattern matches but looks plausible
    letters = sum(1 for c in plate if c.isalpha())
    digits = sum(1 for c in plate if c.isdigit())

    if letters >= 2 and digits >= 2:
        return True, "Plausible India plate (manual review)"

    return False, "Invalid India plate format"


# -------------------- Rapido OCR Configuration --------------------
# Initialize EasyOCR reader for Indian plates
# Using English only as Indian plates use Latin characters
try:
    reader = easyocr.Reader(['en'], gpu=False)  # Set gpu=True if you have CUDA
    print("EasyOCR initialized successfully")
except Exception as e:
    print(f"Error initializing EasyOCR: {e}")
    reader = None

# -------------------- files/paths --------------------
RTSP_URL = "rtsp://admin:Solstium@3042@10.34.157.12:15541/Streaming/Channels/102/"
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
                        "validation_result", "is_bike", "ocr_method"]
        self.df = pd.DataFrame(columns=self.columns)

        if os.path.exists(self.excel_path):
            self.df = pd.read_excel(self.excel_path)
            print(f"Loaded existing API hits from {self.excel_path}")
        else:
            print(f"Creating new API hits storage at {self.excel_path}")

    def add_record(self, plate_number: str, api_status: str, http_status: Optional[int] = None,
                   response_text: Optional[str] = None, image_path: Optional[str] = None,
                   vehicle_type: Optional[str] = None, confidence: Optional[float] = None,
                   validation_result: Optional[str] = None, is_bike: bool = False, ocr_method: str = "easyocr"):
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
            "is_bike": is_bike,
            "ocr_method": ocr_method
        }

        self.df = pd.concat(
            [self.df, pd.DataFrame([record])], ignore_index=True)

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
        self.easyocr_calls = 0
        self.successful_ocr = 0
        self.failed_ocr = 0
        self.validated_plates = 0
        self.rejected_plates = 0
        self.vehicles_detected = defaultdict(int)
        self.plates_detected = []

    def update_excel_stats(self):
        """Update statistics in Excel file"""
        stats = api_storage.get_stats()
        return f"API Hits: {stats['successful']}/{stats['total_hits']} successful, Bikes: {stats['bikes']}, Cars: {stats['cars']}"


stats = SimpleStats()

# -------------------- models ------------------------
car_model = YOLO("yolov8n.pt")   # vehicle detector + tracker

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

# geometry gates
MIN_CAR_AR, MAX_CAR_AR = 1.0, 4.0
MIN_BIKE_AR, MAX_BIKE_AR = 0.5, 2.5
MIN_CAR_AREA = 1500
MIN_BIKE_AREA = 800

# Zone polygon
ZONE_POINTS = np.array([[2, 205], [320, 53], [504, 107],
                        [370, 351], [4, 358], [8, 203]], np.int32)

# -------------------- Image Quality Functions --------------------


def should_process_for_ocr(car_image: np.ndarray) -> bool:
    """Check if image is good enough for OCR."""
    if car_image is None or car_image.size == 0:
        return False

    h, w = car_image.shape[:2]
    if w < 100 or h < 50:
        return False

    if is_image_blurry(car_image, threshold=80.0):
        return False

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


def preprocess_plate_image(image: np.ndarray) -> np.ndarray:
    """Preprocess image specifically for plate detection"""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply adaptive thresholding
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)

    # Apply morphological operations to clean up
    kernel = np.ones((1, 1), np.uint8)
    processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    # Resize if too small
    if processed.shape[1] < 200:
        scale = 200 / processed.shape[1]
        new_width = 200
        new_height = int(processed.shape[0] * scale)
        processed = cv2.resize(processed, (new_width, new_height),
                               interpolation=cv2.INTER_CUBIC)

    return processed

# -------------------- EasyOCR Plate Reading --------------------


def read_plate_easyocr(car_bgr: np.ndarray, is_bike: bool = False) -> Optional[str]:
    """
    Read license plate using EasyOCR with multiple strategies.
    """
    if reader is None or car_bgr is None or car_bgr.size == 0:
        return None

    try:
        stats.easyocr_calls += 1

        # Strategy 1: Read from entire car image
        results = reader.readtext(car_bgr,
                                  paragraph=False,
                                  width_ths=0.7,
                                  height_ths=0.7,
                                  ycenter_ths=0.5)

        plate_candidates = []

        for (bbox, text, confidence) in results:
            text = text.upper().strip()

            # Clean the text
            text = re.sub(r'[^A-Z0-9]', '', text)

            if len(text) < 5:  # Minimum length for Indian plates
                continue

            # Check if it looks like a plate
            letters = sum(1 for c in text if c.isalpha())
            digits = sum(1 for c in text if c.isdigit())

            if letters >= 2 and digits >= 2:  # Minimum requirements
                plate_candidates.append((text, confidence))

        # Strategy 2: Try with preprocessed image
        if not plate_candidates:
            processed = preprocess_plate_image(car_bgr)
            results = reader.readtext(processed,
                                      paragraph=False,
                                      width_ths=0.7,
                                      height_ths=0.7)

            for (bbox, text, confidence) in results:
                text = text.upper().strip()
                text = re.sub(r'[^A-Z0-9]', '', text)

                if len(text) >= 5:
                    letters = sum(1 for c in text if c.isalpha())
                    digits = sum(1 for c in text if c.isdigit())

                    if letters >= 2 and digits >= 2:
                        plate_candidates.append((text, confidence))

        # Strategy 3: Try different image regions
        if not plate_candidates:
            h, w = car_bgr.shape[:2]

            # Check bottom region (where plates usually are)
            bottom_region = car_bgr[int(h*0.6):h, :]
            if bottom_region.size > 0:
                results = reader.readtext(bottom_region,
                                          paragraph=False,
                                          width_ths=0.7,
                                          height_ths=0.7)

                for (bbox, text, confidence) in results:
                    text = text.upper().strip()
                    text = re.sub(r'[^A-Z0-9]', '', text)

                    if len(text) >= 5:
                        letters = sum(1 for c in text if c.isalpha())
                        digits = sum(1 for c in text if c.isdigit())

                        if letters >= 2 and digits >= 2:
                            plate_candidates.append((text, confidence))

        # Select best candidate
        if plate_candidates:
            # Sort by confidence
            plate_candidates.sort(key=lambda x: x[1], reverse=True)
            best_plate, best_conf = plate_candidates[0]

            print(f"EasyOCR candidate: {best_plate} (conf: {best_conf:.2f})")

            # Validate with India plate rules
            is_valid, reason = validate_india_plate(best_plate, is_bike)

            if is_valid:
                stats.successful_ocr += 1
                stats.validated_plates += 1
                stats.plates_detected.append({
                    "plate": best_plate,
                    "timestamp": datetime.now().isoformat(),
                    "source": "easyocr",
                    "is_bike": is_bike,
                    "validation": reason,
                    "confidence": best_conf
                })

                print(
                    f"EasyOCR successful: {best_plate} (conf: {best_conf:.2f}) - {reason}")
                return best_plate
            else:
                print(f"Invalid India plate: {best_plate} - {reason}")
                stats.failed_ocr += 1
                stats.rejected_plates += 1
                return None
        else:
            stats.failed_ocr += 1
            print("EasyOCR: No plate candidates found")
            return None

    except Exception as e:
        print(f"EasyOCR error: {e}")
        stats.failed_ocr += 1
        return None

# -------------------- Utils --------------------


def open_stream():
    cap = cv2.VideoCapture(RTSP_URL)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FPS, 15)
    return cap


def restart(cap):
    print("Restarting stream...")
    cap.release()
    time.sleep(RECONNECT_DELAY_SEC)
    return open_stream()


def zone_contains(cx, cy) -> bool:
    return cv2.pointPolygonTest(ZONE_POINTS, (float(cx), float(cy)), False) >= 0


# -------------------- API push --------------------
API_URL = "https://visitormanagement.solstium.net/security_monitoring/api/admin/store_feed"


def push_api_base64(img64: str, plate: Optional[str], is_bike: bool = False):
    try:
        vehicle_class = "motorcycle" if is_bike else "car/truck"
        payload = {
            "_id": secrets.token_hex(8),
            "object_classification": f"India {vehicle_class}, p:88.0%",
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
            "vehicle_type": "motorcycle" if is_bike else "car",
            "country": "India"
        }
        r = requests.post(API_URL, json=payload, timeout=15)
        print(f"API: {r.status_code} {r.text[:120]}")

        if r.status_code == 200:
            api_storage.add_record(
                plate_number=plate or "UNKNOWN",
                api_status="success",
                http_status=r.status_code,
                response_text=r.text[:200],
                vehicle_type="motorcycle" if is_bike else "car",
                is_bike=is_bike,
                ocr_method="easyocr"
            )
            return True
        else:
            api_storage.add_record(
                plate_number=plate or "UNKNOWN",
                api_status="failed",
                http_status=r.status_code,
                response_text=r.text[:200],
                vehicle_type="motorcycle" if is_bike else "car",
                is_bike=is_bike,
                ocr_method="easyocr"
            )
            return False

    except Exception as e:
        print(f"API push error: {e}")
        api_storage.add_record(
            plate_number=plate or "UNKNOWN",
            api_status="error",
            http_status=None,
            response_text=str(e)[:200],
            vehicle_type="motorcycle" if is_bike else "car",
            is_bike=is_bike,
            ocr_method="easyocr"
        )
        return False


# -------------------- Combined image functions --------------------
BANNER_BGR = (43, 22, 10)


def make_combined_image_from_car(car_image: np.ndarray, plate_text: Optional[str], is_bike: bool = False) -> Optional[Tuple[np.ndarray, str]]:
    if car_image is None or car_image.size == 0:
        return None, None

    display_image = car_image.copy()
    h = display_image.shape[0]
    banner_w = int(max(260, 0.65 * h))
    banner = np.full((h, banner_w, 3), BANNER_BGR, dtype=np.uint8)

    txt = (plate_text or "").strip() or "UNKNOWN"
    full_text = f"{txt}"

    font = cv2.FONT_HERSHEY_SIMPLEX

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
    if not plate_text or plate_text == "UNREADABLE":
        print("Skipping API push: No valid plate text")
        return None

    is_valid, reason = validate_india_plate(plate_text, is_bike)

    if not is_valid:
        print(
            f"Skipping API push: Invalid India plate: {plate_text} - {reason}")

        api_storage.add_record(
            plate_number=plate_text,
            api_status="rejected_invalid",
            http_status=None,
            response_text=reason,
            image_path=None,
            vehicle_type="motorcycle" if is_bike else "car",
            validation_result=reason,
            is_bike=is_bike,
            ocr_method="easyocr"
        )
        stats.rejected_plates += 1
        return None

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
    try:
        api_storage.add_record(
            plate_number=plate_text or "NO_PLATE",
            api_status=f"rejected_{reason}",
            http_status=None,
            response_text=reason,
            image_path=None,
            vehicle_type="motorcycle" if is_bike else "car",
            is_bike=is_bike,
            ocr_method="easyocr"
        )

        print(
            f"Logged failed attempt: {reason} - {plate_text} ({'BIKE' if is_bike else 'CAR'})")
    except Exception as e:
        print(f"Error logging failed attempt: {e}")


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

            # Use EasyOCR instead of Gemini
            plate_text = read_plate_easyocr(car_image, is_bike)

            with ocr_lock:
                ocr_results[tid] = {
                    "text": plate_text,
                    "timestamp": time.time(),
                    "bbox": bbox,
                    "car_image": car_image.copy(),
                    "is_bike": is_bike,
                    "ocr_method": "easyocr"
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
    print("OCR worker thread started (EasyOCR)")


def stop_ocr_worker():
    global stop_ocr_thread
    stop_ocr_thread = True
    if ocr_thread and ocr_thread.is_alive():
        ocr_thread.join(timeout=2.0)
    print("OCR worker thread stopped")

# -------------------- Track memory --------------------


@dataclass
class CarCandidate:
    image: np.ndarray
    conf: float
    sharp: float
    ts: float


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
    ocr_done: bool
    best_candidate_image: Optional[np.ndarray] = None
    is_bike: bool = False


tracks: Dict[int, TrackMem] = {}


def pick_best_candidate(cands: List[CarCandidate]) -> Optional[CarCandidate]:
    if not cands:
        return None

    non_blurry = []
    for c in cands:
        if not is_image_blurry(c.image, threshold=100.0):
            non_blurry.append(c)

    if not non_blurry:
        non_blurry = cands

    best = None
    best_score = -1e9
    for c in non_blurry:
        score = (c.conf * 150.0) + (c.sharp / 10.0) + \
            (time.time() - c.ts) * -0.1
        if score > best_score:
            best_score = score
            best = c

    return best


# -------------------- main loop --------------------
print(f"Starting tracker + EasyOCR (India Plates)")
print("Using EasyOCR for plate detection")
print("India plate validation enabled")
print(f"API hits stored in Excel: {api_storage.excel_path}")

start_ocr_worker()

cap = open_stream()
if not cap.isOpened():
    print("Cannot open stream")
    stop_ocr_worker()
    raise SystemExit(1)

ret, _ = cap.read()
if not ret:
    print("Stream read failed")
    stop_ocr_worker()
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
            time.sleep(0.01)
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
                car_image = res.get("car_image")
                is_bike = res.get("is_bike", False)

                if plate_text:
                    T.final_plate = plate_text
                    print(
                        f"Track {tid} final plate: {plate_text} ({'BIKE' if is_bike else 'CAR'})")

                    if T.in_zone and not T.posted:
                        is_valid, reason = validate_india_plate(
                            plate_text, is_bike)

                        if is_valid:
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
                            log_failed_attempt(plate_text, reason, is_bike)

                        T.ocr_done = True
                        T.ocr_attempts = MAX_OCR_ATTEMPTS_PER_TRACK
                else:
                    T.ocr_done = True

        # ---- Detect/track every N frames ----
        if frame_idx % PROCESS_EVERY_N_FRAMES == 0:
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
                                ocr_done=False,
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
                            if T.best_candidate_image is not None:
                                push_combined_from_car_image(
                                    T.best_candidate_image, T.final_plate, T.is_bike)
                            captures += 1
                            T.posted = True
                            print(
                                f"Posted track {tid} plate={T.final_plate} ({'BIKE' if T.is_bike else 'CAR'})")
                            continue

                        # ---- Collect car images when in zone ----
                        if in_zone and (not T.posted) and (T.ocr_attempts < MAX_OCR_ATTEMPTS_PER_TRACK):
                            if time.time() - T.last_ocr_time >= MIN_SECONDS_BETWEEN_OCR:
                                car_roi = frame[y1:y2, x1:x2]
                                if car_roi is not None and car_roi.size > 0:
                                    if should_process_for_ocr(car_roi):
                                        sharp = sharpness_score(car_roi)
                                        vehicle_type = "bike" if is_bike else "car"

                                        T.candidates.append(CarCandidate(
                                            image=car_roi.copy(),
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

                        # ---- When enough candidates collected, do ONE OCR call ----
                        if in_zone and (not T.posted) and (not T.ocr_done):
                            if len(T.candidates) >= 2 or T.ocr_attempts >= MAX_OCR_ATTEMPTS_PER_TRACK:
                                best = pick_best_candidate(T.candidates)
                                if best is not None:
                                    T.best_candidate_image = best.image.copy()

                                    ocr_queue.put(
                                        (tid, best.image, (x1, y1, x2, y2), T.is_bike))
                                    T.ocr_done = True
                                    vehicle_type = "bike" if T.is_bike else "car"
                                    print(
                                        f"Submitted ONE EasyOCR for track {tid} ({vehicle_type})")

        # cleanup old tracks
        now = time.time()
        dead = [tid for tid, T in tracks.items() if now - T.last_seen > 30]
        for tid in dead:
            tracks.pop(tid, None)

except KeyboardInterrupt:
    pass
finally:
    stop_ocr_worker()
    cap.release()

    # Save final Excel
    api_storage.df.to_excel(api_storage.excel_path, index=False)

    print("\n" + "="*50)
    print("FINAL STATISTICS:")
    print("="*50)
    print(f"Runtime: {time.time() - stats.start_time:.1f} seconds")
    print(f"Total captures: {captures}")
    print(f"EasyOCR calls: {stats.easyocr_calls}")
    print(f"Successful OCR: {stats.successful_ocr}")
    print(f"Failed OCR: {stats.failed_ocr}")
    print(f"Validated plates: {stats.validated_plates}")
    print(f"Rejected plates: {stats.rejected_plates}")
    print(f"Vehicles detected: {dict(stats.vehicles_detected)}")

    api_stats = api_storage.get_stats()
    print(
        f"API Hits in Excel: {api_stats['successful']}/{api_stats['total_hits']} successful")
    print(f"Bikes detected: {api_stats['bikes']}")
    print(f"Cars detected: {api_stats['cars']}")
    print(f"Excel file: {api_storage.excel_path}")
    print("="*50)
    print("Done.")
