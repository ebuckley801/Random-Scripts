from pytube import YouTube
import os
from pathlib import Path

def download_youtube_video(url, output_path=None):
    """
    Download a YouTube video as MP4
    
    Args:
        url (str): YouTube video URL
        output_path (str, optional): Directory to save the video. Defaults to current directory.
    """
    try:
        # Create YouTube object
        yt = YouTube(url)
        
        # Get the highest resolution stream
        video = yt.streams.get_highest_resolution()
        
        # Set output path
        if output_path is None:
            output_path = os.getcwd()
        
        # Create output directory if it doesn't exist
        Path(output_path).mkdir(parents=True, exist_ok=True)
        
        # Download the video
        print(f"Downloading: {yt.title}")
        video.download(output_path)
        print(f"Download completed! Video saved to: {output_path}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    # Get user input
    video_url = input("Enter the YouTube video URL: ").strip()
    output_dir = input("Enter the output directory (press Enter for current directory): ").strip()
    
    # Download the video
    download_youtube_video(video_url, output_dir if output_dir else None) 