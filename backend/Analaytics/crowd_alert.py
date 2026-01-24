# -*- coding: utf-8 -*-
# crowd_count_zone_15min_alert_stable_ids.py
#
# Goal (as you asked):
# - Each person gets an ID and it should NOT change “after some time” as much as possible.
#
# What we do professionally:
# 1) Run YOLO track EVERY frame (not every 30 sec) -> this is the biggest fix for stable IDs
# 2) Use ByteTrack with a strong config (bytetrack.yaml) + keep "lost" tracks longer
# 3) Keep track memory for some time (TRACK_FORGET_SEC) so short misses don't reset logic
# 4) Every 15 minutes -> compute UNIQUE entries into polygon zone (rolling 15-min window)
#    If unique_count > MAX_COUNT -> capture annotated snapshot + push base64 to API
#
# Install:
#   pip install ultralytics opencv-python numpy requests
#
# Run:
#   python crowd_count_zone_15min_alert_stable_ids.py
#
# NOTE:
# - With ByteTrack, if a person fully disappears for long time (out of view / heavy occlusion),
#   tracker may reassign a new id later. This code + config minimizes it.

import os
import time
import cv2
import base64
import requests
import numpy as np
from datetime import datetime
from ultralytics import YOLO

# =================== CONFIG ===================
RTSP_URL = "rtsp://admin:sd123456@fashionislandcctv.ddns.net:554/cam/realmonitor?channel=1&subtype=0"  # HLS/RTSP/MP4
MODEL_PATH = "yolov8m.pt"

# IMPORTANT: Keep tracker config file in same folder as script
TRACKER = "bytetrack.yaml"

IMGSZ = 640
PERSON_CLASS_ID = 0
CONF = 0.35
IOU = 0.5

# =================== ZONE =====================
ZONE_NAME = "Zone-1"
ZONE_POINTS = [[584, 63], [621, 58], [
    638, 237], [557, 249], [552, 85], [586, 67]]
CAMERA_NAME = "Seawind - SideGate"

# =================== CROWD POLICY =============
WINDOW_SEC = 15 * 60      # 15 minutes
MAX_COUNT = 10            # alert if unique entries in window exceed this
COOLDOWN_SEC = 15 * 60    # avoid repeated alerts spam
CAPTURE_ON_ALERT = True

# =================== TRACK STABILITY ==========
# Keep memory of tracks even if YOLO temporarily doesn't detect them (helps avoid logic reset)
TRACK_FORGET_SEC = 120    # keep track state for 2 minutes after last seen
# If your scene has long occlusions, increase to 300

# =================== STREAM ===================
RECONNECT_SLEEP_SEC = 5
MAX_RECONNECT_ATTEMPTS = 10
FRAME_TIMEOUT_SEC = 10

# =================== OUTPUT ===================
SNAP_DIR = "crowd_snaps"
os.makedirs(SNAP_DIR, exist_ok=True)
DRAW_ZONE_ON_SNAPSHOT = True

# =================== API ======================
API_ENDPOINT = "http://127.0.0.1:8000/api/crowd/alerts"
API_TIMEOUT = 15


# =================== HELPERS ==================
def setup_camera():
    cap = cv2.VideoCapture(RTSP_URL)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FPS, 15)
    try:
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
    except Exception:
        pass
    return cap


def is_stream_alive(cap):
    if cap is None or not cap.isOpened():
        return False
    start = time.time()
    while time.time() - start < FRAME_TIMEOUT_SEC:
        if cap.grab():
            return True
        time.sleep(0.1)
    return False


def reconnect_camera(cap, attempt_count):
    print(f"[CAMERA] Reconnect attempt #{attempt_count}...")
    try:
        if cap is not None:
            cap.release()
    except Exception:
        pass

    time.sleep(RECONNECT_SLEEP_SEC)

    new_cap = setup_camera()
    if new_cap and new_cap.isOpened():
        print("[CAMERA] Reconnected ✅")
        return new_cap, attempt_count + 1
    print("[CAMERA] Reconnect failed ❌")
    return None, attempt_count + 1


def point_in_polygon(point, poly):
    x, y = point
    n = len(poly)
    inside = False
    p1x, p1y = poly[0]
    for i in range(1, n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def draw_zone(img):
    pts = np.array(ZONE_POINTS, np.int32)
    overlay = img.copy()
    cv2.fillPoly(overlay, [pts], (255, 0, 255))
    cv2.addWeighted(overlay, 0.25, img, 0.75, 0, img)
    cv2.polylines(img, [pts], True, (255, 0, 255), 2)


def save_snapshot(frame, unique_count):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    img = frame.copy()

    if DRAW_ZONE_ON_SNAPSHOT:
        draw_zone(img)

    label = f"{ZONE_NAME} | Unique(15min): {unique_count} | Max: {MAX_COUNT} | {CAMERA_NAME}"
    cv2.rectangle(
        img, (10, 10), (min(10 + 1400, img.shape[1]-10), 55), (0, 0, 0), -1)
    cv2.putText(img, label, (20, 45), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (0, 255, 255), 2)

    path = os.path.join(SNAP_DIR, f"crowd_{ZONE_NAME}_{unique_count}_{ts}.jpg")
    cv2.imwrite(path, img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return path


def image_to_base64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"[IMG] base64 error: {e}")
        return ""


def push_alert(unique_count, snapshot_path):
    payload = {
        "zone_name": ZONE_NAME,
        "camera_name": CAMERA_NAME,
        "person_count": int(unique_count),
        "image_base64": image_to_base64(snapshot_path) if snapshot_path else "",
        "max_count": int(MAX_COUNT),
    }

    try:
        r = requests.post(API_ENDPOINT, json=payload, timeout=API_TIMEOUT)
        if r.status_code in (200, 201):
            print(f"[API] ✅ Alert sent | count={unique_count} > {MAX_COUNT}")
        else:
            print(f"[API] ❌ Failed {r.status_code} | {r.text}")
    except Exception as e:
        print(f"[API] ❌ Request error: {e}")


# =================== MAIN =====================
def main():
    print("[SYSTEM] Crowd counting started")
    print(
        f"[CONFIG] Window={WINDOW_SEC}s | MaxCount={MAX_COUNT} | Cooldown={COOLDOWN_SEC}s")
    print(f"[CONFIG] Tracker={TRACKER} | TrackForget={TRACK_FORGET_SEC}s")
    print(f"[CONFIG] API={API_ENDPOINT}")

    # Load model
    try:
        model = YOLO(MODEL_PATH)
        print(f"[MODEL] Loaded: {MODEL_PATH}")
    except Exception as e:
        print(f"[ERROR] Model load failed: {e}")
        return

    # Open stream
    cap = setup_camera()
    if not cap or not cap.isOpened():
        print("[ERROR] Cannot open stream:", RTSP_URL)
        return

    reconnect_attempts = 0

    # Track memory:
    # state[tid] = {
    #   "last_seen": float,
    #   "in_zone": bool,
    # }
    state = {}

    # Entry events over rolling 15-min window:
    # entry_events = [(ts, tid), ...]
    entry_events = []

    # Timers
    last_alert_time = 0.0
    last_eval_time = time.time()
    last_frame = None

    print("[SYSTEM] Main loop running... (tracking every frame)")

    while True:
        now = time.time()

        # Stream health check
        if not is_stream_alive(cap):
            print("[CAMERA] Stream dead. Trying reconnect...")
            if reconnect_attempts >= MAX_RECONNECT_ATTEMPTS:
                print("[CAMERA] Max reconnect attempts reached. Exiting.")
                break
            cap, reconnect_attempts = reconnect_camera(cap, reconnect_attempts)
            if cap is None:
                continue
            reconnect_attempts = 0

        ret, frame = cap.read()
        if not ret or frame is None:
            print("[CAMERA] Frame read failed")
            time.sleep(1)
            continue

        last_frame = frame

        # Run tracking EVERY frame for stable IDs
        try:
            results = model.track(
                frame,
                persist=True,
                classes=[PERSON_CLASS_ID],
                conf=CONF,
                iou=IOU,
                imgsz=IMGSZ,
                tracker=TRACKER,
                verbose=False
            )
        except Exception as e:
            print(f"[MODEL] track error: {e}")
            time.sleep(0.05)
            continue

        current_tracks = set()

        if results and len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            if boxes.id is not None:
                for box, tid_tensor in zip(boxes, boxes.id):
                    if int(box.cls) != PERSON_CLASS_ID:
                        continue

                    tid = int(tid_tensor.item())
                    current_tracks.add(tid)

                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2
                    in_zone = point_in_polygon((cx, cy), ZONE_POINTS)

                    if tid not in state:
                        state[tid] = {"last_seen": now, "in_zone": False}
                    else:
                        state[tid]["last_seen"] = now

                    prev_in_zone = state[tid]["in_zone"]
                    state[tid]["in_zone"] = in_zone

                    # Enter event (False -> True)
                    if (not prev_in_zone) and in_zone:
                        entry_events.append((now, tid))
                        print(f"[ENTER] tid={tid} entered {ZONE_NAME}")

        # Prune old entry events
        cutoff = now - WINDOW_SEC
        entry_events = [(t, tid) for (t, tid) in entry_events if t >= cutoff]

        # Prune stale track memory (do NOT delete immediately)
        for tid in list(state.keys()):
            if now - state[tid]["last_seen"] > TRACK_FORGET_SEC:
                del state[tid]

        # Evaluate every 15 minutes (exact ask)
        if now - last_eval_time >= WINDOW_SEC:
            unique_ids = {tid for (t, tid) in entry_events}
            unique_count = len(unique_ids)

            print(
                f"[EVAL] 15min unique entries: {unique_count} (max={MAX_COUNT}) | active_mem={len(state)}")

            if unique_count > MAX_COUNT:
                if now - last_alert_time >= COOLDOWN_SEC:
                    snap_path = ""
                    if CAPTURE_ON_ALERT and last_frame is not None:
                        snap_path = save_snapshot(last_frame, unique_count)
                    push_alert(unique_count, snap_path)
                    last_alert_time = now
                else:
                    print("[ALERT] Skipped due to cooldown")

            last_eval_time = now

        # small sleep
        time.sleep(0.01)

    try:
        cap.release()
    except Exception:
        pass
    cv2.destroyAllWindows()
    print("[SYSTEM] Stopped")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[SYSTEM] Interrupted by user")
