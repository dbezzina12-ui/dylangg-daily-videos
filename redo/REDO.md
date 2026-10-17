# Full-voice redo (Dylan, 2026-10-17)

Dylan: "don't cut off their talking at all... even if I'm repeating myself play my whole voice clip", then: "during whatever clip
is happening it should have the voice still active... if the voice is there for the whole clip it doesn't [sound terrible]. If we
need to fade it out we can also do that." The engine (scripts/hype_edit.py, `git pull` first) now plays his voice LIVE: continuous
at 1.0x through every shot, in sync with the picture, fading out under the next shot at a cut (scripts/batch/EDIT_BRIEF.md rule 3).
It ignores "mute" lists. scripts/edit_qa.py only reports repeats as INFO. Slowed game audio is varispeed (no flanging).

Redo every edit in redo_list.json "pc_redo" with the SAME cut (same shots, camera, captions, popups/voice-over), only the voice changes,
plus his REACTION on the big hits (tilted picture-in-picture, scripts/batch/EDIT_BRIEF.md rule 0, Dylan 2026-10-17):
- Picks page: https://claude.ai/artifact/VmrEDckdntHVjxLSLUxYbY, collection "wins". Each redo doc has status "redo" and editor "pc".
  Set status "editing" when you start one, "edited" when the new file is delivered (keep drive_id / edit_name updated).
- Your own edits: reuse your out\ / work files and EDLs. Cloud-made edits (listed in "cloud_files_in_repo"): their mk.py, edl.json,
  voice_words*.json (hand-corrected timings: keep them), prep.json (T0 = stream time of clip time 0, keep it so the EDL's source
  times still line up), notes.txt and vo.wav (other-streamer voice-overs) are in redo/<id>/. Their paths point at the cloud's
  scratchpad: rewrite src / stems / words / sfx_dir / popups / font paths to this PC's files. Other-streamer ids start with the
  streamer's Kick slug (xposed_...): fetch their clip with KICK_CHANNEL=<slug>; see scripts/batch/OTHERS_EDIT.md.
- Re-prep each clip (same window as prep.json; stem separation on the shot ranges), delete every "mute" list from the EDL (the engine
  ignores them anyway), render, run edit_qa (0 fail) and look at the QA sheet. If his last line is cut by the end of the edit,
  lengthen the last shot a little so it finishes.
  Listen to the QA cuts: what he says in each shot is now exactly what he said at that moment of the stream, so if a shot
  carries off-topic chat (a plug, a long side story) over the big moment, move that shot's start/end a little rather than mute it.
- Same file name as before. Upload and replace the old Drive file (For review: 1hNx_qyumtB4paJxSHAkBNhAkcd3rhXeM; Other streamers:
  163AljHBEEjf_o019WU3Adj6uwba40XeS) once HYPE_UPLOAD_KEY is set; until then keep the files in out\redo\ and note
  "Drive upload pending" on the doc. Biggest wins first.
