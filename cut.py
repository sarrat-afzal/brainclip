"""Cut moments out of the recording with FFmpeg and join them into one reel."""

import json
import os
import shutil
import subprocess


def _ffmpeg():
    exe = shutil.which("ffmpeg")
    if not exe:
        raise SystemExit("FFmpeg not found. Mac: brew install ffmpeg. "
                         "Windows: winget install ffmpeg, then reopen the terminal.")
    return exe


def video_length(path):
    probe = shutil.which("ffprobe")
    if not probe:
        return None
    out = subprocess.run(
        [probe, "-v", "error", "-show_entries", "format=duration",
         "-of", "json", path], capture_output=True, text=True)
    try:
        return float(json.loads(out.stdout)["format"]["duration"])
    except Exception:
        return None


def cut_clips(video, moments, out_dir, vertical=False):
    """Writes clip_1.mp4, clip_2.mp4 ... and reel.mp4 into out_dir."""
    os.makedirs(out_dir, exist_ok=True)
    ff = _ffmpeg()
    clip_files = []
    for m in moments:
        name = f"clip_{m['id']}.mp4"
        path = os.path.join(out_dir, name)
        dur = m["clip_end"] - m["clip_start"]
        vf = ["scale=-2:720"]
        if vertical:
            vf = ["crop=ih*9/16:ih", "scale=720:1280"]
        cmd = [ff, "-y", "-loglevel", "error",
               "-ss", f"{m['clip_start']:.2f}", "-i", video, "-t", f"{dur:.2f}",
               "-vf", ",".join(vf + ["fps=30"]),
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
               "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "128k",
               "-movflags", "+faststart", path]
        subprocess.run(cmd, check=True)
        m["file"] = name
        clip_files.append(path)

    if clip_files:
        list_path = os.path.join(out_dir, "clips.txt")
        with open(list_path, "w") as f:
            for p in clip_files:
                f.write(f"file '{os.path.abspath(p)}'\n")
        subprocess.run([ff, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                        "-i", list_path, "-c", "copy", "-movflags", "+faststart",
                        os.path.join(out_dir, "reel.mp4")], check=True)
        os.remove(list_path)
    return clip_files
