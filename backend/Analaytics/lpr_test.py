import os
import re
import cv2
import json
import time
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from datetime import datetime
from dotenv import load_dotenv
from ultralytics import YOLO
from paddleocr import PaddleOCR

# -------------------- env/threads --------------------
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "4"
load_dotenv()

# -------------------- source & paths -----------------
# <— set your MP4 / RTSP
VIDEO_PATH = "https://api.vms.solstium.net/hls/df3e2570e7/index.m3u8"
LOOP_VIDEO = True
SHOW_PREVIEW = True

BASE_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(BASE_DIR, "car_captures_final")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -------------------- models ------------------------
car_model = YOLO("yolov8n.pt")    # vehicle detector + tracker
plate_model = YOLO("best.pt")     # your license plate detector

print("[INFO] Initializing PaddleOCR...")
paddle_ocr = PaddleOCR(use_angle_cls=True, lang='en')
print("[INFO] PaddleOCR ready.")

# -------------------- tracker -----------------------
TRACKER_CFG = os.path.join(BASE_DIR, "bytetrack.yaml")

# -------------------- thresholds --------------------
CONFIDENCE_THRESHOLD = 0.35        # vehicle det
# plate detection confidence gate (recommended >=0.5)
PLATE_DET_MIN_CONF = 0.20
PLATE_OCR_MIN_CONF = 0.20          # OCR confidence threshold
PLATE_GREEN_CONF = 0.90            # box color
PLATE_YELLOW_CONF = 0.80
PROCESS_EVERY_N_FRAMES = 2

MIN_CAR_AR, MAX_CAR_AR = 1.0, 4.0  # aspect ratio gates
MIN_CAR_AREA = 3500

# -------------------- tripwire -----------------------
TRIPWIRE_Y_NORM = 0.75
TRIPWIRE_THICKNESS = 4
TRIPWIRE_COLOR = (0, 255, 255)
TRIPWIRE_NAME = "Capture Zone"

# -------------------- India plate validation --------
# State/UT codes (common + full set)
STATE_CODES = {
    "AN", "AP", "AR", "AS", "BR", "CG", "CH", "DD", "DL", "DN", "GA", "GJ", "HP", "HR", "JH", "JK",
    "KA", "KL", "LA", "LD", "MH", "ML", "MN", "MP", "MZ", "NL", "OD", "PB", "PY", "RJ", "SK", "TN",
    "TR", "TS", "UK", "UP", "WB"
}

# Standard (very common) formats:
#   TN01AB1234
#   TN01A1234
#   TN01AB123
STD_PLATE_RE = re.compile(r"^([A-Z]{2})(\d{1,2})([A-Z]{1,3})(\d{3,4})$")

# BH plates:
#   21BH1234AA  or  21BH1234A  (some variations exist in the wild)
BH_PLATE_RE = re.compile(r"^(\d{2})BH(\d{4})([A-Z]{1,2})$")


def _clean_alnum(text: str) -> str:
    if not text:
        return ""
    text = text.upper().strip()
    text = text.replace(" ", "").replace("-", "")
    return re.sub(r"[^A-Z0-9]", "", text)


def generate_plate_variants(raw: str) -> List[str]:
    """
    Create a few plausible variants without destroying state codes.
    Only apply ambiguous swaps in likely numeric regions.
    """
    s = _clean_alnum(raw)
    if len(s) < 6 or len(s) > 12:
        return [s]

    # ambiguous maps
    amb_letter_to_digit = {"O": "0", "Q": "0", "D": "0",
                           "I": "1", "L": "1", "Z": "2", "S": "5", "B": "8", "G": "6"}
    amb_digit_to_letter = {"0": "O", "1": "I",
                           "2": "Z", "5": "S", "8": "B", "6": "G"}

    variants = {s}

    # If last 4 chars should be digits, try letter->digit there
    if len(s) >= 4:
        tail = s[-4:]
        fixed_tail = "".join([amb_letter_to_digit.get(ch, ch) for ch in tail])
        variants.add(s[:-4] + fixed_tail)

    # If starts with digits and looks like BH, try digit->letter in suffix
    if "BH" in s and len(s) >= 10:
        # Fix last 1-2 chars to letters if digits
        suffix = s[-2:]
        fixed_suffix = "".join(
            [amb_digit_to_letter.get(ch, ch) for ch in suffix])
        variants.add(s[:-2] + fixed_suffix)

    # Light global attempt (very conservative): only O/Q->0 everywhere
    variants.add(s.replace("O", "0").replace("Q", "0"))

    # Remove duplicates & bad lengths
    out = []
    for v in variants:
        v = _clean_alnum(v)
        if 6 <= len(v) <= 12:
            out.append(v)
    return list(dict.fromkeys(out))


def is_valid_india_plate(text: str) -> bool:
    s = _clean_alnum(text)
    if not (6 <= len(s) <= 12):
        return False

    # BH
    m = BH_PLATE_RE.match(s)
    if m:
        yy = int(m.group(1))
        # sanity on year (00..99 ok) - keep permissive
        return True

    # Standard
    m = STD_PLATE_RE.match(s)
    if not m:
        return False

    st = m.group(1)
    if st not in STATE_CODES:
        return False

    return True


def normalize_to_best_india_plate(raw: str) -> Optional[str]:
    """
    Returns best normalized plate if any variant matches India rules.
    """
    for v in generate_plate_variants(raw):
        if is_valid_india_plate(v):
            return v
    return None

# -------------------- OCR helpers --------------------


def run_paddle_ocr_on_mat(img_mat: np.ndarray) -> Tuple[Optional[str], float]:
    """
    Returns: (best_text, best_conf)
    """
    if img_mat is None or img_mat.size == 0:
        return None, 0.0

    try:
        # Preprocess
        if len(img_mat.shape) == 3:
            gray = cv2.cvtColor(img_mat, cv2.COLOR_BGR2GRAY)
        else:
            gray = img_mat

        gray = cv2.equalizeHist(gray)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        processed_img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        result = paddle_ocr.ocr(processed_img, cls=True)
        if not result or not result[0]:
            return None, 0.0

        candidates: List[Tuple[str, float]] = []
        for line in result:
            if not line:
                continue
            for det in line:
                if not det or len(det) < 2:
                    continue
                bbox, (text, conf) = det
                if not text or conf is None:
                    continue
                cleaned = _clean_alnum(text)
                if len(cleaned) < 6:
                    continue

                # Try to normalize to valid India plate
                norm = normalize_to_best_india_plate(cleaned)
                if norm:
                    candidates.append((norm, float(conf)))
                else:
                    # keep as fallback candidate only if it looks plate-ish
                    if 6 <= len(cleaned) <= 12:
                        # penalize non-validated
                        candidates.append((cleaned, float(conf) * 0.70))

        if not candidates:
            return None, 0.0

        # pick best by confidence (and slightly prefer longer)
        candidates.sort(key=lambda x: (
            x[1] + (len(x[0]) * 0.01)), reverse=True)
        best_text, best_conf = candidates[0]

        # Apply OCR conf gate (but allow slightly lower if valid India plate)
        if is_valid_india_plate(best_text):
            if best_conf >= (PLATE_OCR_MIN_CONF - 0.10):
                return best_text, best_conf
        else:
            if best_conf >= PLATE_OCR_MIN_CONF:
                return best_text, best_conf

        return None, 0.0

    except Exception as e:
        print(f"❌ OCR error: {e}")
        return None, 0.0

# -------------------- IO helpers ---------------------


def open_stream():
    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print("❌ Cannot open video:", VIDEO_PATH)
    return cap


def _fname(prefix: str, plate_text: Optional[str], ext="jpg"):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    safe = re.sub(r"[^A-Za-z0-9]+", "", (plate_text or "UNKNOWN"))
    return f"{prefix}_{ts}_{safe}.{ext}"


def save_car(frame, bbox, plate_text=None):
    x1, y1, x2, y2 = [int(v) for v in bbox]
    crop = frame[y1:y2, x1:x2].copy()
    fp = os.path.join(OUTPUT_DIR, _fname("car", plate_text))
    cv2.imwrite(fp, crop)
    return fp


def save_plate_crop(plate_bgr: np.ndarray, plate_text: Optional[str]) -> Optional[str]:
    if plate_bgr is None or plate_bgr.size == 0:
        return None
    fp = os.path.join(OUTPUT_DIR, _fname("plate", plate_text))
    cv2.imwrite(fp, plate_bgr)
    return fp


# -------------------- combined image -----------------
BANNER_BGR = (245, 245, 245)
TEXT_COLOR = (30, 30, 30)
DIVIDER = (220, 220, 220)
SHADOW = (210, 210, 210)
PLATE_TEXT_COLOR = (0, 100, 200)


def _add_shadow(canvas: np.ndarray, shadow_size=10):
    h, w = canvas.shape[:2]
    out = np.full((h+shadow_size*2, w+shadow_size*2, 3),
                  (255, 255, 255), np.uint8)
    out[shadow_size:shadow_size+h, shadow_size:shadow_size+w] = canvas
    cv2.rectangle(out, (shadow_size-1, shadow_size-1),
                  (shadow_size+w, shadow_size+h), SHADOW, 2)
    return out


def make_combined_image(frame, bbox, plate_text: Optional[str], plate_crop: Optional[np.ndarray] = None):
    x1, y1, x2, y2 = [int(v) for v in bbox]
    car = frame[max(0, y1):max(0, y2), max(0, x1):max(0, x2)].copy()
    if car is None or car.size == 0:
        return None, None

    car_h, car_w = car.shape[:2]
    plate_section_w = int(max(320, 0.55 * car_w))
    total_w = car_w + plate_section_w
    text_section_h = 80
    total_h = car_h + text_section_h

    canvas = np.full((total_h, total_w, 3), BANNER_BGR, np.uint8)
    inset = 12

    car_target_h = total_h - text_section_h - inset*2
    scale = car_target_h / car_h
    car_new_w = int(car_w * scale)
    car_new_h = int(car_h * scale)
    car_resized = cv2.resize(car, (car_new_w, car_new_h),
                             interpolation=cv2.INTER_AREA)
    canvas[inset:inset+car_new_h, inset:inset+car_new_w] = car_resized

    x_div = car_new_w + inset*2
    cv2.line(canvas, (x_div, 0), (x_div, total_h - text_section_h), DIVIDER, 2)

    if plate_crop is not None and plate_crop.size > 0:
        ph, pw = plate_crop.shape[:2]
        target_h = int(0.85 * (total_h - text_section_h))
        target_w = plate_section_w - inset*3
        s = min(target_h / ph, target_w / pw, 4.5)
        new_w, new_h = max(1, int(pw * s)), max(1, int(ph * s))
        plate_resized = cv2.resize(
            plate_crop, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        px = x_div + (plate_section_w - new_w)//2
        py = ((total_h - text_section_h) - new_h)//2
        px = max(px, x_div + inset)
        py = max(py, inset)
        canvas[py:py+new_h, px:px+new_w] = plate_resized

    display_text = plate_text or "NO PLATE DETECTED"
    text_y = total_h - 25
    font_scale = 1.2
    thickness = 3

    text_size = cv2.getTextSize(
        display_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
    text_x = (total_w - text_size[0]) // 2

    bg_padding = 10
    cv2.rectangle(canvas,
                  (text_x - bg_padding, text_y - text_size[1] - bg_padding),
                  (text_x + text_size[0] + bg_padding, text_y + bg_padding),
                  (255, 255, 255), -1)

    border_color = PLATE_TEXT_COLOR if plate_text else (100, 100, 100)
    cv2.rectangle(canvas,
                  (text_x - bg_padding, text_y - text_size[1] - bg_padding),
                  (text_x + text_size[0] + bg_padding, text_y + bg_padding),
                  border_color, 2)

    text_color = PLATE_TEXT_COLOR if plate_text else (100, 100, 100)
    cv2.putText(canvas, display_text, (text_x, text_y),
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, thickness, cv2.LINE_AA)

    cv2.putText(canvas, "Vehicle", (inset, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, TEXT_COLOR, 2, cv2.LINE_AA)
    cv2.putText(canvas, "License Plate", (x_div + inset, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, TEXT_COLOR, 2, cv2.LINE_AA)

    pretty = _add_shadow(canvas, shadow_size=10)
    outp = os.path.join(OUTPUT_DIR, _fname("combined", plate_text))
    cv2.imwrite(outp, pretty, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return pretty, outp


def push_combined_from_frame(frame, bbox, plate_text: Optional[str], plate_crop: Optional[np.ndarray] = None):
    combined, outp = make_combined_image(frame, bbox, plate_text, plate_crop)
    if combined is None:
        return None
    return outp

# -------------------- tracking memory ----------------


@dataclass
class ReadItem:
    text: str
    conf: float
    ts: float


@dataclass
class TrackMem:
    last_seen: float
    bbox: Tuple[int, int, int, int]
    reads: List[ReadItem]
    final_plate: Optional[str]
    posted: bool
    next_ocr_frame: int
    last_plate_conf: float = 0.0
    last_plate_crop: Optional[np.ndarray] = None


tracks: Dict[int, TrackMem] = {}


def add_read(tid: int, text: Optional[str], conf: float):
    if not text:
        return

    text = _clean_alnum(text)
    if len(text) < 6 or len(text) > 12:
        return

    # Only accept as "final" if valid India plate
    norm = normalize_to_best_india_plate(text)
    if not norm:
        return

    T = tracks[tid]
    T.reads.append(ReadItem(norm, float(conf), time.time()))

    # Weighted vote: prefer higher OCR confidence + recent + repeated
    score_map: Dict[str, float] = {}
    for r in T.reads:
        recency_boost = 1.0 if (time.time() - r.ts) < 8 else 0.7
        score_map[r.text] = score_map.get(
            r.text, 0.0) + (r.conf * recency_boost)

    best_plate = max(score_map.items(), key=lambda kv: kv[1])[0]
    freq = sum(1 for r in T.reads if r.text == best_plate)
    best_conf = max(
        (r.conf for r in T.reads if r.text == best_plate), default=0.0)

    # accept if repeated OR super confident
    if freq >= 2 or best_conf >= 0.90:
        T.final_plate = best_plate
        print(
            f"🎯 Track {tid} final plate: {T.final_plate} (freq={freq}, best_conf={best_conf:.2f})")


# -------------------- main loop ----------------------
print(
    f"🚀 YOLO + PaddleOCR | plate_det_conf ≥ {PLATE_DET_MIN_CONF:.2f} | ocr_conf ≥ {PLATE_OCR_MIN_CONF:.2f}")
cap = open_stream()
if not cap or not cap.isOpened():
    raise SystemExit(1)

if SHOW_PREVIEW:
    try:
        cv2.namedWindow("Preview", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Preview", 960, 540)
    except Exception:
        SHOW_PREVIEW = False

frame_idx = 0

try:
    while True:
        ok, frame = cap.read()
        if not ok or frame is None or frame.size == 0:
            if LOOP_VIDEO:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                frame_idx = 0
                tracks.clear()
                continue
            break

        frame_idx += 1
        H, W, _ = frame.shape
        TRIPWIRE_Y = int(H * TRIPWIRE_Y_NORM)

        if frame_idx % PROCESS_EVERY_N_FRAMES == 0:
            tr = car_model.track(
                frame,
                conf=CONFIDENCE_THRESHOLD,
                persist=True,
                verbose=False,
                tracker=TRACKER_CFG,
                classes=[2, 3, 5, 7]  # car, motorcycle, bus, truck
            )

            if tr and len(tr):
                r = tr[0]
                if r.boxes is not None and hasattr(r.boxes, "id") and r.boxes.id is not None:
                    ids = r.boxes.id.int().cpu().tolist()
                    xyxy = r.boxes.xyxy.int().cpu().tolist()
                    confs = r.boxes.conf.cpu().tolist()

                    for (tid, (x1, y1, x2, y2), c) in zip(ids, xyxy, confs):
                        ar = (x2 - x1) / max(1, (y2 - y1))
                        area = (x2 - x1) * (y2 - y1)
                        if ar < MIN_CAR_AR or ar > MAX_CAR_AR or area < MIN_CAR_AREA:
                            continue

                        now = time.time()
                        if tid not in tracks:
                            tracks[tid] = TrackMem(
                                now, (x1, y1, x2, y2), [], None, False, frame_idx)
                            print(f"🆕 New track: {tid}")

                        T = tracks[tid]
                        T.last_seen = now
                        T.bbox = (x1, y1, x2, y2)

                        # ---------- OCR ----------

                        if frame_idx >= T.next_ocr_frame:
                            car_roi = frame[y1:y2, x1:x2]
                            if car_roi is not None and car_roi.size > 0:
                                pres = plate_model.predict(
                                    source=car_roi, conf=0.10, verbose=False, imgsz=640)

                                best_plate_crop = None
                                best_plate_conf = 0.0

                                for pr in pres or []:
                                    if pr is None or pr.boxes is None:
                                        continue
                                    for p in pr.boxes:
                                        try:
                                            pc = float(p.conf)
                                        except Exception:
                                            try:
                                                pc = float(p.conf[0])
                                            except Exception:
                                                pc = 0.0

                                        if pc > best_plate_conf:
                                            px1, py1, px2, py2 = map(
                                                int, p.xyxy[0])

                                            padx = int(0.25 * (px2 - px1))
                                            pady = int(0.30 * (py2 - py1))
                                            px1 = max(0, px1 - padx)
                                            py1 = max(0, py1 - pady)
                                            px2 = min(
                                                car_roi.shape[1] - 1, px2 + padx)
                                            py2 = min(
                                                car_roi.shape[0] - 1, py2 + pady)

                                            if px2 > px1 and py2 > py1:
                                                best_plate_crop = car_roi[py1:py2, px1:px2]
                                                best_plate_conf = pc

                                T.last_plate_conf = best_plate_conf
                                T.last_plate_crop = best_plate_crop.copy() if (
                                    best_plate_crop is not None and best_plate_crop.size > 0) else None

                                if best_plate_crop is not None and best_plate_crop.size > 0 and best_plate_conf >= PLATE_DET_MIN_CONF:
                                    plate_text, ocr_conf = run_paddle_ocr_on_mat(
                                        best_plate_crop)
                                    if plate_text:
                                        add_read(tid, plate_text, ocr_conf)

                                T.next_ocr_frame = frame_idx + 8  # reduce frequency

                        # ---------- tripwire ----------
                        _, _, _, y2_car = T.bbox
                        is_crossing = y2_car >= TRIPWIRE_Y

                        if not T.posted and is_crossing:
                            plate_out = T.final_plate  # only valid India plates land here
                            print(
                                f"📸 Capturing track {tid} - Plate: {plate_out}")

                            combined_path = push_combined_from_frame(
                                frame, (x1, y1, x2, y2), plate_out, T.last_plate_crop)
                            car_path = save_car(
                                frame, (x1, y1, x2, y2), plate_out)
                            plate_path = None
                            if T.last_plate_crop is not None and T.last_plate_crop.size > 0:
                                plate_path = save_plate_crop(
                                    T.last_plate_crop, plate_out)

                            meta = {
                                "ts_utc": datetime.utcnow().isoformat(),
                                "frame_idx": frame_idx,
                                "track_id": int(tid),
                                "plate_text": plate_out,  # valid india plate or None
                                "plate_det_conf": float(T.last_plate_conf),
                                "all_valid_reads": [{"text": r.text, "conf": r.conf, "ts": r.ts} for r in T.reads],
                                "car_path": car_path,
                                "plate_path": plate_path,
                                "combined_path": combined_path,
                            }
                            json_path = os.path.join(
                                OUTPUT_DIR, _fname("meta", plate_out, ext="json"))
                            with open(json_path, "w", encoding="utf-8") as f:
                                json.dump(
                                    meta, f, ensure_ascii=False, indent=2)

                            print(
                                f"✅ Capture saved: {plate_out if plate_out else 'NO VALID PLATE'}")
                            T.posted = True

        # ---------------- Preview -------------------
        if SHOW_PREVIEW:
            disp = frame.copy()
            cv2.line(disp, (0, TRIPWIRE_Y), (W, TRIPWIRE_Y),
                     TRIPWIRE_COLOR, TRIPWIRE_THICKNESS)
            cv2.putText(disp, TRIPWIRE_NAME, (max(10, W - 250), max(20, TRIPWIRE_Y - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, TRIPWIRE_COLOR, 2)

            for tid, T in list(tracks.items()):
                if time.time() - T.last_seen > 30:
                    tracks.pop(tid, None)
                    continue

                x1, y1, x2, y2 = T.bbox
                if T.last_plate_conf >= PLATE_GREEN_CONF:
                    color = (0, 255, 0)
                elif T.last_plate_conf >= PLATE_YELLOW_CONF:
                    color = (0, 215, 255)
                elif T.final_plate:
                    color = (0, 165, 255)
                else:
                    color = (255, 0, 0)

                cv2.rectangle(disp, (x1, y1), (x2, y2), color, 2)

                tag = f"ID {tid}"
                if T.final_plate:
                    tag += f" | {T.final_plate}"
                tag += f" | det:{T.last_plate_conf:.2f}"

                cv2.putText(disp, tag, (x1, max(0, y1 - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            hud = [
                f"Frames: {frame_idx}",
                f"Active tracks: {len(tracks)}",
                f"Plate det conf ≥ {PLATE_DET_MIN_CONF:.2f}",
                f"OCR conf ≥ {PLATE_OCR_MIN_CONF:.2f}",
                "q: quit | s: save"
            ]
            for i, t in enumerate(hud):
                cv2.putText(disp, t, (10, 30 + i * 22),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            cv2.imshow("Preview", disp)
            k = cv2.waitKey(1) & 0xFF
            if k == ord('q'):
                break
            if k == ord('s'):
                fp = os.path.join(OUTPUT_DIR, f"debug_{frame_idx}.jpg")
                cv2.imwrite(fp, disp)
                print("Saved", fp)

except KeyboardInterrupt:
    pass
finally:
    if cap:
        cap.release()
    if SHOW_PREVIEW:
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
    print("✅ Done.")
