import argparse

from downloader import YouTubeDownloader, SUPPORTED_FORMATS


def main():
    parser = argparse.ArgumentParser(description="Download YouTube links as mp3, mp4, webm, mov or mpeg.")
    parser.add_argument("-f", "--format", choices=SUPPORTED_FORMATS, default="mp3",
                        help="output format (default: mp3)")
    parser.add_argument("-o", "--output", default=None,
                        help="output folder (default: <format>_downloads)")
    parser.add_argument("urls", nargs="*", help="YouTube links (default: the example link)")
    args = parser.parse_args()

    # Example array of YouTube links
    links = args.urls or [
        "https://www.youtube.com/watch?v=QyvREl7epGY"
    ]

    downloader = YouTubeDownloader(output_path=args.output or f"{args.format}_downloads", fmt=args.format)
    print(f"Starting download process ({args.format})...")
    results = downloader.download(links)

    print("\nDownload Summary:")
    for result in results:
        status = result['status']
        url = result['url']
        if status == 'success':
            print(f"[OK] {url}")
        else:
            print(f"[ERROR] {url}: {result.get('error')}")


if __name__ == "__main__":
    main()
