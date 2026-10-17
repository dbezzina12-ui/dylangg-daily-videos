# Outsourced 2: Balkan Engineering $3,016.85 (3,016x at $1, $235 Tiltier Spins buy), Sep 16 stream: overnight batch edit in the
# approved Slayers v8 / $4,049 style. Story: blurred GUD ENUFF 2,954.60 cold open -> the buy spin's 4 bonus symbols -> TILTIER SPINS 7
# -> "alright, please be good" (facecam, word captions) -> +1 spin -> spin with x4 nudge: 9.60, "this board is incredible" 22.40,
# 13.50 -> 59.50 -> the LAST spin: 10.20, 14.00, 12.00, the x2 nudge lands, 2,808.00 xWays hit (freeze + popup) + 78.00 -> win screen
# count-up to GUD ENUFF 2,954.60 -> "NOT FUCKING BAD" (facecam) -> red TOTAL WIN 3,016.85 (end; cut before the extra-spin buys).
# No fast-forwards; dead spins cut with glitch cuts; his voice never stretched (stems2 overlay + curated whole-word mutes).
import json, copy, os
D = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(os.path.dirname(D))
B = json.load(open(f"{SP}/oct11/base_edl.json"))
def face(a, b, z0=1.0, z1=1.1, out="glitch", **kw):
    return {"kind": "face", "a": a, "b": b, "speeds": [[a, 1.0]], "cam": [[a, "FACE", z0, 0], [b, "FACE", z1, 0]], "out": out, **kw}
def G(a, b, speeds, cam=None, out="cut", **kw):
    return {"kind": "game", "a": a, "b": b, "speeds": [list(x) for x in speeds], "cam": cam or [[a, "BOARD"], [b, "BOARD"]], "out": out, **kw}
GX, GY, GW, GH = 38, 230, 1288, 695; BAR = 895   # the game's own TOTAL WIN / BALANCE line sits at y ~900-920
def clamp(cx, cy, z, bar=BAR):
    hw, hh = 960 / z, 540 / z
    return [round(min(max(cx, GX + hw + 2), GX + GW - hw - 2)), round(min(max(cy, GY + hh + 2), bar - hh))]
def K(t, cx, cy, z, yaw=0, pitch=3, bar=BAR):
    x, y = clamp(cx, cy, z, bar); return [t, x, y, z, 0, yaw, pitch]
W = [255, 255, 255]; P = [255, 40, 90]; Y = [255, 214, 40]; C = [40, 230, 255]
# pay popups on the board (source px, from gridded full-res frames)
P960, P2240, P1350 = (706, 405), (694, 481), (653, 508)          # 59.50 spin
P1020, P1400, P1200 = (693, 479), (709, 490), (706, 765)         # last spin cascades
NUDGE, P2808, P78 = (603, 740), (685, 405), (683, 735)           # x2 nudge, the big xWays hit, its partner

shots = [
  # 1 cold open: GUD ENUFF 2,954.60 rises in (amount blurred, the TOTAL WIN line kept out of frame), whip into the story
  G(84.35, 85.15, [[84.35, 1.0]], [[84.35, 685, 560, 1.8, 0, -10, 4], [85.15, 685, 560, 1.95, 0, -6, 2]], "whip",
    hits=[[84.4, 0.8, True]], blur=[{"rect": [340, 480, 700, 330], "t": [84.0, 999], "sigma": 40, "darken": 0.25}]),
  # 2 the $235 buy spin: 4 bonus symbols light up, pan + tilt across them
  G(19.5, 21.4, [[19.5, 1.0], [20.4, 0.65], [21.0, 1.0]],
    [[19.5, "BOARD"], [20.3, "BOARD"], K(20.5, 470, 400, 1.9, 10, 5), K(20.85, 600, 600, 1.92, 4, 4), K(21.4, 760, 600, 2.05, -10, 4)],
    "glitch", hits=[[20.5, 0.5]]),
  # 3 TILTIER SPINS 7 card ("it's a super")
  G(21.4, 23.05, [[21.4, 1.0]], [[21.4, "BOARD"], [21.6, "BOARD"], [23.05, 660, 560, 1.7, 0, 0, 2]], "glitch", hits=[[21.55, 0.6]]),
  # 4 hook: "alright, please be good" (arm up on the left of the frame -> captions right)
  face(24.95, 26.4, mask_words=[{"text": "PLEASE", "src": 25.41, "color": W, "x": 0.8, "size": 190},
                                {"text": "BE", "src": 25.57, "color": P, "x": 0.8, "size": 300},
                                {"text": "GOOD", "src": 25.71, "color": Y, "x": 0.8, "size": 250}]),
  # 5 +1 spin lands (the game zooms in on it itself): "plus one spin. Nice"
  G(37.0, 40.75, [[37.0, 1.3], [37.9, 1.0]], [[37.0, "BOARD"], [39.9, "BOARD"], [40.75, 660, 560, 1.7, 0, 4, 2]], "glitch",
    hits=[[38.5, 0.6]]),
  # 6 the 59.50 spin: drop, x4 nudge wild, 9.60, cascades, 22.40 ("this board is incredible"), 13.50, win screen 59.50 (read hold)
  G(42.35, 61.5, [[42.35, 1.6], [44.7, 1.0], [45.5, 2.4], [53.2, 1.0], [53.95, 2.0], [56.3, 1.0], [56.8, 2.2], [59.4, 1.0], [59.9, 1.8], [60.8, 1.0]],
    [[42.35, "BOARD"], [44.75, "BOARD"], K(45.0, *P960, 2.2, 0, 3), K(45.45, *P960, 2.25, 0, 3), [45.75, "BOARD"],
     [53.15, "BOARD"], K(53.45, *P2240, 2.0, -12, 6), K(53.95, P2240[0], P2240[1] - 6, 2.3, -8, 3), [54.3, "BOARD"],
     [56.25, "BOARD"], K(56.45, *P1350, 2.2, 0, 3), K(56.8, *P1350, 2.25, 0, 3), [57.1, "BOARD"],
     [59.4, "BOARD"], [60.75, "BOARD"], K(61.0, 680, 640, 2.15, 10, 4), K(61.5, 680, 638, 2.22, 8, 3)],
    "glitch", hits=[[43.0, 0.45], [45.0, 0.5], [53.5, 0.6], [56.5, 0.5], [61.0, 0.8]]),
  # 7 THE LAST SPIN: drop, 10.20, 14.00, 12.00, the x2 nudge lands (slow-mo), tilt-push onto 2,808.00 (freeze + popup), 78.00,
  #   the cascades run out at 2.2x (TOTAL WIN 114.05 -> 3,000.05 -> 3,016.85)
  G(63.35, 79.85, [[63.35, 1.3], [65.3, 1.0], [65.8, 2.2], [67.9, 1.0], [68.3, 2.2], [71.1, 1.0], [71.5, 2.2], [73.1, 0.6], [73.6, 1.0],
                   [74.3, 0.6], [74.6, 1.0], [75.1, 2.2]],
    [[63.35, "BOARD"], [65.15, "BOARD"], K(65.4, *P1020, 2.2, 0, 3), K(65.8, *P1020, 2.25, 0, 3), [66.1, "BOARD"],
     [67.85, "BOARD"], K(68.0, *P1400, 2.2, 0, 3), K(68.3, *P1400, 2.25, 0, 3), [68.6, "BOARD"],
     [71.05, "BOARD"], K(71.25, *P1200, 2.2, 0, 3), K(71.5, *P1200, 2.25, 0, 3), [71.8, "BOARD"],
     [73.05, "BOARD"], K(73.25, *NUDGE, 2.0, 12, 6), K(73.75, NUDGE[0], NUDGE[1] - 6, 2.2, 8, 3),
     K(74.32, *P2808, 2.0, -12, 6), K(74.62, P2808[0], P2808[1] - 4, 2.3, -8, 3),
     K(74.8, *P78, 2.15, 10, 4), K(75.1, *P78, 2.2, 8, 3), [75.45, "BOARD"], [79.85, "BOARD"]],
    "flash", tension=True,
    hits=[[64.5, 0.45], [65.5, 0.5], [68.0, 0.5], [71.25, 0.5], [73.3, 0.7], [74.45, 1.2, True], [74.8, 0.6]]),
  # 8 win screen count-up: SZOLID FONDATIONZ 1.60 -> ... -> OLMOST THER 319.56 -> GUD ENUFF 2,954.60 (swing push onto it)
  G(79.85, 86.0, [[79.85, 1.0], [80.3, 2.0], [83.5, 1.0], [83.8, 0.7], [84.5, 1.0]],
    [[79.85, "BOARD"], [84.15, "BOARD"], [84.4, 685, 590, 2.0, 0, 14, 5], [84.9, 685, 585, 2.06, 0, 12, 4], [86.0, 685, 580, 2.14, 0, 11, 3]],
    "glitch", hits=[[80.0, 0.6], [84.4, 1.1, True]]),
  # 9 his reaction: "NOT FUCKING BAD" (he sits centre, mic arm top right -> captions left)
  face(87.05, 88.27, mask_words=[{"text": "NOT", "src": 87.30, "color": W, "x": 0.2, "size": 300},
                                 {"text": "FUCKING", "src": 87.56, "color": P, "x": 0.2, "size": 150},
                                 {"text": "BAD", "src": 88.00, "color": Y, "x": 0.2, "size": 300}]),
  # 10 END: red TOTAL WIN counts up and locks on 3,016.85 (cut before the extra-spin buy menu at 89.8)
  G(88.27, 89.72, [[88.27, 1.0]], [[88.27, 682, 525, 1.85, 0, -12, 4], [89.72, 682, 518, 2.05, 0, -9, 3]], "end",
    hits=[[89.2, 1.2, True]]),
]
# whole-word mutes from the clean-voice voice_words.json (onsets fixed from the stem energy: see notes.txt)
MUTES = [[20.73, 21.05],     # "and"
         [21.99, 25.19],     # "and it's a super" (said twice), "I don't know if I have, I don't"
         [36.62, 37.18],     # "that"
         [46.12, 52.48],     # "we had we had nothing ... queen on two, queen on two"
         [55.42, 59.02],     # "no spins though, we need a door bad, we need a jack here"
         [59.54, 64.74],     # "we need, we need a door bad please, whoops, what's good baby, we need a door bad"
         [68.55, 72.90],     # "give me a door, hats, uh, top symbol too"
         [76.57, 79.25],     # "not bad, not fucking bad" (he says "not fucking bad" again on the facecam)
         [81.74, 87.25],     # second "fucking good", "not bad, not bad at all baby"
         [88.25, 99.10]]     # "how much is the rebuy ..." (the extra-spin buys are cut)
E = {k: copy.deepcopy(B[k]) for k in ("game_rect", "face_rect", "formats", "sfx_dir", "sfx_map", "fx", "popups")}
E.update({"src": f"{D}/clip.mp4", "out": f"{D}/edit.mp4", "work": f"{D}/work", "shots": shots, "age_tag": None, "freeze_ring": 0.9,
          "freezes": [{"src": 61.05, "dur": 0.7, "pop": None, "push": 0.04},                               # 59.50 read
                      {"src": 74.55, "dur": 1.5, "pop": {"char": "slot", "line": "no_way"}},              # the big hit: 2,808.00
                      {"src": 89.45, "dur": 0.6, "pop": None, "push": 0.04}],                             # TOTAL WIN 3,016.85 read
          "stems2": {"voice": f"{D}/stems/voice.wav", "game": f"{D}/stems/game.wav", "voice_max_speed": 2.0, "duck_db": 8,
                     "overlay": True, "words": f"{D}/voice_words.json", "max_delay": 0.8, "mute": MUTES}})
json.dump(E, open(f"{D}/edl.json", "w"), indent=1); print("ok", len(shots), "shots")
