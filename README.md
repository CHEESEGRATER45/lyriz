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
cp lyriz-launch bangla_romanize.py ~/.local/bin/
chmod +x ~/.local/bin/lyriz-launch ~/.local/bin/bangla_romanize.py
cp config.yaml.example ~/.config/sptlrx/config.yaml
```

Bind a hotkey to `kitty -e ~/.local/bin/lyriz-launch` to open it in a new terminal window.

## Notes
- Color comes from `~/.local/state/quickshell/user/generated/colors.json` (matugen)
- Don't pipe `sptlrx pipe | figlet` directly — it garbles. Loop + clear per line instead.
