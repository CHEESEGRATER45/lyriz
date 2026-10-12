#!/usr/bin/env python3
import difflib
import json
import queue
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

MUSIC_DIR = Path.home() / "projects/spodsync/music"
BASE_CONFIG = Path.home() / ".config/sptlrx/config.yaml"
CACHE = Path.home() / ".cache/lyriz"


def run(args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=3).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def normalize(value):
    value = value.casefold()
    value = re.sub(r"\.(lrc|mp3|flac|ogg|wav|m4a)$", "", value)
    value = re.sub(r"\s*\((feat\.?|ft\.?).*?\)", "", value)
    return re.sub(r"[^\w]+", "", value)


def active_track():
    candidates = []
    for player in run(["playerctl", "-l"]).splitlines():
        status = run(["playerctl", "-p", player, "status"])
        metadata = run([
            "playerctl", "-p", player, "metadata",
            "--format", "{{title}}\t{{artist}}"
        ])
        if "\t" not in metadata:
            continue
        title, artist = metadata.split("\t", 1)
        if title and title != "No player" and status in ("Playing", "Paused"):
            candidates.append((status, player, title, artist))

    playing = [item for item in candidates if item[0] == "Playing"]
    paused = [item for item in candidates if item[0] == "Paused"]
    chosen = (playing or paused or [None])[0]
    return (chosen[1], chosen[2], chosen[3]) if chosen else None


def find_local_lyrics(title, artist):
    if not MUSIC_DIR.is_dir():
        return None

    clean_title = re.sub(
        r"\s*[\(\[]?\s*(official\s+)?(music\s+video|official\s+audio|lyrics?|visualizer|4k|hd)[^\)\]]*[\)\]]?\s*$",
        "", title, flags=re.IGNORECASE
    )
    if artist:
        clean_title = re.sub(
            r"^\s*" + re.escape(artist) + r"\s*[-–|:]\s*",
            "", clean_title, flags=re.IGNORECASE
        )

    wanted_title = normalize(clean_title)
    wanted_artist = normalize(artist)
    best_path = None
    best_score = 0

    for path in MUSIC_DIR.rglob("*.lrc"):
        parts = path.stem.split(" - ", 1)
        file_title = normalize(parts[0])
        file_artist = normalize(parts[1]) if len(parts) > 1 else ""

        title_score = difflib.SequenceMatcher(None, wanted_title, file_title).ratio()
        artist_score = (
            difflib.SequenceMatcher(None, wanted_artist, file_artist).ratio()
            if wanted_artist and file_artist else 0
        )

        if title_score >= 0.98:
            score = 2 + artist_score
        elif title_score >= 0.86 and artist_score >= 0.45:
            score = title_score + artist_score * 0.25
        else:
            continue

        if score > best_score:
            best_path, best_score = path, score

    return best_path


def replace_section(text, name, replacement):
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines)
                  if line.startswith(name + ":")), None)
    if start is None:
        lines.extend(replacement)
    else:
        end = start + 1
        while end < len(lines):
            line = lines[end]
            if line and not line[0].isspace() and not line.startswith("#"):
                break
            end += 1
        lines[start:end] = replacement
    return "\n".join(lines) + "\n"


def remove_section(text, name):
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines)
                  if line.startswith(name + ":")), None)
    if start is None:
        return text
    end = start + 1
    while end < len(lines):
        line = lines[end]
        if line and not line[0].isspace() and not line.startswith("#"):
            break
        end += 1
    del lines[start:end]
    return "\n".join(lines) + "\n"


def make_config(player, local_file):
    text = BASE_CONFIG.read_text() if BASE_CONFIG.exists() else "player: mpris\n"
    text = re.sub(r"(?m)^player:.*$", "player: mpris", text)
    text = replace_section(text, "mpris", [
        "mpris:",
        "  players: [" + json.dumps(player) + "]"
    ])

    if local_file:
        text = replace_section(text, "local", [
            "local:",
            "  folder: " + json.dumps(str(local_file.parent))
        ])
        mode = "local"
    else:
        text = remove_section(text, "local")
        mode = "online"

    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / ("sptlrx-" + normalize(player) + "-" + mode + ".yaml")
    path.write_text(text)
    return path


def check():
    track = active_track()
    if not track:
        print("No active MPRIS track found.")
        return
    player, title, artist = track
    local_file = find_local_lyrics(title, artist)
    print("Player: " + player)
    print("Title:  " + title)
    print("Artist: " + artist)
    print("Mode:   " + ("local" if local_file else "online fallback"))
    if local_file:
        print("LRC:    " + str(local_file))


def stop_process(process):
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def main():
    if "--check" in sys.argv:
        check()
        return
    if not BASE_CONFIG.exists():
        print("Missing sptlrx config: " + str(BASE_CONFIG), file=sys.stderr)
        sys.exit(1)

    output = queue.Queue()
    process = None
    current_key = None

    def read_output(child):
        if child.stdout:
            for line in child.stdout:
                output.put((child, line.rstrip("\n")))

    try:
        while True:
            track = active_track()
            key = track

            if key != current_key:
                stop_process(process)
                process = None
                current_key = key

                while True:
                    try:
                        output.get_nowait()
                    except queue.Empty:
                        break

                if track:
                    player, title, artist = track
                    local_file = find_local_lyrics(title, artist)
                    config = make_config(player, local_file)
                    process = subprocess.Popen(
                        ["sptlrx", "--config", str(config), "pipe"],
                        stdout=subprocess.PIPE,
                        text=True,
                        bufsize=1
                    )
                    threading.Thread(
                        target=read_output, args=(process,), daemon=True
                    ).start()

            try:
                child, line = output.get(timeout=0.25)
                if child is process:
                    print(line, flush=True)
            except queue.Empty:
                pass

            if process and process.poll() is not None:
                process = None
                current_key = None

            time.sleep(0.25)
    except KeyboardInterrupt:
        pass
    finally:
        stop_process(process)


if __name__ == "__main__":
    main()
