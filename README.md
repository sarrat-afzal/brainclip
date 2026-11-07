# Brainclip

Highlight reels cut by your brain. Wear the headset, play, and Brainclip clips
the moments your excitement or focus spiked above your own baseline.

## Setup

Everyone (Mac and Windows):

    pip install -r requirements.txt

FFmpeg: Mac `brew install ffmpeg`, Windows `winget install ffmpeg` (reopen the terminal after).

Windows laptop only (this is the headset and demo machine):

1. Plug in the Unicorn USB dongle and pair the headset through it, not built-in Bluetooth.
2. Check signal quality in g.tec's Unicorn Suite, then close it (only one program can hold the headset).
3. Install OBS. In OBS: Tools > WebSocket Server Settings > Enable, note the password.
   Set up a Display Capture or Game Capture source for the game.

The Unicorn does not run on Mac. Mac teammates build with fake data, or use the Emotiv.

Emotiv (Mac or Windows):

1. Install EMOTIV Launcher, log in, connect the headset there.
2. emotiv.com > My Account > Cortex Apps > register an app, copy the Client ID and Secret.
3. Run:

       python run_session.py --source emotiv --emotiv-id ID --emotiv-secret SECRET --obs-password YOURPASS

4. Approve the request that pops up in the Launcher the first time.
5. By default this uses Emotiv's band power stream (about 8 updates a second, no license needed)
   and runs the same excitement/focus formulas as the Unicorn. The terminal prints how often data arrives.
   `--emotiv-stream met` uses Emotiv's own Excitement/Focus scores instead, but without a
   license those only update every 10 seconds, which is too slow for clipping.

## Run a session

Demo machine (Windows, real headset, OBS open):

    python run_session.py --source unicorn --obs-password YOURPASS --player "Name" --game "Mario Kart"

Any laptop, no headset, no OBS (fake brain data, 3 minutes at 4x speed):

    python run_session.py --source fake --no-obs --fake-minutes 3 --fake-speed 4

Fake brain data on top of any gameplay video you already have:

    python run_session.py --source fake --video my_gameplay.mp4 --fake-minutes 5 --fake-speed 50 --no-live

What happens:
1. A live graph opens in the browser (put it on a second screen for the room).
2. First 60 seconds = warm-up. Player plays casually; nothing in it gets clipped.
3. Then play. Press Ctrl+C in the terminal to end.
4. Clips get cut and the results page opens.

Every session is saved in `sessions/<date_time>/`.

## Tuning (headset person)

Re-run detection on a saved session without replaying:

    python report.py sessions/2026-11-07_143000 --hype-z 1.8 --focus-z 1.3

Lower numbers = more clips. Defaults and the rest of the settings are at the top of `detect.py`.
Add `--vertical` for 9:16 clips for TikTok/Shorts.

## Files

| File | What it does | Owner |
| --- | --- | --- |
| brain.py | Reads the Unicorn (or fake data), turns raw EEG into excitement and focus scores | Headset |
| detect.py | Compares to baseline, finds Hype and Locked in moments | Headset |
| run_session.py | Runs a session: OBS, headset, live graph, then the reel | Video |
| cut.py | FFmpeg cutting and joining | Video |
| report.py | Builds the results page from a session folder | Results page |
| web/results.html | The results page | Results page |
| web/live.html | Live brain graph during play | Results page |

## How the scores work

From 2 second windows of raw EEG, updated every half second, after filtering 1 to 45 Hz and removing 60 Hz mains hum:

- Focus = beta / (alpha + theta) on Fz, C3, Cz, C4 (the "engagement index", Pope et al. 1995)
- Excitement = (beta + gamma) / alpha across all 8 sensors

Each moment is compared to that player's own previous minute (a rolling baseline), so only
sudden changes count, and a player who slowly gets more into the game doesn't trigger clips nonstop.
These are signal features, not proof of an emotion. Pitch them as "unusual brain activity for you"
and show the player-picked-favorites test (below) as evidence.

## Proving it works (do this before the final demo)

Run 3 short sessions. After each one, before showing the reel, the player writes down the times
of their 3 favorite moments. Then count how many of those are in Brainclip's clips.
Put that number on a slide. Real numbers beat claims.
