# Overnight hype-edit brief (Dylan / DylanJamesGG, Kick slot streams)

You make ONE finished hype edit of one stream win, end to end, unattended (Dylan is asleep: never stop to ask; make the call and
write it in notes.txt). SP = /tmp/claude-0/-home-user-dylangg-daily-videos/c57cb05e-857a-55e7-80f9-9455f18314fd/scratchpad
Your folder: SP/batch/<your id>/ with win.json (the win record). Work only there. Disk is tight (~5 GB free): clean up at the end.

## House style (newest rules win; these come straight from Dylan's feedback)
Reference edits: SP/oct11/mk_s1v7.py (Slayers $7,417, APPROVED final, VS-slot rules) and SP/oct11/mk_s2v2.py ($4,049, same style).
Read both fully before writing yours, plus the manifest notes in
SP/artifact-files/e859168a-e8f3-430f-9e98-7ba0494cd658/manifest.json (keys LOCKED_STYLE_v4, show_the_slot, cold_open, framing,
freeze_popups, no_repeats, mask_captions, swing_moves, voice_real_speed, vs_slots, endings, every_win_reads, blackjack).
Rules, newest first (they override older notes where they conflict):
0. SHOW HIS REACTION ON THE BIG HITS (Dylan, 2026-10-17: "I can hear him reacting but can't see him"; he picked the solid tilted
   picture-in-picture over a see-through face because the see-through one blocks the wins): add "reactions" entries,
   {"src0": a, "src1": b, "style": "pip", "side": "r", "size": 0.29, "pos": [x, y]}, on the GAME shots where he reacts out loud
   (the hit landing, the multiplier/banner, the total): 2-6 s each, usually 2-4 per edit. His webcam (face_rect of the same
   frame, so it is live) swings in tilted, pushes in and pans across him, and swings out. Put "pos" (the window's centre) where
   it covers NO win amount, banner or the reels that matter (default right edge ~[1610, 640]; "side": "l" and a left pos when
   the board sits right). Check the QA frames for it, and look at face_rect crops through
   the window first (scan_vod.py frame --crop): start it where his face is in the webcam (people lean out of frame when they pop off). Facecam shots stay as they are; never put a reaction over a face shot.
1. ~40-55 s. Balance real gameplay and hype; never rushed, never every spin.
2. NO fast-forwards/VHS x8 shots: cut dead spins out with glitch cuts. Each spin that hits plays from the reels dropping to its win.
3. HIS VOICE PLAYS LIVE FOR THE WHOLE SHOT (Dylan, 2026-10-17: "during whatever clip is happening it should have the voice
   still active... if the voice is there for the whole clip it doesn't [sound terrible]. If we need to fade it out we can also do
   that"): "stems2" with "overlay": true and "words": voice_words.json, NO "mute" lists. The engine ("voice_mode": "live", the
   default) plays his voice stem continuously at 1.0x through every shot, from the shot's first frame, exactly as it was live,
   and at a cut lets the word running finish (max 0.25 s) and fades it out. No phrases are picked out, queued or replayed. This is
   what the PC's Xposed 848k redo did and Dylan called it perfect. Slow-mo, freezes and ramps shift his voice against the picture a
   little (it keeps playing at 1.0x); "sync_tol": 0.12 + "max_off": 1.0 make it wait in his pauses / skip ahead between words to
   catch up instead. HYPE_SYNC_ONLY=1 writes work/voice_sync.json ([out time, picture time, voice time]) and exits in ~30 s. So what
   you HEAR is decided by the cut: choose shot ranges where what he says fits the moment (the hype on the hit, not a Discord plug),
   end shots in his pauses where you can, and give the last shot room for his last line. "voice": false on a shot silences him
   there (use it for the cold open if its talking clashes with the story). "voice_mode": "phrases" restores the old phrase engine.
4. Camera: angled swing / tilt push-ins ON THE BOARD onto win amounts as they appear/count up (not only banners); pan/tilt across
   scatters as they land; alternate yaw sides. VS / expanding-wild games: close 2.2x zoom on each VS as it lands left->right, zoom
   OUT to ~1.72-1.78 as soon as multis display, pan reel to reel, BOARD for the count-up. Every zoom stays inside the game window
   and above the balance bar (check with SP/artifact-files/e859168a-e8f3-430f-9e98-7ba0494cd658/tools/cam_bounds.py).
5. Cold open: ~0.8 s of the big win with the amount BLURRED (blur rect), whip into the story. One freeze + popup on the biggest hit
   ("freezes": [{"src": t, "dur": 1.5, "pop": "auto"}], "freeze_ring": 0.9), not on the final total.
6. Word-by-word glitch captions behind him (face shot "mask_words") on his best hype line, on the side his head/arms are NOT on.
7. End on the total. Closing facecam ONLY if he says "not bad" (or similar) or has a genuinely great reaction. No 18+ badge.
8. Slow-mo: keep it short (a beat on a landing/hit, <= ~1.5 s output). The engine varispeeds the game audio under it
   (no flanging); never slow a shot that carries important game sound for long. Freezes + camera moves are the main emphasis.
9. Blackjack / keno / non-slot wins: follow the manifest's blackjack note (cards-follow camera, calm); keep rules 1, 3, 5, 7.

## Steps
Run every long command (prep phases, render, QA) with run_in_background and timeout 7200000 (the max): they can wait a long
time in the shared CPU queue and the default background limit (30 min) kills them.
1. Prep phase 1 (CPU-heavy parts queue on a shared lock automatically; may wait for other editors):
   `python3 SP/batch/prep_edit.py SP/batch/<id>/win.json SP/batch/<id> [--max 300]` -> clip.mp4 (clip time 0 = stream time T0),
   voice_words.json (from the mix), sheet_NN.jpg (2 fps, stamped with CLIP time), prep.json (win moments on the clip timeline).
   win.json times can be off by up to ~30 s (and evidence image stamps too): always locate moments from the sheets/frames.
   The scan's evidence images for your win are in SP/scan/<date>/confirm/ (names in win.json "evidence").
2. Read every sheet. For detail use `python3 SP/oct11/dense.py clip.mp4 out.jpg A B 0.25` (clip times). Read voice_words.json.
   Check the stream layout on a full frame (`ffmpeg -ss T -i clip.mp4 -frames:v 1 f.jpg`): game window rect, facecam rect, where the
   balance bar starts. If it differs from game_rect [38,230,1288,695] / face_rect [1245,695,675,385] / bar at y 862, set yours.
3. Write SP/batch/<id>/mk.py (copy the helpers from mk_s1v7.py; base config from SP/oct11/base_edl.json; "src": your clip.mp4,
   "out": SP/batch/<id>/edit.mp4, "work": SP/batch/<id>/work, stems2 voice/game = your stems, words = your voice_words.json).
   Run it -> edl.json; run cam_bounds.py on it.
3b. Prep phase 2 = voice/game stems for ONLY the source ranges your shots use (merge shots closer than 2 s; Roformer costs ~11 s CPU
   per second of audio): `python3 SP/batch/prep_edit.py SP/batch/<id>/win.json SP/batch/<id> --sep "a-b,c-d,..."` (clip times).
   It also re-transcribes those ranges from the clean voice into voice_words.json: re-check your mutes/captions against it.
4. Render (queue on the lock!): `flock /tmp/hype_cpu.lock python3 SP/os/hype_edit.py SP/batch/<id>/edl.json > render.log 2>&1`
   (~8-10 min). Check the log for "0 words trimmed".
5. QA: `python3 -I SP/tools/edit_qa.py edit.mp4 work` (must be 0 fail) and
   `python3 SP/oct14/sheet.py edit.mp4 qa.jpg auto` then LOOK at qa.jpg (and a sheet at your key moments): framing inside the game,
   no overlay/balance bar leaks, captions readable, blurred cold open. Fix and re-render at most 2 more times; for audio-only fixes
   add `--audio-only` to the render command (reuses the picture).
6. Deliver:
   - name: "<YYYY-MM-DD> <Game> <amount, e.g. 4960> hype edit.mp4"; copy edit.mp4 to that name in your folder.
   - upload: `python3 -I SP/artifact-files/e859168a-e8f3-430f-9e98-7ba0494cd658/tools/drive_upload.py "<file>" "<name>"` (prints the
     file id), then move it into the "For review" folder with the Google Drive update_file tool: fileId = that id,
     parentId = 1hNx_qyumtB4paJxSHAkBNhAkcd3rhXeM. Never leave it in the 1001 Clips root.
   - picks page: ArtifactData get then update (with if_version) on url https://claude.ai/artifact/VmrEDckdntHVjxLSLUxYbY,
     collection "wins", doc_id = your id: {"status": "edited", "drive_id": <id>, "edit_name": <name>, "duration": s,
     "edit_note": "<one line: what's in it / anything Dylan should check>"}. Never change "pick". On failure: status "failed" + why.
7. Clean up: delete clip.mp4, mix.wav, stems/, work/, sheet/dense jpgs and edit.mp4 duplicates; keep mk.py, edl.json, notes.txt,
   render.log, qa.jpg and the named final mp4 (it is needed only until uploaded; delete it too once the upload is confirmed).
Reply with: name, duration, Drive file id, QA result, and anything Dylan should look at.
