# define_spot.py
import os
import cv2
import yaml
import requests
import numpy as np

CONFIG = "config.yaml"

cfg = yaml.safe_load(open(CONFIG, "r", encoding="utf-8"))

# read sources from config
URL  = cfg.get("camera", {}).get("snapshot_url")
FILE = cfg.get("camera", {}).get("snapshot_file")
ROT  = cfg.get("output", {}).get("rotate")  # None | "cw90" | "ccw90" | "180"

# make sure spot key exists
cfg.setdefault("spot", {})

def rotate_if_needed(img):
    if ROT == "cw90":
        return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    if ROT == "ccw90":
        return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    if ROT == "180":
        return cv2.rotate(img, cv2.ROTATE_180)
    return img

def grab():
    # prefer local file if provided and exists
    if FILE:
        if os.path.exists(FILE):
            img = cv2.imread(FILE)
            if img is None:
                raise SystemExit(f"Could not read image file: {FILE}")
            return rotate_if_needed(img)
        else:
            raise SystemExit(f"snapshot_file not found: {FILE}")

    # otherwise use URL
    if URL:
        try:
            r = requests.get(URL, timeout=8)
            r.raise_for_status()
        except Exception as e:
            raise SystemExit(f"HTTP error for {URL}: {e}")
        img = cv2.imdecode(np.frombuffer(r.content, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise SystemExit("Downloaded content did not decode as an image.")
        return rotate_if_needed(img)

    raise SystemExit("Set camera.snapshot_file or camera.snapshot_url in config.yaml")

img = grab()
# Let the user draw the ROI (x,y,w,h). If cancelled, w/h will be 0.
x, y, w, h = cv2.selectROI(
    "Draw your parking spot (press ENTER to save, ESC to cancel)",
    img, showCrosshair=True, fromCenter=False
)
cv2.destroyAllWindows()

if w <= 0 or h <= 0:
    raise SystemExit("No ROI selected. Run again and draw a rectangle.")

cfg["spot"]["box"] = {"x": int(x), "y": int(y), "w": int(w), "h": int(h)}

with open(CONFIG, "w", encoding="utf-8") as f:
    yaml.safe_dump(cfg, f, sort_keys=False)

print("Saved spot box to config.yaml:", cfg["spot"]["box"])