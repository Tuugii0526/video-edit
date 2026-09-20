#!/usr/bin/env python3
import os
import sys
import re
import subprocess
import urllib.request
import urllib.parse
import json
import argparse
import webbrowser

# Define paths
DOWNLOADS_DIR = "mp3_downloads"
PROCESSED_DIR = os.path.join(DOWNLOADS_DIR, "processed")

# Ensure directories exist
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Tempo constants for audio processing
SLOW_TEMP = 0.5
FAST_TEMP = 5.0


# ANSI terminal colors
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def get_songs():
    """
    Scans the DOWNLOADS_DIR for MP3 files and returns a sorted list.
    """
    if not os.path.exists(DOWNLOADS_DIR):
        return []
    files = [f for f in os.listdir(DOWNLOADS_DIR) if f.lower().endswith(".mp3")]
    return sorted(files)


def parse_filename(filename):
    """
    Extracts Artist and Title from the song's filename.
    Removes common tags like (Official Video), [HQ], etc.
    """
    # Remove file extension
    name, _ = os.path.splitext(filename)

    # Remove metadata in brackets or parentheses
    name = re.sub(r"\s*[\(\[][^\)\]]*[\)\]]\s*", " ", name)
    # Replace multiple spaces with single space
    name = re.sub(r"\s+", " ", name).strip()

    # Try splitting by common separators
    separators = [r"\s*-\s*", r"\s*\|\s*", r"\s*•\s*", r"\s*｜\s*"]
    parts = []
    for sep in separators:
        match = re.split(sep, name, maxsplit=1)
        if len(match) == 2:
            parts = [p.strip() for p in match]
            break

    if len(parts) == 2:
        artist, title = parts[0], parts[1]
    else:
        artist, title = "Unknown", name

    return artist, title


def run_ffmpeg(args):
    """
    Runs an ffmpeg command via subprocess.
    """
    try:
        # Run ffmpeg with stdout and stderr redirected to capture any error messages
        result = subprocess.run(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if result.returncode != 0:
            return False, result.stderr
        return True, None
    except Exception as e:
        return False, str(e)


def slow_song(song_path, output_path):
    """
    Slows down a song to SLOW_TEMP speed using atempo filter.
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        song_path,
        "-filter:a",
        f"atempo={SLOW_TEMP}",
        output_path,
    ]
    return run_ffmpeg(cmd)


def fast_song(song_path, output_path):
    """
    Speeds up a song to FAST_TEMP speed using atempo filter.
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        song_path,
        "-filter:a",
        f"atempo={FAST_TEMP}",
        output_path,
    ]
    return run_ffmpeg(cmd)


def reverse_song(song_path, output_path):
    """
    Reverses a song using areverse filter.
    Note: areverse loads the entire audio segment in memory, which works perfectly for songs.
    """
    cmd = ["ffmpeg", "-y", "-i", song_path, "-filter:a", "areverse", output_path]
    return run_ffmpeg(cmd)


def fetch_lyrics(artist, title):
    """
    Fetches lyrics from api.lyrics.ovh.
    Returns lyrics string if found, otherwise None.
    """
    if artist == "Unknown":
        return None

    # Standardize artist and title for URL encoding
    safe_artist = urllib.parse.quote(artist)
    safe_title = urllib.parse.quote(title)
    url = f"https://api.lyrics.ovh/v1/{safe_artist}/{safe_title}"

    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("lyrics")
    except Exception:
        return None


def open_lyrics_search_in_browser(artist, title):
    """
    Fallback method to open a Google lyrics search in the default browser.
    """
    query = f"{artist} {title} lyrics"
    search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    webbrowser.open(search_url)


def display_menu(songs):
    """
    Displays the interactive CLI menu.
    """
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== 🎵 MP3 AUDIO CLI TOOL ==={Colors.ENDC}")
    print(f"Available songs in {Colors.CYAN}{DOWNLOADS_DIR}/{Colors.ENDC}:")

    for idx, song in enumerate(songs, 1):
        artist, title = parse_filename(song)
        print(
            f"  [{Colors.GREEN}{idx}{Colors.ENDC}] {Colors.BOLD}{artist}{Colors.ENDC} - {title}"
        )

    print("\n" + "=" * 30)
    print(f"[{Colors.CYAN}1{Colors.ENDC}] Slow down a song ({SLOW_TEMP}x)")
    print(f"[{Colors.CYAN}2{Colors.ENDC}] Speed up a song ({FAST_TEMP}x)")
    print(f"[{Colors.CYAN}3{Colors.ENDC}] Reverse a song")
    print(f"[{Colors.CYAN}4{Colors.ENDC}] Read lyrics (ug unshih)")
    print(f"[{Colors.CYAN}5{Colors.ENDC}] Exit")
    print("=" * 30)


def main():
    parser = argparse.ArgumentParser(
        description="Process MP3 files (Slow down, Speed up, Reverse, Get Lyrics)"
    )
    parser.add_argument("--song", type=int, help="Index of the song to process")
    parser.add_argument(
        "--slow", action="store_true", help="Slow down the selected song"
    )
    parser.add_argument(
        "--fast", action="store_true", help="Speed up the selected song"
    )
    parser.add_argument(
        "--reverse", action="store_true", help="Reverse the selected song"
    )
    parser.add_argument(
        "--lyrics", action="store_true", help="Fetch lyrics for the selected song"
    )
    parser.add_argument("--list", action="store_true", help="List all available songs")
    parser.add_argument(
        "-s",
        "--slow-temp",
        type=float,
        default=5.0,
        help="Tempo multiplier for slowing down audio (default: 0.5)",
    )
    parser.add_argument(
        "-f",
        "--fast-temp",
        type=float,
        default=10.0,
        help="Tempo multiplier for speeding up audio (default: 3.0)",
    )

    args = parser.parse_args()

    global SLOW_TEMP, FAST_TEMP
    SLOW_TEMP = args.slow_temp
    FAST_TEMP = args.fast_temp

    songs = get_songs()

    if not songs:
        print(
            f"{Colors.FAIL}Error: No MP3 files found in the '{DOWNLOADS_DIR}' directory.{Colors.ENDC}"
        )
        print("Please download some songs first or check the directory structure.")
        sys.exit(1)

    # Check if any action or song option is provided to enter argument-driven mode
    is_arg_mode = (
        args.song is not None
        or args.slow
        or args.fast
        or args.reverse
        or args.lyrics
        or args.list
    )

    # Argument driven mode
    if is_arg_mode:
        if args.list:
            print(f"\n{Colors.HEADER}--- Song Catalog ---{Colors.ENDC}")
            for idx, song in enumerate(songs, 1):
                artist, title = parse_filename(song)
                print(f"[{idx}] {artist} - {title}")
            return

        if args.song is None:
            print(
                f"{Colors.FAIL}Error: Please specify a song index with --song <index>{Colors.ENDC}"
            )
            sys.exit(1)

        if args.song < 1 or args.song > len(songs):
            print(
                f"{Colors.FAIL}Error: Song index out of range (1-{len(songs)}){Colors.ENDC}"
            )
            sys.exit(1)

        song_idx = args.song - 1
        song_name = songs[song_idx]
        song_path = os.path.join(DOWNLOADS_DIR, song_name)
        artist, title = parse_filename(song_name)

        print(f"\nSelected: {Colors.BOLD}{artist} - {title}{Colors.ENDC}")

        if args.slow:
            out_name = f"[Slow] {song_name}"
            out_path = os.path.join(PROCESSED_DIR, out_name)
            print(
                f"Slowing down song... Saving to {Colors.GREEN}{out_path}{Colors.ENDC}"
            )
            success, err = slow_song(song_path, out_path)
            if success:
                print(f"{Colors.GREEN}✔ Success! Output file is ready.{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}✖ Failed! FFMpeg Error: {err}{Colors.ENDC}")

        elif args.fast:
            out_name = f"[Fast] {song_name}"
            out_path = os.path.join(PROCESSED_DIR, out_name)
            print(
                f"Speeding up song... Saving to {Colors.GREEN}{out_path}{Colors.ENDC}"
            )
            success, err = fast_song(song_path, out_path)
            if success:
                print(f"{Colors.GREEN}✔ Success! Output file is ready.{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}✖ Failed! FFMpeg Error: {err}{Colors.ENDC}")

        elif args.reverse:
            out_name = f"[Reversed] {song_name}"

            out_path = os.path.join(PROCESSED_DIR, out_name)
            print(f"Reversing song... Saving to {Colors.GREEN}{out_path}{Colors.ENDC}")
            success, err = reverse_song(song_path, out_path)
            if success:
                print(f"{Colors.GREEN}✔ Success! Output file is ready.{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}✖ Failed! FFMpeg Error: {err}{Colors.ENDC}")

        elif args.lyrics:
            print(
                f"Fetching lyrics for {Colors.CYAN}{artist} - {title}{Colors.ENDC}..."
            )
            lyrics = fetch_lyrics(artist, title)
            if lyrics:
                print(f"\n{Colors.GREEN}=== Lyrics ==={Colors.ENDC}")
                print(lyrics)
            else:
                print(
                    f"{Colors.WARNING}Lyrics not found in standard database.{Colors.ENDC}"
                )
                print("Opening search query in your web browser...")
                open_lyrics_search_in_browser(artist, title)
        else:
            print(
                f"{Colors.WARNING}No action specified. Try adding --slow, --fast, --reverse, or --lyrics{Colors.ENDC}"
            )
        return

    # Interactive mode
    while True:
        display_menu(songs)
        try:
            choice = input(
                f"\nSelect an action ({Colors.CYAN}1-5{Colors.ENDC}): "
            ).strip()
            if choice == "5":
                print(
                    f"\n{Colors.BLUE}Thank you for using MP3 Audio CLI! Goodbye. 👋{Colors.ENDC}"
                )
                break

            if choice not in ["1", "2", "3", "4"]:
                print(
                    f"{Colors.FAIL}Invalid action. Please enter 1, 2, 3, 4, or 5.{Colors.ENDC}"
                )
                continue

            song_idx_input = input(
                f"Enter the song index ({Colors.GREEN}1-{len(songs)}{Colors.ENDC}): "
            ).strip()
            try:
                song_idx = int(song_idx_input) - 1
                if song_idx < 0 or song_idx >= len(songs):
                    raise ValueError()
            except ValueError:
                print(
                    f"{Colors.FAIL}Invalid index. Please enter a number between 1 and {len(songs)}.{Colors.ENDC}"
                )
                continue

            song_name = songs[song_idx]
            song_path = os.path.join(DOWNLOADS_DIR, song_name)
            artist, title = parse_filename(song_name)

            print(f"\nProcessing: {Colors.BOLD}{artist} - {title}{Colors.ENDC}")

            if choice == "1":
                out_name = f"[Slow] {song_name}"
                out_path = os.path.join(PROCESSED_DIR, out_name)
                print(f"Slowing down audio... Saving to: {out_path}")
                success, err = slow_song(song_path, out_path)
                if success:
                    print(
                        f"{Colors.GREEN}✔ Successfully processed! File is stored in {Colors.UNDERLINE}{out_path}{Colors.ENDC}"
                    )
                else:
                    print(f"{Colors.FAIL}✖ Error executing FFmpeg: {err}{Colors.ENDC}")

            elif choice == "2":
                out_name = f"[Fast] {song_name}"
                out_path = os.path.join(PROCESSED_DIR, out_name)
                print(f"Speeding up audio... Saving to: {out_path}")
                success, err = fast_song(song_path, out_path)
                if success:
                    print(
                        f"{Colors.GREEN}✔ Successfully processed! File is stored in {Colors.UNDERLINE}{out_path}{Colors.ENDC}"
                    )
                else:
                    print(f"{Colors.FAIL}✖ Error executing FFmpeg: {err}{Colors.ENDC}")

            elif choice == "3":
                out_name = f"[Reversed] {song_name}"
                out_path = os.path.join(PROCESSED_DIR, out_name)
                print(f"Reversing audio... Saving to: {out_path}")
                success, err = reverse_song(song_path, out_path)
                if success:
                    print(
                        f"{Colors.GREEN}✔ Successfully processed! File is stored in {Colors.UNDERLINE}{out_path}{Colors.ENDC}"
                    )
                else:
                    print(f"{Colors.FAIL}✖ Error executing FFmpeg: {err}{Colors.ENDC}")

            elif choice == "4":
                print(f"Searching lyrics for '{artist} - {title}'...")
                lyrics = fetch_lyrics(artist, title)
                if lyrics:
                    print(
                        f"\n{Colors.GREEN}=== Lyrics for {artist} - {title} ==={Colors.ENDC}\n"
                    )
                    print(lyrics)
                else:
                    print(
                        f"{Colors.WARNING}Lyrics not found in database. Opening browser search fallback...{Colors.ENDC}"
                    )
                    open_lyrics_search_in_browser(artist, title)

            input(f"\n{Colors.BLUE}Press Enter to return to main menu...{Colors.ENDC}")

        except KeyboardInterrupt:
            print(f"\n\n{Colors.BLUE}Exiting CLI. Have a great day! 👋{Colors.ENDC}")
            break
        except Exception as e:
            print(f"\n{Colors.FAIL}An error occurred: {e}{Colors.ENDC}")


if __name__ == "__main__":
    main()
