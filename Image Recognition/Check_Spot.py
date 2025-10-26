# check_spot.py
import os, json, yaml, requests, numpy as np, cv2
from datetime import datetime
from shapely.geometry import box as shp_box
from ultralytics import YOLO

CONFIG = "config.yaml"

with open(CONFIG, "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

URL  = cfg.get("camera", {}).get("snapshot_url")
FILE = cfg.get("camera", {}).get("snapshot_file")
OUT  = cfg.get("output", {}).get("dir", "spot_out")
ROT  = cfg.get("output", {}).get("rotate")
DRAW = bool(cfg.get("output", {}).get("draw_overlay", True))

spot = cfg.get("spot", {}).get("box")
if not spot:
    raise SystemExit("No spot.box in config.yaml. Run define_spot.py first.")

model = YOLO(cfg.get("model", {}).get("weights", "yolov8n.pt"))
conf  = float(cfg.get("model", {}).get("conf", 0.35))

os.makedirs(OUT, exist_ok=True)

def rotate(img):
    if ROT == "cw90":  return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    if ROT == "ccw90": return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    if ROT == "180":  return cv2.rotate(img, cv2.ROTATE_180)
    return img

def grab():
    if FILE and os.path.exists(FILE):
        img = cv2.imread(FILE)
    elif URL:
        r = requests.get(URL, timeout=8)
        img = cv2.imdecode(np.frombuffer(r.content, np.uint8), cv2.IMREAD_COLOR)
    else:
        raise SystemExit("Set camera.snapshot_file or camera.snapshot_url in config.yaml.")
    if img is None:
        raise SystemExit("Snapshot decode failed.")
    return rotate(img)

def evaluate(frame):
    # vehicle classes: car(2), motorcycle(3), bus(5), truck(7)
    res = model.predict(frame, conf=conf, classes=[2,3,5,7], verbose=False)[0]
    dets = []
    if res.boxes is not None:
        for x1,y1,x2,y2 in res.boxes.xyxy.cpu().numpy()[:, :4]:
            dets.append(shp_box(float(x1), float(y1), float(x2), float(y2)))

    sx, sy, sw, sh = spot["x"], spot["y"], spot["w"], spot["h"]
    sbox = shp_box(sx, sy, sx+sw, sy+sh)

    thr = float(cfg["spot"].get("overlap_threshold", 0.12))
    occupied = any(sbox.intersection(d).area / sbox.area > thr for d in dets)
    return occupied, dets, sbox

def draw_overlay(frame, occupied, dets, sbox):
    # draw detections
    for d in dets:
        x1,y1,x2,y2 = map(int, d.bounds)
        cv2.rectangle(frame, (x1,y1), (x2,y2), (200,200,0), 1)
    # draw spot
    sx, sy, sw, sh = spot["x"], spot["y"], spot["w"], spot["h"]
    color = (0,0,255) if occupied else (0,200,0)
    cv2.rectangle(frame, (sx,sy), (sx+sw, sy+sh), color, 2)
    cv2.putText(frame, "occupied" if occupied else "free", (sx, sy-6),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA)
    return frame

if __name__ == "__main__":
    img = grab()
    occ, dets, sbox = evaluate(img)
    status = "occupied" if occ else "free"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    if DRAW:
        vis = draw_overlay(img.copy(), occ, dets, sbox)
        cv2.imwrite(os.path.join(OUT, f"spot_{status}_{ts}.jpg"), vis)

    with open(os.path.join(OUT, f"spot_{ts}.json"), "w", encoding="utf-8") as f:
        json.dump({"timestamp": ts, "status": status}, f, indent=2)

    print(f"{ts} → {status.upper()}")
