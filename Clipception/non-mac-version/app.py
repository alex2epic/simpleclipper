#!/usr/bin/env python3
"""
TikTok Auto Clipper Web Interface - Cloud Ready Version
With secure browser-based TikTok authentication
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import subprocess
import os
import sys
import json
import time
import threading
import uuid
import secrets
from pathlib import Path
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32))

# Cloud-compatible configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIES_DIR = os.environ.get('COOKIES_DIR', os.path.join(BASE_DIR, 'cookies'))
VIDEOS_DIR = os.environ.get('VIDEOS_DIR', os.path.join(BASE_DIR, 'videos'))
UPLOADS_DIR = os.environ.get('UPLOADS_DIR', os.path.join(BASE_DIR, 'uploads'))
TIKTOK_UPLOADER_DIR = os.environ.get('TIKTOK_UPLOADER_DIR', os.path.join(BASE_DIR, 'TiktokAutoUploader'))

# Create necessary directories
for directory in [COOKIES_DIR, VIDEOS_DIR, UPLOADS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Add TikTok uploader to Python path
if TIKTOK_UPLOADER_DIR not in sys.path:
    sys.path.append(TIKTOK_UPLOADER_DIR)

# Global job storage (in production, use Redis or database)
jobs = {}
job_lock = threading.Lock()

def setup_selenium_driver():
    """Setup headless Chrome for TikTok authentication"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Add user agent to appear more like a real browser
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    return webdriver.Chrome(options=chrome_options)

def save_tiktok_session(username, cookies):
    """Save TikTok session cookies securely"""
    session_file = os.path.join(COOKIES_DIR, f'tiktok_session-{username}.json')
    with open(session_file, 'w') as f:
        json.dump(cookies, f)

@app.route('/auth/tiktok', methods=['POST'])
def tiktok_auth():
    """Handle TikTok authentication"""
    data = request.json
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({'error': 'Username is required'}), 400
    
    try:
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        session['auth_session_id'] = session_id
        
        # Start authentication in background
        thread = threading.Thread(
            target=handle_tiktok_auth,
            args=(username, session_id)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'processing',
            'session_id': session_id,
            'message': 'Starting TikTok authentication...'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def handle_tiktok_auth(username, session_id):
    """Handle TikTok authentication in background"""
    try:
        driver = setup_selenium_driver()
        
        # Navigate to TikTok login
        driver.get('https://www.tiktok.com/login')
        
        # Wait for login form
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="username"]'))
        )
        
        # Store initial state
        auth_state = {
            'status': 'waiting',
            'message': 'Please log in to TikTok in the popup window',
            'session_id': session_id
        }
        
        # Save state to file for frontend polling
        state_file = os.path.join(COOKIES_DIR, f'auth_state-{session_id}.json')
        with open(state_file, 'w') as f:
            json.dump(auth_state, f)
        
        # Wait for successful login (check for session cookie)
        WebDriverWait(driver, 60).until(
            lambda d: any('sessionid' in cookie['name'].lower() for cookie in d.get_cookies())
        )
        
        # Get all cookies
        cookies = driver.get_cookies()
        
        # Save session
        save_tiktok_session(username, cookies)
        
        # Update state
        auth_state.update({
            'status': 'success',
            'message': 'Successfully logged in to TikTok',
            'username': username
        })
        
        with open(state_file, 'w') as f:
            json.dump(auth_state, f)
            
    except Exception as e:
        # Update state with error
        auth_state.update({
            'status': 'error',
            'message': f'Authentication failed: {str(e)}'
        })
        
        with open(state_file, 'w') as f:
            json.dump(auth_state, f)
            
    finally:
        try:
            driver.quit()
        except:
            pass

@app.route('/auth/tiktok/status/<session_id>')
def auth_status(session_id):
    """Check authentication status"""
    state_file = os.path.join(COOKIES_DIR, f'auth_state-{session_id}.json')
    
    if not os.path.exists(state_file):
        return jsonify({'error': 'Invalid session ID'}), 404
    
    with open(state_file, 'r') as f:
        state = json.load(f)
    
    # Clean up state file if authentication is complete
    if state['status'] in ['success', 'error']:
        try:
            os.remove(state_file)
        except:
            pass
    
    return jsonify(state)

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