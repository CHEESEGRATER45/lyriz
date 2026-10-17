#!/usr/bin/env python3
"""
lyriz-local-first: print the current lyric line to stdout, one line per change.

Behavior:
  - Internet up:   use sptlrx (online lyrics) only.
  - Internet down: look for a local .lrc file in MUSIC_DIR and play it
                   (synced by this script). If none is found, print nothing.
  - Switches automatically if the connection drops or comes back mid-song.

Usage:
  lyriz-local-first.py           stream lyrics
  lyriz-local-first.py --check   show player, track and chosen source, then exit

Env:
  LYRIZ_MUSIC_DIR   folder with .lrc files (default ~/projects/spodsync/music)
"""
import atexit
import bisect
import os
import queue
import re
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

MUSIC_DIR = Path(os.environ.get("LYRIZ_MUSIC_DIR", "~/projects/spodsync/music")).expanduser()
POLL = 0.2          # seconds between position checks
NET_CHECK = 3       # seconds between internet checks

TS = re.compile(r"\[(\d+):(\d+(?:[.:]\d+)?)\]")
WORD_TAG = re.compile(r"<\d+:\d+(?:[.:]\d+)?>")


# ---------- helpers ----------

def sh(*args, timeout=2):
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return p.stdout.strip() if p.returncode == 0 else ""
    except Exception:
        return ""


def emit(text):
    print(text, flush=True)


def online():
    for host in (("1.1.1.1", 443), ("8.8.8.8", 443)):
        try:
            socket.create_connection(host, timeout=1.5).close()
            return True
        except OSError:
            continue
    return False


def pick_player():
    names = sh("playerctl", "-l").splitlines()
    if not names:
        return None
    for n in names:
        if sh("playerctl", "-p", n, "status") == "Playing":
            return n
    return names[0]


def get_track(player):
    out = sh("playerctl", "-p", player, "metadata", "--format", "{{artist}}|||{{title}}")
    if "|||" not in out:
        return None
    artist, title = out.split("|||", 1)
    return artist.strip(), title.strip()


def get_position(player):
    try:
        return float(sh("playerctl", "-p", player, "position"))
    except ValueError:
        return None


# ---------- LRC matching and parsing ----------

def norm(s):
    s = s.casefold()
    s = re.sub(r"\(.*?\)|\[.*?\]", " ", s)       # drop (remastered), [live], ...
    s = re.sub(r"\b(feat|ft)\b.*", " ", s)       # drop "feat. someone"
    return re.sub(r"[\W_]+", "", s)


def find_lrc(artist, title):
    if not MUSIC_DIR.is_dir():
        return None
    # try the full title, then the title without a " - Remastered 2011" style suffix
    titles = [t for t in dict.fromkeys([norm(title), norm(re.split(r"\s+-\s+", title)[0])]) if t]
    artists = [a for a in (norm(x) for x in re.split(r"[,&;/]", artist)) if a]
    title_only = None
    for p in MUSIC_DIR.rglob("*.lrc"):
        stem = norm(p.stem)
        if not any(t in stem for t in titles):
            continue
        if not artists or any(a in stem for a in artists):
            return p
        if title_only is None:
            title_only = p
    return title_only


def parse_lrc(path):
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    offset = 0.0
    m = re.search(r"\[offset:\s*(-?\d+)\]", raw, re.I)
    if m:
        offset = int(m.group(1)) / 1000.0
    rows = []
    for line in raw.splitlines():
        stamps = TS.findall(line)
        if not stamps:
            continue
        text = WORD_TAG.sub("", TS.sub("", line)).strip()
        for mm, ss in stamps:
            rows.append((int(mm) * 60 + float(ss.replace(":", ".")) - offset, text))
    rows.sort(key=lambda r: r[0])
    return [r[0] for r in rows], [r[1] for r in rows]


class Net:
    """Checks the internet in the background so the main loop never blocks."""

    def __init__(self):
        self.up = online()
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while True:
            time.sleep(NET_CHECK)
            self.up = online()


# ---------- sptlrx (online) ----------

class Sptlrx:
    """Runs `sptlrx pipe` locked onto one specific MPRIS player (any player)."""

    def __init__(self, player=None):
        self.q = queue.Queue()
        self.cfg = None
        self.proc = None
        if player:
            # sptlrx with an empty player list grabs the *first* player on D-Bus,
            # not the one that is playing. Give it a tiny config naming ours.
            try:
                import tempfile
                fd, self.cfg = tempfile.mkstemp(prefix="lyriz-sptlrx-", suffix=".yaml")
                with os.fdopen(fd, "w") as f:
                    f.write(f'player: mpris\nmpris:\n  players: ["{player}"]\n')
                self._start(["sptlrx", "--config", self.cfg, "pipe"])
                time.sleep(0.4)
                if self.proc.poll() not in (None, 0):   # --config unsupported/rejected
                    self._start(["sptlrx", "pipe"])
            except FileNotFoundError:
                raise
            except Exception:
                self._start(["sptlrx", "pipe"])
        else:
            self._start(["sptlrx", "pipe"])

    def _start(self, cmd):
        self.proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1,
        )
        threading.Thread(target=self._read, args=(self.proc,), daemon=True).start()

    def _read(self, proc):
        for line in proc.stdout:
            self.q.put(line.rstrip("\n"))

    def drain(self):
        while True:
            try:
                emit(self.q.get_nowait())
            except queue.Empty:
                return

    def stop(self):
        try:
            self.proc.terminate()
            self.proc.wait(timeout=2)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass
        if self.cfg:
            try:
                os.unlink(self.cfg)
            except OSError:
                pass


# ---------- main loop ----------

def run(check=False):
    net = Net()
    cur_key = None
    cur_up = None
    mode = None            # "local" | "online" | "none"
    times, texts = [], []
    last_idx = None
    sptlrx = None

    def stop_sptlrx():
        nonlocal sptlrx
        if sptlrx:
            sptlrx.stop()
            sptlrx = None

    atexit.register(stop_sptlrx)

    while True:
        player = pick_player()
        track = get_track(player) if player else None
        if not track or not track[1]:
            if check:
                print("No active MPRIS player/track found (is playerctl installed and music playing?)")
                return
            time.sleep(1)
            continue

        key = (player, track)
        up = net.up
        if key != cur_key or up != cur_up:      # new track, or internet went up/down
            stop_sptlrx()
            cur_key, cur_up = key, up
            last_idx = None
            artist, title = track
            path = None
            if up:
                mode = "online"
                source = "sptlrx (internet is up)"
                if not check:
                    emit("")        # don't leave the previous song's last line on screen
                    try:
                        sptlrx = Sptlrx(player)
                    except OSError:
                        mode = "none"
                        source = "sptlrx is not installed"
                        print("lyriz: sptlrx not found in PATH", file=sys.stderr)
            else:
                path = find_lrc(artist, title)
                if path:
                    times, texts = parse_lrc(path)
                mode = "local" if path and times else "none"
                if mode == "local":
                    source = f"local LRC (offline): {path}"
                elif path:
                    source = f"LRC has no timestamps: {path}"
                else:
                    source = "none (offline and no local .lrc found)"
                if mode == "none" and not check:
                    emit("")
            if check:
                print(f"player: {player}\ntrack:  {artist} - {title}\nsource: {source}")
                print(f"music dir: {MUSIC_DIR} (exists: {MUSIC_DIR.is_dir()})")
                return

        if mode == "local":
            pos = get_position(player)
            if pos is not None:
                idx = bisect.bisect_right(times, pos) - 1
                if idx != last_idx:
                    last_idx = idx
                    emit(texts[idx] if idx >= 0 else "")
        elif mode == "online" and sptlrx:
            sptlrx.drain()

        time.sleep(POLL)


def main():
    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, lambda *_: sys.exit(0))
    try:
        run(check="--check" in sys.argv)
    except (KeyboardInterrupt, BrokenPipeError):
        pass


if __name__ == "__main__":
    main()
