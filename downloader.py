import yt_dlp
import os

class YouTubeAudioDownloader:
    def __init__(self, output_path='downloads'):
        self.output_path = output_path
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

    def download(self, urls):
        """
        Downloads an array of YouTube URLs and converts them to MP3.
        """
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
        }

        results = []
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for url in urls:
                try:
                    print(f"Downloading: {url}")
                    ydl.download([url])
                    results.append({"url": url, "status": "success"})
                except Exception as e:
                    print(f"Error downloading {url}: {e}")
                    results.append({"url": url, "status": "failed", "error": str(e)})
        
        return results
