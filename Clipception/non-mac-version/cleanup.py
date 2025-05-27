#!/usr/bin/env python3
"""
Cleanup Script for TikTok Auto Clipper Cloud Deployment
Removes old temporary files to prevent storage issues
"""

import os
import time
import glob
from datetime import datetime, timedelta

# Configuration
MAX_AGE_HOURS = 24  # Remove files older than 24 hours
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def cleanup_directory(directory, max_age_hours=24, file_patterns=None):
    """Clean up old files in a directory"""
    if not os.path.exists(directory):
        print(f"Directory does not exist: {directory}")
        return
    
    if file_patterns is None:
        file_patterns = ['*']
    
    cutoff_time = time.time() - (max_age_hours * 3600)
    removed_count = 0
    removed_size = 0
    
    for pattern in file_patterns:
        pattern_path = os.path.join(directory, pattern)
        for filepath in glob.glob(pattern_path):
            if os.path.isfile(filepath):
                file_age = os.path.getmtime(filepath)
                if file_age < cutoff_time:
                    file_size = os.path.getsize(filepath)
                    try:
                        os.remove(filepath)
                        removed_count += 1
                        removed_size += file_size
                        print(f"Removed: {filepath} ({file_size} bytes)")
                    except Exception as e:
                        print(f"Error removing {filepath}: {e}")
    
    if removed_count > 0:
        print(f"Cleaned up {removed_count} files ({removed_size / 1024 / 1024:.1f} MB) from {directory}")
    else:
        print(f"No old files found in {directory}")

def main():
    """Main cleanup function"""
    print(f"🧹 Starting cleanup at {datetime.now()}")
    print(f"🗂️  Removing files older than {MAX_AGE_HOURS} hours")
    
    # Directories to clean
    cleanup_dirs = [
        {
            'path': os.path.join(BASE_DIR, 'downloads'),
            'patterns': ['*.mp4', '*.mkv', '*.webm', '*.flv', '*.json']
        },
        {
            'path': os.path.join(BASE_DIR, 'videos'),
            'patterns': ['*.mp4', '*.mkv', '*.webm', '*.flv']
        },
        {
            'path': os.path.join(BASE_DIR, 'uploads'),
            'patterns': ['*.mp4', '*.mkv', '*.webm', '*.flv']
        },
        {
            'path': os.path.join(BASE_DIR, 'FeatureTranscribe'),
            'patterns': ['*.mp4', '*.mkv', '*.webm', '*.flv', '*.json', '*.wav', '*.mp3']
        },
        {
            'path': os.path.join(BASE_DIR, 'FeatureTranscribe', 'clips'),
            'patterns': ['*.mp4']
        }
    ]
    
    total_removed = 0
    
    for cleanup_config in cleanup_dirs:
        directory = cleanup_config['path']
        patterns = cleanup_config['patterns']
        
        print(f"\n📁 Cleaning: {directory}")
        cleanup_directory(directory, MAX_AGE_HOURS, patterns)
    
    # Clean up any TikTok uploader temp files
    tiktok_uploader_dir = os.environ.get('TIKTOK_UPLOADER_DIR')
    if tiktok_uploader_dir and os.path.exists(tiktok_uploader_dir):
        videos_path = os.path.join(tiktok_uploader_dir, 'VideosDirPath')
        if os.path.exists(videos_path):
            print(f"\n📁 Cleaning TikTok uploader temp files: {videos_path}")
            cleanup_directory(videos_path, MAX_AGE_HOURS, ['*.mp4', '*.mkv', '*.webm'])
    
    print(f"\n✅ Cleanup completed at {datetime.now()}")

if __name__ == "__main__":
    main() 