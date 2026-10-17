# Xposed, 2026-10-16 stream: Roobet Originals blackjack, C$354,435 (main C$283,549 + PP + 21+3) -> +C$1,488,632 on one hand
# (other-streamer overnight batch edit, 2026-10-17). Clip t = stream t - 1:42:45 (T0 6165).
# Story: raging after a 100x five-scatter bonus ("I'm gonna lose my whole fucking balance now, I'm gonna lose fucking everything")
# -> keno -> switches to blackjack, maxes all three bets -> hand 1: 9+10 = 19, dealer 2,3,8,2,7 BUSTS (22) -> hand 2: 10s 10s =
# PERFECT PAIR (C$921,534.12) + 20 -> he lunges at the cam -> stands, dealer J,4,A,2 = 17 -> WIN -> screaming at the cam
# -> announcer VO + "+C$1,488,632" slam over the table (balance C$2,559,047.75) -> "I'll make my own fucking win."
# The stream audio is MUTED from clip ~25 to 73.4 (keno + the whole blackjack build-up are silent in the VOD), so a Keno Money
# bed runs under the build-up: its first drop lands on the PERFECT PAIRS flash and it tape-stops into his live reaction.
# Blackjack rules (manifest "blackjack"): camera follows the CARDS (shoe -> spot, push-in on landing), sparse smooth keys,
# lighter fx; slow-mo + push-in on the bust card and on the dealer's last card. Roobet Originals is a native 60 fps page, so
# no feed_interp (that's for ~22 fps live tables).
import json, copy, sys
D = sys.argv[1]; SP = sys.argv[2]; B = json.load(open(f"{SP}/oct11/base_edl.json"))
PACK = f"{SP}/artifact-files/e859168a-e8f3-430f-9e98-7ba0494cd658"
def face(a, b, z0=1.0, z1=1.1, out="glitch", **kw):
    return {"kind": "face", "a": a, "b": b, "speeds": [[a, 1.0]], "cam": [[a, "FACE", z0, 0], [b, "FACE", z1, 0]], "out": out, **kw}
def G(a, b, speeds, cam=None, out="cut", **kw):
    return {"kind": "game", "a": a, "b": b, "speeds": [list(x) for x in speeds], "cam": cam or [[a, "BOARD"], [b, "BOARD"]], "out": out, **kw}
GX, GY, GW, GH = 28, 48, 1440, 808          # Roobet browser window (header with the balance at the top, page text below the table)
def clamp(cx, cy, z):
    hw, hh = 960 / z, 540 / z
    return [round(min(max(cx, GX + hw + 2), GX + GW - hw - 2)), round(min(max(cy, GY + hh + 2), GY + GH - hh - 2))]
def key(t, cx, cy, z, yaw=0, pitch=0):
    x, y = clamp(cx, cy, z); return [t, x, y, z, 0, yaw, pitch]
SHOE, PLAYER, DEALER = (1060, 200), (872, 468), (868, 245)      # card shoe (top right), player spot, dealer spot (source px)
TABLE = (760, 345)
BJ = dict(cam_interp="smooth")
shots = [
  # cold open: the winning hand (dealer 17, his 10-10 = 20 turning green), PP / 21+3 payouts blurred, angled swing, whip
  G(77.15, 77.95, [[77.15, 1.0]], [key(77.15, 830, 362, 2.35, -10, 4), key(77.95, 830, 360, 2.5, -6, 2)], "whip",
    hits=[[77.2, 0.8, True]], voice=False,
    blur=[{"rect": [640, 362, 150, 34], "t": [76.0, 79.0], "sigma": 40, "darken": 0.25},
          {"rect": [975, 362, 120, 34], "t": [76.0, 79.0], "sigma": 40, "darken": 0.25},
          {"rect": [340, 165, 110, 150], "t": [76.0, 79.0], "sigma": 40, "darken": 0.25}]),
  # hook: raging after the 100x bonus: "That's fucking crazy. I'm gonna lose my whole fucking balance now." (head right of centre)
  face(10.95, 13.75, mask_words=[{"text": "LOSE", "src": 12.42, "color": [255, 255, 255], "x": 0.2, "size": 300},
                                 {"text": "MY WHOLE", "src": 12.56, "color": [40, 230, 255], "x": 0.2, "size": 170},
                                 {"text": "FUCKING", "src": 12.84, "color": [255, 40, 90], "x": 0.2, "size": 170},
                                 {"text": "BALANCE", "src": 13.20, "color": [255, 214, 40], "x": 0.2, "size": 160}]),
  # one dead keno round (hits 2 of 3 for nothing)
  G(29.45, 30.45, [[29.45, 1.0]], [key(29.45, 870, 330, 2.2), key(30.45, 870, 330, 2.3)], "glitch"),
  # lobby: push onto the BLACKJACK tile
  G(62.35, 63.35, [[62.35, 1.0]], [key(62.35, 615, 430, 2.0), key(63.35, 615, 430, 2.6)], "glitch"),
  # all three bets maxed: C$283,549 main + C$35,443.62 Perfect Pairs + C$35,443.62 21+3 (static close-up on the bet fields)
  G(64.3, 65.6, [[64.3, 1.0]], [key(64.3, 470, 250, 2.7), key(65.6, 470, 250, 2.8)], "glitch", **BJ),
  # hand 1: 9 + 10 = 19 vs dealer 2 ... 3, 8, 2, 7 = 22 BUST (slow-mo + push-in on the 7, pull out to the green hand)
  G(65.6, 70.75, [[65.6, 1.0], [70.05, 0.6], [70.4, 1.0]],
    [key(65.6, *TABLE, 2.0), key(66.1, SHOE[0] - 60, 260, 2.6), key(66.45, *PLAYER, 2.8), key(67.0, *DEALER, 2.8),
     key(67.45, *PLAYER, 2.8), key(67.8, 860, 350, 2.4), key(68.55, 880, 250, 2.8), key(69.2, 900, 250, 2.85),
     key(69.7, 915, 250, 2.9), key(70.1, 930, 248, 3.0), key(70.25, 935, 245, 3.25, 8, 4), key(70.45, 930, 248, 3.3, 6, 3),
     key(70.75, 850, 360, 2.3, 2, 1)], "glitch", hits=[[70.22, 0.7]], **BJ),
  # hand 2 deal: 10s to him, J to the dealer, 10s -> PERFECT PAIR (C$921,534.12): tilt-push onto the pair + badge, freeze
  G(71.1, 73.6, [[71.1, 1.0], [72.8, 0.6], [73.35, 1.0]],
    [key(71.1, *TABLE, 2.0), key(71.5, SHOE[0] - 60, 260, 2.5), key(72.0, *PLAYER, 2.8), key(72.5, *DEALER, 2.8),
     key(72.85, *PLAYER, 2.9), key(73.15, 800, 430, 2.7), key(73.3, 790, 420, 2.7, -12, 6), key(73.6, 785, 415, 2.95, -8, 3)],
    "glitch", hits=[[73.27, 1.1, True]], **BJ),
  # his first reaction: lunges at the cam ("Fuck you!")
  face(73.5, 75.3),
  # stand on 20: dealer flips 4, draws A, then the 2 -> 17 (slow-mo + push-in on the 2), his hand turns green
  G(75.3, 77.45, [[75.3, 1.0], [76.95, 0.6], [77.3, 1.0]],
    [key(75.3, 800, 400, 2.3), key(75.75, *DEALER, 2.8), key(76.05, 880, 250, 2.9), key(76.65, 900, 250, 2.9),
     key(76.95, 915, 250, 3.0), key(77.1, 920, 250, 3.25, -8, 4), key(77.3, 915, 252, 3.3, -6, 3), key(77.45, 880, 330, 2.7, -3, 2)],
    "glitch", hits=[[77.1, 0.8]], **BJ),
  # the scream: jumps at the cam, mouth wide open, leaves the frame
  face(77.45, 79.0, z0=1.0, z1=1.12, out="flash"),
  # the total: angled push-in over the table (balance C$2,559,047.75 up top) + announcer VO + "+C$1,488,632" slam
  G(79.0, 81.6, [[79.0, 1.0]], [key(79.0, 760, 328, 1.95, 12, 4), key(79.6, 760, 320, 2.02, 10, 3), key(81.6, 760, 310, 2.1, 8, 2)],
    "glitch", hits=[[79.08, 1.2, True]], voice=False, **BJ),
  # closing: "I'll make my own fucking win."
  face(94.9, 96.9, out="end", mask_words=[{"text": "MAKE", "src": 95.36, "color": [255, 255, 255], "x": 0.22, "size": 280},
                                            {"text": "MY OWN", "src": 95.66, "color": [40, 230, 255], "x": 0.22, "size": 210},
                                            {"text": "FUCKING", "src": 96.08, "color": [255, 40, 90], "x": 0.22, "size": 170},
                                            {"text": "WIN", "src": 96.44, "color": [255, 214, 40], "x": 0.22, "size": 330}]),
]
MUTES = [[74.95, 76.0], [77.12, 77.95]]   # 'motherfu-, fuck you' (fuck you is already in the face shot) and his 2nd 'that's a million'
# voice_words.json hand-fixes (voice-stem energy + a no-VAD re-transcription): I'll 95.00, make 95.32, added that's a million 76.04-77.12
E = {k: copy.deepcopy(B[k]) for k in ("formats", "sfx_dir", "sfx_map", "popups")}
E.update({"game_rect": [GX, GY, GW, GH], "face_rect": [1489, 50, 400, 225], "fx": {"hit": 0.55, "trans": 0.7},
          "src": f"{D}/clip.mp4", "out": f"{D}/edit.mp4", "work": f"{D}/work", "shots": shots, "age_tag": None, "freeze_ring": 0.9,
          "freezes": [{"src": 73.35, "dur": 1.5, "pop": None}],
          "music": {"file": f"{PACK}/sounds/songs/keno-money.mp3", "at": 14.38, "align_src": 73.27, "end_src": 73.5,
                    "end_style": "tapestop", "end_fade": 0.9, "gain_db": -4},
          "sfx_auto_level": {"over_db": 4, "max_boost_db": 30, "roles": ["glitch", "whip", "_x"]},
          "extra_sfx": [{"file": f"{D}/vo.wav", "src": 79.12, "gain": 1.0}],
          "overlays": [{"src": 79.12, "from": 0, "to": 1488632, "fmt": "+C${:,}", "count": 0.45, "pos": [610, 900], "size": 130,
                        "font": f"{PACK}/tools/Poppins-BoldItalic.ttf", "color": [60, 230, 120], "stroke": [0, 60, 24],
                        "wash": [0, 34, 10], "darken": 0.25, "focus": [610, 860], "until_src": 81.6}],
          "stems2": {"voice": f"{D}/stems/voice.wav", "game": f"{D}/stems/game.wav", "voice_max_speed": 2.0, "duck_db": 8,
                     "overlay": True, "words": f"{D}/voice_words.json", "mute": MUTES, "max_delay": 0.8}})
json.dump(E, open(f"{D}/edl.json", "w"), indent=1); print("ok", len(shots), "shots")
