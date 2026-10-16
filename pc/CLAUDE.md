# Dylan's hype-edit workstation (Windows, RTX 2070 Super)

You make hype edits of DylanJamesGG's Kick slot stream wins. The full house style, engine notes and tools are in the
"Hype Edit Pack" artifact (manifest notes: LOCKED_STYLE_v4, mask_captions, swing_moves, voice_real_speed, vs_slots, endings,
finals_only, overnight_pc). Read the manifest notes first, every session. Pull tools with Artifact read (path tools/...) into .\pack\tools.

## Overnight / unattended runs
- Dylan is asleep: never stop to ask. Make a sensible call, write it in the edit's notes.txt, keep going.
- Queue: the "Stream Win Picks" artifact (https://claude.ai/artifact/VmrEDckdntHVjxLSLUxYbY), collection `wins`: every doc with
  pick == true and status == "new", biggest amount first. Times there are TRUE stream times; cut the clip with
  `python scripts/scan_vod.py clip DATE T0 T1 clip.mp4` (bonus_start - 20 s to end + 10 s). Set status "editing" when you start,
  "edited" when the cut is on the review page (or "failed" + a note). Never touch `pick` (that's Dylan's).
- One edit at a time on the GPU. Per edit: pull 1080p60 segments for the window -> clip.mp4, make_stems2.py (voice/game
  separation, CUDA), transcribe.py on the voice stem -> voice_words.json, write mk_<name>.py from example_edl_slayers_v7.py,
  run hype_edit.py (NVENC + parallel parts are automatic), then QA: edit_qa.py, clicks.py, cam_bounds.py, and a frame sheet.
  Fix and re-render until QA passes (max 3 rounds; then keep the best and note what's wrong).
- Output: .\out\<stream date>\<game> <win> hype edit.mp4 + notes.txt (shots, choices, QA results) + sheet.jpg.
  Add each one to the Hype Edit Review page (manifest note review_page) so Dylan can watch them in the morning.
- NEVER upload to the 1001 Clips Drive folder overnight: only finals Dylan signs off go there (finals_only).
- Append each finished edit to .\out\done.json so a restart doesn't redo it. Delete .\vods segment caches after each edit.

## Nightly run (9 pm, after the stream)
1. `python scripts/scan_vod.py list` -> scan any stream not in .\out\scanned.json with `scan_vod.py sheets` and read every sheet
   (method in scripts/AGENT_BRIEF.md); confirm amounts at 1080p; add each win to the picks page `wins` collection
   (pick = true for >= $1,000 or >= 150x and >= $500, status "new").
2. Then work the queue above until it's empty or it's 8 am.
