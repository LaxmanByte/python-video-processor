import sys
import os
from pytube import YouTube
import moviepy.editor as mpy
import whisper
import pandas as pd
from datetime import datetime

def download_video(url, output_path):
    """
    Download video from YouTube using pytube
    Args:
        url (str): YouTube video URL
        output_path (str): Path to save the video
    Returns:
        str: Path to downloaded video
    """
    try:
        print(f"Downloading video from: {url}")
        yt = YouTube(url)
        print(f"Video title: {yt.title}")
        print(f"Duration: {yt.length} seconds")
        
        # Get highest resolution stream
        video = yt.streams.get_highest_resolution()
        print(f"Downloading {video.resolution} resolution video...")
        
        # Download the video
        video.download(filename=output_path)
        print("Download complete!")
        return output_path
    except Exception as e:
        print(f"Error downloading video: {e}")
        sys.exit(1)

def split_video(video_path, segment_duration, output_dir):
    """
    Split video into segments
    Args:
        video_path (str): Path to input video
        segment_duration (int): Duration of each segment in seconds
        output_dir (str): Directory to save segments
    Returns:
        list: List of segment information dictionaries
    """
    print("\nStarting video splitting process...")
    try:
        video = mpy.VideoFileClip(video_path)
        duration = video.duration
        segments = []
        
        # Calculate total segments
        total_segments = int(duration / segment_duration) + (1 if duration % segment_duration else 0)
        print(f"Video will be split into {total_segments} segments")
        
        for i in range(0, int(duration), segment_duration):
            segment_number = len(segments) + 1
            end_time = min(i + segment_duration, duration)
            segment_path = os.path.join(output_dir, f"segment_{segment_number}.mp4")
            
            print(f"\nProcessing segment {segment_number}/{total_segments}")
            print(f"Time range: {i} to {end_time} seconds")
            
            # Extract and save segment
            segment = video.subclip(i, end_time)
            segment.write_videofile(segment_path, codec='libx264', audio_codec='aac')
            
            # Store segment information
            segments.append({
                'segment_number': segment_number,
                'start_time': i,
                'end_time': end_time,
                'duration': end_time - i,
                'path': segment_path,
                'start_time_formatted': str(datetime.fromtimestamp(i).strftime('%H:%M:%S')),
                'end_time_formatted': str(datetime.fromtimestamp(end_time).strftime('%H:%M:%S'))
            })
            print(f"Segment {segment_number} complete")
        
        video.close()
        return segments
    except Exception as e:
        print(f"Error splitting video: {e}")
        sys.exit(1)

def create_transcript(video_path, model):
    """
    Create transcript from video
    Args:
        video_path (str): Path to video file
        model: Loaded Whisper model
    Returns:
        str: Transcript text
    """
    try:
        print(f"Transcribing {os.path.basename(video_path)}...")
        result = model.transcribe(video_path)
        return result["text"]
    except Exception as e:
        print(f"Error creating transcript: {e}")
        return ""

def create_index(segments):
    """
    Create index files (CSV and Markdown)
    Args:
        segments (list): List of segment information dictionaries
    """
    try:
        # Create CSV index
        df = pd.DataFrame(segments)
        csv_path = 'output/index/segments.csv'
        df.to_csv(csv_path, index=False)
        print(f"\nCreated CSV index: {csv_path}")
        
        # Create Markdown index
        md_path = 'output/index/README.md'
        with open(md_path, 'w') as f:
            f.write('# Video Segments Summary\n\n')
            for seg in segments:
                f.write(f"## Segment {seg['segment_number']}\n")
                f.write(f"- Time Range: {seg['start_time_formatted']} - {seg['end_time_formatted']}\n")
                f.write(f"- Duration: {seg['duration']} seconds\n")
                f.write(f"- Video File: {os.path.basename(seg['path'])}\n")
                if 'transcript_path' in seg:
                    f.write(f"- Transcript: {os.path.basename(seg['transcript_path'])}\n")
                f.write('\n')
        print(f"Created Markdown index: {md_path}")
    except Exception as e:
        print(f"Error creating index: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) < 3:
        print("Usage: python process_video.py <video_url> <segment_duration_minutes>")
        sys.exit(1)
    
    # Get parameters
    video_url = sys.argv[1]
    segment_duration = int(sys.argv[2]) * 60  # Convert minutes to seconds
    
    # Create output directories
    for dir_path in ['output/videos', 'output/transcripts', 'output/index']:
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    try:
        # Process video
        print("\n=== Starting Video Processing ===")
        video_path = download_video(video_url, 'output/videos/input_video.mp4')
        
        print("\n=== Splitting Video ===")
        segments = split_video(video_path, segment_duration, 'output/videos')
        
        print("\n=== Starting Transcription ===")
        print("Loading Whisper model...")
        model = whisper.load_model("base")
        
        # Create transcripts
        for segment in segments:
            transcript = create_transcript(segment['path'], model)
            transcript_path = f"output/transcripts/segment_{segment['segment_number']}_transcript.txt"
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(transcript)
            segment['transcript_path'] = transcript_path
            print(f"Created transcript: {transcript_path}")
        
        print("\n=== Creating Index Files ===")
        create_index(segments)
        
        print("\n=== Processing Complete! ===")
        print(f"Total segments created: {len(segments)}")
        print("Output files are in the 'output' directory")
        
    except Exception as e:
        print(f"\nError during processing: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
