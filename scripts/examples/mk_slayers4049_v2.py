# Slayers Inc bonus 2 ($4,049), Oct 11 stream, v2 in the approved $7,417 v8 style (Dylan, 2026-10-16): no fast-forwards, dead spins cut,
# each big spin from the reels dropping to the banner, close 2.2x zoom on each VS landing, zoom out to 1.72-1.78 as the multis open,
# real-speed voice overlay, ends on the total + the closing "NOT BAD" facecam
import json, copy, sys
D = sys.argv[1]; B = json.load(open(f"{D}/base_edl.json"))
def face(a, b, z0=1.0, z1=1.1, out="glitch", **kw):
    return {"kind": "face", "a": a, "b": b, "speeds": [[a, 1.0]], "cam": [[a, "FACE", z0, 0], [b, "FACE", z1, 0]], "out": out, **kw}
def G(a, b, speeds, cam=None, out="cut", **kw):
    return {"kind": "game", "a": a, "b": b, "speeds": [list(x) for x in speeds], "cam": cam or [[a, "BOARD"], [b, "BOARD"]], "out": out, **kw}
def FF(a, b, sp, caption=None, **kw):
    return G(a, b, [[a, sp]], ff={"label": f"x{int(sp)}", **({"caption": caption} if caption else {})}, **kw)
def swing(a, hit, b, side=-1, cx=682, cy=560, z0=1.95, z1=2.12):
    """angled push-in: holds the board, then swings in from the side onto the hit and settles (yaw 14 -> 11, tilt 5 -> 3)"""
    return [[a, "BOARD"], [hit - 0.1, "BOARD"], [hit + 0.12, cx, cy, z0, 0, 14 * side, 5],
            [hit + 0.6, cx, cy - 3, (z0 + z1) / 2, 0, 12 * side, 4], [b, cx, cy - 6, z1, 0, 11 * side, 3]]
GX, GY, GW, GH = 38, 230, 1288, 695
COLS = {1: 412, 2: 553, 3: 682, 4: 824, 5: 952}; ROWS = {1: 359, 2: 487, 3: 629, 4: 758}
def clamp(cx, cy, z):
    hw, hh = 960 / z, 540 / z
    return [round(min(max(cx, GX + hw + 2), GX + GW - hw - 2)), round(min(max(cy, GY + hh + 2), 862 - hh))]
def key(t, cx, cy, z, col=3, pitch=3):
    x, y = clamp(cx, cy, z); return [t, x, y, z, 0, round((3 - col) * 4.5, 1), pitch]   # yaw tilts toward the side it's on
def big_spin(start, lands, acts, count, banner, end, freeze=False, out="glitch", tension=False):
    """lands: [(t, col, row)] VS landings left->right; acts: [(t, col)] slayer activations; count: payout tally start;
    banner: win banner appears; end: shot end"""
    t_first, t_last = lands[0][0], lands[-1][0]
    speeds = [[start, 1.0], [t_first - 0.12, 0.55], [t_last + 0.2, 1.0]]
    cam = [[start, "BOARD"], [t_first - 0.2, "BOARD"]]
    for t, c, r in lands: cam.append(key(t + 0.02, COLS[c], ROWS[r], 2.2, c))       # zoom onto each VS as it lands
    cam.append(key(t_last + 0.45, COLS[lands[-1][1]], ROWS[lands[-1][2]], 2.2, lands[-1][1]))
    for i, (t, c) in enumerate(acts):                                               # follow the slayer left -> right, reel framed
        cam.append(key(t - 0.15, COLS[c], 560, 1.72, c)); speeds.append([t, 1.0])
        nxt = acts[i + 1][0] if i + 1 < len(acts) else count
        if nxt - t > 1.8: speeds.append([t + 0.9, 1.9])                             # slash at 1.0, then the reel fill / multi roll at 1.9x
        if nxt - t > 1.8: speeds.append([nxt - 0.45, 1.0])                          # back to 1.0 as the multiplier locks in
        cam.append(key(nxt - 0.35, COLS[c], 560, 1.78, c))
    cam += [[count - 0.05, "BOARD"], [banner - 0.15, "BOARD"], [banner + 0.1, 682, 560, 1.95, 0, 12, 4], [end, 682, 556, 2.05, 0, 10, 3]]
    speeds += [[count, 1.0], [count + 0.5, 1.8], [banner - 0.35, 1.0]]
    hits = [[t + 0.02, 0.45] for t, _, _ in lands] + [[t, 0.55] for t, _ in acts] + [[banner, 1.1 if tension else 0.9, tension]]
    return G(start, end, sorted(speeds), cam, out, hits=hits, tension=tension)
shots = [
  G(242.3, 243.1, [[242.3, 1.0]], [[242.3, 682, 560, 1.8, 0, -10, 4], [243.1, 682, 560, 1.95, 0, -6, 2]], "whip",
    hits=[[242.35, 0.8, True]], blur=[{"rect": [380, 520, 620, 160], "t": [241.5, 999], "sigma": 40, "darken": 0.25}]),       # cold open: blurred TOTAL
  G(163.4, 166.4, [[163.4, 1.0], [164.55, 0.5], [165.35, 1.0]],
    [[163.4, "BOARD"], [164.45, "BOARD"], key(164.75, 620, 505, 2.0, 2), key(165.15, 840, 640, 2.0, 4), key(165.9, 830, 640, 2.1, 4), [166.4, "BOARD"]],
    "glitch", hits=[[164.8, 0.5], [165.0, 0.6]]),                                                            # 4 FS land: pan + tilt across them
  face(172.0, 174.0, mask_words=[{"text": "PAY", "src": 172.40, "color": [255, 255, 255], "x": 0.19, "size": 295},
                                 {"text": "A", "src": 172.60, "color": [255, 40, 90], "x": 0.19, "size": 300},
                                 {"text": "MILLION", "src": 172.72, "color": [255, 214, 40], "x": 0.19, "size": 140}]),   # "please pay a million"
  big_spin(184.3, [(185.0, 1, 3), (185.2, 2, 4)], [(186.2, 1), (189.6, 2)], 194.3, 197.4, 198.4),            # SUPER MEGA $2,142
  big_spin(199.3, [(200.0, 2, 3), (200.2, 3, 3)], [(201.0, 2), (205.6, 3)], 210.7, 213.3, 214.3),                # MEGA $806
  big_spin(223.3, [(224.0, 2, 2), (224.2, 3, 3), (224.5, 4, 1)], [(225.0, 2), (229.7, 3), (234.9, 4)],
           236.9, 239.7, 240.7, out="flash", tension=True),                                                   # SUPER MEGA $1,100
  G(241.9, 245.0, [[241.9, 1.0]], [[241.9, "BOARD"], [242.15, "BOARD"], [242.4, 682, 560, 1.9, 0, -12, 4], [245.0, 682, 554, 2.06, 0, -9, 3]],
    "glitch", hits=[[242.35, 1.2, True]]),                                                                    # TOTAL $4,049
  face(248.6, 250.38, out="end", mask_words=[{"text": "NOT", "src": 249.10, "color": [255, 255, 255], "x": 0.19, "size": 275},
                                             {"text": "BAD", "src": 249.24, "color": [255, 214, 40], "x": 0.19, "size": 275},
                                             {"text": "JARED", "src": 249.78, "color": [40, 230, 255], "x": 0.19, "size": 180}]),   # "I mean not bad, Jared" (the NOT BAD ending)
]
E = {k: copy.deepcopy(B[k]) for k in ("game_rect", "face_rect", "formats", "sfx_dir", "sfx_map", "fx", "popups")}
E.update({"src": f"{D}/clip.mp4", "out": f"{D}/hype_edit_slayers4049_v2.mp4", "work": f"{D}/work_s2v2", "shots": shots, "age_tag": None, "freeze_ring": 0.9,
          "freezes": [{"src": 197.9, "dur": 1.5, "pop": "auto"}],
          "stems2": {"voice": f"{D}/stems/s2_voice.wav", "game": f"{D}/stems/s2_game.wav", "voice_max_speed": 2.0, "duck_db": 8,
                     "overlay": True, "words": f"{D}/voice_words.json",
                     "mute": [[194.0, 199.62], [207.58, 209.56], [211.58, 212.46], [234.60, 235.64], [238.18, 243.64]], "max_delay": 0.8}})   # every plain "not bad" except the closing one (keeps "not fucking bad" on the $806 banner)
json.dump(E, open(f"{D}/edl_s2v2.json", "w"), indent=1); print("ok")
