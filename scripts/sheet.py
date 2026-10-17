import cv2, numpy as np, subprocess, sys, json
# sheet.py VIDEO OUT.jpg t1 t2 ...   (or "auto": 16 evenly spaced frames)
video, out = sys.argv[1], sys.argv[2]
ts = sys.argv[3:]
if ts == ["auto"]:
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video], capture_output=True, text=True).stdout)
    ts = [round(0.3 + i * (d - 0.6) / 15, 2) for i in range(16)]
ims = []
for t in map(float, ts):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-ss", str(t), "-i", video, "-frames:v", "1", "-vf", "scale=480:270", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True).stdout
    if len(raw) < 480 * 270 * 3: continue
    im = np.frombuffer(raw, np.uint8).reshape(270, 480, 3).copy(); cv2.putText(im, f"{t}", (8, 30), 0, 0.9, (0, 255, 255), 2); ims.append(im)
while len(ims) % 4: ims.append(np.zeros_like(ims[0]))
cv2.imwrite(out, np.vstack([np.hstack(ims[i:i + 4]) for i in range(0, len(ims), 4)]))
