"""Run one Brainclip session: record, read the brain, then build the reel.

Windows laptop with the Unicorn and OBS open:
    python run_session.py --source unicorn --obs-password YOURPASS --player "Judge Name"

Mac, no headset, no OBS (fake brain data, 3 minutes, 4x speed):
    python run_session.py --source fake --no-obs --fake-minutes 3 --fake-speed 4

Press Ctrl+C to end the session. The first 60 seconds are a warm-up:
the player plays casually; it is never clipped.
"""

import argparse
import datetime
import functools
import http.server
import json
import os
import shutil
import threading
import time
import webbrowser

import report

HERE = os.path.dirname(os.path.abspath(__file__))


def start_live_page(session_dir, port):
    """Serve the live brain graph at http://localhost:<port>/live.html"""
    for page in ("live.html", "overlay.html"):
        shutil.copy(os.path.join(HERE, "web", page), os.path.join(session_dir, page))

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

    handler = functools.partial(Quiet, directory=session_dir)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://localhost:{port}/live.html"
    print(f"Live graph: {url}")
    print(f"OBS overlay (Browser Source, 500x230): http://localhost:{port}/overlay.html")
    webbrowser.open(url)
    return server


class OBS:
    def __init__(self, host, port, password):
        import obsws_python as obs
        self.client = obs.ReqClient(host=host, port=port, password=password, timeout=5)

    def start(self):
        self.client.start_record()
        for _ in range(100):
            if self.client.get_record_status().output_active:
                return time.time()
            time.sleep(0.05)
        raise SystemExit("OBS did not start recording. Check OBS is open and not already recording.")

    def stop(self):
        resp = self.client.stop_record()
        path = getattr(resp, "output_path", None)
        time.sleep(1.5)  # let OBS finish writing the file
        return path


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", choices=["unicorn", "emotiv", "fake"], default="fake")
    ap.add_argument("--serial", default="", help="Unicorn serial number if several are nearby")
    ap.add_argument("--emotiv-id", default=os.environ.get("EMOTIV_CLIENT_ID", ""),
                    help="Cortex app Client ID (or set EMOTIV_CLIENT_ID)")
    ap.add_argument("--emotiv-secret", default=os.environ.get("EMOTIV_CLIENT_SECRET", ""),
                    help="Cortex app Client Secret (or set EMOTIV_CLIENT_SECRET)")
    ap.add_argument("--emotiv-stream", choices=["pow", "met"], default="pow",
                    help="pow = band power 8x/s, no license (default); met = Emotiv's scores")
    ap.add_argument("--player", default="Player")
    ap.add_argument("--game", default="")
    ap.add_argument("--no-obs", action="store_true", help="don't control OBS")
    ap.add_argument("--video", help="use this video file instead of an OBS recording")
    ap.add_argument("--obs-host", default="localhost")
    ap.add_argument("--obs-port", type=int, default=4455)
    ap.add_argument("--obs-password", default="")
    ap.add_argument("--fake-minutes", type=float, default=0, help="stop fake sessions automatically")
    ap.add_argument("--fake-speed", type=float, default=1.0)
    ap.add_argument("--port", type=int, default=8765, help="live graph port")
    ap.add_argument("--no-live", action="store_true")
    ap.add_argument("--vertical", action="store_true")
    a = ap.parse_args()

    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    session_dir = os.path.join(HERE, "sessions", stamp)
    os.makedirs(session_dir)
    brain_path = os.path.join(session_dir, "brain.jsonl")
    open(brain_path, "w").close()

    if a.source == "unicorn":
        from brain import UnicornSource
        source = UnicornSource(serial_number=a.serial)
    elif a.source == "emotiv":
        if not (a.emotiv_id and a.emotiv_secret):
            raise SystemExit("Emotiv needs --emotiv-id and --emotiv-secret from your Cortex app.")
        from brain import EmotivSource
        source = EmotivSource(a.emotiv_id, a.emotiv_secret, stream=a.emotiv_stream)
    else:
        from brain import FakeSource
        source = FakeSource(speed=a.fake_speed)

    if not a.no_live:
        start_live_page(session_dir, a.port)

    obs = None if (a.no_obs or a.video) else OBS(a.obs_host, a.obs_port, a.obs_password)

    print("Connecting to the brain source...")
    source.start()
    brain_t0 = source.t0
    video_offset = 0.0
    if obs:
        rec_t0 = obs.start()
        # brain readings say "seconds since brain start"; shift them onto video time
        video_offset = round(brain_t0 - rec_t0, 3)
        print("OBS recording.")

    print("Session running. First 60 seconds = warm-up (play casually, never clipped). Ctrl+C to stop.")
    limit = a.fake_minutes * 60 if a.source == "fake" and a.fake_minutes else None
    try:
        with open(brain_path, "a") as f:
            while True:
                r = source.read()
                if r is None:
                    continue
                f.write(json.dumps(r) + "\n")
                f.flush()
                if limit and r["t"] >= limit:
                    break
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        source.stop()

    video = a.video
    if obs:
        video = obs.stop()
        print(f"Recording saved: {video}")

    meta = {"player": a.player, "game": a.game, "source": a.source,
            "video": os.path.abspath(video) if video else None,
            "video_offset_s": video_offset, "started": stamp}
    with open(os.path.join(session_dir, "session.json"), "w") as f:
        json.dump(meta, f, indent=2)

    page = report.build(session_dir, vertical=a.vertical)
    webbrowser.open("file://" + page)


if __name__ == "__main__":
    main()