# OBS setup for Brainclip

## On any laptop
1. Install OBS from obsproject.com and open it.
2. Sources > + :
   - Mac: macOS Screen Capture, Method = Display Capture
   - Windows: Game Capture (fullscreen game) or Display Capture (windowed or browser game)
3. Tools > WebSocket Server Settings: tick Enable WebSocket server and
   Enable Authentication, port 4455. Show Connect Info > copy the password.
4. Settings > Output: Recording Format = MP4.
5. Mac only: System Settings > Privacy & Security > Screen & System Audio
   Recording > turn on OBS, then quit and reopen OBS. Otherwise it records black.
6. Windows only: if Display Capture shows black, go to Settings > System >
   Display > Graphics > OBS Studio > Options > Power saving, then reopen OBS.

## Optional overlay (while a session is running)
Sources > + > Browser
- URL: http://localhost:8765/overlay.html
- Width 500, Height 240
- Keep it above the screen capture in the Sources list.
- If blank: right-click > Refresh.

## Run a session (demo laptop, PowerShell)
python run_session.py --source emotiv --emotiv-id ID --emotiv-secret "SECRET" --obs-password "PASS" --player "Name" --game "Game"

- Put quotes around the secret and the password.
- The terminal should say "Emotiv scores arriving every 0.1 to 0.2 s".
- If the Windows Firewall asks about Python, allow Private networks.

## Tested
- Prachi's Mac, fake data: OBS recorded, 3 clips cut, video_offset_s = -0.215 s
- Demo laptop (Dhruvi's Windows), Emotiv Insight: scores every 0.12 s, OBS recorded and saved
- Demo laptop timing test (Emotiv, jaw clench + pause): clips lined up with the
  pause screen, no noticeable offset. Timing is good.
