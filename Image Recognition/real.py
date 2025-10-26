# save_snapshots.py
import os
import time
import requests
import numpy as np
import cv2
from datetime import datetime

# ====== CONFIG ======
SNAP_URL = "http://atharva-2.local:8081"  # put your working URL (add USER:PASS if needed)
OUT_DIR = "snaps"                  # base folder for images
INTERVAL_SEC = 5                   # how often to capture
MAKE_DAILY_SUBFOLDERS = True       # True -> snaps/2025-10-10/snap_*.jpg
ROTATE = None                      # None | "cw90" | "ccw90" | "180"
TIMEOUT_SEC = 6                    # HTTP timeout in seconds
JPEG_QUALITY = 90                  # 0..100
# =====================

def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path

def rotate_if_needed(img):
    if ROTATE == "cw90":
        return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    if ROTATE == "ccw90":
        return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    if ROTATE == "180":
        return cv2.rotate(img, cv2.ROTATE_180)
    return img

def save_snapshot_once():
    # choose output folder
    sub = datetime.now().strftime("%Y-%m-%d") if MAKE_DAILY_SUBFOLDERS else ""
    folder = ensure_dir(os.path.join(OUT_DIR, sub) if sub else OUT_DIR)

    # fetch snapshot
    r = requests.get(SNAP_URL, timeout=TIMEOUT_SEC)
    r.raise_for_status()
    img = cv2.imdecode(np.frombuffer(r.content, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise RuntimeError("Snapshot did not decode as an image")

    img = rotate_if_needed(img)

    # unique filename (millisecond precision)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    path = os.path.join(folder, f"snap_{ts}.jpg")

    # write (fixed: encode as JPG, then write bytes)
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
    if not ok:
        raise RuntimeError("JPEG encode failed")
    with open(path, "wb") as f:
        f.write(buf.tobytes())

    print("Saved", path)
    return path

def main():
    print(f"Saving every {INTERVAL_SEC}s to '{OUT_DIR}' (Ctrl+C to stop)")
    while True:
        try:
            save_snapshot_once()
        except KeyboardInterrupt:
            print("\nStopped by user.")
            break
        except Exception as e:
            print("Capture error:", e)
        time.sleep(INTERVAL_SEC)

if __name__ == "__main__":
    main()
