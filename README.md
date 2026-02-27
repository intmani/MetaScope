# MetaScope

MetaScope is a terminal tool for inspecting and editing metadata in **image** and **audio** files.

It provides a guided interactive flow to:
- show basic file information (size, created, modified)
- read image EXIF metadata
- read GPS coordinates when available
- read audio ID3 metadata
- edit common audio tags (artist, title, album, genre, date)
- add/change/remove audio comment and cover art

---

## Requirements

- Python 3.9+
- Dependencies listed in `requirements.txt`

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Run

From the project root:

```bash
python metadata_.py
```

The program will ask you to enter a file path.

---

## Supported File Categories

File type mapping is defined in `config.json`.

Current relevant categories for metadata handling:
- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`
- **Audio**: `.mp3`, `.wav`, `.flac`, `.aac`

> Note: Metadata editing is implemented for audio via ID3 tags (most commonly MP3).

---

## Usage Notes

- You can paste paths wrapped in single or double quotes.
- `~` home-directory paths are supported.
- If the file path is invalid or points to a folder, MetaScope will display an error instead of crashing.
- If EXIF/ID3 metadata is missing or malformed, MetaScope attempts to fail gracefully with a readable message.

### Examples

```text
📂 Enter the file path: ~/Music/song.mp3
```

```text
📂 Enter the file path: "C:\\Users\\you\\Pictures\\photo.jpg"
```

---

## Audio Editing Controls

When editing audio metadata:
- Enter `.` to skip a field.
- For existing comments:
  - enter `` ` `` at the start to delete
  - enter `.` to skip
- For cover art:
  - choose Delete / Change / No action when a cover exists
  - add a new image path when no cover exists

---

## Troubleshooting

- **`config.json not found`**
  - Run the script from the project root where `config.json` exists.
- **Unsupported file type**
  - Add extension mapping to `config.json` if needed.
- **Unable to read metadata**
  - The file may be corrupted or not contain metadata blocks.

---

## Project Files

- `metadata_.py` — main interactive metadata tool
- `config.json` — file extension to category mapping
- `requirements.txt` — Python dependencies
