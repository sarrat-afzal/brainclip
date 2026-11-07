"""Find moments, cut clips and build the results page for one session folder.

Run on its own to re-tune an old session without replaying:
    python report.py sessions/2026-11-07_1430 --hype-z 1.8
"""

import argparse
import json
import os
import shutil

from detect import find_moments, SETTINGS
from cut import cut_clips, video_length

HERE = os.path.dirname(os.path.abspath(__file__))


def load_readings(session_dir):
    path = os.path.join(session_dir, "brain.jsonl")
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def build(session_dir, video=None, settings=None, vertical=False, cut=True):
    meta_path = os.path.join(session_dir, "session.json")
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)
    video = video or meta.get("video")
    offset = float(meta.get("video_offset_s", 0))

    readings = load_readings(session_dir)
    # brain time -> video time
    for r in readings:
        r["t"] = round(r["t"] + offset, 3)

    length = video_length(video) if video and os.path.exists(video) else None
    moments, baseline, zs = find_moments(readings, length, settings)
    print(f"Found {len(moments)} moments")
    for m in moments:
        print(f"  #{m['id']} {m['label']:<9} {m['clip_start']:7.1f}s to "
              f"{m['clip_end']:7.1f}s  strength {m['peak_z']}")

    out_dir = os.path.join(session_dir, "results")
    os.makedirs(out_dir, exist_ok=True)
    if cut and video and moments:
        cut_clips(video, moments, out_dir, vertical=vertical)
    elif not video:
        print("No video given, so no clips were cut. The page will show the graph only.")

    data = {
        "player": meta.get("player", "Player"),
        "game": meta.get("game", ""),
        "duration": readings[-1]["t"] if readings else 0,
        "baseline_s": (settings or {}).get("baseline_s", SETTINGS["baseline_s"]) + offset,
        "baseline": baseline,
        "moments": moments,
        # [time, excitement z, focus z]: the exact numbers detection used
        "readings": [[r["t"], round(float(zs["excitement"][i]), 3) if zs else 0,
                      round(float(zs["focus"][i]), 3) if zs else 0]
                     for i, r in enumerate(readings)],
        "has_reel": os.path.exists(os.path.join(out_dir, "reel.mp4")),
    }
    with open(os.path.join(out_dir, "data.js"), "w") as f:
        f.write("window.BRAINCLIP = " + json.dumps(data) + ";\n")
    shutil.copy(os.path.join(HERE, "web", "results.html"), os.path.join(out_dir, "index.html"))
    page = os.path.abspath(os.path.join(out_dir, "index.html"))
    print(f"Results page: {page}")
    return page


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("session_dir")
    ap.add_argument("--video", help="override the recording path")
    ap.add_argument("--hype-z", type=float, help=f"default {SETTINGS['hype_z']}")
    ap.add_argument("--focus-z", type=float, help=f"default {SETTINGS['focus_z']}")
    ap.add_argument("--max-moments", type=int, help=f"default {SETTINGS['max_moments']}")
    ap.add_argument("--vertical", action="store_true", help="9:16 clips for TikTok/Shorts")
    ap.add_argument("--no-cut", action="store_true", help="skip FFmpeg, just rebuild the page")
    a = ap.parse_args()
    s = {}
    if a.hype_z is not None:
        s["hype_z"] = a.hype_z
    if a.focus_z is not None:
        s["focus_z"] = a.focus_z
    if a.max_moments is not None:
        s["max_moments"] = a.max_moments
    build(a.session_dir, a.video, s, a.vertical, cut=not a.no_cut)
