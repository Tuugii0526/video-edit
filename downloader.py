import os
import subprocess

import yt_dlp

SUPPORTED_FORMATS = ('mp3', 'mp4', 'webm', 'mov', 'mpeg')


class YouTubeDownloader:
    def __init__(self, output_path='downloads', fmt='mp3'):
        fmt = fmt.lower()
        if fmt not in SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format '{fmt}'. Choose from: {', '.join(SUPPORTED_FORMATS)}")
        self.output_path = output_path
        self.fmt = fmt
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

    def _format_opts(self):
        if self.fmt == 'mp3':
            return {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
        if self.fmt == 'mp4':
            return {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'merge_output_format': 'mp4',
            }
        if self.fmt == 'mov':
            # video/quicktime
            return {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'merge_output_format': 'mp4',
                'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mov'}],
            }
        if self.fmt == 'mpeg':
            # video/mpeg: download mp4 first, then convert with ffmpeg (see _to_mpeg)
            return {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'merge_output_format': 'mp4',
            }
        return {
            'format': 'bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]/best',
            'merge_output_format': 'webm',
        }

    @staticmethod
    def _to_mpeg(src):
        dst = os.path.splitext(src)[0] + '.mpeg'
        subprocess.run(
            ['ffmpeg', '-y', '-i', src, '-c:v', 'mpeg2video', '-q:v', '3', '-c:a', 'mp2', dst],
            check=True, capture_output=True,
        )
        os.remove(src)

    def download(self, urls):
        """
        Downloads an array of YouTube URLs in the configured format (mp3, mp4, webm, mov or mpeg).
        """
        ydl_opts = {
            **self._format_opts(),
            'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
        }

        results = []
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for url in urls:
                try:
                    print(f"Downloading: {url}")
                    info = ydl.extract_info(url, download=True)
                    if self.fmt == 'mpeg':
                        for item in info.get('requested_downloads') or [info]:
                            self._to_mpeg(item['filepath'])
                    results.append({"url": url, "status": "success"})
                except Exception as e:
                    print(f"Error downloading {url}: {e}")
                    results.append({"url": url, "status": "failed", "error": str(e)})

        return results


# Backwards-compatible name
YouTubeAudioDownloader = YouTubeDownloader
