# lyriz

Live Spotify lyrics in a terminal, rendered as big ASCII text, colored to your
current wallpaper accent. Japanese and Bangla lines get auto-romanized to
English pronunciation.

<img width="1920" height="1078" alt="image" src="https://github.com/user-attachments/assets/002e471d-c850-435f-a302-be947aac7555" />


## Requires
- sptlrx-bin, figlet, kakasi, jq
- `pip install indic-transliteration --break-system-packages`
- Spotify open and playing (uses MPRIS)

## Install
```fish
cp lyriz-launch lyriz-launch-inner bangla_romanize.py ~/.local/bin/
chmod +x ~/.local/bin/lyriz-launch*
cp config.yaml.example ~/.config/sptlrx/config.yaml
```

Bind `lyriz-launch` to a hotkey to open it.

## Notes
- Color comes from `~/.local/state/quickshell/user/generated/colors.json` (matugen)
- Don't pipe `sptlrx pipe | figlet` directly — it garbles. Loop + clear per line instead.
