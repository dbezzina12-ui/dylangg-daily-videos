# Other-streamer edits (Xposed, Yassuo, Cabrzy): differences from EDIT_BRIEF.md

Follow EDIT_BRIEF.md (SP/batch/EDIT_BRIEF.md) for everything, EXCEPT:

1. Source: their own Kick VOD. Prep with the channel set: `KICK_CHANNEL=<slug> python3 SP/batch/prep_edit.py win.json OUTDIR ...`
   (slugs: xposed, yassuo, cabrzy). win.json has "game_rect"/"face_rect" from the scan: VERIFY on a frame and use them in the
   EDL ("game_rect", "face_rect"); recompute the zoom limits (every zoom inside the game window and clear of any stream overlay
   or balance bar; adapt the clamp() helper in the reference mk.py to the new rects).
2. NO talking pop-up sticker (no character popups at all): freezes use "pop": null.
3. VOICE-OVER at the big win instead: write ONE short announcer line that fits the moment (e.g. "TEN THOUSAND X. ARE YOU KIDDING ME?",
   "HE JUST HIT FOR TWO HUNDRED GRAND"; numbers in words; <= ~2.5 s), make it with
   `python3 SP/vo/make_vo.py SP/batch/<id>/vo.wav "<line>"` (queues on the CPU lock, ~1-3 min; it checks the words and keeps the best take),
   place it with "extra_sfx": [{"file": "<abs path to vo.wav>", "src": <source time of the hit/freeze>, "gain": 1.0}]
   (extra_sfx paths are relative to sfx_dir unless absolute: use an absolute path). Never mute or cut the streamer (their
   voice plays live through every shot, EDIT_BRIEF rule 3): put the line in a pause or on the freeze where you can, and add
   "duck_voice": 10 to that extra_sfx entry so their voice dips 10 dB under the line (and comes straight back) instead of being cut. Then QA by ear-proxy: the edit_qa transcript must contain the line.
4. ON-SCREEN CAPTION with it: an "overlays" entry at the same moment, style "slam" (or "pop"), the win as text, e.g.
   {"src": t, "from": 0, "to": 124500, "fmt": "${:,}", "count": 0.45, "pos": [960, 300], "size": 170,
    "font": "SP/artifact-files/e859168a-e8f3-430f-9e98-7ba0494cd658/tools/Poppins-BoldItalic.ttf", "color": [255, 214, 40],
    "stroke": [80, 50, 0], "until_src": t + 2.5} — or a static text like "1,000X" via "fmt": "1,000X" with from = to = 0.
   Put it where it doesn't cover the game's own win number.
5. Word captions behind them (mask_words) are optional: only if their facecam is big enough and the line is great.
6. Name: "<Streamer> <YYYY-MM-DD> <Game> <amount> hype edit.mp4" (e.g. "Xposed 2026-10-16 Wanted Dead or a Wild 124500 hype edit.mp4").
   Upload with drive_upload.py, then MOVE it into the "Other streamers" folder: parentId 163AljHBEEjf_o019WU3Adj6uwba40XeS.
7. Record: the win is a doc on the picks page (collection "wins", doc_id = your id). Get it, then update with status "edited",
   drive_id, edit_name, duration, edit_note (with if_version).
