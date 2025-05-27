#!/usr/bin/env python3
"""
TikTok Auto Clipper Web Interface - Cloud Ready Version
With simplified cookie-based TikTok authentication
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
import requests

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32))

# Cloud-compatible configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIES_DIR = os.environ.get('COOKIES_DIR', os.path.join(BASE_DIR, 'cookies'))
VIDEOS_DIR = os.environ.get('VIDEOS_DIR', os.path.join(BASE_DIR, 'videos'))
UPLOADS_DIR = os.environ.get('UPLOADS_DIR', os.path.join(BASE_DIR, 'uploads'))
TIKTOK_UPLOADER_DIR = os.environ.get('TIKTOK_UPLOADER_DIR', os.path.join(BASE_DIR, 'TiktokAutoUploader'))

# Create necessary directories with proper permissions
for directory in [COOKIES_DIR, VIDEOS_DIR, UPLOADS_DIR]:
    try:
        os.makedirs(directory, exist_ok=True)
        # Ensure directory is writable
        os.chmod(directory, 0o777)
    except Exception as e:
        print(f"Warning: Could not create directory {directory}: {e}")

# Add TikTok uploader to Python path
if TIKTOK_UPLOADER_DIR not in sys.path:
    sys.path.append(TIKTOK_UPLOADER_DIR)

# Global job storage (in production, use Redis or database)
jobs = {}
job_lock = threading.Lock()

@app.route('/auth/tiktok/simple', methods=['POST'])
def simple_tiktok_auth():
    """Handle super simple TikTok cookie submission"""
    data = request.json
    username = data.get('username', '').strip().replace('@', '')
    cookies_text = data.get('cookies', '').strip()
    
    if not username:
        return jsonify({'error': 'Username is required'}), 400
    
    if not cookies_text:
        return jsonify({'error': 'Please paste the result from TikTok'}), 400
    
    try:
        # Parse the simple cookie format
        cookies = parse_simple_cookies(cookies_text)
        
        # Validate we have the essential cookies
        required_cookies = ['sessionid', 'ttwid', 'msToken']
        missing_cookies = [cookie for cookie in required_cookies if cookie not in cookies]
        
        if missing_cookies:
            return jsonify({
                'error': f'Missing required cookies: {", ".join(missing_cookies)}. Make sure you\'re logged into TikTok and try again.'
            }), 400
        
        # Test if cookies actually work
        if not test_tiktok_cookies(cookies):
            return jsonify({
                'error': 'These cookies don\'t seem to work. Make sure you\'re logged into TikTok and the cookies are fresh.'
            }), 400
        
        # Save the session
        save_tiktok_session(username, cookies)
        
        # Log success for monitoring
        print(f"✅ Successfully authenticated TikTok user: {username}")
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully connected @{username} to TikTok!',
            'username': username,
            'expires_in_days': estimate_cookie_lifespan(cookies)
        })
        
    except Exception as e:
        print(f"❌ TikTok auth error for {username}: {str(e)}")
        return jsonify({
            'error': 'Something went wrong processing your cookies. Please try again or contact support.'
        }), 500

def parse_simple_cookies(cookies_text):
    """Parse cookies from raw document.cookie output"""
    cookies = {}
    
    # Remove any quotes if present
    cookies_text = cookies_text.strip('"\'')
    
    # Split by semicolon and parse each cookie
    for cookie_pair in cookies_text.split(';'):
        cookie_pair = cookie_pair.strip()
        if '=' in cookie_pair:
            name, value = cookie_pair.split('=', 1)
            name = name.strip()
            value = value.strip()
            
            # Only keep TikTok-relevant cookies
            if any(keyword in name.lower() for keyword in ['sessionid', 'ttwid', 'mstoken', 'sid_guard', 'uid_tt', 'sid_tt']):
                cookies[name] = value
    
    return cookies

def test_tiktok_cookies(cookies):
    """Test if TikTok cookies are valid by making a simple request"""
    try:
        # Create a session with the cookies
        session = requests.Session()
        
        # Convert cookies to requests format
        for name, value in cookies.items():
            session.cookies.set(name, value, domain='.tiktok.com')
        
        # Make a simple request to TikTok
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = session.get('https://www.tiktok.com/api/user/detail/', headers=headers, timeout=10)
        
        # If we get a response that's not a login redirect, cookies are good
        return response.status_code != 401 and 'login' not in response.url.lower()
        
    except Exception as e:
        print(f"Cookie test failed: {e}")
        return False  # Assume cookies are bad if test fails

def estimate_cookie_lifespan(cookies):
    """Estimate how long cookies will last (rough guess)"""
    # This is a rough estimation based on typical TikTok behavior
    if 'msToken' in cookies:
        # msToken usually expires quickly
        return 7  # 1 week estimate
    else:
        # Without msToken, might last longer
        return 30  # 1 month estimate

def save_tiktok_session(username, cookies):
    """Save TikTok session with metadata"""
    try:
        session_data = {
            'username': username,
            'cookies': cookies,
            'created_at': time.time(),
            'last_used': time.time(),
            'estimated_expiry': time.time() + (estimate_cookie_lifespan(cookies) * 24 * 3600),
            'upload_count': 0
        }
        
        session_file = os.path.join(COOKIES_DIR, f'tiktok_session-{username}.json')
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        # Set file permissions
        os.chmod(session_file, 0o600)  # Only owner can read/write
        
    except Exception as e:
        print(f"Error saving session for {username}: {e}")
        raise

@app.route('/auth/tiktok/status/<username>')
def check_tiktok_status(username):
    """Check the status of a TikTok session"""
    try:
        session_file = os.path.join(COOKIES_DIR, f'tiktok_session-{username}.json')
        
        if not os.path.exists(session_file):
            return jsonify({
                'status': 'not_connected',
                'message': 'No TikTok account connected'
            })
        
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        # Check if cookies are likely expired
        estimated_expiry = session_data.get('estimated_expiry', 0)
        days_remaining = (estimated_expiry - time.time()) / (24 * 3600)
        
        if days_remaining <= 0:
            return jsonify({
                'status': 'expired',
                'message': 'TikTok session has expired. Please reconnect.',
                'days_remaining': 0
            })
        elif days_remaining <= 3:
            return jsonify({
                'status': 'expiring_soon',
                'message': f'TikTok session expires in {int(days_remaining)} days',
                'days_remaining': int(days_remaining)
            })
        else:
            return jsonify({
                'status': 'active',
                'message': f'TikTok session active ({int(days_remaining)} days remaining)',
                'days_remaining': int(days_remaining),
                'upload_count': session_data.get('upload_count', 0),
                'connected_since': session_data.get('created_at')
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Error checking TikTok status'
        }), 500

def setup_selenium_driver():
    """Setup headless Chrome for TikTok authentication"""
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')  # Updated headless mode
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-notifications')
    
    # Add user agent to appear more like a real browser
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    try:
        return webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print(f"Error creating Chrome driver: {e}")
        raise

def save_tiktok_session(username, cookies):
    """Save TikTok session cookies securely"""
    try:
        session_file = os.path.join(COOKIES_DIR, f'tiktok_session-{username}.json')
        with open(session_file, 'w') as f:
            json.dump(cookies, f)
        os.chmod(session_file, 0o666)
    except Exception as e:
        print(f"Error saving session: {e}")
        raise

@app.route('/auth/check', methods=['POST'])
def check_auth():
    """Check if user is logged in"""
    data = request.json
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({'error': 'Username is required'}), 400
    
    try:
        # Check if session file exists
        session_file = os.path.join(COOKIES_DIR, f'tiktok_session-{username}.json')
        if os.path.exists(session_file):
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            return jsonify({
                'status': 'success',
                'message': 'Already logged in',
                'username': username
            })
        else:
            return jsonify({
                'status': 'not_logged_in',
                'message': 'Please log in to TikTok'
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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