# Lyriz

Lyriz is a terminal-based lyrics display for Linux. It follows music playing through MPRIS-compatible players, prioritizes local `.lrc` lyric files, and renders lyrics as large ASCII text using your current Matugen accent color.

It supports Japanese and Bangla romanization, making lyrics easier to read without requiring knowledge of their original scripts.

<img width="1920" height="1078" alt="image" src="https://github.com/user-attachments/assets/002e471d-c850-435f-a302-be947aac7555" /

## Features

- Prioritizes local `.lrc` lyric files.
- Supports MPRIS-compatible music players.
- Romanizes Japanese lyrics using `pykakasi`.
- Supports Bangla romanization through the included helper script.
- Uses the primary color from your generated Matugen color configuration.
- Displays lyrics using `figlet`.
- Supports local music playback alongside compatible streaming players.

## Requirements

- Linux
- Python 3
- `figlet`
- `jq`
- `pykakasi`
- An MPRIS-compatible music player
- Matugen-generated colors for dynamic terminal colors

## Installation

### 1. Install dependencies

On Arch Linux:

```bash
sudo pacman -S python figlet jq
yay -S python-pykakasi
```

### 2. Clone the repository

```bash
git clone https://github.com/CHEESEGRATER45/lyriz.git
cd lyriz
```

### 3. Install the scripts

```bash
mkdir -p ~/.local/bin
cp lyriz-launch lyriz-local-first.py lyriz-romanize.py bangla_romanize.py ~/.local/bin/
chmod +x ~/.local/bin/lyriz-launch
```

Keep all four files in `~/.local/bin/`, as the launcher calls the helper scripts from that directory.

### 4. Run Lyriz

Start playback in a supported music player, then run:

```bash
~/.local/bin/lyriz-launch
```

To launch it in a separate Kitty terminal:

```bash
kitty -e ~/.local/bin/lyriz-launch
```

## Local Lyrics

Lyriz prioritizes local `.lrc` files when matching lyrics to the currently playing track.

For better matching, name lyric files using the track title and artist.

Example:

```text
AIZO - King Gnu.lrc
```

Standard LRC files contain timestamps followed by lyric lines:

```text
[00:12.30]First lyric line
[00:15.80]Second lyric line
[00:19.20]Third lyric line
```

The local lyrics helper handles matching files to the current track. Online fallback behavior depends on the implementation and configuration of the helper.

## Romanization

Lyriz can romanize supported lyrics before displaying them.

- **Japanese:** Uses `pykakasi` to convert Japanese text into Latin-script pronunciation.
- **Bangla:** Uses the included `bangla_romanize.py` helper.
- **Other text:** Passes through text that does not match the supported scripts.

Romanization represents pronunciation rather than translation.

## Matugen Integration

Lyriz reads the primary accent color from:

```text
~/.local/state/quickshell/user/generated/colors.json
```

The launcher uses this color to style the terminal output. If the file is missing or the color cannot be parsed, the text defaults to white.

## Troubleshooting

### Lyrics are not appearing

- Make sure a supported music player is running and playing a track.
- Verify that the player exposes its metadata through MPRIS.
- Check that a matching `.lrc` file exists if you expect local lyrics.
- Check the lyric source and fallback behavior configured in your installation.

### Japanese romanization is not working

- Verify that `pykakasi` is installed in the Python environment used by Lyriz.
- Ensure `lyriz-romanize.py` exists in `~/.local/bin/`.

### Bangla romanization is not working

- Ensure `bangla_romanize.py` exists in `~/.local/bin/`.
- Test the helper independently to identify any missing dependencies or errors.

### Matugen colors are not appearing

- Verify that `colors.json` exists at the expected path.
- Ensure the file contains a valid `primary` hexadecimal color.

## Project Structure

```text
lyriz/
├── README.md
├── bangla_romanize.py
├── config.yaml.example
├── lyriz-launch
├── lyriz-local-first.py
└── lyriz-romanize.py
```

## License

See the repository for license information.


