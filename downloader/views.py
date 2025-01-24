from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import StreamingHttpResponse
import yt_dlp
import os
import tempfile
import subprocess
import re

# Render the frontend page
def index(request):
    return render(request, 'downloader/index.html')

class VideoDownloadView(APIView):
    def post(self, request, *args, **kwargs):
        links = request.data.get('links', [])
        download_option = request.data.get('option', 'single')  # 'single', 'multiple', or 'audio'

        if not links:
            return Response({"error": "No links provided"}, status=status.HTTP_400_BAD_REQUEST)

        if download_option == 'single' and len(links) == 1:
            # Logic for streaming a single video
            return self.stream_video(links[0], download_option)

        if download_option == 'multiple' and len(links) > 1:
            return self.download_multiple_videos(links)

        if download_option == 'audio':
            return self.download_audio_only(links)

        return Response({"error": "Invalid download option or number of links."}, status=status.HTTP_400_BAD_REQUEST)

    def get_video_title(self, link):
        # Use yt-dlp to get the title of the video
        with yt_dlp.YoutubeDL({'quiet': True, 'noplaylist': True}) as ydl:
            info_dict = ydl.extract_info(link, download=False)
            return info_dict.get('title', 'Untitled Video')

    def clean_filename(self, title):
        # Clean the title to make it safe for filenames (e.g., remove invalid characters)
        return re.sub(r'[\\/*?:"<>|]', "_", title)

    def stream_video(self, link, download_option):
        try:
            video_title = self.get_video_title(link)  # Fetch video title
            video_title_cleaned = self.clean_filename(video_title)  # Clean title for safe filename

            temp_video_path = tempfile.mktemp(suffix='.mp4', prefix='temp_video_')
            temp_audio_path = tempfile.mktemp(suffix='.m4a', prefix='temp_audio_')

            # yt-dlp options to download video and audio separately
            ydl_opts_video = {
                'outtmpl': temp_video_path,  # Video path
                'format': 'bestvideo',
                'noplaylist': True,
                'quiet': True,
            }

            ydl_opts_audio = {
                'outtmpl': temp_audio_path,  # Audio path
                'format': 'bestaudio',
                'noplaylist': True,
                'quiet': True,
            }

            # Download the video and audio separately
            with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
                ydl.download([link])

            with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
                ydl.download([link])

            # Merge the video and audio files using ffmpeg (converting audio to AAC)
            merged_file_path = tempfile.mktemp(suffix='.mp4', prefix=f'merged_{video_title_cleaned}_')

            # Specify the full path to ffmpeg executable (adjust path accordingly)
            ffmpeg_path = r'C:\path\to\ffmpeg.exe'  # Replace with your actual ffmpeg path

            ffmpeg_command = [
                ffmpeg_path,
                '-i', temp_video_path,
                '-i', temp_audio_path,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-strict', 'experimental',
                merged_file_path
            ]

            subprocess.run(ffmpeg_command, check=True)

            # Stream the merged video to the user with a proper filename
            response = StreamingHttpResponse(
                open(merged_file_path, 'rb'),
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{video_title_cleaned}.mp4"'
            return response

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def download_audio_only(self, links):
        try:
            download_dir = 'downloads'
            os.makedirs(download_dir, exist_ok=True)

            for link in links:
                audio_title = self.get_video_title(link)  # Fetch video title for audio
                audio_title_cleaned = self.clean_filename(audio_title)  # Clean title for safe filename

                temp_audio_path = tempfile.mktemp(suffix='.m4a', prefix=f'temp_audio_{audio_title_cleaned}_')

                ydl_opts_audio = {
                    'outtmpl': temp_audio_path,
                    'format': 'bestaudio',
                    'noplaylist': True,
                    'quiet': True,
                }

                with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
                    ydl.download([link])

                # Move the audio file to the desired directory with the video title as filename
                audio_file_path = os.path.join(download_dir, f"{audio_title_cleaned}.mp3")
                os.rename(temp_audio_path, audio_file_path)

            # Once all files are downloaded, you can package them into a zip or return directly
            return Response(
                {"message": "Audio files downloaded successfully", "links": links},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def download_multiple_videos(self, links):
        try:
            download_dir = 'downloads'
            os.makedirs(download_dir, exist_ok=True)

            for link in links:
                video_title = self.get_video_title(link)  # Fetch video title for video files
                video_title_cleaned = self.clean_filename(video_title)  # Clean title for safe filename

                temp_video_path = tempfile.mktemp(suffix='.mp4', prefix=f'temp_video_{video_title_cleaned}_')
                temp_audio_path = tempfile.mktemp(suffix='.m4a', prefix=f'temp_audio_{video_title_cleaned}_')

                ydl_opts_video = {
                    'outtmpl': temp_video_path,
                    'format': 'bestvideo',
                    'noplaylist': True,
                    'quiet': True,
                }

                ydl_opts_audio = {
                    'outtmpl': temp_audio_path,
                    'format': 'bestaudio',
                    'noplaylist': True,
                    'quiet': True,
                }

                with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
                    ydl.download([link])

                with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
                    ydl.download([link])

                # Merge video and audio files
                merged_file_path = os.path.join(download_dir, f"{video_title_cleaned}.mp4")

                ffmpeg_path = r'C:\path\to\ffmpeg.exe'

                ffmpeg_command = [
                    ffmpeg_path,
                    '-i', temp_video_path,
                    '-i', temp_audio_path,
                    '-c:v', 'copy',
                    '-c:a', 'aac',
                    '-strict', 'experimental',
                    merged_file_path
                ]

                subprocess.run(ffmpeg_command, check=True)

                # Clean up temporary files
                os.remove(temp_video_path)
                os.remove(temp_audio_path)

            return Response(
                {"message": "Multiple videos downloaded successfully", "links": links},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
