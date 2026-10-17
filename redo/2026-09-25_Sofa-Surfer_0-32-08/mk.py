# Sofa Surfer $3,465 (5,775x), Sep 25 stream: Bonus Buy 2 (240 at 0.60), 12 FS, multiplier x3 -> x18, spin 8 pays KNOCKOUT 2,937.60.
# House style of the approved Slayers $7,417 v8 (mk_s1v7.py): no fast-forwards, dead spins glitch-cut, every hit spin from the reels
# dropping to its win, tilt push-ins on the board amounts (collect value, "N x multi" header), banner swings alternating sides,
# real-speed voice overlay (stems2 + words), one freeze+popup on the KNOCKOUT 2,937.60 (not the total), ends on the total +
# the closing "I mean not bad, Podge" facecam.
import json, copy, sys
D = sys.argv[1]; SP = sys.argv[2]; B = json.load(open(f"{SP}/oct11/base_edl.json"))
def face(a, b, z0=1.0, z1=1.1, out="glitch", **kw):
    return {"kind": "face", "a": a, "b": b, "speeds": [[a, 1.0]], "cam": [[a, "FACE", z0, 0], [b, "FACE", z1, 0]], "out": out, **kw}
def G(a, b, speeds, cam=None, out="cut", **kw):
    return {"kind": "game", "a": a, "b": b, "speeds": [list(x) for x in speeds], "cam": cam or [[a, "BOARD"], [b, "BOARD"]], "out": out, **kw}
GX, GY, GW, GH = 38, 230, 1288, 695
BAR = 850                                   # top of the game's BALANCE / WIN / BET row on this layout
def clamp(cx, cy, z):
    hw, hh = 960 / z, 540 / z
    return [round(min(max(cx, GX + hw + 2), GX + GW - hw - 2)), round(min(max(cy, GY + hh + 2), BAR - hh))]
def key(t, cx, cy, z, yaw=0, pitch=3):
    x, y = clamp(cx, cy, z); return [t, x, y, z, 0, yaw, pitch]
def W(text, src, color, size, x=0.19): return {"text": text, "src": src, "color": color, "x": x, "size": size}
WH, PK, YE, CY = [255, 255, 255], [255, 40, 90], [255, 214, 40], [40, 230, 255]
BLUR_KO = [{"rect": [370, 630, 660, 190], "t": [82.5, 999], "sigma": 40, "darken": 0.25},      # KNOCKOUT 2,937.60
           {"rect": [440, 236, 490, 52], "t": [82.5, 999], "sigma": 30, "darken": 0.2},       # "163.20 x 18" header
           {"rect": [96, 540, 200, 240], "t": [82.5, 999], "sigma": 30, "darken": 0.2}]       # left multiplier history meter
shots = [
  # cold open: the KNOCKOUT WIN landing, amount blurred, whip into the story
  G(83.05, 83.85, [[83.05, 1.0]], [key(83.05, 700, 548, 1.8, -10, 4), key(83.85, 700, 548, 1.95, -6, 2)], "whip",
    hits=[[83.1, 0.8, True]], blur=BLUR_KO, voice=False),
  # hook: "Podgy, the first one was really bad. We're doing one more."
  face(10.45, 12.7, mask_words=[W("REALLY", 11.19, WH, 170, 0.21), W("BAD.", 11.39, PK, 260, 0.21), W("ONE", 12.01, YE, 280, 0.21), W("MORE.", 12.25, CY, 190, 0.21)]),
  # Bonus Buy 2 card, push onto the 240.00
  G(10.3, 11.45, [[10.3, 1.3]], [key(10.3, 682, 540, 1.76, 6, 3), key(10.95, 690, 540, 1.82, 8, 3), key(11.45, 690, 541, 1.95, 10, 4)],
    "glitch", hits=[[11.0, 0.5]], voice=False),
  # the trigger: tilt across the scatters as they land, ride the reel-6 tease, the fifth scatter at 0.6x ("five scat?" .. "bang?")
  G(12.45, 17.7, [[12.45, 1.0], [12.95, 0.6], [13.7, 1.0], [14.1, 1.7], [16.2, 0.6], [16.8, 1.0]],
    [[12.45, "BOARD"], [12.85, "BOARD"], key(13.05, 470, 430, 2.0, 10, 4), key(13.5, 760, 700, 2.0, -6, 3),
     key(14.1, 930, 560, 1.85, -10, 4), key(16.2, 900, 520, 1.9, -10, 4), key(16.6, 945, 500, 2.1, -12, 5),
     [17.25, "BOARD"], [17.7, "BOARD"]], "glitch", hits=[[13.05, 0.5], [13.5, 0.5], [16.55, 0.7]]),
  # 12 FREE GAMES card
  G(19.45, 20.35, [[19.45, 1.0]], [key(19.45, 682, 560, 1.76, 8, 3), key(20.35, 682, 556, 1.88, 6, 2)], "glitch", hits=[[19.5, 0.6]]),
  # spin 2/12: 15x coin -> collect 9.00 -> x10 sofa lands, multi x3 -> x13 -> x16 -> "9.00 x 16" -> MEGA 144.00
  G(35.3, 47.4, [[35.3, 1.0], [35.6, 0.6], [36.0, 1.0], [37.3, 2.0], [38.55, 0.6], [39.0, 1.0], [40.3, 1.6], [41.55, 0.6], [41.95, 1.0],
                 [43.6, 1.8], [46.0, 1.0]],
    [[35.3, "BOARD"], [35.55, "BOARD"], key(35.8, 521, 570, 2.0, 12, 5), key(36.3, 600, 570, 2.05, 10, 4),
     key(36.6, 676, 565, 2.2, 8, 4), key(37.25, 676, 560, 2.35, 6, 3), [37.6, "BOARD"], [38.5, "BOARD"],
     key(38.8, 560, 420, 2.0, 6, 5), key(39.7, 300, 380, 2.0, 12, 4), key(41.0, 300, 380, 2.1, 10, 3), key(42.1, 300, 380, 2.2, 8, 3),
     key(42.7, 682, 380, 2.0, -6, 5), [43.4, "BOARD"], [46.35, "BOARD"], key(46.6, 682, 560, 1.95, -12, 4), key(47.4, 682, 554, 2.1, -10, 3)],
    "glitch", hits=[[35.8, 0.45], [36.5, 0.5], [38.8, 0.45], [39.75, 0.55], [41.75, 0.6], [46.5, 0.9]]),
  # spin 6/12: 25x / 5x / 1x coins -> collect 18.60
  G(60.45, 62.8, [[60.45, 1.0], [61.15, 0.6], [61.6, 1.0]],
    [[60.45, "BOARD"], [61.0, "BOARD"], key(61.3, 830, 545, 2.0, -12, 5), key(61.85, 700, 568, 2.15, -9, 4), key(62.8, 695, 565, 2.3, -7, 3)],
    "glitch", hits=[[61.3, 0.45], [61.8, 0.55]]),
  # ... multi x16 -> x18, "18.60 x 18" -> KNOCKOUT 334.80 -> "We still have half the spins left"
  G(65.95, 71.7, [[65.95, 1.0], [66.05, 0.6], [66.5, 1.0], [68.0, 1.8], [69.15, 1.0]],
    [key(65.95, 300, 380, 2.0, 12, 4), key(66.7, 300, 380, 2.15, 10, 3), key(67.2, 682, 380, 2.0, -4, 5), [67.85, "BOARD"],
     [69.1, "BOARD"], key(69.35, 682, 560, 1.95, 12, 4), key(70.3, 682, 554, 2.1, 10, 3), key(70.6, 682, 380, 2.0, -6, 5),
     key(71.7, 682, 380, 2.1, -4, 3)], "glitch", hits=[[66.25, 0.5], [67.25, 0.5], [69.3, 0.9]]),
  # spin 8/12, the big one: 20x, 250x, 2x coins drop -> collect 163.20 ("oh")
  G(74.4, 77.55, [[74.4, 1.0], [74.55, 1.5], [75.6, 0.6], [76.25, 1.0]],
    [[74.4, "BOARD"], [75.4, "BOARD"], key(75.75, 425, 663, 2.0, 12, 5), key(76.05, 626, 700, 2.1, 6, 4), key(76.4, 900, 600, 2.1, -8, 4),
     key(76.85, 684, 568, 2.2, -12, 5), key(77.55, 684, 562, 2.45, -9, 3)],
    "glitch", hits=[[75.75, 0.5], [76.05, 0.8, True], [76.4, 0.45], [76.8, 0.8]]),
  # his reaction: both arms up, "wait, does that do it?"
  face(77.55, 79.45),
  # "163.20 x 18" -> count-up -> MEGA -> KNOCKOUT 2,937.60 (freeze + popup) -> "= 2,937.60" -> "not fucking bad, paji"
  G(79.9, 89.15, [[79.9, 1.0], [81.2, 1.8], [82.45, 0.6], [83.1, 1.0], [85.55, 1.6], [86.85, 1.0]],
    [key(79.9, 682, 380, 2.0, 6, 5), key(80.6, 682, 380, 2.2, 4, 3), [81.0, "BOARD"], [82.4, "BOARD"],
     key(82.6, 690, 560, 1.95, -14, 5), key(83.2, 690, 557, 2.03, -12, 4), key(85.4, 690, 554, 2.12, -11, 3),
     key(85.9, 682, 380, 2.0, 6, 5), key(86.8, 682, 380, 2.15, 4, 3), key(89.15, 682, 520, 1.75, 2, 2)],
    "glitch", hits=[[80.25, 0.5], [82.5, 0.8], [83.0, 1.2, True]], tension=True),
  # "FUCKING 250X COIN. That's all we needed, paji."
  face(90.45, 94.1, mask_words=[W("FUCKING", 90.55, WH, 130, 0.21), W("250X", 91.1, PK, 250, 0.21), W("COIN", 91.98, YE, 230, 0.21)]),
  # the total: CONGRATULATIONS 3,465.00
  G(102.2, 104.55, [[102.2, 1.0]], [[102.2, "BOARD"], [102.5, "BOARD"], key(102.72, 690, 560, 1.92, 12, 4), key(104.55, 690, 554, 2.08, 9, 3)],
    "glitch", hits=[[102.7, 1.2, True]], voice=False),
  # closing: "I mean not bad, Podge"
  face(102.05, 104.0, out="end", mask_words=[W("NOT", 102.46, WH, 290, 0.8), W("BAD", 102.64, YE, 290, 0.8), W("PODGE", 103.5, CY, 180, 0.8)]),
]
E = {k: copy.deepcopy(B[k]) for k in ("game_rect", "face_rect", "formats", "sfx_dir", "sfx_map", "fx", "popups")}
E.update({"src": f"{D}/clip.mp4", "out": f"{D}/edit.mp4", "work": f"{D}/work", "shots": shots, "age_tag": None, "freeze_ring": 0.9,
          "freezes": [{"src": 46.95, "dur": 0.7, "pop": None, "push": 0.04},        # MEGA 144.00
                      {"src": 69.6, "dur": 0.7, "pop": None, "push": 0.04},         # KNOCKOUT 334.80
                      {"src": 83.3, "dur": 1.5, "pop": "auto"}],                    # KNOCKOUT 2,937.60, the big one
          "stems2": {"voice": f"{D}/stems/voice.wav", "game": f"{D}/stems/game.wav", "voice_max_speed": 2.0, "duck_db": 8,
                     "overlay": True, "words": f"{D}/voice_words.json",
                     "mute": [[20.05, 21.3],      # "these are just extra spins"
                              [46.5, 48.3],       # "guys why do you keep making these accounts"
                              [69.85, 71.52],     # "I mean, it's not bad so far, paji" (keeps "not bad" for the ending)
                              [74.80, 76.04],     # "and and and uh"
                              [81.4, 85.25],      # first "not fucking bad" under the count-up / popup (said again at 86.9)
                              [103.80, 106.2]],   # "you brought us back to even" after the closing line
                     "max_delay": 0.8}})
json.dump(E, open(f"{D}/edl.json", "w"), indent=1); print("ok")
