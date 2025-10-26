import os, time, traceback
import requests, numpy as np, cv2
from datetime import datetime

# ===== EDIT THESE TO MATCH THE ONE-SHOT TEST =====
BASE = "http://atharva-2.local:8081/video"   # same as one-shot
PATH = "/snapshot.jpg"               # whichever worked
USER = "your_user"                   # "" if auth off
PASS = "your_pass"
INTERVAL_SEC = 5
OUT_DIR = "snaps"
ROTATE = None                        # "cw90" | "ccw90" | "180" | None
JPEG_QUALITY = 90
TIMEOUT_SEC = 8
# ================================================

URL = BASE + PATH
AUTH = (USER, PASS) if USER else None
os.makedirs(OUT_DIR, exist_ok=True)
session = requests.Session()

def rotate(img):
    if ROTATE == "cw90":   return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    if ROTATE == "ccw90":  return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    if ROTATE == "180":    return cv2.rotate(img, cv2.ROTATE_180)
    return img

def save_once():
    # fetch
    r = session.get(URL, timeout=TIMEOUT_SEC, auth=AUTH)
    r.raise_for_status()
    if not r.headers.get("content-type","").lower().startswith("image"):
        raise RuntimeError(f"Not an image: {r.headers.get('content-type')} status={r.status_code}")
    img = cv2.imdecode(np.frombuffer(r.content, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise RuntimeError("decode failed")

    img = rotate(img)

    # timestamped filename + latest
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    path = os.path.join(OUT_DIR, f"snap_{ts}.jpg")
    latest = os.path.join(OUT_DIR, "latest.jpg")

    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
    if not ok:
        raise RuntimeError("jpeg encode failed")

    with open(path, "wb") as f: f.write(buf.tobytes())
    with open(latest, "wb") as f: f.write(buf.tobytes())

    print("Saved:", path, flush=True)
    return path

if __name__ == "__main__":
    print(f"CWD: {os.getcwd()}")
    print(f"Saving every {INTERVAL_SEC}s to '{OUT_DIR}'. URL={URL} (Ctrl+C to stop)")
    while True:
        try:
            save_once()
        except KeyboardInterrupt:
            print("\nStopped by user."); break
        except Exception as e:
            print("Capture error:", e)
            traceback.print_exc(limit=1)
        time.sleep(INTERVAL_SEC)
