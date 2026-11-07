"""Find the moments worth clipping in a session's brain readings.

Each player is compared to their own first 60 seconds (the baseline),
so a naturally "high" player doesn't get clipped constantly.

Two kinds of moment:
    Hype      - excitement jumps well above baseline for a short burst
    Locked in - focus stays well above baseline for a longer stretch
"""

import numpy as np

SETTINGS = {
    "baseline_s": 60,       # warm-up minute: play casually, never clipped
    "baseline_mode": "rolling",  # "rolling" = compare to the last minute; "fixed" = to the warm-up
    "rolling_s": 60,
    "gap_s": 5,             # leave out the last few seconds so a spike isn't compared to itself
    "smooth_s": 1.5,        # rolling average to ignore single noisy readings
    "hype_z": 2.0,          # how far above baseline counts as a spike
    "hype_min_s": 1.5,      # spike has to last this long
    "focus_z": 1.5,
    "focus_min_s": 6.0,
    "merge_gap_s": 10,      # moments closer than this become one
    "max_moments": 6,       # how many make the reel
    "pre_s": 8,             # seconds of buildup before the moment
    "post_s": 4,            # seconds after
    "max_clip_s": 20,
}


def _smooth(x, n):
    if n <= 1:
        return x
    # trailing average (same as the live page), no edge dips
    c = np.cumsum(np.insert(x, 0, 0.0))
    out = np.empty_like(x)
    for i in range(len(x)):
        a = max(0, i - n + 1)
        out[i] = (c[i + 1] - c[a]) / (i + 1 - a)
    return out


def _runs(mask):
    """(start_index, end_index) for each run of True values."""
    runs, start = [], None
    for i, m in enumerate(mask):
        if m and start is None:
            start = i
        elif not m and start is not None:
            runs.append((start, i - 1))
            start = None
    if start is not None:
        runs.append((start, len(mask) - 1))
    return runs


def rolling_z(x, t, s):
    """How unusual each reading is compared to the player's recent past.

    Each point is compared to the window from `rolling_s` seconds ago up to
    `gap_s` seconds ago. A rolling baseline means a player who slowly gets
    more into the game doesn't trigger clips nonstop; only sudden changes do.
    The warm-up minute is never clipped.
    """
    z = np.zeros_like(x)
    warm = t <= s["baseline_s"]
    w_mu = float(np.mean(x[warm])) if warm.sum() >= 5 else float(np.mean(x))
    w_sd = float(np.std(x[warm])) if warm.sum() >= 5 else float(np.std(x))
    for i in range(len(x)):
        if warm[i]:
            continue
        if s["baseline_mode"] == "fixed":
            mu, sd = w_mu, w_sd
        else:
            m = (t >= t[i] - s["rolling_s"]) & (t <= t[i] - s["gap_s"])
            if m.sum() < 5:
                mu, sd = w_mu, w_sd
            else:
                mu, sd = float(np.mean(x[m])), float(np.std(x[m]))
        # floor the spread so a very still stretch doesn't make tiny wiggles look huge
        sd = max(sd, 0.25 * w_sd, 1e-6)
        z[i] = (x[i] - mu) / sd
    return z, {"mean": w_mu, "std": w_sd}


def z_series(readings, settings=None):
    s = dict(SETTINGS, **(settings or {}))
    t = np.array([r["t"] for r in readings])
    step = float(np.median(np.diff(t))) if len(t) > 1 else 0.5
    smooth_n = max(1, int(round(s["smooth_s"] / step)))
    out, baseline = {}, {}
    for key in ("excitement", "focus"):
        x = _smooth(np.array([r[key] for r in readings], dtype=float), smooth_n)
        out[key], baseline[key] = rolling_z(x, t, s)
    return t, step, out, baseline


def find_moments(readings, video_length_s=None, settings=None):
    s = dict(SETTINGS, **(settings or {}))
    if len(readings) < 10:
        return [], {}, {}

    t, step, zs, baseline = z_series(readings, s)
    found = []
    kinds = [
        ("Hype", "excitement", s["hype_z"], s["hype_min_s"]),
        ("Locked in", "focus", s["focus_z"], s["focus_min_s"]),
    ]
    for label, key, z_cut, min_s in kinds:
        z = zs[key]
        for a, b in _runs(z > z_cut):
            if (t[b] - t[a]) + step < min_s:
                continue
            peak_i = a + int(np.argmax(z[a:b + 1]))
            found.append({
                "label": label,
                "start": float(t[a]),
                "end": float(t[b]),
                "peak_t": float(t[peak_i]),
                "peak_z": round(float(z[peak_i]), 2),
            })

    # merge overlapping or close moments, keep the stronger label
    found.sort(key=lambda m: m["start"])
    merged = []
    for m in found:
        if merged and m["start"] - merged[-1]["end"] <= s["merge_gap_s"]:
            prev = merged[-1]
            prev["end"] = max(prev["end"], m["end"])
            if m["peak_z"] > prev["peak_z"]:
                prev.update(label=m["label"], peak_z=m["peak_z"], peak_t=m["peak_t"])
        else:
            merged.append(dict(m))

    best = sorted(merged, key=lambda m: m["peak_z"], reverse=True)[: s["max_moments"]]
    best.sort(key=lambda m: m["start"])

    for i, m in enumerate(best, 1):
        clip_start = max(0.0, m["start"] - s["pre_s"])
        clip_end = m["end"] + s["post_s"]
        if clip_end - clip_start > s["max_clip_s"]:
            clip_start = clip_end - s["max_clip_s"]
        if video_length_s:
            clip_end = min(clip_end, video_length_s)
        m.update(id=i, clip_start=round(clip_start, 2), clip_end=round(clip_end, 2))

    return best, baseline, zs
