import requests, cv2, numpy as np, sys, pathlib

BASE = "http://atharva-2.local:8081"  # change if your IP/port changed

# If you got a real snapshot URL from step 1, paste it here:
EXACT = ""  # e.g. "http://172.16.83.107:8081/snapshot.jpg"

# Common snapshot endpoints many apps expose:
CANDIDATES = [
    "/snapshot.jpg",
    "/shot.jpg",
    "/photo.jpg",
    "/capture",
]

# If the app has auth, set these and uncomment 'auth=creds' below:
USER, PASS = None, None
creds = (USER, PASS) if USER else None

def try_url(url):
    print("\n---- Trying:", url)
    try:
        r = requests.get(url, timeout=6, auth=creds)
    except Exception as e:
        print("Request error:", repr(e)); return False

    print("Status:", r.status_code)
    print("Content-Type:", r.headers.get("content-type"))
    print("Bytes:", len(r.content))

    # Save headers/body for debugging
    pathlib.Path("last_headers.txt").write_text(str(r.headers))
    pathlib.Path("last_bytes.bin").write_bytes(r.content[:512])

    if r.status_code == 401:
        print("401 Unauthorized → set USER/PASS in the script or disable auth in the app.")
        return False

    if r.status_code == 200 and r.headers.get("content-type","").lower().startswith("image"):
        img = cv2.imdecode(np.frombuffer(r.content, np.uint8), cv2.IMREAD_COLOR)
        if img is not None:
            cv2.imwrite("snap.jpg", img)
            print("✅ Saved snap.jpg")
            return True
        else:
            print("Decode failed (content said image but wasn’t decodable).")
            return False

    print("Not an image. The URL may be a viewer page, not a snapshot.")
    return False

# 1) Try EXACT first if provided
if EXACT:
    if try_url(EXACT):
       sys.exit(0)

# 2) Try common paths
for p in CANDIDATES:
    if try_url(BASE + p):
        sys.exit(0)

print("\n❌ No snapshot worked. Open last_headers.txt and tell me the Content-Type/status shown.")
