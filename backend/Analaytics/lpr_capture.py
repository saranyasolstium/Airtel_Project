#!/usr/bin/env python3
"""
Gate Zone-Lock ANPR (OFFLINE) - CONFIG driven (no CLI needed)

Features:
- Works with RTSP URL or local video file (set in CONFIG)
- Gate polygon zone lock (1 vehicle session at a time => stable vehicle_id)
- Plate detection (license_plate_detector.pt)
- Vehicle detection (yolov8n.pt) => FULL car crop (not only plate)
- Strict India validation: state/UT + length + BH series
- Async OCR (RapidOCR)
- Best-per-vehicle update: replace only if new OCaR conf is higher
- On valid plate: generate combined image (car + banner) + base64
- Writes 1 row per vehicle to CSV when vehicle leaves zone
- RTSP reconnect + TCP + low buffer for stability

Run:
  python gate_anpr_run.py
"""

from rapidocr_onnxruntime import RapidOCR
from ultralytics import YOLO
import pandas as pd
import numpy as np
import cv2
import os
import sys
import re
import time
import json
import base64
import subprocess
from pathlib import Path
from datetime import datetime
from queue import Queue, Empty
from threading import Thread, Event

# ============================================================
# ✅ CONFIG (EDIT ONLY THIS)
# ============================================================
CONFIG = {
    # Source: RTSP or file
    "SOURCE": "rtsp://admin:sd123456@fashionislandcctv.ddns.net:554/cam/realmonitor?channel=1&subtype=0",
    # "SOURCE": "./test1.mp4",

    # Gate polygon zone (either JSON file path or inline points)
    "ZONE_JSON": "./gate_zone.json",          # preferred
    # "ZONE_POINTS": [[200,300],[1100,300],[1100,650],[200,650]],  # optional fallback

    # Models (local files)
    "PLATE_MODEL": "./license_plate_detector.pt",
    "VEHICLE_MODEL": "./yolov8n.pt",

    # Outputs
    "OUTPUT_DIR": "./output",
    "SAVE_PREVIEW": True,
    "SHOW_WINDOW": True,
    "SAVE_SNIPS": True,

    # Performance
    "STRIDE": 2,
    "IMGSZ": 640,

    # Detection thresholds
    "PLATE_CONF": 0.30,
    "PLATE_IOU": 0.45,
    "VEHICLE_CONF": 0.35,

    # OCR / validation
    "OCR_MIN_CONF": 0.30,
    "BLUR_VAR_TH": 45.0,
    "OCR_COOLDOWN_SEC": 0.20,
    "FAST_UP": 1.4,
    "HEAVY_UP": 1.9,

    # Session end: if plate is outside zone for N consecutive processed frames
    "EXIT_OUTSIDE_FRAMES": 12,

    # RTSP robustness
    "RTSP_TCP": True,
    "CAP_BUFFER": 1,
    "RECONNECT_SLEEP_SEC": 1.0,

    # Base64 quality
    "B64_JPEG_QUALITY": 92,

    # Banner color BGR
    "BANNER_BGR": (35, 35, 35),

    # Vehicle classes in COCO
    "VEHICLE_CLASSES": {2, 3, 5, 7},  # car, motorcycle, bus, truck
}
# ============================================================


# -------------------------
# Auto-install dependencies
# -------------------------
REQUIRED_PIP = [
    "ultralytics>=8.0.0",
    "opencv-python>=4.7.0.72",
    "numpy>=1.23.0",
    "pandas>=2.0.0",
    "rapidocr-onnxruntime>=1.3.0",
]


def pip_install(pkgs):
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade"] + pkgs
    print("[INSTALL]", " ".join(cmd))
    subprocess.check_call(cmd)


def ensure_imports():
    missing = []
    for pkg in ["cv2", "numpy", "pandas"]:
        try:
            __import__(pkg)
        except:
            missing.append(pkg)
    try:
        import ultralytics  # noqa
    except:
        missing.append("ultralytics")
    try:
        import rapidocr_onnxruntime  # noqa
    except:
        missing.append("rapidocr-onnxruntime")
    if missing:
        print("[WARN] Missing:", missing)
        print("[INFO] Installing...")
        pip_install(REQUIRED_PIP)


ensure_imports()


# -------------------------
# India validation (strict + BH)
# -------------------------
INDIA_STATE_CODES = {
    "AN", "AP", "AR", "AS", "BR", "CH", "CG", "DD", "DL", "DN", "GA", "GJ", "HP", "HR", "JH",
    "JK", "KA", "KL", "LA", "LD", "MH", "ML", "MN", "MP", "MZ", "NL", "OD", "PB", "PY",
    "RJ", "SK", "TN", "TR", "TS", "UK", "UP", "WB"
}
RX_STD_1 = re.compile(r"^[A-Z]{2}\d{1,2}[A-Z]{1,3}\d{4}$")
RX_STD_2 = re.compile(r"^[A-Z]{2}\d{1,2}[A-Z]{1,2}\d{3,4}$")
RX_BH = re.compile(r"^\d{2}BH\d{4}[A-Z]{1,2}$")
CHAR_FIX = str.maketrans({"O": "0", "I": "1", "Z": "2", "S": "5", "B": "8"})


def clean_plate_text(s: str) -> str:
    s = (s or "").strip().upper()
    s = "".join(ch for ch in s if ch.isalnum())
    if len(s) < 6:
        return ""
    return s.translate(CHAR_FIX)


def is_valid_india_plate(s: str) -> bool:
    if not s:
        return False
    if RX_BH.match(s):
        return True
    if len(s) < 8 or len(s) > 11:
        return False
    if s[:2] not in INDIA_STATE_CODES:
        return False
    return bool(RX_STD_1.match(s) or RX_STD_2.match(s))


# -------------------------
# Helper functions
# -------------------------
def now_wall():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def laplacian_variance(gray: np.ndarray) -> float:
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def preprocess_fast(crop_bgr: np.ndarray, upscale=1.4):
    if upscale != 1.0:
        crop_bgr = cv2.resize(crop_bgr, None, fx=upscale,
                              fy=upscale, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 5, 35, 35)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)


def preprocess_heavy(crop_bgr: np.ndarray, upscale=1.9):
    if upscale != 1.0:
        crop_bgr = cv2.resize(crop_bgr, None, fx=upscale,
                              fy=upscale, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 7, 50, 50)
    clahe = cv2.createCLAHE(2.0, (8, 8))
    g2 = clahe.apply(gray)
    thr = cv2.adaptiveThreshold(
        g2, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 7)
    return cv2.cvtColor(thr, cv2.COLOR_GRAY2BGR)


def point_in_poly(pt, poly):
    return cv2.pointPolygonTest(poly, pt, False) >= 0


def bbox_center_xyxy(b):
    x1, y1, x2, y2 = b
    return ((x1+x2)/2.0, (y1+y2)/2.0)


def iou_xyxy(a, b) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    iw = max(0.0, inter_x2 - inter_x1)
    ih = max(0.0, inter_y2 - inter_y1)
    inter = iw * ih
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter + 1e-9
    return inter / union


def b64_jpeg(img_bgr: np.ndarray, quality=92) -> str:
    ok, buf = cv2.imencode(
        ".jpg", img_bgr, [cv2.IMWRITE_JPEG_QUALITY, int(quality)])
    if not ok:
        return ""
    return base64.b64encode(buf.tobytes()).decode("utf-8")

# -------------------------
# Combined image generator (your logic)
# -------------------------


def make_combined_image_from_car(car_image: np.ndarray, plate_text: str, accepted_dir: str, banner_bgr=(35, 35, 35)):
    if car_image is None or car_image.size == 0:
        return None, None

    display_image = car_image.copy()
    h = display_image.shape[0]
    banner_w = int(max(260, 0.65 * h))
    banner = np.full((h, banner_w, 3), banner_bgr, dtype=np.uint8)

    txt = (plate_text or "").strip() or "UNKNOWN"
    font = cv2.FONT_HERSHEY_SIMPLEX

    margin = int(0.12 * h)
    max_w = banner_w - 2 * margin
    max_h = h - 2 * margin

    lo, hi = 0.5, 9.0
    best_scale = lo
    while hi - lo > 0.02:
        mid = (lo + hi) / 2.0
        (tw, th), _ = cv2.getTextSize(txt, font, mid, 8)
        if tw <= max_w and th <= max_h:
            best_scale = mid
            lo = mid
        else:
            hi = mid

    (tw, th), _ = cv2.getTextSize(txt, font, best_scale, 8)
    tx = (banner_w - tw) // 2
    ty = (h + th) // 2 - int(0.05 * h)

    cv2.putText(banner, txt, (tx, ty), font,
                best_scale, (0, 0, 0), 18, cv2.LINE_AA)
    cv2.putText(banner, txt, (tx, ty), font, best_scale,
                (25, 25, 25), 12, cv2.LINE_AA)
    cv2.putText(banner, txt, (tx, ty), font, best_scale,
                (230, 210, 60), 6, cv2.LINE_AA)
    cv2.putText(banner, txt, (tx, ty), font, best_scale,
                (255, 240, 120), 2, cv2.LINE_AA)

    combined = np.hstack([display_image, banner])

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_txt = re.sub(r"[^A-Za-z0-9]+", "", txt)
    out_path = os.path.join(
        accepted_dir, f"combined_{ts}_{safe_txt or 'UNKNOWN'}.jpg")
    cv2.imwrite(out_path, combined, [cv2.IMWRITE_JPEG_QUALITY, 95])

    return combined, out_path

# -------------------------
# Async OCR pool
# -------------------------


class OCRPool:
    def __init__(self, n_workers=2, max_q=2048):
        self.in_q = Queue(maxsize=max_q)
        self.out_q = Queue(maxsize=max_q)
        self.stop_event = Event()
        self.threads = []
        for _ in range(n_workers):
            t = Thread(target=self._loop, daemon=True)
            t.start()
            self.threads.append(t)

    def submit(self, job):
        try:
            self.in_q.put_nowait(job)
            return True
        except:
            return False

    def poll(self, max_items=300):
        out = []
        for _ in range(max_items):
            try:
                out.append(self.out_q.get_nowait())
            except Empty:
                break
        return out

    def _loop(self):
        ocr = RapidOCR()
        while not self.stop_event.is_set():
            try:
                job = self.in_q.get(timeout=0.1)
            except Empty:
                continue
            if job is None:
                break

            (veh_id, frame_idx, now_sec, det_conf, plate_crop,
             ocr_min_conf, blur_th, fast_up, heavy_up) = job

            best_text, best_conf, valid = "", 0.0, False
            try:
                if plate_crop is not None and plate_crop.size > 0:
                    gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
                    blur = laplacian_variance(gray)
                    if blur >= blur_th:
                        img_fast = preprocess_fast(plate_crop, fast_up)
                        res, _ = ocr(img_fast)
                        if res:
                            for it in res:
                                if len(it) >= 3:
                                    txt = clean_plate_text(it[1])
                                    sc = float(it[2])
                                    if txt and sc > best_conf:
                                        best_text, best_conf = txt, sc

                        if best_conf < max(ocr_min_conf, 0.45):
                            best_text, best_conf = "", 0.0
                            img_heavy = preprocess_heavy(plate_crop, heavy_up)
                            res2, _ = ocr(img_heavy)
                            if res2:
                                for it in res2:
                                    if len(it) >= 3:
                                        txt = clean_plate_text(it[1])
                                        sc = float(it[2])
                                        if txt and sc > best_conf:
                                            best_text, best_conf = txt, sc

                        if best_conf < ocr_min_conf:
                            best_text, best_conf = "", 0.0

                        valid = is_valid_india_plate(
                            best_text) if best_text else False
            except:
                best_text, best_conf, valid = "", 0.0, False

            self.out_q.put({
                "vehicle_id": veh_id,
                "frame": frame_idx,
                "time_sec": now_sec,
                "det_conf": float(det_conf),
                "ocr_text": best_text,
                "ocr_conf": float(best_conf),
                "valid": bool(valid),
            })

    def stop(self):
        self.stop_event.set()
        for _ in self.threads:
            try:
                self.in_q.put_nowait(None)
            except:
                pass
        for t in self.threads:
            t.join(timeout=1.0)


def open_capture(source: str):
    # RTSP stability
    if source.startswith("rtsp://") and CONFIG.get("RTSP_TCP", True):
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        return None
    try:
        cap.set(cv2.CAP_PROP_BUFFERSIZE, int(CONFIG.get("CAP_BUFFER", 1)))
    except Exception:
        pass
    return cap


def load_polygon():
    if "ZONE_JSON" in CONFIG and CONFIG["ZONE_JSON"] and os.path.exists(CONFIG["ZONE_JSON"]):
        with open(CONFIG["ZONE_JSON"], "r", encoding="utf-8") as f:
            z = json.load(f)
        pts = z["polygon"]
        return np.array(pts, dtype=np.int32)

    pts = CONFIG.get("ZONE_POINTS")
    if pts and isinstance(pts, list) and len(pts) >= 3:
        return np.array(pts, dtype=np.int32)

    raise FileNotFoundError(
        "No polygon provided. Set CONFIG['ZONE_JSON'] or CONFIG['ZONE_POINTS'].")


def main():
    source = CONFIG["SOURCE"]
    out_dir = CONFIG["OUTPUT_DIR"]
    snips_dir = os.path.join(out_dir, "snips")
    accepted_dir = os.path.join(out_dir, "accepted")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    Path(snips_dir).mkdir(parents=True, exist_ok=True)
    Path(accepted_dir).mkdir(parents=True, exist_ok=True)

    poly = load_polygon()

    plate_model = CONFIG["PLATE_MODEL"]
    vehicle_model = CONFIG["VEHICLE_MODEL"]
    if not os.path.exists(plate_model):
        raise FileNotFoundError(f"Plate model not found: {plate_model}")
    if not os.path.exists(vehicle_model):
        raise FileNotFoundError(f"Vehicle model not found: {vehicle_model}")

    plate_detector = YOLO(plate_model)
    vehicle_detector = YOLO(vehicle_model)
    ocr_pool = OCRPool(n_workers=2, max_q=2048)

    cap = open_capture(source)
    if cap is None:
        raise RuntimeError(f"Cannot open source: {source}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    fps = fps if fps and fps > 1 else 25.0
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

    preview_path = os.path.join(out_dir, "preview_gate_zone.mp4")
    csv_path = os.path.join(out_dir, "gate_zone_events.csv")
    debug_path = os.path.join(out_dir, "gate_zone_debug.csv")

    writer = None
    if CONFIG["SAVE_PREVIEW"]:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(preview_path, fourcc, fps, (W, H))

    fields = [
        "vehicle_id", "entry_time", "exit_time",
        "entry_time_sec", "exit_time_sec", "duration_sec",
        "final_plate", "final_ocr_conf", "best_det_conf",
        "combined_image_path", "combined_image_base64"
    ]
    rows = []
    debug_rows = []

    # session
    session_active = False
    vid_counter = 0
    session = {
        "vehicle_id": None,
        "entry_time": None,
        "exit_time": None,
        "entry_time_sec": None,
        "exit_time_sec": None,
        "outside_count": 0,

        "best_plate": "",
        "best_ocr_conf": 0.0,
        "best_det_conf": 0.0,

        "last_plate_crop": None,
        "best_car_crop": None,

        "combined_path": "",
        "combined_b64": "",

        "last_ocr_time": -999.0,
    }

    def start_session(now_sec):
        nonlocal session_active, vid_counter
        session_active = True
        vid_counter += 1
        session["vehicle_id"] = f"V{vid_counter:05d}"
        session["entry_time"] = now_wall()
        session["exit_time"] = now_wall()
        session["entry_time_sec"] = float(now_sec)
        session["exit_time_sec"] = float(now_sec)
        session["outside_count"] = 0
        session["best_plate"] = ""
        session["best_ocr_conf"] = 0.0
        session["best_det_conf"] = 0.0
        session["last_plate_crop"] = None
        session["best_car_crop"] = None
        session["combined_path"] = ""
        session["combined_b64"] = ""
        session["last_ocr_time"] = -999.0

    def end_session():
        nonlocal session_active, rows
        if not session_active:
            return
        session_active = False
        session["exit_time"] = now_wall()
        duration = float(session["exit_time_sec"] - session["entry_time_sec"])

        rows.append({
            "vehicle_id": session["vehicle_id"],
            "entry_time": session["entry_time"],
            "exit_time": session["exit_time"],
            "entry_time_sec": round(session["entry_time_sec"], 3),
            "exit_time_sec": round(session["exit_time_sec"], 3),
            "duration_sec": round(duration, 3),
            "final_plate": session["best_plate"],
            "final_ocr_conf": round(float(session["best_ocr_conf"]), 4),
            "best_det_conf": round(float(session["best_det_conf"]), 4),
            "combined_image_path": session["combined_path"],
            "combined_image_base64": session["combined_b64"],
        })

        pd.DataFrame(rows, columns=fields).to_csv(csv_path, index=False)

    frame_idx = -1
    stride = int(CONFIG["STRIDE"])
    imgsz = int(CONFIG["IMGSZ"])

    plate_conf = float(CONFIG["PLATE_CONF"])
    plate_iou = float(CONFIG["PLATE_IOU"])
    vehicle_conf = float(CONFIG["VEHICLE_CONF"])

    ocr_min = float(CONFIG["OCR_MIN_CONF"])
    blur_th = float(CONFIG["BLUR_VAR_TH"])
    ocr_cooldown = float(CONFIG["OCR_COOLDOWN_SEC"])
    fast_up = float(CONFIG["FAST_UP"])
    heavy_up = float(CONFIG["HEAVY_UP"])

    exit_outside_frames = int(CONFIG["EXIT_OUTSIDE_FRAMES"])
    b64_q = int(CONFIG["B64_JPEG_QUALITY"])
    banner_bgr = tuple(CONFIG["BANNER_BGR"])
    vehicle_classes = set(CONFIG["VEHICLE_CLASSES"])

    while True:
        ret, frame = cap.read()
        if not ret:
            # RTSP reconnect
            if str(source).startswith("rtsp://"):
                print("[WARN] RTSP frame lost. Reconnecting...")
                try:
                    cap.release()
                except:
                    pass
                time.sleep(float(CONFIG.get("RECONNECT_SLEEP_SEC", 1.0)))
                cap = open_capture(source)
                if cap is None:
                    continue
                continue
            break

        frame_idx += 1
        now_sec = frame_idx / float(fps)

        # apply OCR results
        for r in ocr_pool.poll(300):
            if not session_active:
                continue
            if r["vehicle_id"] != session["vehicle_id"]:
                continue
            if not r["valid"]:
                continue

            plate = r["ocr_text"]
            ocr_conf = float(r["ocr_conf"])
            det_conf = float(r["det_conf"])

            # update only if better confidence
            if ocr_conf > float(session["best_ocr_conf"]):
                session["best_plate"] = plate
                session["best_ocr_conf"] = ocr_conf
                session["best_det_conf"] = det_conf
                session["exit_time"] = now_wall()
                session["exit_time_sec"] = float(now_sec)

                # On valid plate -> create combined image from FULL CAR crop
                if session["best_car_crop"] is not None and session["best_car_crop"].size > 0:
                    combined, out_path = make_combined_image_from_car(
                        session["best_car_crop"], plate, accepted_dir, banner_bgr=banner_bgr
                    )
                    if combined is not None:
                        session["combined_path"] = out_path or ""
                        session["combined_b64"] = b64_jpeg(
                            combined, quality=b64_q)

        # stride
        if stride > 1 and (frame_idx % stride != 0):
            if writer is not None:
                writer.write(frame)
            continue

        annotated = frame.copy()
        cv2.polylines(annotated, [poly], True, (255, 0, 255), 2)

        # 1) Detect plate inside polygon
        detp = plate_detector.predict(
            source=frame, conf=plate_conf, iou=plate_iou, imgsz=imgsz,
            verbose=False, device="cpu"
        )[0]

        best_plate_det = None
        if detp.boxes is not None and len(detp.boxes) > 0:
            xyxy = detp.boxes.xyxy.cpu().numpy()
            confs = detp.boxes.conf.cpu().numpy()
            best_c = -1.0
            for b, c in zip(xyxy, confs):
                x1, y1, x2, y2 = b.tolist()
                cx, cy = bbox_center_xyxy([x1, y1, x2, y2])
                if point_in_poly((cx, cy), poly):
                    if float(c) > best_c:
                        best_c = float(c)
                        best_plate_det = (x1, y1, x2, y2, float(c))

        if best_plate_det is not None:
            if not session_active:
                start_session(now_sec)

            session["outside_count"] = 0
            session["exit_time"] = now_wall()
            session["exit_time_sec"] = float(now_sec)

            px1, py1, px2, py2, pconf = best_plate_det
            x1i, y1i, x2i, y2i = map(
                int, [max(0, px1), max(0, py1), min(W-1, px2), min(H-1, py2)])
            plate_crop = frame[y1i:y2i, x1i:x2i]
            if plate_crop.size > 0:
                session["last_plate_crop"] = plate_crop.copy()

            # 2) Detect vehicles and map plate->vehicle via IoU
            detv = vehicle_detector.predict(
                source=frame, conf=vehicle_conf, iou=0.45, imgsz=imgsz,
                verbose=False, device="cpu"
            )[0]

            best_vehicle_box = None
            best_i = 0.0
            if detv.boxes is not None and len(detv.boxes) > 0:
                v_xyxy = detv.boxes.xyxy.cpu().numpy()
                v_confs = detv.boxes.conf.cpu().numpy()
                v_cls = detv.boxes.cls.cpu().numpy()

                plate_box = [float(px1), float(py1), float(px2), float(py2)]
                for vb, vc, cl in zip(v_xyxy, v_confs, v_cls):
                    if int(cl) not in vehicle_classes:
                        continue
                    bx1, by1, bx2, by2 = vb.tolist()
                    i = iou_xyxy(plate_box, [bx1, by1, bx2, by2])
                    if i > best_i:
                        best_i = i
                        best_vehicle_box = (bx1, by1, bx2, by2, float(vc))

            if best_vehicle_box is not None:
                vx1, vy1, vx2, vy2, vconf = best_vehicle_box
                vx1i, vy1i, vx2i, vy2i = map(
                    int, [max(0, vx1), max(0, vy1), min(W-1, vx2), min(H-1, vy2)])
                car_crop = frame[vy1i:vy2i, vx1i:vx2i]
                if car_crop.size > 0:
                    session["best_car_crop"] = car_crop.copy()

                cv2.rectangle(annotated, (vx1i, vy1i),
                              (vx2i, vy2i), (255, 200, 0), 2)
                cv2.putText(annotated, f"CAR {vconf:.2f}", (vx1i, max(20, vy1i-10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 200, 0), 2)

            # OCR cooldown
            if plate_crop is not None and plate_crop.size > 0:
                if (now_sec - float(session["last_ocr_time"])) >= ocr_cooldown:
                    session["last_ocr_time"] = float(now_sec)
                    ocr_pool.submit((
                        session["vehicle_id"], frame_idx, float(
                            now_sec), float(pconf), plate_crop.copy(),
                        ocr_min, blur_th, fast_up, heavy_up
                    ))

            cv2.rectangle(annotated, (x1i, y1i), (x2i, y2i), (0, 255, 0), 2)
            cv2.putText(annotated, f"PLATE {pconf:.2f}", (x1i, max(20, y1i-10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        else:
            if session_active:
                session["outside_count"] += 1
                session["exit_time"] = now_wall()
                session["exit_time_sec"] = float(now_sec)
                if session["outside_count"] >= exit_outside_frames:
                    end_session()

        # overlay status
        if session_active:
            txt = session["best_plate"] if session["best_plate"] else "reading..."
            cv2.putText(annotated, f"{session['vehicle_id']}  {txt} ({session['best_ocr_conf']:.2f})",
                        (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)

        debug_rows.append({
            "frame": frame_idx,
            "time_sec": round(now_sec, 3),
            "active": int(session_active),
            "vehicle_id": session["vehicle_id"] if session_active else "",
            "best_plate": session["best_plate"] if session_active else "",
            "best_conf": round(float(session["best_ocr_conf"]), 4) if session_active else 0.0,
            "outside_count": int(session["outside_count"]) if session_active else 0,
        })

        if writer is not None:
            writer.write(annotated)

        if CONFIG["SHOW_WINDOW"]:
            cv2.imshow("Gate ANPR (Zone Lock)", annotated)
            if cv2.waitKey(1) & 0xFF == 27:
                break

    # finalize
    if session_active:
        end_session()

    cap.release()
    if writer is not None:
        writer.release()
    if CONFIG["SHOW_WINDOW"]:
        cv2.destroyAllWindows()
    ocr_pool.stop()

    pd.DataFrame(debug_rows).to_csv(debug_path, index=False)

    print("\n[DONE]")
    print(" CSV:", csv_path)
    print(" Debug:", debug_path)
    if CONFIG["SAVE_PREVIEW"]:
        print(" Preview:", preview_path)
    print(" Combined images:", os.path.join(out_dir, "accepted"))


if __name__ == "__main__":
    main()
