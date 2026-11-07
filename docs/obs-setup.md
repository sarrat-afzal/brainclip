# OBS setup for Brainclip

## On any laptop
1. Install OBS from obsproject.com and open it.
2. Sources > + :
   - Mac: macOS Screen Capture, Method = Display Capture
   - Windows: Game Capture (fullscreen game) or Display Capture (windowed game)
3. Tools > WebSocket Server Settings: tick Enable WebSocket server and
   Enable Authentication, port 4455. Show Connect Info > copy the password.
4. Settings > Output: Recording Format = MP4.
5. Mac only: System Settings > Privacy & Security > Screen & System Audio
   Recording > turn on OBS, then quit and reopen OBS. Otherwise it records black.

## Optional overlay (while a session is running)
Sources > + > Browser
- URL: http://localhost:8765/overlay.html
- Width 500, Height 240
- Keep it above the screen capture in the Sources list.
- If blank: right-click > Refresh.

## Run a session
python run_session.py --source emotiv --emotiv-id ID --emotiv-secret SECRET --obs-password "PASS" --player "Name" --game "Game"

## Tested
- Prachi's Mac, fake data: OBS recorded, 3 clips cut, video_offset_s = -0.215 s
- Demo laptop timing test: (fill in after Step C)