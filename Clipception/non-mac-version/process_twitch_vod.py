import subprocess
import os
import sys
from pathlib import Path
import re
import yt_dlp
import time

def sanitize_filename(filename):
    """Convert filename to safe string without spaces"""
    # Remove file extension if present
    base = os.path.splitext(filename)[0]
    # Replace spaces and special characters with underscores
    safe_name = re.sub(r'[^\w\-_.]', '_', base)
    # Add back the original extension
    extension = os.path.splitext(filename)[1]
    return f"{safe_name}{extension}"

def is_url(string):
    """Check if string is a URL"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(string) is not None

def download_video(url, output_dir="./downloads"):
    """Download video from URL using yt-dlp"""
    print(f"🔗 Downloading video from: {url}")
    
    # Create downloads directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Configure yt-dlp options
    ydl_opts = {
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'format': 'best[height<=1080]',  # Download best quality up to 1080p
        'writeinfojson': True,  # Save metadata
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Get video info first
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video')
            duration = info.get('duration', 0)
            
            print(f"📹 Video: {title}")
            if duration:
                hours = duration // 3600
                minutes = (duration % 3600) // 60
                print(f"⏱️  Duration: {hours:02d}:{minutes:02d}:{duration%60:02d}")
            
            # Download the video
            print("⬇️  Starting download...")
            download_start = time.time()
            ydl.download([url])
            download_end = time.time()
            
            print(f"✅ Download completed in {download_end - download_start:.1f} seconds")
            
            # Find the downloaded file
            safe_title = sanitize_filename(title)
            possible_extensions = ['.mp4', '.mkv', '.webm', '.flv']
            
            for ext in possible_extensions:
                potential_file = os.path.join(output_dir, f"{title}{ext}")
                if os.path.exists(potential_file):
                    return potential_file
                    
                # Try with sanitized filename
                potential_file = os.path.join(output_dir, f"{safe_title}{ext}")
                if os.path.exists(potential_file):
                    return potential_file
            
            # If exact match not found, look for any video file in the directory
            for file in os.listdir(output_dir):
                if file.endswith(tuple(possible_extensions)) and title.replace(' ', '_') in file:
                    return os.path.join(output_dir, file)
            
            raise FileNotFoundError("Downloaded video file not found")
            
    except Exception as e:
        print(f"❌ Error downloading video: {str(e)}")
        raise

def run_script(command):
    try:
        print(f"Running: {command}")
        process = subprocess.run(command, check=True, shell=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {str(e)}")
        return False

def main():
    # Check for OpenRouter API key
    if not os.getenv("OPEN_ROUTER_KEY"):
        print("Error: OPEN_ROUTER_KEY environment variable is not set")
        print("Please set it with: export OPEN_ROUTER_KEY='your_key_here'")
        sys.exit(1)

    if len(sys.argv) != 2:
        print("Usage: python process_twitch_vod.py <video_path_or_url>")
        print("Examples:")
        print("  python process_twitch_vod.py /path/to/your/video.mp4")
        print("  python process_twitch_vod.py https://www.twitch.tv/videos/123456789")
        print("  python process_twitch_vod.py https://youtube.com/watch?v=...")
        sys.exit(1)

    input_path = sys.argv[1]
    
    # Determine if input is URL or local file
    if is_url(input_path):
        print("🌐 URL detected - downloading video first...")
        try:
            video_path = download_video(input_path)
            print(f"📁 Downloaded to: {video_path}")
        except Exception as e:
            print(f"❌ Failed to download video: {str(e)}")
            sys.exit(1)
    else:
        # Local file path
        video_path = input_path
        if not os.path.exists(video_path):
            print(f"Error: Video file not found: {video_path}")
            sys.exit(1)

    try:
        # Sanitize filename if needed
        video_filename = os.path.basename(video_path)
        safe_filename = sanitize_filename(video_filename)
        
        # Create a clean path with sanitized filename if needed
        if video_filename != safe_filename:
            safe_video_path = os.path.join(os.path.dirname(video_path), safe_filename)
            os.rename(video_path, safe_video_path)
            video_path = safe_video_path
            print(f"Renamed video file to: {safe_filename}")
        
        base_name = Path(video_path).stem
        output_dir = "./FeatureTranscribe"
        os.makedirs(output_dir, exist_ok=True)

        # Copy input video to FeatureTranscribe directory
        feature_transcribe_path = os.path.join(output_dir, os.path.basename(video_path))
        if video_path != feature_transcribe_path:
            os.system(f"cp \"{video_path}\" \"{feature_transcribe_path}\"")
            print(f"Copied video to: {feature_transcribe_path}")

        # Step 1: Run enhanced transcription
        print("\nStep 1: Generating enhanced transcription...")
        cmd1 = f"python transcription.py \"{feature_transcribe_path}\""
        if not run_script(cmd1):
            sys.exit(1)

        transcription_json = os.path.join(output_dir, f"{base_name}.enhanced_transcription.json")
        if not os.path.exists(transcription_json):
            print(f"Error: Expected transcription file {transcription_json} was not generated")
            sys.exit(1)

        # Step 2: Generate clips JSON using GPU acceleration
        print("\nStep 2: Processing transcription for clip selection...")
        cmd2 = (f"python gpu_clip.py \"{transcription_json}\" "
                f"--output_file \"{os.path.join(output_dir, 'top_clips_one.json')}\" "
                f"--site_url 'http://localhost' "
                f"--site_name 'Local Test' "
                f"--num_clips 20 "
                f"--chunk_size 5")
        if not run_script(cmd2):
            sys.exit(1)

        clips_json = os.path.join(output_dir, "top_clips_one.json")
        if not os.path.exists(clips_json):
            print(f"Error: Expected top clips file {clips_json} was not generated")
            sys.exit(1)

        # Step 3: Extract video clips
        print("\nStep 3: Extracting clips...")
        clips_output_dir = os.path.join(output_dir, "clips")
        os.makedirs(clips_output_dir, exist_ok=True)
        cmd3 = f"python clip.py \"{feature_transcribe_path}\" \"{clips_output_dir}\" \"{clips_json}\""
        if not run_script(cmd3):
            sys.exit(1)

        print("\n🎉 All processing completed successfully!")
        print(f"Generated files:")
        print(f"1. Transcription: {transcription_json}")
        print(f"2. Clip selections: {clips_json}")
        print(f"3. Video clips: {clips_output_dir}/")
        
        # Show clip count
        clip_files = [f for f in os.listdir(clips_output_dir) if f.endswith('.mp4')]
        print(f"4. Total clips created: {len(clip_files)}")

    except Exception as e:
        print(f"Error processing video: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 