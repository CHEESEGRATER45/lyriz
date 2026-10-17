# lyriz

Live lyrics in a terminal, rendered as big ASCII text, colored to your
current wallpaper accent. Japanese and Bangla lines get auto-romanized to
English pronunciation.

<img width="1918" height="1078" alt="image" src="https://github.com/user-attachments/assets/3a520ac8-8a50-49fc-a3cc-e76922b98583" />

<img width="1918" height="1078" alt="image" src="https://github.com/user-attachments/assets/608f42fc-c577-4913-9e7c-ffa3f8fed4b2" />

<img width="1918" height="1078" alt="image" src="https://github.com/user-attachments/assets/7df36273-5fab-4f7a-a60c-ffec295b9926" />

## How it works

```
lyriz-local-first.py  ->  lyriz-romanize.py  ->  lyriz-launch (figlet + color)
```

1. `lyriz-local-first.py` finds the active MPRIS player (via `playerctl`) and
   picks a lyrics source:
   - **Internet up:** runs `sptlrx pipe` locked onto the player that is
     playing, so it works with any MPRIS player, not just Spotify.
   - **Internet down:** looks for a matching local `.lrc` file and plays it,
     synced to the player's position. If none matches, nothing is shown.
   - It checks the connection every few seconds and switches automatically if
     it drops or returns mid-song.
2. `lyriz-romanize.py` romanizes Japanese (`pykakasi`) and Bangla
   (`bangla_romanize.py`) lines. Other lines pass through unchanged.
3. `lyriz-launch` clears the screen and prints each line with `figlet`, colored
   from your matugen accent.

## Requires

- `sptlrx`, `figlet`, `jq`, `playerctl`, `python`
- `pykakasi` (Python package, for Japanese romanization)
- `kitty` (or any terminal, see the keybind step)
- Any MPRIS player that is open and playing (Spotify, mpv, Firefox, ...)

## Setup on Arch Linux + Hyprland

Every command below works the same in bash and fish unless a step shows
separate bash / fish blocks.

### 1. Install dependencies

```
sudo pacman -S --needed git python figlet jq playerctl kitty
```

`sptlrx` is in the AUR. Use whichever AUR helper you have:

```
yay -S sptlrx-bin
```

or

```
paru -S sptlrx-bin
```

Install `pykakasi`. If an AUR package named `python-pykakasi` exists for you,
use it. Otherwise use pip:

```
pip install --user --break-system-packages pykakasi
```

### 2. Get the files

```
git clone https://github.com/CHEESEGRATER45/lyriz.git
cd lyriz
```

### 3. Copy the scripts into `~/.local/bin`

```
mkdir -p ~/.local/bin
cp lyriz-launch lyriz-local-first.py lyriz-romanize.py bangla_romanize.py ~/.local/bin/
chmod +x ~/.local/bin/lyriz-launch ~/.local/bin/lyriz-local-first.py ~/.local/bin/lyriz-romanize.py ~/.local/bin/bangla_romanize.py
```

### 4. Make sure `~/.local/bin` is on your PATH

bash:

```
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

fish:

```
fish_add_path ~/.local/bin
```

### 5. Check that it sees your player

Start playing a song in any player, then run:

```
playerctl -l
lyriz-local-first.py --check
```

`--check` prints the player, the track, and which lyrics source it will use,
then exits. If it says no player or track was found, fix that first.

### 6. Try it in a terminal

```
lyriz-launch
```

Lyrics should appear as big text and change with the song. Press `Ctrl+C` to
stop.

### 7. Bind a key in Hyprland

Add this line to `~/.config/hypr/hyprland.conf`:

```
bind = SUPER, L, exec, kitty --class lyriz -e ~/.local/bin/lyriz-launch
```

Then reload:

```
hyprctl reload
```

`--class lyriz` lets you write a window rule for it (for example, to make it
float). Window rule syntax differs between Hyprland versions, so check the
Hyprland wiki for yours.

### 8. (Optional) Local `.lrc` files for offline use

Put `.lrc` files in a folder, named like `Title - Artist.lrc`. Matching ignores
case and punctuation, and ignores things like `(Remastered)` and `feat. ...`.
Subfolders are searched.

The folder defaults to `~/projects/spodsync/music`. To use your own, set
`LYRIZ_MUSIC_DIR`. Setting it in `~/.bashrc` or fish config will **not** reach
a program started from a Hyprland keybind, so put it in the bind itself:

```
bind = SUPER, L, exec, env LYRIZ_MUSIC_DIR=~/Music kitty --class lyriz -e ~/.local/bin/lyriz-launch
```

To test it from a terminal first:

bash:

```
LYRIZ_MUSIC_DIR=~/Music lyriz-local-first.py --check
```

fish:

```
env LYRIZ_MUSIC_DIR=~/Music lyriz-local-first.py --check
```

Local files are only used while the internet is down. To test, turn off
Wi-Fi and run `lyriz-local-first.py --check`. It should say
`local LRC (offline)`.

### 9. (Optional) sptlrx config

You don't need to copy a config. `lyriz-local-first.py` generates a small one
to lock sptlrx onto the player that is playing. If you do keep your own
`~/.config/sptlrx/config.yaml`, leave the player list empty so it doesn't
restrict you to one player:

```
player: mpris
mpris:
  players: []
```

## Notes

- Color comes from `~/.local/state/quickshell/user/generated/colors.json`
  (matugen). If that file is missing, text is white.
- Don't pipe `sptlrx pipe | figlet` directly, it garbles. Loop + clear per line
  instead (that's what `lyriz-launch` does).
- Bangla romanization is rule-based and approximate; some conjuncts are
  irregular.
- The offline check connects to `1.1.1.1` and `8.8.8.8` on port 443. If your
  network blocks those, lyriz may think you're offline.

## Troubleshooting

| Problem | Try |
| --- | --- |
| Nothing shows | `lyriz-local-first.py --check`, and make sure `playerctl -l` lists your player |
| Wrong player used | Pause the other players, or check the `--check` output |
| Lyrics missing for a song | Online: sptlrx may not have it. Offline: check the `.lrc` filename and `LYRIZ_MUSIC_DIR` |
| `command not found` | `~/.local/bin` isn't on your PATH (step 4) |
| Japanese lines not romanized | `pykakasi` isn't installed (step 1) |
| White text only | The matugen colors file doesn't exist at the path above |
