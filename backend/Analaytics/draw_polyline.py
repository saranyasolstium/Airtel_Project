# click_zone.py
# pip install opencv-python numpy
import cv2
import os
import json
import numpy as np

RTSP_URL = "https://api.vms.solstium.net/hls/df3e2570e7/index.m3u8"
OUT_JSON = "zone_points.json"

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
    "rtsp_transport;tcp|stimeout;5000000|rw_timeout;5000000|reorder_queue_size;0|max_delay;5000000"
)
cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)

ok, frame = cap.read()
if not ok or frame is None:
    raise SystemExit("Couldn’t read a frame from RTSP. Check URL/credentials.")

pts = []


def on_mouse(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        pts.append([int(x), int(y)])


cv2.namedWindow(
    "Draw zone (L-click points, s=save, u=undo, r=reset, Esc=quit)")
cv2.setMouseCallback(
    "Draw zone (L-click points, s=save, u=undo, r=reset, Esc=quit)", on_mouse)

while True:
    disp = frame.copy()
    if len(pts) >= 1:
        for i, (x, y) in enumerate(pts):
            cv2.circle(disp, (x, y), 6, (0, 255, 255), -1)
            cv2.putText(disp, str(i + 1), (x + 8, y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        if len(pts) >= 2:
            poly = np.array(pts, np.int32)
            cv2.polylines(disp, [poly], False, (255, 0, 255), 2, cv2.LINE_AA)

    cv2.imshow(
        "Draw zone (L-click points, s=save, u=undo, r=reset, Esc=quit)", disp)
    k = cv2.waitKey(20) & 0xFF
    if k == ord('u') and pts:
        pts.pop()
    elif k == ord('r'):
        pts.clear()
    elif k == ord('s') and len(pts) >= 3:
        data = {"size": [frame.shape[1], frame.shape[0]], "pts_px": pts}
        json.dump(data, open(OUT_JSON, "w"))
        print("Saved:", OUT_JSON, "points:", pts)
        break
    elif k == 27:  # Esc
        break

cv2.destroyAllWindows()
cap.release()
