# Team plan

Everyone owns different files, so nobody edits the same file at the same time.
That's what keeps GitHub merges painless. Need something changed in someone
else's file? Ask them in the group chat.

## Who does what

Updated 3:20pm Saturday. We're using the Emotiv Insight. The full task lists, with a prompt
for each person's own Claude chat, are in the shared plan doc.

| Who | Role | Laptop | Owns these files |
| --- | --- | --- | --- |
| Dhruvi | Headset (Emotiv) and demo laptop | Windows | `brain.py`, `detect.py` |
| Prachi | Recording and video | Mac, then the demo laptop | `run_session.py`, `cut.py`, `docs/obs-setup.md` |
| Sarrat | Design and GitHub | Mac | `web/` files |
| Tuline | Pitch and testing | Mac | `docs/pitch.md`, `docs/results-log.md`, `README.md` |

Demo command (demo laptop, Emotiv connected in EMOTIV Launcher, OBS open):

    python run_session.py --source emotiv --emotiv-id ID --emotiv-secret SECRET --obs-password PASS --player "Name" --game "Mario Kart"

Never commit the Emotiv Client ID or Secret.

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
