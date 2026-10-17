# dylangg-daily-videos

Daily DylanGG "Live Standings" leaderboard video, uploaded to the **1001 Clips** Google Drive folder as `YYYY-MM-DD.mp4` with its Social HQ caption metadata `YYYY-MM-DD.hq.json`.

## How it runs

1. Each morning (8:24 AM Toronto) the **Daily Live Standings Video (to Drive)** routine reads dylanjames.gg, checks the numbers and writes `data/YYYY-MM-DD.json`.
2. It renders the 14 s 1920×1080 video with `scripts/render_day.py` (`kit/`).
   The background is drawn in code and rotates with the date (`--world auto` in `kit/make_daily.py`, worlds in `kit/standings.js`):
   **coin storm** (a giant turning coin behind the headline, coins raining at the camera into the pool slam, a coin fountain on the end
   card), **reel wall** (giant slot reels that land $ $ $ on the pool slam) and **vault** (tumbler rings that lock on the slam and open
   into a ring tunnel). The date also varies directions and layouts, so no two days look the same. (Until 2026-10-17 it was one
   Higgsfield footage plate, `kit/assets/plate.mp4`, every day; `--world plate` still uses it.)
   The video opens with 1-2 s of a viral fail clip cut on its impact (`scripts/viral_intro.py`).
3. `scripts/drive_hq_upload.py` uploads the video and its caption metadata to 1001 Clips through Dylan's Apps Script uploader (below). Nothing is pushed to GitHub.
4. Social HQ picks both up from 1001 Clips.

## Drive uploader (Apps Script)

`scripts/drive_uploader.gs` is the web app in Dylan's **1001 Clips Uploader** Apps Script project. It runs as Dylan, so the session never holds Google credentials: it only needs `HYPE_UPLOAD_KEY` (the same value as the Script Property `Hype_upload_key`) in the Hypeedit environment.

```sh
python scripts/drive_hq_upload.py pull-history data/                       # before writing the headline
python scripts/drive_hq_upload.py upload OUT/2026-10-14.mp4 data/2026-10-14.json
python scripts/drive_hq_upload.py metadata data/2026-10-13.json            # caption metadata for a video already in Drive
```

- `upload` sends the MP4, then `YYYY-MM-DD.hq.json` carrying that upload's Drive ID and MD5, then saves the day's numbers in the uploader's history. If the video went up but the metadata didn't, rerun with `--video-id <Drive ID>` to add only the metadata.
- The uploader keeps the last 45 days of numbers and headlines (Script Properties), which is the history the headline and caption rules use now that nothing is pushed here. `pull-history` copies them into `data/` without overwriting files already there.
- With the current script, a rerun replaces the same-named file instead of making a duplicate (it refuses if 1001 Clips already holds two files with that name), and Drive's own MD5 is checked against the local file.
- The previous deployment accepts videos only. With it, `upload` sends the video, then stops and names the `--video-id` to rerun with once this script is deployed; `metadata` stops with "needs the updated uploader script".

To update the web app: paste `scripts/drive_uploader.gs` over the project's code, save, then **Deploy → Manage deployments → edit → Version: New version → Deploy**. The `/exec` URL and the saved key stay the same.

## GitHub Actions (not in use)

`.github/workflows/daily-video.yml` can render and upload a day from a push to `data/` on `main`, or from **Actions → Daily leaderboard video → Run workflow**. It needs the settings below, which aren't set; the routine above doesn't use it.

| Name | Kind | Value |
| --- | --- | --- |
| `GDRIVE_CLIENT_ID` | secret | OAuth client ID (Google account that owns 1001 Clips) |
| `GDRIVE_CLIENT_SECRET` | secret | OAuth client secret |
| `GDRIVE_REFRESH_TOKEN` | secret | refresh token with scope `https://www.googleapis.com/auth/drive` |
| `GDRIVE_FOLDER_ID` | variable | `1waRIY_FHC3KJnmpEKEOgoLWfiL1d6xpT` |

The OAuth consent screen must be **In production**: in Testing, Google expires refresh tokens after 7 days. To replace the footage plate, import a new one with **Actions → Import template asset**.

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

Every daily upload also writes `YYYY-MM-DD.hq.json` into **1001 Clips** (`scripts/drive_hq_upload.py`, or `scripts/upload_drive.py` in the GitHub workflow). It builds a short caption from the existing daily JSON (date, prize pool and displayed leader); Claude does not need to supply a social caption. The sidecar includes the verified Drive video ID and MD5, title, summary and source link. The caption itself omits links because the current X publishing connection does not support them.

The `caption` is one or two short lines, e.g. "And today’s leaderboard is… 👀" / "$13,972 in the pool.", picked from a rotation of about 35 openings (leaderboard check-ins, prize-pool updates, pool growth, occasional leader mentions):

- **Real numbers only.** Pool, leader and days left come from that day's file. It says the pool grew (and by how much) only when the pool is higher than the previous data file from the same round (same `round`, and `ends` doesn't differ). "Holding the top spot" / "new name at the top" compare with that same snapshot.
- **No repeats.** An opening isn't reused within 7 days. The history is rebuilt from the earlier files in `data/`, which `pull-history` fills from the uploader's 45-day store. The kind of caption rotates by date and avoids yesterday's kind. No links or hashtags, at most one emoji, and a question at most once a week.
- **Tonight's stream** is mentioned only when the day's file has `"stream_tonight": true` (set it only when the schedule is confirmed), and never for an older video.
- **Older videos** (a past date re-run) use their own date instead of "today", and drop "days left".
- Reruns give the same caption.

HQ imports the sidecar during **Sync Drive** and offers it as a draft in **Queue → Edit post → Use this caption**. The owner still approves the caption and posting time. Uploading does not publish a social post. Reruns replace the matching MP4 and sidecar, reject duplicate Drive filenames, and verify the uploaded size and MD5. If the video uploads but the metadata step fails, the next sync can use a clearly marked basic draft; rerunning the uploader repairs the metadata.

Run uploader checks without credentials or external writes:

```sh
python -m unittest discover -s tests -v
```
