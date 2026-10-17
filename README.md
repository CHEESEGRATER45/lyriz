# lyriz

Live lyrics in a terminal, rendered as big ASCII text, colored to your
current wallpaper accent. Japanese and Bangla lines get auto-romanized to
English pronunciation.

<img width="1918" height="1078" alt="image" src="https://github.com/user-attachments/assets/3a520ac8-8a50-49fc-a3cc-e76922b98583" />

<img width="1918" height="1078" alt="image" src="https://github.com/user-attachments/assets/2db84c95-5ba8-4130-9141-c17092c295e0" />

<img width="1918" height="1078" alt="image" src="https://github.com/user-attachments/assets/7df36273-5fab-4f7a-a60c-ffec295b9926" />

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
