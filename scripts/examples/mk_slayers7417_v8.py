# Slayers Inc bonus 1 ($7,417), Oct 11 stream, v5: no fast-forwards; full big spins with VS landing pans and left-to-right activation pans (Dylan, 2026-10-16): real gameplay at 1.3-2x with his voice, fast-forward only the two dead stretches,
# angled swing push-ins + slow-mo on the hits (the Oct 12 look), word-by-word glitch captions behind him, no 18+ badge,
# stems2 audio (separate voice/game, rubberband) so speed-ups keep his voice without flanging
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
  G(123.6, 124.4, [[123.6, 1.0]], [[123.6, 682, 560, 1.8, 0, -10, 4], [124.4, 682, 560, 1.95, 0, -6, 2]], "whip",
    hits=[[123.65, 0.8, True]], blur=[{"rect": [380, 520, 620, 160], "t": [123.0, 999], "sigma": 40, "darken": 0.25}]),
  face(13.5, 15.25, mask_words=[{"text": "WE'RE", "src": 13.78, "color": [255, 255, 255], "x": 0.17, "size": 160},
                                {"text": "FUCKING", "src": 14.16, "color": [255, 40, 90], "x": 0.17, "size": 115},
                                {"text": "COOKED", "src": 14.44, "color": [255, 214, 40], "x": 0.17, "size": 120}]),
  G(24.4, 30.1, [[24.4, 1.0], [25.3, 1.8], [27.9, 0.6], [29.4, 1.0]],
    [[24.4, "BOARD"], [24.9, "BOARD"], [25.4, 580, 560, 1.8, 0, 10, 4], [27.6, 600, 575, 1.9, 0, 8, 3],
     [28.6, 790, 590, 2.0, 0, -6, 3], [29.6, 800, 605, 2.1, 0, -4, 2], [30.1, "BOARD"]], "glitch", hits=[[25.5, 0.5], [28.8, 0.6]]),
  big_spin(51.9, [(52.35, 1, 4), (52.95, 3, 1), (53.15, 4, 4)], [(53.7, 1), (58.4, 3), (63.4, 4)], 69.2, 73.2, 74.2),        # SUPER MEGA $1,920
  big_spin(88.5, [(89.15, 2, 1), (89.35, 3, 3), (89.55, 4, 4), (89.95, 5, 3)], [(90.85, 2), (95.9, 3), (100.9, 4), (105.9, 5)],
           110.4, 116.3, 118.0, out="flash", tension=True),                                                              # EPIC $4,930
  G(122.6, 127.4, [[122.6, 1.0]], [[122.6, "BOARD"], [123.0, "BOARD"], [123.3, 682, 560, 1.9, 0, -12, 4], [127.4, 682, 554, 2.08, 0, -9, 3]],
    "end", hits=[[123.2, 1.2, True]]),                      # ends on the total: no closing facecam unless it's "NOT BAD" or a real reaction                                                                               # TOTAL $7,417
]
E = {k: copy.deepcopy(B[k]) for k in ("game_rect", "face_rect", "formats", "sfx_dir", "sfx_map", "fx", "popups")}
E.update({"src": f"{D}/clip.mp4", "out": f"{D}/hype_edit_slayers7417_v8.mp4", "work": f"{D}/work_s1v7", "shots": shots, "age_tag": None, "freeze_ring": 0.9,
          "freezes": [{"src": 116.7, "dur": 1.5, "pop": "auto"}],
          "stems2": {"voice": f"{D}/stems/s2_voice.wav", "game": f"{D}/stems/s2_game.wav", "voice_max_speed": 2.0, "duck_db": 8,
                     "overlay": True, "words": f"{D}/voice_words.json",
                     "mute": [[116.5, 124.8], [129.3, 132.2], [67.70, 69.12], [71.60, 74.34], [57.76, 64.74], [94.44, 96.74], [99.46, 103.20], [114.72, 115.98], [124.8, 127.4]], "max_delay": 0.8}})
json.dump(E, open(f"{D}/edl_s1v7.json", "w"), indent=1); print("ok")
