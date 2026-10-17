# Roo's VIP Blackjack 2 (live), Sep 28 stream: two back-to-back wins at the end of the stream (overnight batch, 2026-10-17)
#   hand 1: CA$2,000 (+200 side bet), K+9 = 19 stands vs dealer 6, hole 6 (12), draws a 10 -> 22 BUST -> YOU WIN CA$4,000
#   hand 2: CA$800, 8+2 = 10 vs dealer 3, he DOUBLES to CA$1,600, gets a 5 (15), dealer 3+2+6+3 = 14 draws an 8 -> 22 BUST
#           -> YOU WIN CA$3,200. Balance CA$2,201.31 -> CA$5,401.31 (start balance $5,000: "hoping to break even").
# Live-blackjack rules (manifest "blackjack"): feed_interp for the ~22 fps table feed, lighter fx, camera follows the CARDS
# (shoe -> spot, small push-in on landing, sparse smooth keys), slow-mo + push-in on each bust card, then the win.
# Stream layout (same as the Sep 25 blackjack): game feed x 40-1240 (webcam box covers x>1240 below y 695), y 244-919.
# Clip t = stream t - 1:23:25.
import json, copy, sys
D = sys.argv[1]; SP = sys.argv[2]; B = json.load(open(f"{SP}/oct11/base_edl.json"))
def face(a, b, z0=1.0, z1=1.1, out="glitch", **kw):
    return {"kind": "face", "a": a, "b": b, "speeds": [[a, 1.0]], "cam": [[a, "FACE", z0, 0], [b, "FACE", z1, 0]], "out": out, **kw}
def G(a, b, speeds, cam=None, out="cut", **kw):
    return {"kind": "game", "a": a, "b": b, "speeds": [list(x) for x in speeds], "cam": cam or [[a, "BOARD"], [b, "BOARD"]], "out": out, **kw}
GX, GY, GW, GH = 40, 244, 1200, 675
def clamp(cx, cy, z):
    hw, hh = 960 / z, 540 / z
    return [round(min(max(cx, GX + hw + 1), GX + GW - hw - 1)), round(min(max(cy, GY + hh + 1), GY + GH - hh - 1))]
def key(t, cx, cy, z, yaw=0, pitch=0):
    x, y = clamp(cx, cy, z); return [t, x, y, z, 0, yaw, pitch]
SHOE, PLAYER, DEALER, CHIP = (960, 650), (686, 785), (688, 690), (682, 840)   # card shoe (right), player cards, dealer cards, bet chip
def C(t, p, z, yaw=0, pitch=0, dx=0, dy=0): return key(t, p[0] + dx, p[1] + dy, z, yaw, pitch)
BJ = dict(cam_interp="smooth")
BLUR4K = [{"rect": [490, 512, 390, 82], "t": [36.6, 38.0], "sigma": 40, "darken": 0.25},       # "CA$ 4,000.00" on the banner
          {"rect": [70, 255, 200, 45], "t": [36.6, 38.0], "sigma": 30, "darken": 0.2}]          # table limits "CA$ 250 - 50,000" (QA OCR)
shots = [
  # cold open: YOU WIN CA$4,000 (amount blurred), angled swing, whip into the story (no voice: his words there come later)
  G(36.80, 37.60, [[36.80, 1.0]], [key(36.80, 682, 560, 2.05, 10, 4), key(37.60, 682, 560, 2.2, 6, 2)], "whip",
    hits=[[36.85, 0.8, True]], blur=BLUR4K, voice=False),
  # hook: "Yeah, I was just hoping to fucking break even, bro" (start balance $5,000, he's at CA$2,201)
  face(9.05, 11.62, mask_words=[{"text": "HOPING", "src": 10.18, "color": [255, 255, 255], "x": 0.19, "size": 175},
                                {"text": "BREAK", "src": 10.66, "color": [255, 40, 90], "x": 0.19, "size": 200},
                                {"text": "EVEN", "src": 10.92, "color": [255, 214, 40], "x": 0.19, "size": 250},
                                {"text": "BRO", "src": 11.20, "color": [40, 230, 255], "x": 0.19, "size": 300}]),
  # hand 1, CA$2,000: "Just give me a good one and call it a night" over the bet / ALL BETS CONFIRMED, then the deal (K, 6 up, 9, hole)
  G(21.60, 28.70, [[21.60, 1.0]],
    [C(21.60, CHIP, 2.2, dy=-60), C(23.90, CHIP, 2.45, dy=-50), key(25.85, 820, 680, 2.5), C(26.75, PLAYER, 2.8),
     C(27.20, DEALER, 2.75, dy=20), C(28.05, PLAYER, 2.85), C(28.45, DEALER, 2.8, dy=25), C(28.70, DEALER, 2.85, dy=25)], "glitch", **BJ),
  # stands on 19 -> "You couldn't have just gave me fucking three sixes, you dickhead" / dealer: "you stand here, shows a 12"
  # -> the 10 from the shoe, 22 BUST (0.6x slow-mo + push-in) -> YOU WIN CA$4,000 (the one freeze + popup) -> "not bad though"
  G(31.30, 38.60, [[31.30, 1.0], [35.20, 0.6], [35.95, 1.0]],
    [C(31.30, DEALER, 2.6, dy=15), C(33.15, DEALER, 2.75, dy=5), C(33.70, DEALER, 3.1, -6, 3), C(34.55, DEALER, 2.8, dy=5),
     key(34.95, 880, 660, 2.6), C(35.40, DEALER, 3.0, dx=-20), key(35.62, 650, 690, 3.4, 10, 5), key(35.98, 655, 688, 3.5, 8, 3),
     key(36.40, 682, 610, 2.4), key(36.75, 682, 560, 2.05, -12, 4), key(38.60, 682, 556, 2.3, -9, 3)],
    "flash", hits=[[35.62, 1.0, True], [36.85, 1.1, True]], tension=True, **BJ),
  face(41.75, 43.55),                                                                       # "Holy... fuck" (balance CA$4,001)
  # hand 2, CA$800: the deal (2, dealer 3, 8 = 10)
  G(52.40, 55.40, [[52.40, 1.0]],
    [key(52.40, 840, 670, 2.5), C(53.35, PLAYER, 2.8), C(53.85, DEALER, 2.75, dy=20), C(54.60, PLAYER, 2.85), C(55.40, DEALER, 2.8, dy=25)],
    "glitch", **BJ),
  # "I have to double" -> 800 becomes 1.6K (push onto the chip) -> (wait for the card at 1.5x) -> the 5 (15)
  G(56.35, 62.75, [[56.35, 1.0], [59.05, 1.5], [61.10, 1.0]],
    [C(56.35, PLAYER, 2.6, dy=-10), C(58.40, CHIP, 2.7, dy=-30), C(58.85, CHIP, 3.0, 8, 4, dy=-30), C(59.60, PLAYER, 2.7),
     key(61.40, 880, 670, 2.55), C(62.00, PLAYER, 2.75, dy=-20), C(62.40, PLAYER, 3.0, -6, 3), C(62.75, PLAYER, 3.05, -5, 2)], "glitch", **BJ),
  # dealer: hole card 2 (5), draws 6 (11), draws 3 (14)
  G(62.75, 67.60, [[62.75, 1.0], [64.15, 1.35], [65.05, 1.0]],
    [C(62.75, DEALER, 2.6, dy=20), C(63.95, DEALER, 3.0, dy=5), C(65.10, DEALER, 2.7, dy=10), key(65.35, 880, 665, 2.6),
     C(66.00, DEALER, 3.0, dx=-25), key(66.45, 860, 665, 2.6), C(67.25, DEALER, 3.05, dx=-30), C(67.60, DEALER, 3.1, dx=-30)], "glitch", **BJ),
  face(67.60, 68.30),                                                                       # both hands on his head
  # the 8 -> 22 BUST (slow-mo + push-in, "PLEASE!") -> YOU WIN CA$3,200 ("GOD!"), end on the total
  G(68.30, 71.05, [[68.30, 1.0], [68.75, 0.6], [69.40, 1.0], [70.10, 0.85]],
    [key(68.30, 860, 665, 2.6), C(68.95, DEALER, 3.0, dx=-40), key(69.10, 640, 690, 3.4, -10, 5), key(69.50, 645, 688, 3.5, -8, 3),
     key(69.80, 682, 610, 2.4), key(70.05, 682, 560, 2.05, 12, 4), key(71.05, 682, 556, 2.25, 9, 3)],
    "glitch", hits=[[69.10, 1.0, True], [70.15, 1.2, True]], tension=True, **BJ),
  # closing facecam: his real reaction, "WE'RE BACK, WE'RE BACK" (word times from the voice-stem energy)
  face(71.05, 72.50, out="end", mask_words=[{"text": "WE'RE", "src": 71.10, "color": [255, 255, 255], "x": 0.80, "size": 210},
                                            {"text": "BACK", "src": 71.32, "color": [255, 40, 90], "x": 0.80, "size": 250},
                                            {"text": "WE'RE", "src": 71.84, "color": [255, 214, 40], "x": 0.80, "size": 210},
                                            {"text": "BACK", "src": 71.94, "color": [40, 230, 255], "x": 0.80, "size": 250}]),
]
# whole-word mutes (source t): the dealer's chatter on hand 1, "this guy's voice is super annoying" (and its repeat "that guy's voice
# is super fucking annoying"), the DK chatter, the 2nd/3rd "I have to double" + "give me", the faint "ace ten", the 2nd
# "please please don't fuck me" + "ten", everything after the 2nd "we're back". QA v1: "give me a ace" muted too ("give me a" twice).
# voice_words.json: whisper stretched words in 54-60 and 65-74 (e.g. "please" 66.20-68.98); those were re-timed from the voice-stem
# energy (original kept as voice_words_prep2.json)
MUTES = [[24.65, 31.40], [35.20, 37.49], [38.12, 41.80], [43.50, 57.38], [58.31, 63.25], [64.45, 68.30], [72.10, 80.0]]
E = {k: copy.deepcopy(B[k]) for k in ("face_rect", "formats", "sfx_dir", "sfx_map", "popups")}
E.update({"game_rect": [GX, GY, GW, GH], "fx": {"hit": 0.55, "trans": 0.7}, "feed_interp": ["game"],
          "src": f"{D}/clip.mp4", "out": f"{D}/edit.mp4", "work": f"{D}/work", "shots": shots, "age_tag": None, "freeze_ring": 0.9,
          "freezes": [{"src": 37.05, "dur": 1.5, "pop": "auto"}],
          "stems2": {"voice": f"{D}/stems/voice.wav", "game": f"{D}/stems/game.wav", "voice_max_speed": 2.0, "duck_db": 8,
                     "overlay": True, "words": f"{D}/voice_words.json", "mute": MUTES, "max_delay": 0.8}})
json.dump(E, open(f"{D}/edl.json", "w"), indent=1); print("ok", len(shots), "shots")
