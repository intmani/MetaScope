import os
import json
from io import BytesIO
from datetime import datetime
from PIL import Image, ExifTags
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, COMM, APIC
from exif import Image as IM
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
console = Console()


def normalize_path(path):
    return os.path.expanduser(path.strip().strip('"').strip("'"))


# ---------------- Utils ---------------- #
def get_category(path):
    try:
        with open("config.json", 'r', encoding="utf-8") as config:
            config_file = json.load(config)
    except FileNotFoundError:
        console.print("[red]❌ config.json not found.[/red]")
        return "Others"
    except json.JSONDecodeError:
        console.print("[red]❌ config.json is invalid JSON.[/red]")
        return "Others"

    split = os.path.splitext(path)
    for category, suffixes in config_file.items():
        if split[1].lower() in suffixes:
            return category
    return "Others"

def basic_metadata(path):
    size = f"{round(os.path.getsize(path)/1048576,2)} MB"
    created = datetime.fromtimestamp(int(os.path.getctime(path)))
    modified = datetime.fromtimestamp(int(os.path.getmtime(path)))

    table = Table(title="📁 Basic File Info")
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    table.add_row("Size", size)
    table.add_row("Created", str(created))
    table.add_row("Modified", str(modified))

    console.print(table)
    return modified

def decimal_coordinate(coordinate, ref):
    degrees = coordinate[0] + coordinate[1] / 60 + coordinate[2] / 3600
    return -degrees if ref in ("S", "W") else degrees

def image_coordinate(path):
    try:
        with open(path, 'rb') as image:
            img = IM(image)
            if img.has_exif:
                try:
                    coordinate = (
                        decimal_coordinate(img.gps_latitude, img.gps_latitude_ref),
                        decimal_coordinate(img.gps_longitude, img.gps_longitude_ref)
                    )
                except AttributeError:
                    console.print("[red]❌ No GPS data found.[/red]")
                    return None
            else:
                console.print("[red]❌ This image has no EXIF information.[/red]")
                return None
    except Exception as error:
        console.print(f"[red]❌ Failed to read GPS data: {error}[/red]")
        return None

    console.print("\n🌍 [bold green]Location Info:[/bold green]")
    console.print(f"   • Latitude : [cyan]{coordinate[0]}[/cyan]")
    console.print(f"   • Longitude: [cyan]{coordinate[1]}[/cyan]")
    return "Be creative ;)"

def image_metadata(path):
    try:
        basic_metadata(path)
        photo = Image.open(path)
        exif = Image.Image.getexif(photo)
    except Exception as error:
        console.print(f"[red]❌ Unable to read image metadata: {error}[/red]")
        return None

    table = Table(title="🖼 EXIF Metadata")
    table.add_column("Tag", style="cyan")
    table.add_column("Value", style="magenta")

    if exif:
        for tag, value in exif.items():
            label = ExifTags.TAGS.get(tag, tag)
            table.add_row(str(label), str(value))
    else:
        table.add_row("EXIF", "❌ No EXIF metadata")

    console.print(table)
    console.print(f"[yellow]Format: {photo.format}[/yellow]")

    if Confirm.ask("🔎 Do you want to check GPS location data?"):
        return image_coordinate(path)
    return None

def audio_metadata(path):
    try:
        basic_metadata(path)
        audio_mp3 = MP3(path)
        audio_id3 = ID3(path)
        try:
            audio_easy = EasyID3(path)
        except Exception:
            audio_easy = {}
    except Exception as error:
        console.print(f"[red]❌ Unable to read audio metadata: {error}[/red]")
        return None

    # Table for audio tags
    table = Table(title="🎵 Audio Metadata")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="magenta")

    if audio_easy:
        for index in audio_easy:
            value = audio_easy.get(index)
            if value:
                table.add_row(index.capitalize(), value[0])
    else:
        table.add_row("Tags", "❌ No easy ID3 tags")

    if "COMM::eng" in audio_id3:
        table.add_row("Comment", audio_id3["COMM::eng"].text[0])
    else:
        table.add_row("Comment", "❌ None")

    has_cover = any(k.startswith("APIC") for k in audio_id3.keys())
    table.add_row("Cover", "✅ Exists" if has_cover else "❌ None")

    table.add_row("Duration", f"{round(audio_mp3.info.length / 60, 2)} min")
    table.add_row("Bitrate", f"{round(audio_mp3.info.bitrate / 1000, 2)} kbps")

    console.print(table)

    if has_cover and Confirm.ask("🖼 Do you want to view the cover image?"):
        cover_key = next(k for k in audio_id3.keys() if k.startswith("APIC"))
        cover_data = audio_id3[cover_key].data
        try:
            cover_image = Image.open(BytesIO(cover_data))
            cover_image.show()
        except Exception as error:
            console.print(f"[red]❌ Failed to open cover image: {error}[/red]")

    if Confirm.ask("✏️ Do you want to edit this audio file's metadata?"):
        console.print("[yellow]Tip: Enter (.) to skip a field.[/yellow]")
        return edit_audio(path)
    return "Be Creative ;)"

def set_if_not_skip(audio, key, prompt):
    value = Prompt.ask(f"{prompt}", default=".")
    if value.strip() != "." and value.strip() != "":
        audio[key] = value

def edit_audio(path):
    try:
        audio_easy = EasyID3(path)
    except Exception:
        audio_easy = EasyID3()
        audio_easy.save(path)
        audio_easy = EasyID3(path)
    set_if_not_skip(audio_easy, "artist", "Artist")
    set_if_not_skip(audio_easy, "title", "Title")
    set_if_not_skip(audio_easy, "album", "Album")
    set_if_not_skip(audio_easy, "genre", "Genre")
    set_if_not_skip(audio_easy, "date", "Date")
    audio_easy.save()

    try:
        audio_id3 = ID3(path)
    except Exception:
        audio_id3 = ID3()

    # Comments
    if "COMM::eng" in audio_id3:
        comment = Prompt.ask("💬 Enter new comment (`=delete, .=skip)")
        if comment and comment[0] == "`":
            del audio_id3["COMM::eng"]
        elif comment and comment[0] != ".":
            audio_id3.add(COMM(encoding=3, lang="eng", desc="", text=comment))
    else:
        if Confirm.ask("No comment found. Do you want to add one?"):
            comment = Prompt.ask("💬 Enter your comment")
            audio_id3.add(COMM(encoding=3, lang="eng", desc="", text=comment))

    # Cover
    has_cover = any(k.startswith("APIC") for k in audio_id3.keys())
    if has_cover:
        action = Prompt.ask("This file has a cover. [D]elete / [C]hange / [N]o action", default="N").lower()
        if action == "d":
            for k in list(audio_id3.keys()):
                if k.startswith("APIC"):
                    del audio_id3[k]
        elif action == "c":
            for k in list(audio_id3.keys()):
                if k.startswith("APIC"):
                    del audio_id3[k]
            enter = normalize_path(Prompt.ask("Enter the path of the new cover"))
            try:
                with open(enter, 'rb') as cover:
                    new_cover = cover.read()
                    mime_type = "image/jpeg" if enter.lower().endswith((".jpg", ".jpeg")) else "image/png"
                    audio_id3.add(APIC(encoding=3, mime=mime_type, type=3, desc="Cover", data=new_cover))
            except OSError as error:
                console.print(f"[red]❌ Failed to update cover: {error}[/red]")
    else:
        if Confirm.ask("No cover found. Do you want to add one?"):
            enter = normalize_path(Prompt.ask("Enter the path of the cover image"))
            try:
                with open(enter, 'rb') as cover:
                    new_cover = cover.read()
                    mime_type = "image/jpeg" if enter.lower().endswith((".jpg", ".jpeg")) else "image/png"
                    audio_id3.add(APIC(encoding=3, mime=mime_type, type=3, desc="Cover", data=new_cover))
            except OSError as error:
                console.print(f"[red]❌ Failed to add cover: {error}[/red]")

    audio_id3.save(path, v2_version=3)

    console.print("\n[bold green]✅ Metadata updated successfully![/bold green]")
    return audio_metadata(path)

def handler():
    general = normalize_path(Prompt.ask("📂 Enter the file path"))

    if not os.path.exists(general):
        console.print("[red]❌ File not found. Please enter a valid path.[/red]")
        return None
    if not os.path.isfile(general):
        console.print("[red]❌ The provided path is not a file.[/red]")
        return None

    category = get_category(general).lower()

    if category == "images":
        return image_metadata(general)
    elif category == "audio":
        return audio_metadata(general)
    else:
        console.print("[red]⚠ Unsupported file type.[/red]")
        return None

if __name__ == "__main__":
    print(handler())
