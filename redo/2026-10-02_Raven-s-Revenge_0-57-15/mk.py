# Raven's Revenge $2,774.10 (CA$, bet C$3 -> ~925x), Oct 2 stream, bonus hunt #9 (SUPER free spins, Valkyrie Studio).
# House style of the approved Slayers $7,417 v8 (mk_s1v7.py): no fast-forwards, dead spins glitch-cut, every hit spin from the
# reels dropping to its win, tilt push-ins on the board amounts as they land, swings onto the tree / BIG WIN / TOTAL alternating
# yaw sides, real-speed voice overlay (stems2 + words), one freeze + popup on the 1,305.00 wild pay (the big hit, not the total),
# ends on TOTAL WIN 2,774.10 + the closing "NOT FUCKING BAD" facecam.
# usage: python3 mk.py <batch folder> <scratchpad>
import json, copy, sys
D = sys.argv[1]; SP = sys.argv[2]; B = json.load(open(f"{SP}/oct11/base_edl.json"))
def face(a, b, z0=1.0, z1=1.1, out="glitch", **kw):
    return {"kind": "face", "a": a, "b": b, "speeds": [[a, 1.0]], "cam": [[a, "FACE", z0, 0], [b, "FACE", z1, 0]], "out": out, **kw}
def G(a, b, speeds, cam=None, out="cut", **kw):
    return {"kind": "game", "a": a, "b": b, "speeds": [list(x) for x in speeds], "cam": cam or [[a, "BOARD"], [b, "BOARD"]], "out": out, **kw}
GX, GY, GW, GH = 38, 230, 1288, 695
BAR = 806                                   # top of the game's own BALANCE / WIN / BONUS ENHANCER / FREE SPINS row on this layout
def clamp(cx, cy, z):
    hw, hh = 960 / z, 540 / z
    return [round(min(max(cx, GX + hw + 2), GX + GW - hw - 2)), round(min(max(cy, GY + hh + 2), BAR - hh))]
def key(t, cx, cy, z, yaw=0, pitch=3):
    x, y = clamp(cx, cy, z); return [t, x, y, z, 0, yaw, pitch]
def W(text, src, color, size, x=0.19): return {"text": text, "src": src, "color": color, "x": x, "size": size}
WH, PK, YE, CY = [255, 255, 255], [255, 40, 90], [255, 214, 40], [40, 230, 255]
# board grid (source px): reels x 457 570 680 793 900, rows y 375 490 600 712; tree / banner amounts at (680, ~757)
BLUR_BIG = [{"rect": [490, 715, 380, 90], "t": [90.0, 999], "sigma": 40, "darken": 0.25}]      # tree counter 820.04 -> 1,479.00
shots = [
  # cold open: the BIG WIN shield (1,479.00 blurred), whip into the story
  G(90.9, 91.7, [[90.9, 1.0]], [key(90.9, 680, 519, 1.88, -10, 4), key(91.7, 680, 516, 1.98, -6, 2)], "whip",
    hits=[[90.98, 0.8, True]], blur=BLUR_BIG, voice=False),
  # hook: "Okay, we just need a shitload of fucking birds" (the wild ravens)
  face(32.25, 34.15, mask_words=[W("SHITLOAD", 33.30, WH, 118, 0.22), W("OF", 33.60, PK, 260, 0.22), W("FUCKING", 33.67, YE, 120, 0.22), W("BIRDS", 33.88, CY, 200, 0.22)]),
  # "you guys weren't lying": the three bonus symbols light up (pan + tilt across them) -> 10 SUPER FREE SPINS card
  G(25.3, 29.4, [[25.3, 1.0], [26.0, 0.7], [26.7, 1.0], [27.0, 2.0], [27.85, 1.0]],
    [[25.3, "BOARD"], [25.9, "BOARD"], key(26.1, 461, 367, 2.0, 10, 5), key(26.45, 682, 600, 2.0, 0, 4), key(26.8, 903, 488, 2.0, -10, 4),
     [27.1, "BOARD"], [27.9, "BOARD"], key(28.1, 662, 560, 1.92, 8, 3), key(29.4, 662, 556, 2.08, 6, 2)],
    "glitch", hits=[[26.15, 0.45], [26.5, 0.45], [26.85, 0.45], [28.05, 0.7]]),
  # spin 9/10 just paid: "can you please give me another bird, please"
  face(63.35, 65.05),
  # spin 10/10: the bonus symbol lands (tilt on it), wild pays 10.00 / 9.00, "that's an extra free spin" -> +2FS
  G(65.05, 70.45, [[65.05, 1.0], [65.3, 0.65], [65.75, 1.0], [68.75, 1.6], [69.35, 1.0]],
    [[65.05, "BOARD"], [65.25, "BOARD"], key(65.5, 680, 600, 2.0, -10, 5), key(66.1, 680, 600, 2.1, -8, 3),
     key(66.5, 590, 590, 2.1, 8, 4), key(67.6, 600, 585, 2.25, 6, 3), [68.9, "BOARD"], [69.3, "BOARD"],
     key(69.5, 680, 545, 2.0, -12, 5), key(70.45, 680, 540, 2.15, -9, 3)],
    "glitch", hits=[[65.5, 0.5], [66.5, 0.45], [69.45, 0.8]]),
  # spin 11/12: 228.00 -> 126.00 -> 79.80 wild pays (tilt + pan across them), tree tally 310.43
  G(71.0, 77.0, [[71.0, 1.4], [72.7, 1.0], [72.95, 0.6], [73.45, 1.0], [74.4, 1.8], [75.8, 1.0]],
    [[71.0, "BOARD"], [72.75, "BOARD"], key(73.0, 545, 575, 2.05, 12, 5), key(73.5, 560, 640, 2.1, 10, 4),
     key(74.05, 600, 600, 2.15, 8, 3), [74.6, "BOARD"], [75.85, "BOARD"], key(76.05, 680, 560, 1.95, -12, 4), key(77.0, 680, 556, 2.05, -10, 3)],
    "glitch", hits=[[73.0, 0.5], [73.5, 0.5], [74.0, 0.5], [76.0, 0.8]]),
  # spin 12/12 ("last bit, go crazy"): bonus symbol lands, 150.00, tree 180.00 -> "give me one of these birds for the last spin"
  # -> +2FS -> "oh, it's two free spins" -> spin 13/14: 174.00 then the 1,305.00 wild (freeze + popup) -> tree -> BIG WIN 1,479.00
  G(78.3, 91.75, [[78.3, 1.0], [79.4, 1.6], [80.3, 1.0], [81.3, 1.8], [83.9, 1.0], [86.3, 1.3], [87.9, 1.0], [88.35, 0.6], [88.9, 1.0],
                  [89.7, 1.5], [90.4, 1.0]],
    [[78.3, "BOARD"], [78.6, "BOARD"], key(78.85, 457, 600, 2.0, 10, 5), key(79.35, 470, 600, 2.05, 8, 4), [79.8, "BOARD"],
     key(80.45, 600, 570, 2.1, -8, 4), key(81.2, 600, 566, 2.25, -6, 3), [81.5, "BOARD"], [84.75, "BOARD"],
     key(84.95, 457, 560, 2.0, 10, 5), key(85.9, 457, 556, 2.15, 8, 3), [86.2, "BOARD"], [87.9, "BOARD"],
     key(88.05, 590, 600, 2.0, -12, 5), key(88.5, 660, 680, 2.2, -12, 6), key(89.4, 660, 672, 2.35, -9, 3), [89.65, "BOARD"],
     [90.75, "BOARD"], key(90.95, 680, 520, 1.95, 12, 4), key(91.75, 680, 515, 2.08, 10, 3)],
    "flash", hits=[[78.85, 0.45], [80.45, 0.5], [85.0, 0.7], [88.05, 0.5], [88.5, 1.1, True], [90.98, 1.0, True]], tension=True),
  # the last spin 14/14: 198.00 + 138.60 wild pays, the wild tally 40.43 -> 131.32, tree 249.46 -> NICE WIN 336.60
  G(92.9, 99.35, [[92.9, 1.3], [94.8, 0.7], [95.5, 1.0], [96.0, 1.6], [97.75, 1.0]],
    [[92.9, "BOARD"], [94.8, "BOARD"], key(94.98, 580, 600, 2.0, 12, 5), key(95.4, 590, 625, 2.15, 10, 4), [95.9, "BOARD"],
     key(96.6, 680, 600, 2.0, -10, 4), key(97.7, 680, 596, 2.15, -8, 3), [97.9, "BOARD"], key(98.3, 680, 520, 1.95, 12, 4),
     key(99.35, 680, 515, 2.05, 10, 3)],
    "glitch", hits=[[95.0, 0.5], [95.35, 0.5], [96.65, 0.45], [98.33, 0.9]]),
  # TOTAL WIN 2,774.10
  G(99.5, 102.3, [[99.5, 1.0]], [[99.5, "BOARD"], [99.62, "BOARD"], key(99.78, 680, 580, 1.95, -12, 4), key(102.3, 680, 576, 2.08, -9, 3)],
    "glitch", hits=[[99.72, 1.2, True]], voice=False),
  # closing: "NOT FUCKING BAD" (big grin)
  face(107.1, 108.62, out="end", mask_words=[W("NOT", 107.25, WH, 260, 0.77), W("FUCKING", 107.67, PK, 120, 0.77), W("BAD", 108.07, YE, 260, 0.77)]),
]
MUTE = [[26.66, 31.0],     # "solid super" (mumble under the card)
        [63.0, 63.55],     # "bad." (tail of an earlier "not bad")
        [68.73, 72.8],
        [73.63, 77.6],     # "yeah, not bad, not bad ... sure" (keeps "not bad" for the BIG WIN + ending)
        [77.6, 83.4],      # "we have no spins left, okay wait ... we get one more spin, please"
        [87.51, 90.15],
        [91.1, 94.85],     # "not fucking bad! ... we need" (the closing line is his later "NOT FUCKING BAD")
        [95.26, 106.9],    # "I mean not bad, not fucking bad at all, this game is fucking good bro..." (no chatter over the total)
        [108.62, 126.0]]   # "I said we needed to get to 3k ..." after the closing line
E = {k: copy.deepcopy(B[k]) for k in ("game_rect", "face_rect", "formats", "sfx_dir", "sfx_map", "fx", "popups")}
E.update({"src": f"{D}/clip.mp4", "out": f"{D}/edit.mp4", "work": f"{D}/work", "shots": shots, "age_tag": None, "freeze_ring": 0.9,
          "freezes": [{"src": 88.62, "dur": 1.5, "pop": {"char": "slot", "line": "no_way"}}],     # 1,305.00 wild pay
          "stems2": {"voice": f"{D}/stems/voice.wav", "game": f"{D}/stems/game.wav", "voice_max_speed": 2.0, "duck_db": 8,
                     "overlay": True, "words": f"{D}/voice_words.json", "mute": MUTE, "max_delay": 0.8}})
json.dump(E, open(f"{D}/edl.json", "w"), indent=1); print("ok")
