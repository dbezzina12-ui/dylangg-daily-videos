import cv2, numpy as np, subprocess, sys
# dense.py VIDEO OUT.jpg START END STEP  (game rect crop, 6 columns)
v, out, a, b, st = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
ims = []; t = a
while t <= b:
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-ss", f"{t:.2f}", "-i", v, "-frames:v", "1", "-vf", "scale=320:180", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True).stdout
    if len(raw) >= 320*180*3:
        im = np.frombuffer(raw, np.uint8).reshape(180, 320, 3).copy(); cv2.putText(im, f"{t:.1f}", (4, 22), 0, 0.7, (0, 255, 255), 2); ims.append(im)
    t += st
while len(ims) % 6: ims.append(np.zeros_like(ims[0]))
cv2.imwrite(out, np.vstack([np.hstack(ims[i:i+6]) for i in range(0, len(ims), 6)]), [cv2.IMWRITE_JPEG_QUALITY, 80])
