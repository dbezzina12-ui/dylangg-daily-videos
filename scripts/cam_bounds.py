# cam_bounds.py EDL.json: every explicit camera key [t, cx, cy, z, ...] on a game shot must keep the 1920x1080 view inside the
# game window (game_rect), or the stream overlay (Roobet header, chat, webcam box) shows. Run before every render of a board tilt.
import json, sys
E = json.load(open(sys.argv[1])); gx, gy, gw, gh = E["game_rect"]; W, H = E.get("out_size", [1920, 1080]); bad = 0
for s in E["shots"]:
    if s["kind"] != "game": continue
    for k in s["cam"]:
        if len(k) >= 4 and not isinstance(k[1], str):
            t, cx, cy, z = k[:4]; hw, hh = W / 2 / z, H / 2 / z
            if cx - hw < gx or cx + hw > gx + gw or cy - hh < gy or cy + hh > gy + gh:
                bad += 1; print(f"OUT OF WINDOW shot {s['a']}: key {k} (view x {cx - hw:.0f}-{cx + hw:.0f}, y {cy - hh:.0f}-{cy + hh:.0f})")
print("ok" if not bad else f"{bad} keys out of the game window")
