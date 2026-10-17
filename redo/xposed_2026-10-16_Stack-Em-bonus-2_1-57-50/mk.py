# Xposed, 2026-10-16 stream: Stack'Em (Hacksaw) bonus 2, $848,100 (1,131x on $750), natural trigger (other-streamer overnight batch edit, 2026-10-17).
# Clip t = stream t - 1:54:52 (T0 6892). Story: "please just pay me two hundred and fifteen thousand dollars" -> the trigger (hat throw)
# -> a mystery box flips X then 5 and the multiplier climbs 66x -> 330x -> MEGA WIN 62,325 -> SUPER MEGA WIN 146,625 -> the big one:
# 75 x 442 = 33,150 then 750 x 442 = 331,500 on the board (freeze) -> he lunges at the cam -> EPIC WIN 364,837.50 -> fist pump
# -> last spin, TOTAL WIN $848,100 in the game bar + announcer VO "He just hit eight hundred forty-eight grand!" + gold slam
# -> "Ladies and gentlemen, THE MAN!" (laughing, waving).
# Layout: Roobet page, game window [28,96,1440,760]; Stack'Em is a narrow 5-wide tower in the middle (x ~525-955), multiplier
# box at (740, 201), the game's own bar (balance / TOTAL WIN) at y ~775-830 (bottom of the game window). BOARD = the tower framed
# from the hearts to the bottom row, above the bar: (740, 432) z 1.64. Webcam [1489,50,400,225] (inside the box, above its stripe).
import json, copy, sys
D = sys.argv[1]; SP = sys.argv[2]; B = json.load(open(f"{SP}/oct11/base_edl.json"))
PACK = f"{SP}/artifact-files/e859168a-e8f3-430f-9e98-7ba0494cd658"
W = json.load(open(f"{D}/voice_words.json"))
def face(a, b, z0=1.0, z1=1.1, out="glitch", **kw):
    return {"kind": "face", "a": a, "b": b, "speeds": [[a, 1.0]], "cam": [[a, "FACE", z0, 0], [b, "FACE", z1, 0]], "out": out, **kw}
def G(a, b, speeds, cam=None, out="cut", **kw):
    return {"kind": "game", "a": a, "b": b, "speeds": [list(x) for x in speeds], "cam": cam or [[a, "BOARD"], [b, "BOARD"]], "out": out, **kw}
GX, GY, GW, GH = 28, 96, 1440, 760
BAR = 768                                      # top of the game's balance / total-win bar
def clamp(cx, cy, z, bottom=BAR):
    hw, hh = 960 / z, 540 / z
    return [round(min(max(cx, GX + hw + 2), GX + GW - hw - 2)), round(min(max(cy, GY + hh + 2), bottom - hh))]
def key(t, cx, cy, z, yaw=0, pitch=0, bottom=BAR):
    x, y = clamp(cx, cy, z, bottom); return [t, x, y, z, 0, yaw, pitch]
def wt(word, near):                            # start of the transcribed word closest to `near`
    c = [w for w in W if word.lower() in w[2].lower() and abs(w[0] - near) < 1.5]
    return min(c, key=lambda w: abs(w[0] - near))[0] if c else near
def mute(a, b):                                # whole-word mute of every word that starts in [a, b)
    ws = [w for w in W if a <= w[0] < b]
    return [min(w[0] for w in ws), max(w[1] for w in ws)] if ws else None
TOWER = (740, 432, 1.64)
shots = [
  # cold open: EPIC WIN 364,837.50 over the tower, the amount blurred, angled swing, whip
  G(184.3, 185.1, [[184.3, 1.0]], [key(184.3, 740, 440, 1.8, -10, 4), key(185.1, 740, 440, 1.95, -6, 2)], "whip",
    hits=[[184.35, 0.8, True]], voice=False,
    blur=[{"rect": [190, 372, 1100, 180], "t": [183.6, 185.5], "sigma": 40, "darken": 0.25}]),
  # hook: "(please just) pay me fucking two hundred and fucking fifteen thousand dollars" (head right of centre -> words left)
  face(22.78, 26.42, mask_words=[{"text": "PAY ME", "src": wt("pay", 22.83), "color": [255, 255, 255], "x": 0.21, "size": 230},
                                 {"text": "TWO HUNDRED", "src": wt("two", 23.49), "color": [40, 230, 255], "x": 0.21, "size": 120},
                                 {"text": "FIFTEEN", "src": wt("fifteen", 24.79), "color": [255, 40, 90], "x": 0.21, "size": 190},
                                 {"text": "THOUSAND", "src": wt("thousand", 25.47), "color": [255, 214, 40], "x": 0.21, "size": 165}]),
  # the trigger spin: tumble, 4,950 pays (tilt-push onto it), the mascot throws his hat (bonus), iris out
  G(27.45, 30.4, [[27.45, 1.3], [28.1, 1.0]],
    [[27.45, "BOARD"], [28.1, "BOARD"], key(28.3, 700, 505, 1.95, 12, 6), key(28.85, 705, 500, 2.05, 9, 3),
     key(29.2, 880, 470, 1.8, -8, 4), key(30.4, 900, 470, 1.85, -6, 2)], "glitch", hits=[[28.27, 0.5], [29.25, 0.8]]),
  # mystery box: ? flies to the middle, flips X, then 5 -> the multiplier climbs 66x -> 330x (tilt up onto the counter)
  G(73.3, 78.55, [[73.3, 1.0], [73.4, 0.6], [73.7, 1.0], [74.7, 0.6], [75.0, 1.0]],
    [key(73.3, 670, 380, 1.9, -12, 5), key(73.6, 715, 480, 2.15, -10, 4), key(74.55, 735, 482, 2.3, -8, 3),
     key(74.85, 735, 482, 2.45, 10, 4), key(75.45, 738, 368, 2.0, 8, 6), key(77.0, 738, 343, 2.2, 4, 3), key(78.55, 738, 323, 2.4, 2, 2)],
    "glitch", hits=[[73.52, 0.6], [74.8, 0.9, True]]),
  # same spin keeps tumbling: 187.50 x 330 -> 61,875 (push onto it) -> MEGA WIN 62,325
  G(81.1, 86.95, [[81.1, 1.5], [82.35, 1.0], [83.45, 0.6], [83.85, 1.0], [84.25, 1.7], [85.6, 1.0]],
    [[81.1, "BOARD"], [82.25, "BOARD"], key(82.45, 720, 498, 2.0, 12, 6), key(83.5, 735, 520, 2.3, 9, 4), key(84.2, 735, 516, 2.35, 7, 3),
     [84.45, "BOARD"], [85.6, "BOARD"], key(85.8, 740, 440, 1.85, -12, 4), key(86.95, 740, 436, 2.0, -9, 3)],
    "glitch", hits=[[82.45, 0.5], [83.5, 0.7], [85.78, 1.0, True]]),
  # SUPER MEGA WIN 146,625: drop, 3,750, then 375 x 381 -> 142,875 (push onto it), banner swing
  G(119.4, 126.05, [[119.4, 1.0], [120.7, 1.6], [121.7, 1.0], [121.9, 1.5], [122.4, 1.0], [123.35, 0.6], [123.75, 1.0], [123.95, 1.7], [124.9, 1.0]],
    [[119.4, "BOARD"], [120.25, "BOARD"], key(120.45, 710, 444, 2.0, -10, 5), key(120.9, 715, 450, 2.1, -8, 3), [121.3, "BOARD"],
     [121.65, "BOARD"], key(121.85, 785, 511, 2.1, 12, 6), key(122.5, 800, 515, 2.2, 10, 4), key(123.4, 810, 520, 2.4, 8, 3),
     key(123.9, 810, 522, 2.45, 6, 2), [124.1, "BOARD"], [124.85, "BOARD"], key(125.05, 740, 420, 1.8, 12, 4), key(126.05, 740, 416, 1.95, 9, 3)],
    "glitch", hits=[[120.5, 0.5], [123.5, 0.7], [125.02, 1.0, True]]),
  # THE HIT: 75 x 442 = 33,150, then 750 x 442 = 331,500 on the board (slow-mo + freeze)
  G(175.7, 182.05, [[175.7, 1.0], [178.45, 0.6], [178.85, 1.0], [179.05, 1.5], [179.7, 1.0], [181.4, 0.6], [181.8, 1.0]],
    [[175.7, "BOARD"], [176.6, "BOARD"], key(176.75, 642, 360, 2.1, -12, 6), key(177.5, 665, 365, 2.15, -10, 4), key(178.5, 650, 360, 2.35, -8, 3),
     key(178.95, 655, 362, 2.4, -7, 3), [179.15, "BOARD"], key(179.75, 900, 491, 2.1, 12, 6), key(180.5, 840, 491, 2.15, 10, 4),
     key(181.5, 837, 491, 2.35, 8, 3), key(182.05, 837, 488, 2.45, 6, 2)],
    "flash", hits=[[176.77, 0.5], [178.5, 0.7], [179.77, 0.5], [181.5, 1.2, True]]),
  # he lunges into the cam ("YEAH!")
  face(182.05, 183.6, z0=1.0, z1=1.12),
  # the counter rolls into EPIC WIN 364,837.50
  G(183.9, 184.95, [[183.9, 1.0]], [[183.9, "BOARD"], [184.15, "BOARD"], key(184.3, 740, 440, 1.8, 12, 4), key(184.95, 740, 436, 1.9, 10, 3)],
    "glitch", hits=[[184.27, 1.1, True]]),
  # fist pump, "Let's go!"
  face(184.95, 186.55, z0=1.0, z1=1.1),
  # last spin -> TOTAL WIN $848,100.00 in the game bar (tilt down onto it, slow-mo) + VO + gold slam
  G(208.8, 212.35, [[208.8, 1.0], [210.35, 0.6], [211.25, 1.0]],
    [[208.8, "BOARD"], [210.2, "BOARD"], key(210.4, 900, 584, 1.9, -10, 5, bottom=853), key(211.25, 930, 584, 2.0, -7, 3, bottom=853),
     key(212.35, 930, 584, 2.05, -5, 2, bottom=853)],
    "glitch", hits=[[210.42, 1.2, True]]),
  # closing: laughing, waving: "THE MAN!" (he leans out of the top of the webcam during "ladies and gentlemen", so that part is cut)
  face(215.75, 217.45, out="end"),
]
MUTES = [m for m in [
    mute(26.3, 26.9),        # "connecting" (tail of the hook line)
    mute(27.3, 28.3),        # "yeah, keep going here, right?" (filler)
    mute(29.9, 33.2),        # "cut, pay me 200 grand right now" (repeat of the hook)
    mute(74.0, 75.0),        # "mm-hmm"
    mute(78.2, 81.6),        # "oh my god, Scott, oh my god, I mean you can't do it again, yep" (oh my god is kept once, on the 331,500)
    mute(81.5, 83.05),       # "yep, skulls are in full hearts"
    mute(85.3, 88.2),        # "oh my god, brother" (repeat)
    mute(117.0, 119.6),      # "do we have full hearts here?"
    mute(120.0, 121.6),      # "oh, oh my god, no!" (repeat)
    mute(176.7, 177.7),      # "oh my god" (repeat; his "OH MY GOD!" on the 331,500 stays)
    mute(184.5, 185.1),      # extra "yeah yeah" (two kept)
    mute(187.3, 190.0),      # extra "let's go"
    mute(210.3, 213.1),      # "what a hit, what a fucking hit" (under the VO; "oh, what a hit" stays)
    mute(213.5, 214.4),      # "let's go"
] if m]
VO_T = 210.45
E = {k: copy.deepcopy(B[k]) for k in ("formats", "sfx_dir", "sfx_map", "fx", "popups")}
E.update({"game_rect": [GX, GY, GW, GH], "face_rect": [1489, 50, 400, 225], "board": list(TOWER),
          "src": f"{D}/clip.mp4", "out": f"{D}/edit.mp4", "work": f"{D}/work", "shots": shots, "age_tag": None, "freeze_ring": 0.9,
          "freezes": [{"src": 181.62, "dur": 1.5, "pop": None}],
          "extra_sfx": [{"file": f"{D}/vo.wav", "src": VO_T, "gain": 1.0}],
          "overlays": [{"src": VO_T, "from": 0, "to": 848100, "fmt": "${:,}", "count": 0.45, "pos": [960, 300], "size": 170,
                        "font": f"{PACK}/tools/Poppins-BoldItalic.ttf", "color": [255, 214, 40], "stroke": [80, 50, 0],
                        "until_src": 212.35}],
          "stems2": {"voice": f"{D}/stems/voice.wav", "game": f"{D}/stems/game.wav", "voice_max_speed": 2.0, "duck_db": 8,
                     "overlay": True, "words": f"{D}/voice_words.json", "mute": MUTES, "max_delay": 0.8}})
json.dump(E, open(f"{D}/edl.json", "w"), indent=1); print("ok", len(shots), "shots; mutes", MUTES)
