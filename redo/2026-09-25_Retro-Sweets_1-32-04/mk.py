# Retro Sweets $3,614.60 (3,615x at $1), Sep 25 stream: overnight batch edit in the approved Slayers v8 / $4,049 style.
# Story: blurred 3,528.00 cold open -> "I think we do one more, baby" (he rebuys the CA$400 Super Free Spins) -> the buy spin drops
# the tapes ("this could be good") -> 10 free spins awarded ("one magnet and it's GG's") -> +2 retriggers to 14 -> "please do not be
# dead spins" -> 13 dead spins later the LAST spin (14/14): 15.00 up top, then the left cluster counts up, x7 -> x6 -> x6 = 3,528.00
# (freeze + popup) -> his reaction facecam ("not fucking bad, hold the fucking phone") -> BIG -> SWEET WIN 3,543.00 -> WIN 3,614.60 (end).
# No fast-forwards; dead spins cut with glitch cuts; his voice never stretched (stems2 overlay + curated whole-word mutes).
import json, copy, sys, os
D = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(os.path.dirname(D))
B = json.load(open(f"{SP}/oct11/base_edl.json"))
def face(a, b, z0=1.0, z1=1.1, out="glitch", **kw):
    return {"kind": "face", "a": a, "b": b, "speeds": [[a, 1.0]], "cam": [[a, "FACE", z0, 0], [b, "FACE", z1, 0]], "out": out, **kw}
def G(a, b, speeds, cam=None, out="cut", **kw):
    return {"kind": "game", "a": a, "b": b, "speeds": [list(x) for x in speeds], "cam": cam or [[a, "BOARD"], [b, "BOARD"]], "out": out, **kw}
GX, GY, GW, GH = 38, 230, 1288, 695; BAR = 880   # in-game WIN / balance line sits at y ~890-915 (board bottom ~875)
def clamp(cx, cy, z, bar=BAR):
    hw, hh = 960 / z, 540 / z
    return [round(min(max(cx, GX + hw + 2), GX + GW - hw - 2)), round(min(max(cy, GY + hh + 2), bar - hh))]
def K(t, cx, cy, z, yaw=0, pitch=3, bar=BAR):
    x, y = clamp(cx, cy, z, bar); return [t, x, y, z, 0, yaw, pitch]
AMT = (575, 648)        # the left cluster's pay amount on the board (3,528.00)
TOP = (865, 345)        # the top-right cluster's pay amount (2.00 -> 15.00)
BAN = (650, 548)        # win-screen amount (BIG / SWEET WIN)
W = [255, 255, 255]; P = [255, 40, 90]; Y = [255, 214, 40]; C = [40, 230, 255]

shots = [
  # 1 cold open: 3,528.00 lands on the board (amount blurred, WIN meter kept out of frame), whip into the story
  G(135.3, 136.1, [[135.3, 1.0]], [K(135.3, 600, 570, 1.85, -10, 4), K(136.1, 600, 580, 1.98, -6, 2)], "whip",
    hits=[[135.35, 0.8, True]], blur=[{"rect": [440, 610, 280, 80], "t": [135.0, 999], "sigma": 40, "darken": 0.25}]),
  # 2 hook: "I think we do one more, baby" (rebuying the bonus after the last one paid 112)
  face(19.0, 20.75, mask_words=[{"text": "ONE", "src": 19.56, "color": W, "x": 0.17, "size": 300},
                                 {"text": "MORE", "src": 19.76, "color": P, "x": 0.17, "size": 250},
                                 {"text": "BABY", "src": 20.14, "color": Y, "x": 0.17, "size": 250}]),
  # 3 the buy spin: board clears, the tapes drop ("oh wow ... this could be good")
  G(20.75, 24.6, [[20.75, 1.0]],
    [[20.75, "BOARD"], [20.9, "BOARD"], K(21.1, 520, 640, 1.9, 9, 4), K(22.2, 560, 600, 1.95, 6, 3), K(23.3, 700, 560, 2.0, -6, 3),
     [24.6, "BOARD"]], "glitch", hits=[[20.9, 0.5], [23.4, 0.45]]),
  # 4 10 FREE SPINS awarded -> free spins start ("one good magnet and it's fucking GG's")
  G(62.6, 67.7, [[62.6, 1.0]],
    [K(62.6, 650, 560, 1.75, 10, 4), K(63.7, 650, 556, 1.92, 8, 3), [64.3, "BOARD"], [65.6, "BOARD"], K(67.7, 682, 580, 1.7, -4, 2)],
    "glitch", hits=[[62.7, 0.6]]),
  # 5 first +2 lands bottom right -> 12 spins ("good, extra spins too, hold on")
  G(69.5, 72.0, [[69.5, 1.0]], [[69.5, "BOARD"], [69.8, "BOARD"], K(70.1, 860, 760, 2.0, -12, 5), K(72.0, 855, 750, 2.1, -9, 3)],
    "glitch", hits=[[70.1, 0.55]]),
  # 6 second +2 lands top right -> 14 spins ("extra spins again")
  G(74.4, 76.4, [[74.4, 1.0]], [[74.4, "BOARD"], [74.7, "BOARD"], K(75.0, 860, 330, 2.0, 12, 5), K(76.4, 850, 330, 2.1, 9, 3)],
    "glitch", hits=[[75.0, 0.55]]),
  # 7 "please do not be dead spins" (spin 8 drops: dead)
  G(97.7, 99.9, [[97.7, 1.0]], [[97.7, "BOARD"], [98.8, "BOARD"], [99.9, 682, 555, 1.68, 0, 4, 2]], "glitch", hits=[[98.95, 0.4]]),
  # 8 THE LAST SPIN (14/14) (slow-mo only as two short beats, x7 and the final x6, rule 8): drop, 15.00 top right, left cluster counts 1.00 -> 14.00, x7 = 98.00, x6 = 588.00, x6 = 3,528.00
  G(121.9, 136.2, [[121.9, 1.0], [122.6, 1.6], [126.3, 1.25], [129.3, 1.5], [133.5, 0.7], [133.95, 1.0], [135.0, 0.6], [135.55, 1.0]],
    [[121.9, "BOARD"], [126.2, "BOARD"], K(126.5, TOP[0], TOP[1], 1.95, -12, 6), K(129.0, TOP[0], TOP[1], 2.1, -8, 3),
     [129.35, "BOARD"], K(129.7, 600, 640, 1.9, 10, 4), K(133.3, 590, 645, 2.0, 8, 3),
     K(133.65, AMT[0], AMT[1], 2.15, -12, 6), K(134.0, AMT[0], AMT[1] - 3, 2.2, -8, 4),
     K(134.35, AMT[0], AMT[1], 2.25, 12, 6), K(134.7, AMT[0], AMT[1] - 3, 2.3, 8, 4),
     K(135.15, AMT[0], AMT[1], 2.35, -12, 6), K(135.55, AMT[0], AMT[1] - 4, 2.45, -9, 3), K(136.2, AMT[0], AMT[1] - 6, 2.5, -8, 3)],
    "flash", tension=True,
    hits=[[122.7, 0.45], [126.5, 0.5], [129.0, 0.5], [129.6, 0.45], [133.65, 0.7], [134.35, 0.8], [135.15, 1.1, True]]),
  # 9 his reaction: "not bad... not fucking bad, hold the fucking phone"
  face(136.2, 141.1, mask_words=[{"text": "NOT", "src": 138.15, "color": W, "x": 0.8, "size": 300},
                                 {"text": "FUCKING", "src": 138.64, "color": P, "x": 0.8, "size": 150},
                                 {"text": "BAD", "src": 139.16, "color": Y, "x": 0.8, "size": 300},
                                 {"text": "HOLD", "src": 139.66, "color": C, "x": 0.8, "size": 250},
                                 {"text": "THE", "src": 140.06, "color": W, "x": 0.8, "size": 300},
                                 {"text": "FUCKING", "src": 140.28, "color": P, "x": 0.8, "size": 150},
                                 {"text": "PHONE", "src": 140.68, "color": Y, "x": 0.8, "size": 200}]),
  # 10 BIG WIN -> SUPER -> EPIC -> SWEET WIN 3,543.00 (the spin's pay)
  G(141.0, 148.9, [[141.0, 1.0], [141.3, 2.0], [146.7, 0.7], [147.6, 1.0]],
    [[141.0, "BOARD"], [141.2, "BOARD"], K(141.5, BAN[0], BAN[1], 1.7, 0, 2), [146.6, BAN[0], 552, 1.75, 0, 0, 2],
     K(147.0, BAN[0], BAN[1], 1.95, 12, 4), K(148.9, BAN[0], BAN[1] + 2, 2.08, 9, 3)],
    "glitch", hits=[[141.05, 0.6], [143.5, 0.5], [145.5, 0.6], [147.0, 1.1, True]]),
  # 11 TOTAL: board with WIN 3,614.60 CAD -> tilt push onto the win meter (ends on the total; no closing facecam)
  G(150.0, 152.3, [[150.0, 1.0]],
    [[150.0, "BOARD"], [150.3, "BOARD"], K(150.6, 590, 690, 2.25, -12, 4, bar=924), K(152.3, 590, 692, 2.35, -9, 2, bar=924)],
    "end", hits=[[150.55, 1.2, True]]),
]
# whole-word mutes from the clean-voice voice_words.json (5 stretched onsets corrected from the stem energy: see notes.txt)
MUTES = [[21.92, 23.64],     # "that's that that that" stammer
         [24.54, 25.20],     # "give me"
         [63.24, 64.20],     # first "we just need" (said twice)
         [99.42, 99.76],     # "hello"
         [126.36, 128.72],   # first "profit potentially, I'm not sure is" (he says "profit potentially" again on the count-up)
         [141.10, 143.64],   # "wait, Sean, do you ever bet?" (chat)
         [147.08, 149.80],   # "not bad, not fucking bad at all, baby" (repeat of the reaction line)
         [151.70, 153.36]]   # "so did you ever bet, nice?" (chat)
E = {k: copy.deepcopy(B[k]) for k in ("game_rect", "face_rect", "formats", "sfx_dir", "sfx_map", "fx", "popups")}
E.update({"src": f"{D}/clip.mp4", "out": f"{D}/edit.mp4", "work": f"{D}/work", "shots": shots, "age_tag": None, "freeze_ring": 0.9,
          "freezes": [{"src": 135.45, "dur": 1.5, "pop": {"char": "robot", "line": "multiplier_insane"}}],   # the big hit: 3,528.00 (x7 x6 x6); not the cat "not bad" (he says it next)
          "stems2": {"voice": f"{D}/stems/voice.wav", "game": f"{D}/stems/game.wav", "voice_max_speed": 2.0, "duck_db": 8,
                     "overlay": True, "words": f"{D}/voice_words.json", "max_delay": 0.8,
                     "mute": MUTES}})
json.dump(E, open(f"{D}/edl.json", "w"), indent=1); print("ok", len(shots), "shots")
