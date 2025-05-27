# 🚀 TikTok Auto Clipper - Render Cloud Deployment Guide

## 📋 Overview

This guide explains how to deploy the TikTok Auto Clipper system to Render cloud platform. The cloud version has been optimized with:

- ✅ **Dynamic path handling** (no hardcoded Mac paths)
- ✅ **Environment variables** for configuration
- ✅ **CPU-optimized dependencies** (no GPU requirements)
- ✅ **Background job processing**
- ✅ **Automatic cleanup** of temporary files
- ✅ **Health checks** and monitoring

## 🏗️ Architecture

The cloud deployment consists of:

1. **Web Service** - Flask app with web interface
2. **Worker Service** - Background video processing (optional)
3. **Cron Job** - Daily cleanup of temporary files
4. **Environment Variables** - Configuration management

## 🔧 Prerequisites

1. **GitHub Repository** with your code
2. **Render Account** (free tier available)
3. **OpenRouter API Key** for AI processing
4. **TikTok Cookies** (manual setup required)

## 📦 Files Added for Cloud Deployment

### Core Files:
- `Clipception/non-mac-version/app.py` - Cloud-ready Flask app
- `Clipception/non-mac-version/process_and_upload_cloud.py` - Cloud processing script
- `Clipception/non-mac-version/requirements-cloud.txt` - Cloud dependencies
- `Clipception/non-mac-version/cleanup.py` - File cleanup script
- `render.yaml` - Render deployment configuration

### Key Changes Made:
- **Removed hardcoded paths**: `/Users/alexfreedman/simpleclipper/` → environment variables
- **Added dynamic configuration**: Uses `os.environ.get()` for all paths
- **CPU-only dependencies**: Removed CUDA/GPU packages
- **Cloud-compatible commands**: No virtual environment activation needed

## 🚀 Deployment Steps

### Step 1: Prepare Your Repository

1. **Push to GitHub:**
```bash
git add .
git commit -m "Add cloud deployment configuration"
git push origin main
```

### Step 2: Create Render Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repository
4. Render will detect the `render.yaml` file automatically

### Step 3: Configure Environment Variables

In the Render dashboard, set these environment variables:

| Variable | Value | Description |
|----------|--------|-------------|
| `OPEN_ROUTER_KEY` | `your_api_key_here` | Required for AI processing |
| `FLASK_ENV` | `production` | Flask environment |
| `PYTHONUNBUFFERED` | `1` | Real-time logging |

### Step 4: Deploy

1. Click **"Apply"** in Render dashboard
2. Watch the build logs for any errors
3. The deployment will take 5-10 minutes

## 🍪 TikTok Cookie Setup (Manual)

Since browser automation doesn't work in cloud environments, TikTok login requires manual cookie setup:

### Option 1: Local Export Method
1. Login to TikTok on your local machine
2. Use browser dev tools to export cookies
3. Upload cookie files to the server (contact admin)

### Option 2: Cookie Management API
```python
# Future enhancement - API endpoint for cookie upload
POST /api/upload_cookies
{
  "account_name": "my_tiktok_account",
  "cookies": "exported_cookie_data"
}
```

## 🔍 Monitoring & Health Checks

### Health Check Endpoint
```
GET /health
```

Returns:
```json
{
  "status": "healthy",
  "timestamp": 1234567890,
  "version": "1.0.0",
  "directories": {
    "cookies": true,
    "videos": true,
    "uploads": true
  }
}
```

### System Information
```
GET /api/system_info
```

Returns configuration details and system status.

## 🧹 Automatic Cleanup

The system includes automatic cleanup:

- **Cron Job**: Runs daily at 2 AM
- **File Age**: Removes files older than 24 hours
- **File Types**: Videos, audio, temporary processing files
- **Storage Management**: Prevents disk space issues

## 📊 Usage Limits & Costs

### Render Free Tier:
- ✅ **Web Service**: 750 hours/month
- ✅ **Cron Jobs**: Included
- ⚠️ **Processing Time**: 15-minute timeout per request
- ⚠️ **Storage**: Ephemeral (files deleted on restart)

### Render Paid Plans:
- 💰 **Starter**: $25/month - Better for production
- 💰 **Standard**: $85/month - Higher limits
- 💰 **Pro**: $340/month - Enterprise features

## ⚡ Performance Optimization

### Video Processing Tips:
1. **Shorter videos** process faster (< 30 minutes recommended)
2. **Batch processing** reduces memory usage
3. **CPU optimization** for cloud environment

### Code Optimizations Made:
```python
# Before (Mac-specific):
sys.path.append('/Users/alexfreedman/simpleclipper/TiktokAutoUploader')

# After (Cloud-compatible):
TIKTOK_UPLOADER_DIR = os.environ.get('TIKTOK_UPLOADER_DIR', 
                                    os.path.join(BASE_DIR, '..', 'TiktokAutoUploader'))
sys.path.append(TIKTOK_UPLOADER_DIR)
```

## 🐛 Troubleshooting

### Common Issues:

1. **Build Fails**: Check `requirements-cloud.txt` dependencies
2. **Import Errors**: Verify `PYTHONPATH` environment variable
3. **File Not Found**: Check directory permissions and paths
4. **Memory Issues**: Reduce concurrent processing

### Debug Commands:
```bash
# Check logs in Render dashboard
# View system info
curl https://your-app.onrender.com/api/system_info

# Health check
curl https://your-app.onrender.com/health
```

## 🔄 Updates & Maintenance

### Updating the Application:
1. Push changes to GitHub
2. Render auto-deploys from main branch
3. Monitor deployment in dashboard

### Manual Restart:
1. Go to Render dashboard
2. Click service → "Manual Deploy"
3. Or restart via API

## 🌟 Production Recommendations

For production use:

1. **Upgrade to paid plan** for better performance
2. **Set up Redis** for job queue management
3. **Add monitoring** with external services
4. **Implement user authentication**
5. **Add rate limiting** to prevent abuse
6. **Set up database** for persistent job storage

## 📞 Support

If you encounter issues:

1. Check the [Render Documentation](https://render.com/docs)
2. Review application logs in Render dashboard
3. Test locally first with the cloud configuration
4. Verify all environment variables are set correctly

## 🎉 Success!

Once deployed, your TikTok Auto Clipper will be available at:
```
https://your-app-name.onrender.com
```

The system can now:
- ✅ Process videos from URLs
- ✅ Generate AI-powered clips
- ✅ Upload to TikTok automatically
- ✅ Handle multiple concurrent users
- ✅ Scale based on demand 