# lyriz

Live lyrics in a terminal, rendered as big ASCII text, colored to your
current wallpaper accent. Japanese and Bangla lines get auto-romanized to
English pronunciation.

<img width="1920" height="1078" alt="image" src="https://github.com/user-attachments/assets/e4bb508d-3a56-4960-a9f3-3e61906b6852" />

<img width="1920" height="1078" alt="image" src="https://github.com/user-attachments/assets/9c9a3702-6a46-4f01-bddb-932b6bb5b17f" />

<img width="1915" height="1077" alt="image" src="https://github.com/user-attachments/assets/096b9924-3bcc-4bfc-9ea3-d5d347aa03c8" />

## How it works

```
lyriz-local-first.py  ->  lyriz-romanize.py  ->  lyriz-launch (figlet + color)
```

1. `lyriz-local-first.py` finds the active MPRIS player (via `playerctl`), looks
   for a matching local `.lrc` file, and runs `sptlrx pipe` with a generated
   config. If no local file matches, it falls back to sptlrx's online lyrics.
2. `lyriz-romanize.py` romanizes Japanese (`pykakasi`) and Bangla
   (`bangla_romanize.py`) lines. Other lines pass through unchanged.
3. `lyriz-launch` clears the screen and prints each line with `figlet`, colored
   from your matugen accent.

## Requires

- sptlrx, figlet, jq, playerctl
- `pip install pykakasi --break-system-packages`
- Any MPRIS player that is open and playing (Spotify, etc.)

## Install

```
cp lyriz-launch lyriz-local-first.py lyriz-romanize.py bangla_romanize.py ~/.local/bin/
chmod +x ~/.local/bin/lyriz-launch ~/.local/bin/lyriz-local-first.py \
         ~/.local/bin/lyriz-romanize.py ~/.local/bin/bangla_romanize.py
mkdir -p ~/.config/sptlrx
cp config.yaml.example ~/.config/sptlrx/config.yaml
```

Bind a hotkey to `kitty -e ~/.local/bin/lyriz-launch` to open it in a new terminal window.

## Local lyrics (optional)

Put `.lrc` files named `Title - Artist.lrc` in the folder set by `MUSIC_DIR` at
the top of `lyriz-local-first.py` (default: `~/projects/spodsync/music`).
Edit that path to point at your own library. Tracks without a match use
online lyrics.

Run `lyriz-local-first.py --check` to see which player, track, and lyrics
source it picks.

## Notes

- Color comes from `~/.local/state/quickshell/user/generated/colors.json` (matugen)
- Don't pipe `sptlrx pipe | figlet` directly, it garbles. Loop + clear per line instead.
- Bangla romanization is rule-based and approximate; some conjuncts are irregular.
