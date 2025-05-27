#!/usr/bin/env python3
"""
TikTok Auto Clipper Web Interface - Cloud Ready Version
Optimized for Render deployment with dynamic path handling
"""

from flask import Flask, render_template, request, jsonify
import subprocess
import os
import sys
import json
import time
import threading
import uuid
from pathlib import Path
import re

app = Flask(__name__)

# Cloud-compatible configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIES_DIR = os.environ.get('COOKIES_DIR', os.path.join(BASE_DIR, 'cookies'))
VIDEOS_DIR = os.environ.get('VIDEOS_DIR', os.path.join(BASE_DIR, 'videos'))
UPLOADS_DIR = os.environ.get('UPLOADS_DIR', os.path.join(BASE_DIR, 'uploads'))
TIKTOK_UPLOADER_DIR = os.environ.get('TIKTOK_UPLOADER_DIR', os.path.join(BASE_DIR, '..', 'TiktokAutoUploader'))

# Create necessary directories
for directory in [COOKIES_DIR, VIDEOS_DIR, UPLOADS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Add TikTok uploader to Python path
if TIKTOK_UPLOADER_DIR not in sys.path:
    sys.path.append(TIKTOK_UPLOADER_DIR)

# Global job storage (in production, use Redis or database)
jobs = {}
job_lock = threading.Lock()

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

def get_tiktok_accounts():
    """Get list of logged in TikTok accounts"""
    try:
        if not os.path.exists(COOKIES_DIR):
            return []
        
        accounts = []
        for file in os.listdir(COOKIES_DIR):
            if file.startswith("tiktok_session-"):
                account_name = file.split("tiktok_session-")[1]
                # Remove .cookie extension if present
                if account_name.endswith(".cookie"):
                    account_name = account_name[:-7]
                accounts.append(account_name)
        return accounts
    except Exception as e:
        print(f"Error getting TikTok accounts: {e}")
        return []

def update_job_status(job_id, status, message="", progress=0, clips_generated=0):
    """Update job status thread-safely"""
    with job_lock:
        if job_id in jobs:
            jobs[job_id].update({
                'status': status,
                'message': message,
                'progress': progress,
                'clips_generated': clips_generated,
                'updated_at': time.time()
            })

def run_processing_job(job_id, video_url, tiktok_user, max_uploads, base_title):
    """Run the video processing job in background - Cloud Version"""
    try:
        update_job_status(job_id, 'downloading', 'Starting video download...', 10)
        
        # Set up environment variables for cloud processing
        env = os.environ.copy()
        env.update({
            'COOKIES_DIR': COOKIES_DIR,
            'VIDEOS_DIR': VIDEOS_DIR,
            'UPLOADS_DIR': UPLOADS_DIR,
            'TIKTOK_UPLOADER_DIR': TIKTOK_UPLOADER_DIR,
            'PYTHONPATH': f"{BASE_DIR}:{TIKTOK_UPLOADER_DIR}:{env.get('PYTHONPATH', '')}"
        })
        
        # Cloud-compatible processing command (no virtual environment activation needed)
        cmd = [
            'python', 'process_and_upload_cloud.py',
            video_url,
            '--tiktok-user', tiktok_user,
            '--max-uploads', str(max_uploads),
            '--base-title', base_title
        ]
        
        update_job_status(job_id, 'processing', 'Processing video with AI...', 30)
        
        # Run the command
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=BASE_DIR
        )
        
        # Monitor output
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                line = output.strip()
                print(f"Job {job_id}: {line}")
                
                # Update status based on output
                if "Downloading video" in line:
                    update_job_status(job_id, 'downloading', 'Downloading video...', 15)
                elif "Generating enhanced transcription" in line:
                    update_job_status(job_id, 'transcribing', 'AI transcribing audio...', 40)
                elif "AI analyzing clips" in line:
                    update_job_status(job_id, 'analyzing', 'AI analyzing viral potential...', 60)
                elif "Extracting video clips" in line:
                    update_job_status(job_id, 'extracting', 'Creating video clips...', 75)
                elif "Starting TikTok uploads" in line:
                    update_job_status(job_id, 'uploading', 'Uploading to TikTok...', 85)
                elif "Generated" in line and "clips successfully" in line:
                    try:
                        clips_count = int(re.search(r'Generated (\d+) clips', line).group(1))
                        update_job_status(job_id, 'uploading', f'Generated {clips_count} clips, uploading...', 80, clips_count)
                    except:
                        pass
                elif "Successfully uploaded" in line:
                    update_job_status(job_id, 'uploading', 'Uploading clips to TikTok...', 90)
        
        # Check if process completed successfully
        return_code = process.poll()
        if return_code == 0:
            update_job_status(job_id, 'completed', 'All clips uploaded successfully!', 100)
        else:
            stderr = process.stderr.read()
            update_job_status(job_id, 'failed', f'Processing failed: {stderr}', 0)
            
    except Exception as e:
        update_job_status(job_id, 'failed', f'Error: {str(e)}', 0)

@app.route('/')
def index():
    """Main page"""
    accounts = get_tiktok_accounts()
    return render_template('index.html', accounts=accounts)

@app.route('/api/submit_job', methods=['POST'])
def submit_job():
    """Submit a new processing job"""
    data = request.json
    
    video_url = data.get('video_url', '').strip()
    tiktok_user = data.get('tiktok_user', '').strip()
    max_uploads = int(data.get('max_uploads', 3))
    base_title = data.get('base_title', '').strip()
    
    # Validation
    if not video_url:
        return jsonify({'error': 'Video URL is required'}), 400
    
    if not is_url(video_url):
        return jsonify({'error': 'Invalid URL format'}), 400
    
    if not tiktok_user:
        return jsonify({'error': 'TikTok user is required'}), 400
    
    # Check if user is logged in (in cloud, this might need manual setup)
    accounts = get_tiktok_accounts()
    if not accounts:
        return jsonify({'error': 'No TikTok accounts configured. Please contact admin.'}), 400
    
    if tiktok_user not in accounts:
        return jsonify({'error': f'TikTok user "{tiktok_user}" not found in configured accounts'}), 400
    
    # Create job
    job_id = str(uuid.uuid4())
    
    with job_lock:
        jobs[job_id] = {
            'id': job_id,
            'video_url': video_url,
            'tiktok_user': tiktok_user,
            'max_uploads': max_uploads,
            'base_title': base_title,
            'status': 'queued',
            'message': 'Job queued for processing',
            'progress': 0,
            'clips_generated': 0,
            'created_at': time.time(),
            'updated_at': time.time()
        }
    
    # Start processing in background
    thread = threading.Thread(
        target=run_processing_job,
        args=(job_id, video_url, tiktok_user, max_uploads, base_title)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({'job_id': job_id, 'status': 'queued'})

@app.route('/api/job_status/<job_id>')
def job_status(job_id):
    """Get job status"""
    with job_lock:
        if job_id not in jobs:
            return jsonify({'error': 'Job not found'}), 404
        
        job = jobs[job_id].copy()
        return jsonify(job)

@app.route('/api/accounts')
def get_accounts():
    """Get list of TikTok accounts"""
    accounts = get_tiktok_accounts()
    return jsonify({'accounts': accounts})

@app.route('/api/login_tiktok', methods=['POST'])
def login_tiktok():
    """Initiate TikTok login - Cloud Version"""
    data = request.json
    account_name = data.get('account_name', '').strip()
    
    if not account_name:
        return jsonify({'error': 'Account name is required'}), 400
    
    # In cloud deployment, TikTok login requires manual cookie setup
    return jsonify({
        'message': 'TikTok login in cloud deployment requires manual cookie configuration.',
        'instructions': [
            '1. Login to TikTok on your local machine',
            '2. Export the session cookies',
            '3. Upload them to the server via admin panel',
            '4. Contact admin for assistance with cookie setup'
        ],
        'note': 'Browser-based login not available in cloud environment'
    })

@app.route('/health')
def health():
    """Health check endpoint for Render"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'version': '1.0.0',
        'directories': {
            'cookies': os.path.exists(COOKIES_DIR),
            'videos': os.path.exists(VIDEOS_DIR),
            'uploads': os.path.exists(UPLOADS_DIR)
        }
    })

@app.route('/api/system_info')
def system_info():
    """System information endpoint"""
    return jsonify({
        'base_dir': BASE_DIR,
        'cookies_dir': COOKIES_DIR,
        'videos_dir': VIDEOS_DIR,
        'uploads_dir': UPLOADS_DIR,
        'tiktok_uploader_dir': TIKTOK_UPLOADER_DIR,
        'accounts_configured': len(get_tiktok_accounts()),
        'python_path': sys.path[:3],  # First 3 entries
        'environment': 'cloud'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 4000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    print(f"🚀 Starting TikTok Auto Clipper (Cloud Version)")
    print(f"📁 Base Directory: {BASE_DIR}")
    print(f"🍪 Cookies Directory: {COOKIES_DIR}")
    print(f"🎬 Videos Directory: {VIDEOS_DIR}")
    print(f"📤 Uploads Directory: {UPLOADS_DIR}")
    print(f"🎵 TikTok Uploader: {TIKTOK_UPLOADER_DIR}")
    print(f"🌐 Starting on port {port}")
    
    app.run(debug=debug, host='0.0.0.0', port=port) 