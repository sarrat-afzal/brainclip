# Team plan

Everyone owns different files, so nobody edits the same file at the same time.
That's what keeps GitHub merges painless. Need something changed in someone
else's file? Ask them in the group chat.

## Who does what

| # | Who | Role | Laptop | Owns these files | Done when |
| --- | --- | --- | --- | --- | --- |
| 1 | Dhruvi | Headset | Windows (Unicorn) | `brain.py`, `detect.py` | Real brain data streams and the clips match moments the player agrees with |
| 2 | Prachi | Recording and video | Mac, then the Windows demo laptop | `run_session.py`, `cut.py`, `docs/obs-setup.md` | OBS records the game, timing is checked, vertical export works |
| 3 | Sarrat | Design | Mac | `web/results.html`, `web/live.html`, `web/overlay.html` | Both pages look great on the projector and there's a streamer overlay |
| 4 | Tuline | Pitch and testing | Mac (Emotiv) | `docs/pitch.md`, `docs/results-log.md`, `README.md` | Slides done, favorites test run 3 times, demo rehearsed twice |

### 1. Headset: Dhruvi (Windows)

1. Pair the Unicorn through its USB dongle, check signal quality in g.tec's Unicorn Suite, then close it.
2. `python run_session.py --source unicorn --no-obs --player "Your name"` and play something for 3 to 5 minutes.
3. If it errors, paste the error into Claude with `brain.py`.
4. Open the results page. Did the clips match moments you felt? Tune with
   `python report.py sessions/<folder> --hype-z 1.8` (lower = more clips) until they do.
5. Once you have good values, change the defaults at the top of `detect.py` and push.

### 2. Recording and video: Prachi

1. On your Mac: install OBS, add a Display Capture source, turn on Tools > WebSocket Server Settings.
2. `python run_session.py --source fake --obs-password YOURPASS --fake-minutes 3` and play anything. Check a reel comes out.
3. Timing test: during a session, clench your jaw hard for 3 seconds right as something obvious happens on screen.
   Jaw clenches show up as a big spike. Check the clip lands on that moment. Write down how far off it is.
4. Write the OBS setup steps in `docs/obs-setup.md`, then set up OBS on the Windows demo laptop the same way.
5. Test `--vertical` clips for TikTok/Shorts.

### 3. Design: Sarrat

1. `python run_session.py --source fake --no-obs --fake-minutes 3 --fake-speed 4` gives you pages to work on.
2. Polish `web/results.html` (the reel page judges see) and `web/live.html` (the live screen during play).
   Aesthetics is a judging criterion.
3. Make `web/overlay.html`: a small transparent version of the live graph for an OBS Browser Source,
   so a streamer could show their brain live on stream. It's a quick, flashy extra.
4. Test both pages on a projector-sized screen.

### 4. Pitch and testing: Tuline (Mac + Emotiv)

1. Get the Emotiv working on your Mac (README > Emotiv). This is the backup headset.
2. Run the favorites test 3 times (README > Proving it works). Log results in `docs/results-log.md`.
3. Find one clip where nothing obvious happens on screen but the player still reacted. That's the "why do you need a headset" moment.
4. Write the pitch in `docs/pitch.md` and build the slides. Use "unusual brain activity for you", not "we read emotions".
5. Run the demo twice from start to finish before 8pm.

## GitHub workflow

First time (everyone):

    git clone https://github.com/OWNER/brainclip.git
    cd brainclip
    pip install -r requirements.txt

Every time you start working:

    git checkout main
    git pull
    git checkout -b yourname-what-youre-doing     # e.g. sarrat-results-polish

Every time something works (aim for at least once an hour):

    git add .
    git commit -m "What you changed, in plain words"
    git push -u origin yourname-what-youre-doing

Then on github.com, click "Compare & pull request", then "Merge pull request".
If it says there are conflicts, ask the owner of that file.

Rules:
- Only edit your own files.
- Never commit videos or session folders. `.gitignore` already blocks them.
- Pull main before starting anything new.
- At 8pm, nobody merges anything without telling the group.

## Getting help

Everyone has the shared Claude chat. Open it, continue the conversation, and start your message
with your role, e.g. "I'm #3 Design. The reel page won't load the clips: (paste the error)".
Paste the full error text and the file you were editing; Claude can't see your laptop.
