# popcheck.py EDL.json -> for each popup freeze: the popup line's output window and any of his words the live voice plays in it
import json, sys, os, subprocess
E = json.load(open(sys.argv[1])); W = json.load(open(E["stems2"]["words"])); S = json.load(open(os.path.join(E["work"], "voice_sync.json")))
pk = json.load(open(os.path.join(E["popups"]["dir"], "pack.json")))
for f in E.get("freezes", []):
    p = f.get("pop")
    if not isinstance(p, dict): continue
    ln = next(l for l in pk["chars"][p["char"]]["lines"] if l["id"] == p["line"])
    L = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                              os.path.join(E["popups"]["dir"], ln["file"])], capture_output=True, text=True).stdout)
    fr = [s for s in S if abs(s[1] - f["src"]) < 0.02]
    outs = sorted(set(round(s[0], 3) for s in fr))
    # the freeze in output time: the frames whose picture sits on f["src"] (voice_sync only lists frames where his voice plays)
    sync_all = [s for s in S]
    runs = []                                            # the engine freezes the LAST showing of the moment (the cold open can reuse it)
    for o in outs:
        if runs and o - runs[-1][-1] < 0.05: runs[-1].append(o)
        else: runs.append([o])
    t0 = runs[-1][0] if runs else None
    print(f'freeze {f["src"]}: {p["char"]}/{p["line"]} len {L:.2f}s, first out frame on it {t0}')
    if t0 is None: continue
    a, b = t0 + 0.18, t0 + 0.18 + L
    play = [s for s in S if a - 0.1 <= s[0] <= b + 0.1]
    hit = sorted({w[2] + f"@{w[0]:.2f}" for s in play for w in W if w[0] - 0.05 <= s[2] <= w[1] + 0.05})
    vs = [s[2] for s in play]
    print(f'  popup out {a:.2f}-{b:.2f}; his voice plays there: {len(play)} frames, voice src {min(vs) if vs else "-"}-{max(vs) if vs else "-"}; words: {hit or "none"}')
