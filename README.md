# dylangg-daily-videos

Daily DylanGG "Live Standings" leaderboard video, rendered by GitHub Actions and uploaded to the **1001 Clips** Google Drive folder as `YYYY-MM-DD.mp4`.

## How it runs

1. Each morning (8:24 AM Toronto) Claude reads dylanjames.gg, checks the numbers and pushes `data/YYYY-MM-DD.json`.
2. The push starts `.github/workflows/daily-video.yml`, which renders the 14 s 1920×1080 video with `kit/`, keeps it as a 7-day workflow artifact and uploads it to Drive (a same-named file is replaced, not duplicated).
   The background is `kit/assets/plate.mp4`, a 14 s cinematic footage plate made once with Higgsfield (Seedance 2.5): vault door, gold coin avalanche, marble board room, hourglass, spotlight stage. The live numbers are drawn on top each day; no AI generation runs daily. To replace the plate, import a new one with **Actions → Import template asset**.
3. Social HQ picks it up from 1001 Clips.

To render a past day again: **Actions → Daily leaderboard video → Run workflow**, enter the date.

## Settings (Settings → Secrets and variables → Actions)

| Name | Kind | Value |
| --- | --- | --- |
| `GDRIVE_CLIENT_ID` | secret | OAuth client ID (Google account that owns 1001 Clips) |
| `GDRIVE_CLIENT_SECRET` | secret | OAuth client secret |
| `GDRIVE_REFRESH_TOKEN` | secret | refresh token with scope `https://www.googleapis.com/auth/drive` |
| `GDRIVE_FOLDER_ID` | variable | `1waRIY_FHC3KJnmpEKEOgoLWfiL1d6xpT` |

The OAuth consent screen must be **In production**: in Testing, Google expires refresh tokens after 7 days.

## Data file

```json
{"date": "2026-10-09", "pool": 13053, "main": 11748, "raffle": 652, "multi": 652,
 "round": "01", "ends": "2026-10-15",
 "top": [["Inne****", 276431.57, 4111], ["Jame********", 108574.22, 1762]],
 "headline": ["INNE**** LEADS", "BY $168K"]}
```

`top` rows are `[name as shown on the site, wagered, prize]` in rank order (up to 5). Omit `round`/`ends` when the round dates aren't known. `kit/make_daily.py` refuses numbers that don't split 90/5/5 or aren't in rank order, so nothing wrong reaches Drive.

## Intro text (different every day)

`headline` is the intro's text: 1-2 lines, each at most 20 characters of A-Z 0-9 and `$,.!?'&+%*#:/-`. The morning run writes a new one from that day's numbers. `scripts/render_day.py` uses it when it's valid and hasn't appeared in the last 14 data files. Otherwise it builds one from the numbers: pool growth since the previous file, the leader's margin, a new #1, days left, #1 and #5 prizes, top-5 wagered, raffle/multi. It rotates by date and skips anything used recently. The intro animation also rotates by date (slam, typewriter, scramble, countdown). It drops back to the slam when the headline would clash, e.g. a pool total on a scramble day.


## Social HQ caption metadata

The uploader now also writes `YYYY-MM-DD.hq.json` into **1001 Clips**. It builds a short caption from the existing daily JSON (date, prize pool and displayed leader); Claude does not need to supply a social caption. The sidecar includes the verified Drive video ID and MD5, title, summary and source link. The caption itself omits links because the current X publishing connection does not support them.

The `caption` is one or two short lines, e.g. "And today’s leaderboard is… 👀" / "$13,972 in the pool.", picked from a rotation of about 35 openings (leaderboard check-ins, prize-pool updates, pool growth, occasional leader mentions):

- **Real numbers only.** Pool, leader and days left come from that day's file. It says the pool grew (and by how much) only when the pool is higher than the previous data file from the same round (same `round`, and `ends` doesn't differ). "Holding the top spot" / "new name at the top" compare with that same snapshot.
- **No repeats.** An opening isn't reused within 7 days. The history is rebuilt from the earlier files in `data/`, so it's only as complete as that folder. The kind of caption rotates by date and avoids yesterday's kind. No links or hashtags, at most one emoji, and a question at most once a week.
- **Tonight's stream** is mentioned only when the day's file has `"stream_tonight": true` (set it only when the schedule is confirmed), and never for an older video.
- **Older videos** (a past date re-run) use their own date instead of "today", and drop "days left".
- Reruns give the same caption.

HQ imports the sidecar during **Sync Drive** and offers it as a draft in **Queue → Edit post → Use this caption**. The owner still approves the caption and posting time. Uploading does not publish a social post. Reruns replace the matching MP4 and sidecar, reject duplicate Drive filenames, and verify the uploaded size and MD5. If the video uploads but the metadata step fails, the next sync can use a clearly marked basic draft; rerunning the uploader repairs the metadata.

Run uploader checks without credentials or external writes:

```sh
python -m unittest discover -s tests -v
```
