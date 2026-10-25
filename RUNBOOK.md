# Daily cricket Short — runbook

Faceless YouTube channel (Ku Mama, @KuMama-f4b). One vertical cricket Short per day, English, posted 9:00 AM IST via Metricool.

## Steps

1. **Research** the last 24 hours of cricket (IST):
   - `fetch_sports_data` with league `cricket`, `data_type: scores`, then `game_stats` for the 2–3 biggest matches.
   - Pick 3 stories. Priority: India men/women, other full-member internationals, major leagues (IPL, BBL, WBBL, PSL, The Hundred, CPL, SA20), then remarkable associate results (record lows, huge totals, hat-tricks).
   - Add one `live` card for big matches happening today, if any.
   - Every number on screen must come from Sportradar data or be confirmed by a reliable outlet (ESPNcricinfo, ICC, BBC, Reuters). If unsure, leave it out.
2. **Write** `stories/YYYY-MM-DD.json` (see `stories/2026-10-25.json`). Scene types:
   - `chase` — scoreboard counting the winning chase (`teams`, `runs`, `wickets`, `sub`)
   - `collapse` — stumps hit, "N ALL OUT" (`teams`, `runs`)
   - `bigtotal` — bat swing, big total (`teams`, `runs`, `wickets`)
   - `star` — player milestone ring (`big`, e.g. "112*" or "5/12")
   - `live` — today's matches (`matches`: [[title, subtitle], ...], max 3)
   - All story scenes: `tag` (uppercase), `color` (blue/red/green/gold), `headline` (2 lines, max ~20 chars each), `details` (1–3 lines, max ~34 chars), optional `headline_size` (default 84; use 76 for long lines).
   - Team codes with flag colours are in `FLAGS` in `tools/make_short.py`; unknown codes get grey.
3. **Render**:
   ```
   python3 tools/make_short.py /tmp/v.mp4 stories/DATE.json        # prints duration
   python3 tools/make_music.py <duration> /tmp/m.wav
   ffmpeg -y -i /tmp/v.mp4 -i /tmp/m.wav -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart shorts/cricket_short_DATE.mp4
   ```
   Grab 4 frames with ffmpeg and look at them: no text overflowing the panel or screen edges.
4. **Publish** to GitHub: commit `stories/DATE.json` and `shorts/cricket_short_DATE.mp4`, push to `main`. Check
   `https://raw.githubusercontent.com/Kunal130799/ku-cricket-videos/main/shorts/cricket_short_DATE.mp4` returns 200.
5. **Schedule** with Metricool `createScheduledPost`: blogId `7641985`, network `youtube`, `youtubeData.type: "short"`, privacy public, category SPORTS, `madeForKids: false`, `isAiGeneratedContent: false`, timezone `Asia/Calcutta`, 09:00 the same day. Title under 100 chars ending with `#shorts`; description summarising the 3 stories + a comment question + 4–6 hashtags.

## Rules
- No channel name on screen. No real photos, logos or broadcast footage — only the drawn visuals in the script.
- Never invent scores, names or stats.
- If no worthwhile international/major-league cricket happened, still post using the best available results; never skip silently — report what was done.
