import sys, subprocess, numpy as np
x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "quiet", "-i", sys.argv[1], "-vn", "-ac", "1", "-ar", "48000", "-f", "f32le", "-"], capture_output=True).stdout, np.float32)
hop = 96; e = np.sqrt(np.add.reduceat(x[:len(x)//hop*hop] ** 2, np.arange(0, len(x)//hop*hop, hop)) / hop) + 1e-9; db = 20 * np.log10(e)
ref = np.convolve(db, np.ones(25) / 25, mode="same"); idx = np.where((db < ref - 14) & (ref > -35))[0]; g = []
for i in idx:
    if not g or i - g[-1][-1] > 3: g.append([i])
    else: g[-1].append(i)
short = [round(k[0] * hop / 48000, 2) for k in g if len(k) <= 5]
print(sys.argv[1].split('/')[-1], "micro-dropouts:", len(short), short[:20])
