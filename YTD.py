#!/usr/bin/env python3
"""
YouTube Downloader (Python 3.10+)

Install dependencies:
  1) yt-dlp:
     pip install yt-dlp
  2) ffmpeg (required for merging video+audio and mp3 conversion):
     - macOS:   brew install ffmpeg
     - Ubuntu:  sudo apt install ffmpeg
     - Windows: choco install ffmpeg   (or download from https://ffmpeg.org)

Usage:
  python youtube_downloader.py
"""

from __future__ import annotations

import math
import re
import sys
from typing import Any

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


def bytes_to_human(size: int | None) -> str:
    """Convert bytes to a readable value."""
    if not size or size <= 0:
        return "N/A"

    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024
    return "N/A"


def clean_text(text: str) -> str:
    """Normalize text for cleaner terminal output."""
    return re.sub(r"\s+", " ", text).strip()


def fetch_video_info(url: str) -> dict[str, Any]:
    """Fetch metadata without downloading."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)


def build_format_rows(info: dict[str, Any]) -> list[dict[str, Any]]:
    """Create a simplified list of downloadable formats for display/selection."""
    rows: list[dict[str, Any]] = []
    formats = info.get("formats", [])

    for fmt in formats:
        fmt_id = fmt.get("format_id")
        if not fmt_id:
            continue

        vcodec = fmt.get("vcodec") or "none"
        acodec = fmt.get("acodec") or "none"
        has_video = vcodec != "none"
        has_audio = acodec != "none"

        kind = "video+audio" if has_video and has_audio else "video-only" if has_video else "audio-only" if has_audio else "other"
        ext = fmt.get("ext") or "?"
        resolution = fmt.get("resolution") or (f"{fmt.get('width')}x{fmt.get('height')}" if fmt.get("width") and fmt.get("height") else "audio")
        fps = fmt.get("fps")
        abr = fmt.get("abr")
        tbr = fmt.get("tbr")
        size = fmt.get("filesize") or fmt.get("filesize_approx")
        note = clean_text(fmt.get("format_note") or "")

        rows.append(
            {
                "format_id": str(fmt_id),
                "kind": kind,
                "ext": ext,
                "resolution": resolution,
                "fps": fps,
                "abr": abr,
                "tbr": tbr,
                "size": size,
                "note": note,
                "has_video": has_video,
                "has_audio": has_audio,
            }
        )

    def sort_key(row: dict[str, Any]) -> tuple[int, float, float]:
        pref = {"video+audio": 0, "video-only": 1, "audio-only": 2}.get(row["kind"], 3)
        tbr_value = float(row["tbr"] or 0)
        abr_value = float(row["abr"] or 0)
        return pref, -tbr_value, -abr_value

    return sorted(rows, key=sort_key)


def display_formats(rows: list[dict[str, Any]]) -> None:
    """Print available formats in a compact table."""
    print("\nAvailable formats:")
    print("-" * 120)
    print(f"{'Idx':<4} {'ID':<8} {'Type':<11} {'Ext':<5} {'Resolution':<12} {'FPS':<5} {'Bitrate':<10} {'Size':<10} Note")
    print("-" * 120)

    for idx, row in enumerate(rows):
        bitrate = row["tbr"] or row["abr"]
        bitrate_text = f"{bitrate:.0f}k" if isinstance(bitrate, (int, float)) and not math.isnan(bitrate) else "N/A"
        fps_text = str(int(row["fps"])) if isinstance(row["fps"], (int, float)) else "-"
        print(
            f"{idx:<4} {row['format_id']:<8} {row['kind']:<11} {row['ext']:<5} {str(row['resolution']):<12} "
            f"{fps_text:<5} {bitrate_text:<10} {bytes_to_human(row['size']):<10} {row['note']}"
        )


def choose_mode() -> str:
    """Let the user choose normal, audio-only, or auto-best mode."""
    print("\nDownload mode:")
    print("  1) Select specific format manually")
    print("  2) Download highest available quality automatically")
    print("  3) Download audio only (mp3)")

    while True:
        choice = input("Enter 1, 2, or 3: ").strip()
        if choice == "1":
            return "manual"
        if choice == "2":
            return "auto"
        if choice == "3":
            return "audio"
        print("Invalid choice. Please enter 1, 2, or 3.")


def choose_format(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Allow choosing by table index or direct format_id."""
    by_id = {row["format_id"]: row for row in rows}

    while True:
        raw = input("\nEnter format index or format ID: ").strip()
        if raw == "":
            print("Please enter a value.")
            continue

        if raw.isdigit():
            idx = int(raw)
            if 0 <= idx < len(rows):
                return rows[idx]

        if raw in by_id:
            return by_id[raw]

        print("Invalid selection. Use a valid index or format ID from the list.")


def progress_hook(status: dict[str, Any]) -> None:
    """Display download progress in-place."""
    if status.get("status") == "downloading":
        percent = status.get("_percent_str", "").strip()
        speed = status.get("_speed_str", "").strip()
        eta = status.get("_eta_str", "").strip()
        print(f"\rDownloading... {percent:>8} | Speed: {speed:>10} | ETA: {eta:>8}", end="", flush=True)
    elif status.get("status") == "finished":
        print("\nDownload phase finished, finalizing file...")


def download_with_selection(url: str, selected: dict[str, Any]) -> None:
    """Download chosen format and merge audio automatically when needed."""
    fmt_id = selected["format_id"]

    if selected["has_video"] and not selected["has_audio"]:
        # Video-only stream selected: combine with best available audio using ffmpeg.
        format_string = f"{fmt_id}+bestaudio/best"
    else:
        format_string = fmt_id

    ydl_opts = {
        "format": format_string,
        "noplaylist": True,
        "outtmpl": "%(title).200B [%(id)s].%(ext)s",
        "progress_hooks": [progress_hook],
        "merge_output_format": "mp4",
        "restrictfilenames": False,
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def download_auto_best(url: str) -> None:
    """Download best video+audio, with fallback to best overall."""
    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "noplaylist": True,
        "outtmpl": "%(title).200B [%(id)s].%(ext)s",
        "progress_hooks": [progress_hook],
        "merge_output_format": "mp4",
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def download_audio_mp3(url: str) -> None:
    """Download best audio and convert to mp3 via ffmpeg."""
    ydl_opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "outtmpl": "%(title).200B [%(id)s].%(ext)s",
        "progress_hooks": [progress_hook],
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def main() -> int:
    """Main workflow: gather URL, show formats, choose mode, and download."""
    print("YouTube Downloader (yt-dlp)")
    url = input("Enter YouTube video URL: ").strip()

    if not url:
        print("Error: URL cannot be empty.")
        return 1

    try:
        info = fetch_video_info(url)
        title = info.get("title", "Unknown title")
        uploader = info.get("uploader", "Unknown uploader")
        print(f"\nTitle   : {title}")
        print(f"Uploader: {uploader}")

        mode = choose_mode()

        if mode == "audio":
            download_audio_mp3(url)
            print("\nDone: audio downloaded as mp3.")
            return 0

        if mode == "auto":
            download_auto_best(url)
            print("\nDone: best available quality downloaded.")
            return 0

        rows = build_format_rows(info)
        if not rows:
            print("No downloadable formats found for this URL.")
            return 1

        display_formats(rows)
        selected = choose_format(rows)
        print(f"\nSelected format: ID={selected['format_id']} ({selected['kind']}, {selected['resolution']}, {selected['ext']})")

        download_with_selection(url, selected)
        print("\nDone: download completed successfully.")
        return 0

    except DownloadError as exc:
        print(f"\nDownload error: {exc}")
        print("Tip: Check URL validity, internet connection, and whether ffmpeg is installed.")
        return 1
    except KeyboardInterrupt:
        print("\nOperation canceled by user.")
        return 130
    except Exception as exc:  # Catch unexpected issues gracefully.
        print(f"\nUnexpected error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
