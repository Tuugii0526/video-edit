from downloader import YouTubeAudioDownloader

def main():
    # Example array of YouTube links
    links = [
"https://www.youtube.com/watch?v=QyvREl7epGY"
]


    downloader = YouTubeAudioDownloader(output_path='mp3_downloads')
    print("Starting download process...")
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
