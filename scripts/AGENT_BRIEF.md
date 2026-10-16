# Win scan brief (Dylan / DylanJamesGG Kick slot streams)

Goal: list EVERY win in your assigned streams that is good enough for its own hype edit, with exact stream times and
confirmed amounts. You only scan and report: do not edit, render, upload, post or delete anything outside your own folders.

Tool: `python3 /tmp/claude-0/-home-user-dylangg-daily-videos/c57cb05e-857a-55e7-80f9-9455f18314fd/scratchpad/scan/scan_vod.py`
(run it with no args for usage). For each assigned DATE the folder `.../scratchpad/scan/DATE/` already holds:
- `sheet_NN.jpg`: contact sheets, one frame every 15 s, 48 per sheet, each stamped with stream time h:mm:ss (yellow, top left).
- `loud.txt`: loudest 10 s windows (he yells on big hits); `clips.txt`: chat clips; `vod.json`.

Stream layout (1920x1080): the slot game sits at x 38-1326, y 230-925; his webcam bottom right; the Bonus Hunt panel / chat on the right.
Streams are usually a $5,000 bonus hunt: he buys many bonuses, then opens them one after another. Big wins show full-screen
banners (BIG / MEGA / SUPER MEGA / EPIC / GODLIKE WIN, TOTAL WIN, Pragmatic "Congratulations you won", Nolimit "xWays"), so look for
banner frames, golden/flashy boards, and him reacting (hands up, standing).

Method per stream:
1. Read every sheet (use the Read tool on each jpg). Note each bonus opening (game name if readable) and every frame that looks like a
   big win banner or a big board.
2. For each candidate, confirm with 1080p: `scan_vod.py strip DATE T0 T1 out.jpg --step 1` (game-window strip, T as h:mm:ss) and/or
   `scan_vod.py frame DATE T out.jpg [--crop x,y,w,h]`. Read the game's own TOTAL WIN / win banner amount and the bet. Find:
   `bonus_start` (bonus intro / first spin), `hit` (the spin or moment that makes the win), `banner` (final total shown), `end`.
   Keep strips small (<= 40 frames each) and put them in `.../scratchpad/scan/DATE/confirm/`.
3. The Bonus Hunt panel (top right, ~x 1330-1920, y 0-230 and the list below it) lists each bonus and its payout once opened: a 1080p
   frame near the end of the opening phase is a fast cross-check that you found every big one. The panel can be wrong; the game's own
   amount wins.

What counts (report all of these): any single bonus or spin paying >= $1,000, or >= 100x the bet, or a genuinely great moment
(huge reaction, max-win, near-miss drama, a big blackjack hand). Also list $500-999 wins as `minor` so he can decide.

Output: write `.../scratchpad/scan/DATE/wins.json` for every assigned date (an empty list if nothing qualifies):
[{"date": "2026-10-07", "game": "Slayers Inc", "provider": "Hacksaw", "amount": 4049.00, "bet": 20.0, "multi": 202,
  "bonus_start": "1:02:10", "hit": "1:04:55", "banner": "1:05:30", "end": "1:05:40",
  "tier": "edit" | "minor", "confidence": "confirmed" | "likely", "evidence": "confirm/xyz.jpg",
  "notes": "VS game, 3 VS landed on the last spin; he stands up and yells"}]
Then reply with a compact table of all wins across your dates (date, game, amount, x, hit time, tier, confidence) and anything odd
(missing VOD, unreadable amounts). Be exact: never guess an amount you did not read; mark it "likely" and say why.
