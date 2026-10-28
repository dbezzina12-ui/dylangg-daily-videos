# Instagram backfill (Dylan, 2026-10-28: "I want all my older edits to have the Instagram edits")

Make the 9:16 **ghost** version of each of Dylan's older hype edits. The cloud session is doing its own 17; the PC does the 24 in `pc.json`
(the edits it made itself, so their mk/EDL, voice_words and notes are on the PC).

Per edit, one at a time on the GPU, biggest amount first:
1. Find the edit's working folder from the original PC edit (EDL or mk script, voice_words.json, notes). If clip.mp4 or the stems are gone,
   re-cut the clip with `python scripts/scan_vod.py clip DATE T0 T1 clip.mp4` using the SAME T0/T1 as before and rebuild the stems the same
   way, so the cut matches the X edit.
2. Render the 9:16 only, from the same EDL with nothing else changed: add `"formats": ["ig"]`, `"ig_layout": "ghost"`,
   `"ig_banner": "<pack>/tools/ig_banner.png"` and point `out`/`work` at fresh files so the X edit isn't overwritten. Engine:
   `scripts/hype_edit.py` from this branch (git pull first; it has the ghost layout). Ghost automatically drops the pop-up and its line.
   If the EDL still has an announcer voice-over (`extra_sfx` vo.wav), drop it.
3. QA: `scripts/edit_qa.py` on the `_ig.mp4` (0 fail) and look at a contact sheet: the slot screen fills the middle, the big tilted webcam
   card swings in above it on reactions, face shots are a tall panel, the banner sits under the picture.
4. Upload: `python scripts/drive_upload.py "<file>" "<ig_name from pc.json>"` (prints the Drive id). If you have the Google Drive tool, move it
   into the Instagram folder `1PSRixosvIwcbG4XWsRG4etk83LuzeoFA` (update_file parentId). Never print or store HYPE_UPLOAD_KEY.
5. Record it: append `{"id": ..., "ig_drive_id": ..., "duration": ...}` to `queue/ig_backfill/done_pc.json`, commit and push to
   `claude/happy-gates-mejqvx` after each edit (the cloud session moves anything left in the 1001 Clips root and updates the picks page).
   If an edit can't be rebuilt, add `{"id": ..., "failed": "<why>"}` instead and move on.
6. Delete the clip/stems/work for that edit once it's uploaded (disk).

Dylan is asleep: don't stop to ask, make a sensible call and note it.
