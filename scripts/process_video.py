import sys
import os
import yt_dlp as youtube_dl
import moviepy.editor as mpy
import whisper
import pandas as pd
from datetime import datetime

def download_video(url, output_path):
    """Download video from YouTube"""
    print(f"Downloading video from: {url}")
    ydl_opts = {
        'format': 'best',
        'outtmpl': output_path
    }
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return output_path
    except Exception as e:
        print(f"Error downloading video: {e}")
        sys.exit(1)

def split_video(video_path, segment_duration, output_dir):
    """Split video into segments"""
    print("Starting video splitting process...")
    try:
        video = mpy.VideoFileClip(video_path)
        duration = video.duration
        segments = []
        
        for i in range(0, int(duration), segment_duration):
            end_time = min(i + segment_duration, duration)
            segment_path = os.path.join(output_dir, f"segment_{len(segments)+1}.mp4")
            
            print(f"Creating segment {len(segments)+1}...")
            segment = video.subclip(i, end_time)
            segment.write_videofile(segment_path, codec='libx264')
            
            segments.append({
                'segment_number': len(segments) + 1,
                'start_time': i,
                'end_time': end_time,
                'duration': end_time - i,
                'path': segment_path
            })
        
        video.close()
        return segments
    except Exception as e:
        print(f"Error splitting video: {e}")
        sys.exit(1)

def create_transcript(audio_path, model):
    """Create transcript from audio"""
    try:
        result = model.transcribe(audio_path)
        return result["text"]
    except Exception as e:
        print(f"Error creating transcript: {e}")
        return ""

def create_index(segments):
    """Create index file with segment information"""
    try:
        df = pd.DataFrame(segments)
        index_path = 'output/index/segments.csv'
        df.to_csv(index_path, index=False)
        
        # Create a readable markdown summary
        with open('output/index/README.md', 'w') as f:
            f.write('# Video Segments Summary\n\n')
            for seg in segments:
                f.write(f"## Segment {seg['segment_number']}\n")
                f.write(f"- Duration: {seg['duration']} seconds\n")
                f.write(f"- Start Time: {seg['start_time']}\n")
                f.write(f"- End Time: {seg['end_time']}\n\n")
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
    os.makedirs('output/videos', exist_ok=True)
    os.makedirs('output/transcripts', exist_ok=True)
    os.makedirs('output/index', exist_ok=True)
    
    try:
        # Process video
        print("Starting video processing...")
        video_path = download_video(video_url, 'output/videos/input_video.mp4')
        
        print("Splitting video into segments...")
        segments = split_video(video_path, segment_duration, 'output/videos')
        
        # Load Whisper model for transcription
        print("Loading transcription model...")
        model = whisper.load_model("base")
        
        # Create transcripts
        print("Creating transcripts...")
        for segment in segments:
            print(f"Transcribing segment {segment['segment_number']}...")
            transcript = create_transcript(segment['path'], model)
            transcript_path = f"output/transcripts/segment_{segment['segment_number']}_transcript.txt"
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(transcript)
            segment['transcript_path'] = transcript_path
        
        # Create index files
        print("Creating index files...")
        create_index(segments)
        
        print("Processing complete!")
        
    except Exception as e:
        print(f"Error during processing: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
