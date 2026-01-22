import cv2
import json
import os
import numpy as np

VIDEO_SOURCE = "../data/test1.mp4"  # rtsp/hls/mp4
OUT_JSON = "zonesss.json"


def draw_polygon(win, frame, title):
    pts = []

    def mouse(event, x, y, flags, param):
        nonlocal pts
        if event == cv2.EVENT_LBUTTONDOWN:
            pts.append([x, y])
        elif event == cv2.EVENT_RBUTTONDOWN and len(pts) > 0:
            pts.pop()

    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(win, mouse)

    while True:
        disp = frame.copy()
        if len(pts) >= 2:
            cv2.polylines(disp, [np.array(pts, np.int32).reshape(
                (-1, 1, 2))], False, (0, 255, 255), 2)
        for p in pts:
            cv2.circle(disp, tuple(p), 4, (0, 0, 255), -1)

        cv2.putText(disp, title, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(disp, "Left click: add point | Right click: undo | Press S: save | R: reset", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.imshow(win, disp)

        k = cv2.waitKey(1) & 0xFF
        if k == ord('r'):
            pts = []
        elif k == ord('s'):
            if len(pts) < 3:
                print("Need at least 3 points")
                continue
            cv2.destroyWindow(win)
            return pts
        elif k == 27:
            cv2.destroyAllWindows()
            raise SystemExit("Cancelled")


def main():
    cap = cv2.VideoCapture(VIDEO_SOURCE)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise SystemExit("Cannot read frame from source")

    entry = draw_polygon(
        "ZONE", frame, "Draw ENTRY zone, then press S to save")
    exit_ = draw_polygon("ZONE", frame, "Draw EXIT zone, then press S to save")

    with open(OUT_JSON, "w") as f:
        json.dump({"entry": entry, "exit": exit_}, f, indent=2)

    print("Saved:", OUT_JSON)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
