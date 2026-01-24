# -*- coding: utf-8 -*-
# loitering_using_saved_zone.py
# pip install ultralytics opencv-python pillow requests

import cv2
import time
import os
import json
import csv
import requests
import numpy as np
import base64
import secrets
from ultralytics import YOLO
from datetime import datetime

# =============== CONFIGURATION =================
RTSP_URL = "https://api.vms.solstium.net/hls/1732a735de/index.m3u8"
MODEL_PATH = "yolov8m.pt"
IMGSZ = 640  # Reduced for better performance
PERSON_CLASS_ID = 0
CONF = 0.35
IOU = 0.5
TRACKER = "bytetrack.yaml"

# =============== ZONE DEFINITION =================
ZONE_POINTS = [[584, 63], [621, 58], [
    638, 237], [557, 249], [552, 85], [586, 67]]

# =============== LOITERING POLICY =================
DWELL_THRESHOLD_SEC = 30      # 30 seconds for testing
COOLDOWN_SEC = 60             # 1 minute cooldown for testing
CAPTURE_ONCE_PER_STAY = True

# =============== STREAM CONFIG =================
RECONNECT_SLEEP_SEC = 5
MAX_RECONNECT_ATTEMPTS = 10
FRAME_TIMEOUT_SEC = 10

# =============== OUTPUT CONFIG =================
DRAW = False  # No preview
PROCESSING_INTERVAL = 30      # Process every 30 seconds
WINDOW_TITLE = "Loitering Detection - 30 Sec Threshold"
SNAP_DIR = "loiter_snaps"
os.makedirs(SNAP_DIR, exist_ok=True)
EVENT_LOG_CSV = os.path.join(SNAP_DIR, "events.csv")

# =============== API CONFIG =================
API_ENDPOINT = "https://visitormanagement.solstium.net/security_monitoring/api/admin/add_alarm"
API_TIMEOUT = 15

# =============== ALERT CONFIG =================
# Fixed: replaced special dash with regular dash
CAMERA_NAME = "Seawind - SideGate"
LOCATION_ID = "6864f64a6fbcc7432ee477f4"
LOCATION_NAME = "Seawind"


def setup_camera():
    """Initialize camera with proper timeout settings"""
    cap = cv2.VideoCapture(RTSP_URL)

    # Set timeouts
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FPS, 15)

    # Try to set OpenCV timeouts (may not work on all systems)
    try:
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
    except:
        pass

    return cap


def is_stream_alive(cap):
    """Check if stream is still alive"""
    if cap is None or not cap.isOpened():
        return False

    # Try to grab a frame with timeout
    start_time = time.time()
    while time.time() - start_time < FRAME_TIMEOUT_SEC:
        if cap.grab():
            return True
        time.sleep(0.1)

    return False


def reconnect_camera(cap, attempt_count):
    """Reconnect to camera stream"""
    print(f"[CAMERA] Attempting reconnect #{attempt_count}...")

    if cap is not None:
        try:
            cap.release()
        except:
            pass

    time.sleep(RECONNECT_SLEEP_SEC)

    new_cap = setup_camera()
    if new_cap and new_cap.isOpened():
        print("[CAMERA] Reconnected successfully")
        return new_cap, attempt_count + 1
    else:
        print("[CAMERA] Reconnect failed")
        return None, attempt_count + 1


def point_in_polygon(point, poly):
    """Check if point is inside polygon"""
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


def save_evidence(frame, bbox, track_id, dwell_time):
    """Save evidence images and return paths"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save cropped image of person
    x1, y1, x2, y2 = [int(coord) for coord in bbox]
    # Add padding to crop
    pad = 15
    x1_pad = max(0, x1 - pad)
    y1_pad = max(0, y1 - pad)
    x2_pad = min(frame.shape[1], x2 + pad)
    y2_pad = min(frame.shape[0], y2 + pad)

    crop_img = frame[y1_pad:y2_pad, x1_pad:x2_pad]
    crop_filename = f"crop_tid{track_id}_{int(dwell_time)}s_{timestamp}.jpg"
    crop_path = os.path.join(SNAP_DIR, crop_filename)

    if crop_img.size > 0:
        cv2.imwrite(crop_path, crop_img)
    else:
        crop_path = ""

    # Save full frame with annotations
    annotated_frame = frame.copy()

    # Draw zone on annotated frame
    pts_array = np.array(ZONE_POINTS, np.int32)
    overlay = annotated_frame.copy()
    cv2.fillPoly(overlay, [pts_array], (255, 0, 255))
    cv2.addWeighted(overlay, 0.3, annotated_frame, 0.7, 0, annotated_frame)
    cv2.polylines(annotated_frame, [pts_array], True, (255, 0, 255), 2)

    # Draw bounding box
    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

    # Add text info
    info_text = f"ID: {track_id} - Dwell: {dwell_time:.1f}s"
    cv2.putText(annotated_frame, info_text, (x1, max(0, y1-10)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    frame_filename = f"frame_tid{track_id}_{int(dwell_time)}s_{timestamp}.jpg"
    frame_path = os.path.join(SNAP_DIR, frame_filename)
    cv2.imwrite(frame_path, annotated_frame)

    return crop_path, frame_path


def log_event(track_id, dwell_time, crop_path, frame_path):
    """Log event to CSV file"""
    timestamp = datetime.now().isoformat()

    file_exists = os.path.isfile(EVENT_LOG_CSV)

    with open(EVENT_LOG_CSV, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(
                ['timestamp', 'track_id', 'dwell_seconds', 'crop_path', 'frame_path'])
        writer.writerow(
            [timestamp, track_id, f"{dwell_time:.2f}", crop_path, frame_path])

    print(
        f"[EVENT] Loitering detected - Track ID: {track_id}, Dwell: {dwell_time:.1f}s")


def image_to_base64(image_path):
    """Convert image to base64 string"""
    try:
        with open(image_path, "rb") as img_file:
            image_base64 = base64.b64encode(img_file.read()).decode("utf-8")
        return image_base64
    except Exception as e:
        print(f"[API] Error converting image to base64: {e}")
        return ""


def send_alert(track_id, dwell_time, image_path):
    """Send alert to API"""
    if not API_ENDPOINT:
        print("[API] No API endpoint configured")
        return

    try:
        # Convert image to base64
        snapshot_base64 = image_to_base64(image_path)
        if not snapshot_base64:
            print("[API] Failed to convert image to base64")
            return

        # Generate random ID
        random_id = secrets.token_hex(8)

        # Get current date in required format
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Construct payload
        payload = {
            "camera": CAMERA_NAME,
            "alert_type": "loitering",
            "location_id": LOCATION_ID,
            "location_name": LOCATION_NAME,
            "severity": "high" if dwell_time > 60 else "medium",
            "status": "new",
            "date_time": current_date,
            "dwellSec": int(dwell_time),
            "snapshotUrl": snapshot_base64,
            "track_id": track_id
        }

        # Send request
        response = requests.post(
            API_ENDPOINT, json=payload, timeout=API_TIMEOUT)

        if response.status_code == 200:
            print(
                f"? Alert sent successfully for track {track_id} (dwell: {dwell_time:.1f}s)")
        else:
            print(
                f"? Failed to send alert. Status code: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"? Request error: {e}")
    except Exception as e:
        print(f"[API] Unexpected error: {e}")


def main():
    print("Starting loitering detection system...")
    print(
        f"Threshold: {DWELL_THRESHOLD_SEC} seconds ({DWELL_THRESHOLD_SEC/60:.1f} minutes)")
    print(f"Processing Interval: {PROCESSING_INTERVAL} seconds")
    print(f"Preview: DISABLED")
    print(f"API Endpoint: {API_ENDPOINT}")

    # Initialize model
    try:
        model = YOLO(MODEL_PATH)
        print(f"[MODEL] Loaded: {MODEL_PATH}")
    except Exception as e:
        print(f"[ERROR] Failed to load model: {e}")
        return

    # Initialize camera
    cap = setup_camera()
    if not cap or not cap.isOpened():
        print("[ERROR] Failed to initialize camera")
        return

    # Tracking state
    track_states = {}  # track_id -> {first_seen: timestamp, alerted: bool, last_bbox: tuple}
    reconnect_attempts = 0
    last_processing_time = 0
    frame_count = 0

    print("[SYSTEM] Starting main loop...")

    while True:
        current_time = time.time()

        # Check if stream is alive
        if not is_stream_alive(cap):
            print("[CAMERA] Stream appears dead, attempting reconnect...")
            if reconnect_attempts >= MAX_RECONNECT_ATTEMPTS:
                print("[CAMERA] Max reconnection attempts reached. Exiting.")
                break

            cap, reconnect_attempts = reconnect_camera(cap, reconnect_attempts)
            if cap is None:
                continue
            else:
                reconnect_attempts = 0

        # Read frame
        ret, frame = cap.read()
        if not ret or frame is None:
            print("[CAMERA] Failed to read frame")
            time.sleep(1)
            continue

        frame_count += 1

        # Process only at specified intervals
        if current_time - last_processing_time >= PROCESSING_INTERVAL:
            print(
                f"[PROCESSING] Analyzing frame {frame_count} at {datetime.now().strftime('%H:%M:%S')}")

            # Resize frame for faster processing if needed
            original_height, original_width = frame.shape[:2]
            if original_width > 1280:
                scale = 1280 / original_width
                new_width = 1280
                new_height = int(original_height * scale)
                frame_processed = cv2.resize(frame, (new_width, new_height))
            else:
                frame_processed = frame

            # Run object detection
            try:
                results = model.track(
                    frame_processed,
                    persist=True,
                    classes=[PERSON_CLASS_ID],
                    conf=CONF,
                    iou=IOU,
                    imgsz=IMGSZ,
                    tracker=TRACKER,
                    verbose=False
                )
            except Exception as e:
                print(f"[MODEL] Detection error: {e}")
                last_processing_time = current_time
                continue

            current_tracks = set()

            if results and len(results) > 0:
                boxes = results[0].boxes
                if boxes is not None and boxes.id is not None:
                    for box, track_id in zip(boxes, boxes.id):
                        if int(box.cls) != PERSON_CLASS_ID:
                            continue

                        track_id = int(track_id.item())
                        current_tracks.add(track_id)

                        # Get bounding box
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                        # Calculate center point
                        center_x = (x1 + x2) // 2
                        center_y = (y1 + y2) // 2

                        # Check if person is in zone
                        in_zone = point_in_polygon(
                            (center_x, center_y), ZONE_POINTS)

                        # Update track state
                        if track_id not in track_states:
                            track_states[track_id] = {
                                'first_seen': current_time if in_zone else None,
                                'alerted': False,
                                'last_bbox': (x1, y1, x2, y2)
                            }

                        # Update bounding box
                        track_states[track_id]['last_bbox'] = (x1, y1, x2, y2)

                        if in_zone:
                            if track_states[track_id]['first_seen'] is None:
                                # Just entered the zone
                                track_states[track_id]['first_seen'] = current_time
                                track_states[track_id]['alerted'] = False
                                print(f"[TRACK] ID {track_id} entered zone")

                            # Calculate dwell time
                            dwell_time = current_time - \
                                track_states[track_id]['first_seen']

                            print(
                                f"[TRACK] ID {track_id} in zone for {dwell_time:.1f}s")

                            # Check for loitering alert
                            if (dwell_time >= DWELL_THRESHOLD_SEC and
                                not track_states[track_id]['alerted'] and
                                    (not CAPTURE_ONCE_PER_STAY or not track_states[track_id].get('alerted_this_stay', False))):

                                print(
                                    f"?? LOITERING ALERT: Track {track_id} - {dwell_time:.1f}s")

                                # Save evidence
                                crop_path, frame_path = save_evidence(
                                    frame_processed,
                                    (x1, y1, x2, y2),
                                    track_id,
                                    dwell_time
                                )

                                # Log event
                                log_event(track_id, dwell_time,
                                          crop_path, frame_path)

                                # Send alert to API
                                send_alert(track_id, dwell_time, frame_path)

                                # Update track state
                                track_states[track_id]['alerted'] = True
                                if CAPTURE_ONCE_PER_STAY:
                                    track_states[track_id]['alerted_this_stay'] = True

                        else:
                            # Person left the zone
                            if track_states[track_id]['first_seen'] is not None:
                                dwell_time = current_time - \
                                    track_states[track_id]['first_seen']
                                print(
                                    f"[TRACK] ID {track_id} left zone after {dwell_time:.1f}s")
                                if CAPTURE_ONCE_PER_STAY:
                                    track_states[track_id]['alerted_this_stay'] = False
                                track_states[track_id]['first_seen'] = None

            # Clean up stale tracks
            stale_tracks = [tid for tid in track_states.keys()
                            if tid not in current_tracks]
            for tid in stale_tracks:
                print(
                    f"[TRACK] ID {tid} no longer detected, removing from tracking")
                del track_states[tid]

            # Update processing time
            last_processing_time = current_time
            print(
                f"[STATUS] Active tracks: {len(track_states)}, Total frames: {frame_count}")

        # Small sleep to prevent CPU overload
        time.sleep(0.1)

    # Cleanup
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()
    print("[SYSTEM] Stopped")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[SYSTEM] Interrupted by user")
    except Exception as e:
        print(f"[SYSTEM] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
