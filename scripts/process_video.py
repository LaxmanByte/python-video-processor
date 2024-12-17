# Copy this content into process_video.py
import sys
import os
import youtube_dl
from moviepy.editor import VideoFileClip
import whisper
import pandas as pd

def download_video(url, output_path):
    """Download video from YouTube"""
    ydl_opts = {
        'format': 'best',
        'outtmpl': output_path
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output_path

def split_video(video_path, segment_duration, output_dir):
    """Split video into segments"""
    video = VideoFileClip(video_path)
    duration = video.duration
    segments = []
    
    for i in range(0, int(duration), segment_duration):
        end_time = min(i + segment_duration, duration)
        segment_path = f"{output_dir}/segment_{len(segments)+1}.mp4"
        
        # Extract segment
        segment = video.subclip(i, end_time)
        segment.write_videofile(segment_path)
        
        segments.append({
            'segment_number': len(segments) + 1,
            'start_time': i,
            'end_time': end_time,
            'duration': end_time - i,
            'path': segment_path
        })
    
    video.close()
    return segments

def main():
    if len(sys.argv) < 3:
        print("Usage: python process_video.py <video_url> <segment_duration_minutes>")
        sys.exit(1)
        
    video_url = sys.argv[1]
    segment_duration = int(sys.argv[2]) * 60  # Convert minutes to seconds
    
    # Create output directories
    os.makedirs('output/videos', exist_ok=True)
    os.makedirs('output/transcripts', exist_ok=True)
    os.makedirs('output/index', exist_ok=True)
    
    # Process video
    print("Downloading video...")
    video_path = download_video(video_url, 'output/videos/input_video.mp4')
    
    print("Splitting video into segments...")
    segments = split_video(video_path, segment_duration, 'output/videos')
    
    # Save segment information
    df = pd.DataFrame(segments)
    df.to_csv('output/index/segments.csv', index=False)
    
    print("Processing complete!")

if __name__ == '__main__':
    main()
