# dylangg-daily-videos

Daily DylanGG "Live Standings" leaderboard video, rendered by GitHub Actions and uploaded to the **1001 Clips** Google Drive folder as `YYYY-MM-DD.mp4`.

## How it runs

1. Each morning (8:24 AM Toronto) Claude reads dylanjames.gg, checks the numbers and pushes `data/YYYY-MM-DD.json`.
2. The push starts `.github/workflows/daily-video.yml`, which renders the 14 s 1920×1080 video with `kit/`, keeps it as a 7-day workflow artifact and uploads it to Drive (a same-named file is replaced, not duplicated).
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
 "top": [["Inne****", 276431.57, 4111], ["Jame********", 108574.22, 1762]]}
```

`top` rows are `[name as shown on the site, wagered, prize]` in rank order (up to 5). Omit `round`/`ends` when the round dates aren't known. `kit/make_daily.py` refuses numbers that don't split 90/5/5 or aren't in rank order, so nothing wrong reaches Drive.
