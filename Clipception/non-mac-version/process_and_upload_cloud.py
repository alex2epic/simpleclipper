#!/usr/bin/env python3
"""
Integrated TikTok Auto Clipper & Uploader - Cloud Version
Processes videos/VODs, generates viral clips, and auto-uploads to TikTok
Optimized for cloud deployment with dynamic path handling
"""

import subprocess
import os
import sys
import json
import time
from pathlib import Path
import re
import yt_dlp
import argparse

# Cloud-compatible configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIES_DIR = os.environ.get('COOKIES_DIR', os.path.join(BASE_DIR, 'cookies'))
VIDEOS_DIR = os.environ.get('VIDEOS_DIR', os.path.join(BASE_DIR, 'videos'))
UPLOADS_DIR = os.environ.get('UPLOADS_DIR', os.path.join(BASE_DIR, 'uploads'))
TIKTOK_UPLOADER_DIR = os.environ.get('TIKTOK_UPLOADER_DIR', os.path.join(BASE_DIR, '..', 'TiktokAutoUploader'))

# Add TikTok uploader to path
if TIKTOK_UPLOADER_DIR not in sys.path:
    sys.path.append(TIKTOK_UPLOADER_DIR)

# Create necessary directories
for directory in [COOKIES_DIR, VIDEOS_DIR, UPLOADS_DIR]:
    os.makedirs(directory, exist_ok=True)

def sanitize_filename(filename):
    """Convert filename to safe string without spaces"""
    base = os.path.splitext(filename)[0]
    safe_name = re.sub(r'[^\w\-_.]', '_', base)
    extension = os.path.splitext(filename)[1]
    return f"{safe_name}{extension}"

def is_url(string):
    """Check if string is a URL"""
    url_pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(string) is not None

def download_video(url, output_dir=None):
    """Download video from URL using yt-dlp"""
    if output_dir is None:
        output_dir = os.path.join(BASE_DIR, "downloads")
    
    print(f"🔗 Downloading video from: {url}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    ydl_opts = {
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'format': 'best[height<=1080]',
        'writeinfojson': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video')
            duration = info.get('duration', 0)
            
            print(f"📹 Video: {title}")
            if duration:
                hours = duration // 3600
                minutes = (duration % 3600) // 60
                print(f"⏱️  Duration: {hours:02d}:{minutes:02d}:{duration%60:02d}")
            
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
                    return potential_file, title
                    
                potential_file = os.path.join(output_dir, f"{safe_title}{ext}")
                if os.path.exists(potential_file):
                    return potential_file, title
            
            # Look for any video file in the directory
            for file in os.listdir(output_dir):
                if file.endswith(tuple(possible_extensions)) and title.replace(' ', '_') in file:
                    return os.path.join(output_dir, file), title
            
            raise FileNotFoundError("Downloaded video file not found")
            
    except Exception as e:
        print(f"❌ Error downloading video: {str(e)}")
        raise

def run_script(command, cwd=None):
    """Run shell command and return success status"""
    try:
        print(f"Running: {command}")
        if cwd is None:
            cwd = BASE_DIR
        process = subprocess.run(command, check=True, shell=True, cwd=cwd)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {str(e)}")
        return False

def process_video_to_clips(video_path):
    """Process video and generate clips"""
    print("🎬 Starting video processing pipeline...")
    
    # Sanitize filename if needed
    video_filename = os.path.basename(video_path)
    safe_filename = sanitize_filename(video_filename)
    
    if video_filename != safe_filename:
        safe_video_path = os.path.join(os.path.dirname(video_path), safe_filename)
        os.rename(video_path, safe_video_path)
        video_path = safe_video_path
        print(f"Renamed video file to: {safe_filename}")
    
    base_name = Path(video_path).stem
    output_dir = os.path.join(BASE_DIR, "FeatureTranscribe")
    os.makedirs(output_dir, exist_ok=True)

    # Copy input video to FeatureTranscribe directory
    feature_transcribe_path = os.path.join(output_dir, os.path.basename(video_path))
    if video_path != feature_transcribe_path:
        import shutil
        shutil.copy2(video_path, feature_transcribe_path)
        print(f"Copied video to: {feature_transcribe_path}")

    # Step 1: Run enhanced transcription
    print("\nStep 1: Generating enhanced transcription...")
    cmd1 = f"python transcription.py \"{feature_transcribe_path}\""
    if not run_script(cmd1):
        return None

    transcription_json = os.path.join(output_dir, f"{base_name}.enhanced_transcription.json")
    if not os.path.exists(transcription_json):
        print(f"Error: Expected transcription file {transcription_json} was not generated")
        return None

    # Step 2: Generate clips JSON using AI
    print("\nStep 2: AI analyzing clips for viral potential...")
    cmd2 = (f"python gpu_clip.py \"{transcription_json}\" "
            f"--output_file \"{os.path.join(output_dir, 'top_clips_one.json')}\" "
            f"--site_url 'http://localhost' "
            f"--site_name 'Cloud Processing' "
            f"--num_clips 20 "
            f"--chunk_size 5")
    if not run_script(cmd2):
        return None

    clips_json = os.path.join(output_dir, "top_clips_one.json")
    if not os.path.exists(clips_json):
        print(f"Error: Expected top clips file {clips_json} was not generated")
        return None

    # Step 3: Extract video clips
    print("\nStep 3: Extracting video clips...")
    clips_output_dir = os.path.join(output_dir, "clips")
    os.makedirs(clips_output_dir, exist_ok=True)
    cmd3 = f"python clip.py \"{feature_transcribe_path}\" \"{clips_output_dir}\" \"{clips_json}\""
    if not run_script(cmd3):
        return None

    return clips_output_dir, clips_json

def get_clip_metadata(clips_json_path):
    """Load clip metadata from JSON file"""
    try:
        with open(clips_json_path, 'r') as f:
            data = json.load(f)
            return data.get('top_clips', [])
    except Exception as e:
        print(f"Error loading clip metadata: {e}")
        return []

def upload_clips_to_tiktok(clips_dir, clips_metadata, tiktok_user, max_uploads=5, base_title=""):
    """Upload clips to TikTok using the TikTok uploader - Cloud Version"""
    print(f"\n🚀 Starting TikTok uploads for user: {tiktok_user}")
    
    # Get list of clip files
    clip_files = [f for f in os.listdir(clips_dir) if f.endswith('.mp4')]
    clip_files.sort()  # Sort to get consistent ordering
    
    # Limit uploads
    clips_to_upload = clip_files[:max_uploads]
    
    uploaded_count = 0
    
    for i, clip_file in enumerate(clips_to_upload):
        clip_path = os.path.join(clips_dir, clip_file)
        
        # Get metadata for this clip if available
        clip_title = f"{base_title} - Viral Moment {i+1}"
        if i < len(clips_metadata):
            clip_info = clips_metadata[i]
            clip_name = clip_info.get('name', f'Clip {i+1}')
            clip_title = f"{base_title} - {clip_name}"
        
        # Ensure title is not too long (TikTok has limits)
        if len(clip_title) > 100:
            clip_title = clip_title[:97] + "..."
        
        print(f"\n📤 Uploading clip {i+1}/{len(clips_to_upload)}: {clip_file}")
        print(f"📝 Title: {clip_title}")
        
        # Copy clip to TikTok uploader's video directory
        tiktok_videos_dir = os.path.join(TIKTOK_UPLOADER_DIR, "VideosDirPath")
        os.makedirs(tiktok_videos_dir, exist_ok=True)
        
        tiktok_clip_path = os.path.join(tiktok_videos_dir, clip_file)
        import shutil
        shutil.copy2(clip_path, tiktok_clip_path)
        
        # Upload using TikTok CLI - Cloud compatible
        upload_cmd = f"python cli.py upload --user {tiktok_user} -v \"{clip_file}\" -t \"{clip_title}\""
        
        if run_script(upload_cmd, cwd=TIKTOK_UPLOADER_DIR):
            uploaded_count += 1
            print(f"✅ Successfully uploaded: {clip_title}")
            # Add delay between uploads to avoid rate limiting
            if i < len(clips_to_upload) - 1:
                print("⏳ Waiting 30 seconds before next upload...")
                time.sleep(30)
        else:
            print(f"❌ Failed to upload: {clip_title}")
    
    return uploaded_count

def main():
    parser = argparse.ArgumentParser(description='Process videos and auto-upload clips to TikTok (Cloud Version)')
    parser.add_argument('input', help='Video file path or URL (Twitch VOD, YouTube, etc.)')
    parser.add_argument('--tiktok-user', required=True, help='TikTok username (must be logged in first)')
    parser.add_argument('--max-uploads', type=int, default=3, help='Maximum number of clips to upload (default: 3)')
    parser.add_argument('--base-title', default='', help='Base title for TikTok posts')
    
    args = parser.parse_args()
    
    # Check for OpenRouter API key
    if not os.getenv("OPEN_ROUTER_KEY"):
        print("Error: OPEN_ROUTER_KEY environment variable is not set")
        print("Please set it in your cloud environment variables")
        sys.exit(1)
    
    input_path = args.input
    original_title = ""
    
    print(f"🌐 Cloud Environment Configuration:")
    print(f"📁 Base Directory: {BASE_DIR}")
    print(f"🍪 Cookies Directory: {COOKIES_DIR}")
    print(f"🎬 Videos Directory: {VIDEOS_DIR}")
    print(f"📤 Uploads Directory: {UPLOADS_DIR}")
    print(f"🎵 TikTok Uploader Directory: {TIKTOK_UPLOADER_DIR}")
    
    # Determine if input is URL or local file
    if is_url(input_path):
        print("🌐 URL detected - downloading video first...")
        try:
            video_path, original_title = download_video(input_path)
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
        original_title = Path(video_path).stem
    
    # Use provided base title or derive from video
    base_title = args.base_title if args.base_title else original_title[:50]
    
    try:
        # Process video to generate clips
        result = process_video_to_clips(video_path)
        if not result:
            print("❌ Failed to process video")
            sys.exit(1)
        
        clips_dir, clips_json = result
        
        # Load clip metadata
        clips_metadata = get_clip_metadata(clips_json)
        
        # Show clip count
        clip_files = [f for f in os.listdir(clips_dir) if f.endswith('.mp4')]
        print(f"\n🎉 Generated {len(clip_files)} clips successfully!")
        
        # Upload to TikTok
        uploaded_count = upload_clips_to_tiktok(
            clips_dir, 
            clips_metadata, 
            args.tiktok_user, 
            args.max_uploads,
            base_title
        )
        
        print(f"\n🎊 COMPLETE! Successfully uploaded {uploaded_count}/{args.max_uploads} clips to TikTok!")
        print(f"📁 All clips available in: {clips_dir}")
        
    except Exception as e:
        print(f"❌ Error in processing pipeline: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 