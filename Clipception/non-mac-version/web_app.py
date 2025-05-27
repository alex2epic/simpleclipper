#!/usr/bin/env python3
"""
TikTok Auto Clipper Web Interface
Simple web frontend for processing videos and uploading to TikTok
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
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
        cookies_dir = "/Users/alexfreedman/simpleclipper/TiktokAutoUploader/CookiesDir"
        if not os.path.exists(cookies_dir):
            return []
        
        accounts = []
        for file in os.listdir(cookies_dir):
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
    """Run the video processing job in background"""
    try:
        update_job_status(job_id, 'downloading', 'Starting video download...', 10)
        
        # Change to the correct directory
        os.chdir('/Users/alexfreedman/simpleclipper/Clipception/non-mac-version')
        
        # Activate virtual environment and run processing
        cmd = f"""
        source clipception_env/bin/activate && \
        python process_and_upload.py "{video_url}" \
        --tiktok-user "{tiktok_user}" \
        --max-uploads {max_uploads} \
        --base-title "{base_title}"
        """
        
        update_job_status(job_id, 'processing', 'Processing video with AI...', 30)
        
        # Run the command
        process = subprocess.Popen(
            cmd, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            executable='/bin/bash'
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
                    # Extract number of clips
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
    
    if not is_url(video_url) and not os.path.exists(video_url):
        return jsonify({'error': 'Invalid URL or file path'}), 400
    
    if not tiktok_user:
        return jsonify({'error': 'TikTok user is required'}), 400
    
    # Check if user is logged in
    accounts = get_tiktok_accounts()
    if tiktok_user not in accounts:
        return jsonify({'error': f'TikTok user "{tiktok_user}" not logged in'}), 400
    
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
    """Initiate TikTok login"""
    data = request.json
    account_name = data.get('account_name', '').strip()
    
    if not account_name:
        return jsonify({'error': 'Account name is required'}), 400
    
    try:
        # Change to TikTok uploader directory
        os.chdir('/Users/alexfreedman/simpleclipper/TiktokAutoUploader')
        
        # Run login command
        cmd = f'source ../Clipception/non-mac-version/clipception_env/bin/activate && python cli.py login -n "{account_name}"'
        
        # Start login process (this will open browser)
        process = subprocess.Popen(
            cmd,
            shell=True,
            executable='/bin/bash'
        )
        
        return jsonify({'message': f'Login process started for {account_name}. Check your browser.'})
        
    except Exception as e:
        return jsonify({'error': f'Failed to start login: {str(e)}'}), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    print("🚀 Starting TikTok Auto Clipper Web Interface...")
    print("📱 Open http://localhost:4000 in your browser")
    
    app.run(debug=True, host='0.0.0.0', port=4000) 