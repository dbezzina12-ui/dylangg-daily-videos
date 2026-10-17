# Keno 4/4 high risk $2,590 (259x on $10), Oct 7 stream. Story: Raven's Revenge bonus buys not paying ("we're down four",
# "money back again... fuck"), switches to Keno, bumps the bet $5 -> $10 + Medium -> High, first round hits 4/4 = 259x.
# Keno rules (manifest keno_feedback): camera LOCKED on the board, a static close-up on the bet change, ONE punch-in for the
# story beat (balance pill jumping to C$4,181.95 as he says "we're back"), the angled push-in at the end. Glitch cuts only.
# Brief rules 1/3/5/7: ~40 s, his voice never stretched (stems2 overlay + words), blurred cold open, one freeze + popup on the
# hit (the 259x box landing), end on the total (no closing facecam: no "not bad" line after the win).
import json, copy, sys
D = sys.argv[1]; SP = "/tmp/claude-0/-home-user-dylangg-daily-videos/c57cb05e-857a-55e7-80f9-9455f18314fd/scratchpad"
B = json.load(open(f"{SP}/oct11/base_edl.json"))
def face(a, b, z0=1.0, z1=1.1, out="glitch", **kw):
    return {"kind": "face", "a": a, "b": b, "speeds": [[a, 1.0]], "cam": [[a, "FACE", z0, 0], [b, "FACE", z1, 0]], "out": out, **kw}
def G(a, b, speeds, cam=None, out="glitch", **kw):
    return {"kind": "game", "a": a, "b": b, "speeds": [list(x) for x in speeds], "cam": cam, "out": out, **kw}
K = lambda t: [t, 680, 560, 1.78]            # keno board locked: whole keno panel, no Roobet header / footer / webcam
S = lambda t: [t, 680, 535, 2.0]             # Raven's Revenge reels, above the balance bar
def still(a, b, k): return [k(a), k(b)]
shots = [
  # cold open: the 259x box just landed, amount blurred, small angled push (yaw -), glitch into the story
  G(186.3, 187.1, [[186.3, 1.0]], [[186.3, 790, 505, 2.2, 0, -10, 4], [187.1, 790, 505, 2.35, 0, -6, 2]],
    hits=[[186.35, 0.8, True]], voice=False, blur=[{"rect": [740, 450, 185, 125], "t": [186.0, 999], "sigma": 40, "darken": 0.25}]),
  G(93.55, 95.95, [[93.55, 1.0]], still(93.55, 95.95, S)),                        # "this game's good, it's just not doing it today"
  G(106.55, 107.55, [[106.55, 1.0]], still(106.55, 107.55, S), hits=[[106.62, 0.5]]),   # buys another: 10 SUPER FREE SPINS
  G(114.22, 118.2, [[114.22, 1.0]], still(114.22, 118.2, S)),                      # "nothing's paying man, we bought everything..."
  face(123.82, 126.95),                                                          # "lost 2K, we lost, we're down, we're down four"
  G(145.5, 148.85, [[145.5, 1.0]], still(145.5, 148.85, S), hits=[[145.95, 0.4]]),  # "+2FS ... they gave me an extra 1,600, we lost it all"
  G(170.25, 173.45, [[170.25, 1.0]], still(170.25, 173.45, S), hits=[[171.45, 0.5]]),   # TOTAL WIN 184.80 on a $200 buy: "money back again... fuck"
  G(178.7, 182.3, [[178.7, 1.0]], still(178.7, 182.3, K)),                        # to the lobby -> Keno, picks 7 8 5 10
  G(183.0, 184.25, [[183.0, 1.0]], [[183.0, 345, 415, 3.2], [184.25, 345, 415, 3.2]], hits=[[183.8, 0.4]]),   # static close-up: High, 2x -> C$10
  G(184.25, 186.6, [[184.25, 1.0], [185.72, 0.55], [186.15, 1.0]], still(184.25, 186.6, K),
    hits=[[184.92, 0.3], [185.22, 0.3], [185.7, 0.35], [185.93, 0.7], [186.1, 1.0, True]], tension=True),   # 8, 5, 7 ... 10 = 4/4, 259x
  face(186.6, 189.2),                                                            # the reaction: "BANG! Fucking bang!"
  G(189.2, 191.6, [[189.2, 1.0]], [K(189.2), K(190.75), [190.92, 645, 384, 2.6], [191.6, 645, 384, 2.68]],
    hits=[[190.92, 0.6]]),                                                       # THE punch-in: balance pill C$4,181.95, "we're back"
  face(191.6, 193.12, mask_words=[{"text": "WE'RE", "src": 192.0, "color": [255, 255, 255], "x": 0.2, "size": 230},
                                   {"text": "FUCKING", "src": 192.16, "color": [255, 40, 90], "x": 0.2, "size": 150},
                                   {"text": "BACK", "src": 192.49, "color": [255, 214, 40], "x": 0.2, "size": 260}]),
  face(197.6, 200.2),                                                           # "what an absolute fucking snipe"
  # END on the total: angled push-in (yaw +) onto the 259.00x / C$2590.00 box, no voice (his lines were used above)
  G(187.9, 190.9, [[187.9, 1.0]], [K(187.9), K(188.05), [188.3, 745, 515, 1.95, 0, 14, 5], [188.9, 760, 512, 2.03, 0, 12, 4],
                                   [190.9, 785, 509, 2.14, 0, 11, 3]], out="end", hits=[[188.3, 1.1, True]], voice=False),
]
E = {k: copy.deepcopy(B[k]) for k in ("face_rect", "formats", "sfx_dir", "sfx_map", "fx", "popups")}
E.update({"game_rect": [38, 175, 1202, 750],          # Roobet window, header included, stopping left of the webcam box (x 1240)
          "src": f"{D}/clip.mp4", "out": f"{D}/edit.mp4", "work": f"{D}/work", "shots": shots, "age_tag": None, "freeze_ring": 0.9,
          "freezes": [{"src": 186.3, "dur": 1.5, "pop": {"char": "frog", "line": "lets_go"}}],
          "sfx_auto_level": {"over_db": 4, "max_boost_db": 30, "roles": ["glitch", "whip", "_x"]},
          "stems2": {"voice": f"{D}/stems/voice.wav", "game": f"{D}/stems/game.wav", "voice_max_speed": 2.0, "duck_db": 8,
                     "overlay": True, "words": f"{D}/voice_words.json",
                     "mute": [[101.5, 111.3], [178.0, 181.4], [118.2, 119.3], [189.3, 190.4], [193.1, 194.5]], "max_delay": 0.8}})
json.dump(E, open(f"{D}/edl.json", "w"), indent=1); print("ok")
