"""Brain data sources for Brainclip.

Every source gives back one reading at a time:
    {"t": seconds since session start, "excitement": float, "focus": float}

Sources:
    UnicornSource  - g.tec Unicorn through BrainFlow (Windows laptop only)
    FakeSource     - made-up data with spikes, for building without a headset
"""

import json
import math
import random
import threading
import time

import numpy as np
from scipy.signal import welch, butter, sosfiltfilt, iirnotch, filtfilt

# Unicorn channel order from BrainFlow: Fz, C3, Cz, C4, Pz, PO7, Oz, PO8
FRONTAL_CENTRAL = [0, 1, 2, 3]   # Fz, C3, Cz, C4: used for focus
ALL_EEG = list(range(8))

BANDS = {
    "theta": (4, 8),
    "alpha": (8, 13),
    "beta": (13, 30),
    "gamma": (30, 45),
}


def band_powers(window, fs):
    """Average power per band across the given channels.

    window: array of shape (channels, samples), microvolts
    """
    out = {name: 0.0 for name in BANDS}
    for ch in window:
        freqs, psd = welch(ch, fs=fs, nperseg=min(len(ch), int(fs)))
        for name, (lo, hi) in BANDS.items():
            mask = (freqs >= lo) & (freqs < hi)
            out[name] += float(np.trapezoid(psd[mask], freqs[mask]))
    n = max(len(window), 1)
    return {k: v / n for k, v in out.items()}


def scores_from_window(window, fs):
    """Turn a 2 second chunk of raw EEG into excitement and focus.

    focus      = beta / (alpha + theta) on frontal/central sensors
                 (the classic "engagement index", Pope et al. 1995)
    excitement = (beta + gamma) / alpha across all sensors
                 (rough arousal measure; face and jaw tension during
                 exciting moments also pushes it up, which helps here)
    """
    fc = band_powers(window[FRONTAL_CENTRAL], fs)
    allp = band_powers(window[ALL_EEG], fs)
    eps = 1e-9
    focus = fc["beta"] / (fc["alpha"] + fc["theta"] + eps)
    excitement = (allp["beta"] + allp["gamma"]) / (allp["alpha"] + eps)
    return float(excitement), float(focus)


def clean(window, fs):
    """Remove drift and 60 Hz mains hum (US power), keep 1 to 45 Hz."""
    sos = butter(4, [1, 45], btype="bandpass", fs=fs, output="sos")
    out = sosfiltfilt(sos, window, axis=1)
    b, a = iirnotch(60, 30, fs)
    return filtfilt(b, a, out, axis=1)


class UnicornSource:
    """Reads the g.tec Unicorn with BrainFlow. Windows only.

    Pair the headset through the Unicorn USB dongle, not built-in Bluetooth.
    """

    def __init__(self, serial_number="", window_s=2.0, step_s=0.5):
        from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds

        params = BrainFlowInputParams()
        params.serial_number = serial_number
        self.board_id = BoardIds.UNICORN_BOARD
        self.board = BoardShim(self.board_id, params)
        self.fs = BoardShim.get_sampling_rate(self.board_id)
        self.eeg_rows = BoardShim.get_eeg_channels(self.board_id)
        self.window_n = int(window_s * self.fs)
        self.step_s = step_s

    def start(self):
        self.board.prepare_session()
        self.board.start_stream()
        self.t0 = time.time()
        time.sleep(2.2)  # fill the first window

    def read(self):
        time.sleep(self.step_s)
        data = self.board.get_current_board_data(self.window_n)
        window = data[self.eeg_rows]
        if window.shape[1] < self.window_n:
            return None
        excitement, focus = scores_from_window(clean(window, self.fs), self.fs)
        return {"t": round(time.time() - self.t0, 3),
                "excitement": round(excitement, 4),
                "focus": round(focus, 4)}

    def stop(self):
        try:
            self.board.stop_stream()
        finally:
            self.board.release_session()


class EmotivSource:
    """Reads Emotiv's built-in Excitement and Focus scores through the Cortex API.

    Works on Mac and Windows. Needs:
      1. EMOTIV Launcher installed, logged in, headset connected in the Launcher
      2. A Cortex app: emotiv.com > My Account > Cortex Apps > Register, copy the
         Client ID and Client Secret
      3. pip install websocket-client
    The first run pops up an approval request in the Launcher. Click Approve.

    Without a paid license the scores ("met" stream) may only update about
    every 10 seconds. The script prints how often they actually arrive.
    """

    URL = "wss://localhost:6868"

    def __init__(self, client_id, client_secret, step_s=0.5, stream="pow"):
        self.stream = stream  # "pow" = band power, 8x/s, no license; "met" = Emotiv scores
        import websocket  # websocket-client
        import ssl
        self.ws = websocket.create_connection(
            self.URL, sslopt={"cert_reqs": ssl.CERT_NONE})  # Cortex runs locally with a self-signed cert
        self.client_id, self.client_secret = client_id, client_secret
        self.step_s = step_s
        self._id = 0
        self.latest = None
        self.updates = []
        self.running = False

    def _call(self, method, params):
        self._id += 1
        self.ws.send(json.dumps({"jsonrpc": "2.0", "id": self._id,
                                 "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self._id:
                if "error" in msg:
                    raise SystemExit(f"Cortex {method} failed: {msg['error'].get('message')}")
                return msg["result"]

    def start(self):
        creds = {"clientId": self.client_id, "clientSecret": self.client_secret}
        if not self._call("requestAccess", creds).get("accessGranted"):
            input("Approve Brainclip in the EMOTIV Launcher, then press Enter...")
        token = self._call("authorize", dict(creds, debit=1))["cortexToken"]
        headsets = self._call("queryHeadsets", {})
        if not headsets:
            raise SystemExit("No Emotiv headset found. Connect it in the EMOTIV Launcher first.")
        hs = headsets[0]["id"]
        if headsets[0].get("status") != "connected":
            self._call("controlDevice", {"command": "connect", "headset": hs})
            time.sleep(3)
        session = self._call("createSession", {"cortexToken": token, "headset": hs,
                                               "status": "active"})["id"]
        sub = self._call("subscribe", {"cortexToken": token, "session": session,
                                       "streams": [self.stream]})
        if not sub.get("success"):
            raise SystemExit(f"Could not subscribe to {self.stream}: {sub.get('failure')}")
        cols = sub["success"][0]["cols"]
        if self.stream == "met":
            self.i_exc = cols.index("exc")
            self.i_foc = cols.index("foc") if "foc" in cols else cols.index("eng")
        else:
            # cols look like "AF3/theta", "AF3/alpha", "AF3/betaL", "AF3/betaH", "AF3/gamma", ...
            self.cols = cols
            front = [c for c in cols if c.split("/")[0] in ("AF3", "AF4", "F3", "F4", "FC5", "FC6")]
            self.front = front or cols
        print(f"Emotiv connected ({hs}), stream '{self.stream}', {len(cols)} columns")
        self.running = True
        self.t0 = time.time()
        threading.Thread(target=self._listen, daemon=True).start()
        while self.latest is None:  # wait for first score
            time.sleep(0.2)

    def _listen(self):
        while self.running:
            try:
                msg = json.loads(self.ws.recv())
            except Exception:
                break
            vals = None
            if self.stream == "met" and "met" in msg:
                m = msg["met"]
                exc, foc = m[self.i_exc], m[self.i_foc]
                if exc is not None and foc is not None:
                    vals = (float(exc), float(foc))
            elif self.stream == "pow" and "pow" in msg:
                vals = self._from_pow(msg["pow"])
            if vals:
                self.latest = vals
                self.updates.append(time.time())
                if len(self.updates) == 5:
                    gap = (self.updates[-1] - self.updates[0]) / 4
                    print(f"Emotiv scores arriving every {gap:.2f} s")

    def _from_pow(self, row):
        """Same formulas as the Unicorn, using Emotiv's own band powers."""
        def total(cols, band_names):
            s = 0.0
            for c, v in zip(self.cols, row):
                if c in cols and c.split("/")[1] in band_names and v is not None:
                    s += float(v)
            return s
        eps = 1e-9
        allc = set(self.cols)
        frontc = set(self.front)
        beta = ("betaL", "betaH")
        focus = total(frontc, beta) / (total(frontc, ("alpha", "theta")) + eps)
        excitement = total(allc, beta + ("gamma",)) / (total(allc, ("alpha",)) + eps)
        return excitement, focus

    def read(self):
        time.sleep(self.step_s)
        exc, foc = self.latest
        return {"t": round(time.time() - self.t0, 3),
                "excitement": round(exc, 4), "focus": round(foc, 4)}

    def stop(self):
        self.running = False
        try:
            self.ws.close()
        except Exception:
            pass


class FakeSource:
    """Made-up brain data with a few clear spikes. For building without a headset.

    speed > 1 runs faster than real time (handy for testing detection).
    """

    def __init__(self, step_s=0.5, speed=1.0, seed=None):
        self.step_s = step_s
        self.speed = speed
        self.rng = random.Random(seed)
        self.t = 0.0
        self.hype_at = []
        self.focus_at = []

    def start(self):
        self.t0 = time.time()
        self.t = 0.0
        # schedule events after the 60 s baseline
        t = 75.0
        while t < 3600:
            if self.rng.random() < 0.6:
                self.hype_at.append(t)
            else:
                self.focus_at.append(t)
            t += self.rng.uniform(25, 60)

    def _bump(self, events, width):
        v = 0.0
        for e in events:
            if e - 1 <= self.t <= e + width:
                v = max(v, math.sin(math.pi * (self.t - e + 1) / (width + 1)))
        return v

    def read(self):
        if self.speed > 0:
            time.sleep(self.step_s / self.speed)
        self.t += self.step_s
        excitement = 1.0 + self.rng.gauss(0, 0.08) + 1.2 * self._bump(self.hype_at, 4)
        focus = 0.6 + self.rng.gauss(0, 0.05) + 0.45 * self._bump(self.focus_at, 12)
        return {"t": round(self.t, 3),
                "excitement": round(excitement, 4),
                "focus": round(focus, 4)}

    def stop(self):
        pass
