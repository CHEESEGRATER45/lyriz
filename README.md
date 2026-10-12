# lyriz

Live synced lyrics in your terminal, rendered as big ASCII text and colored to your current wallpaper accent. Japanese and Bangla lines are auto-romanized so you can sing along.

ss

## Features

- Big figlet-style lyrics, one line at a time, synced via [sptlrx](https://github.com/raitonoberu/sptlrx)
- Accent color follows your matugen palette
- Japanese romanization via kakasi, Bangla via `bangla_romanize.py`
- Works with Spotify through MPRIS

## Requirements

- Arch Linux (other distros should work, but untested)
- [illogical-impulse / dots-hyprland](https://github.com/end-4/dots-hyprland) or anything else that writes matugen colors to `~/.local/state/quickshell/user/generated/colors.json`
- `sptlrx-bin`, `figlet`, `kakasi`, `jq`
- Python package `indic-transliteration`
- Spotify open and playing

## Install

```bash
yay -S sptlrx-bin figlet kakasi jq
pip install indic-transliteration --break-system-packages

git clone https://github.com/CHEESEGRATER45/lyriz
cd lyriz
mkdir -p ~/.local/bin ~/.config/sptlrx
cp lyriz-launch bangla_romanize.py ~/.local/bin/
chmod +x ~/.local/bin/lyriz-launch ~/.local/bin/bangla_romanize.py
```

Already have an sptlrx config? Back it up first, since this overwrites it:

```bash
cp ~/.config/sptlrx/config.yaml ~/.config/sptlrx/config.yaml.bak
cp config.yaml.example ~/.config/sptlrx/config.yaml
```

Make sure `~/.local/bin` is in your `PATH`.

## Usage

Run it directly:

```bash
lyriz-launch
```

Or bind it to a key. Hyprland example:

```
bind = SUPER, L, exec, kitty -e ~/.local/bin/lyriz-launch
```

## How it works

`sptlrx pipe` can't be piped straight into figlet because the output garbles. lyriz instead loops over each line and clears the screen between them.

## Roadmap

- [ ] Local mp3 + `.lrc` playback (e.g. files from spodsync)
- [ ] Fallback accent color when no matugen colors are found

## Credits

[sptlrx](https://github.com/raitonoberu/sptlrx), [kakasi](https://github.com/miurahr/pykakasi), [indic-transliteration](https://github.com/indic-transliteration/indic_transliteration_py), figlet.

## License

MIT, see [LICENSE](LICENSE).
