# 🚀 TikTok Auto Upload Integration Setup

## 🎉 Complete Pipeline: Twitch VOD → AI Clips → Auto TikTok Upload!

You now have a complete end-to-end system that can:
1. Download Twitch VODs automatically
2. Generate viral clips using AI
3. Upload the best clips directly to TikTok

## 🔑 First Time Setup: Login to TikTok

Before you can upload clips, you need to login to your TikTok account once:

```bash
# Navigate to TikTok uploader directory
cd /Users/alexfreedman/simpleclipper/TiktokAutoUploader

# Login to TikTok (this will open a browser)
python cli.py login -n my_tiktok_account
```

**What happens:**
- A browser window will open
- Login to your TikTok account normally
- The system will save your session cookies locally
- You only need to do this once!

## 🎬 Complete Auto Pipeline Usage

Once logged in, you can process any video and auto-upload clips:

```bash
# Navigate back to Clipception
cd /Users/alexfreedman/simpleclipper/Clipception/non-mac-version

# Complete pipeline: VOD → Clips → TikTok Upload
python process_and_upload.py "https://www.twitch.tv/videos/123456789" --tiktok-user my_tiktok_account --max-uploads 3 --base-title "Epic Gaming Moments"
```

## 📋 Command Options

```bash
python process_and_upload.py <video_or_url> --tiktok-user <username> [options]

Required:
  video_or_url          Video file path or URL (Twitch, YouTube, etc.)
  --tiktok-user         TikTok username (from login step)

Optional:
  --max-uploads         Number of clips to upload (default: 3)
  --base-title          Base title for TikTok posts (default: video title)
```

## 🎯 Example Commands

```bash
# Process Twitch VOD and upload top 3 clips
python process_and_upload.py "https://www.twitch.tv/videos/2345678901" --tiktok-user my_account --max-uploads 3

# Process local video file
python process_and_upload.py "~/Downloads/stream.mp4" --tiktok-user my_account --max-uploads 5 --base-title "Best Moments"

# Process YouTube video
python process_and_upload.py "https://youtube.com/watch?v=dQw4w9WgXcQ" --tiktok-user my_account --max-uploads 2
```

## 🔄 What Happens During the Complete Pipeline

1. **🔗 Auto Download** (if URL) - Downloads video from Twitch/YouTube
2. **🎵 Audio Extraction** - Extracts audio for analysis
3. **📝 AI Transcription** - Uses Whisper to transcribe speech
4. **🔊 Audio Analysis** - Analyzes excitement, volume, reactions
5. **🤖 AI Ranking** - DeepSeek AI ranks clips by viral potential
6. **✂️ Clip Extraction** - Creates video clips (20-120 seconds)
7. **📤 TikTok Upload** - Automatically uploads best clips
8. **⏳ Smart Delays** - Waits between uploads to avoid rate limits

## 📁 Output Structure

```
FeatureTranscribe/
├── video_name.enhanced_transcription.json
├── top_clips_one.json
├── video_name.mp4
└── clips/
    ├── clip_1.mp4  ← Uploaded to TikTok
    ├── clip_2.mp4  ← Uploaded to TikTok  
    ├── clip_3.mp4  ← Uploaded to TikTok
    └── ...         ← Additional clips (not uploaded)
```

## ⚡ Pro Tips

- **Rate Limiting**: The system waits 30 seconds between uploads to avoid TikTok rate limits
- **Title Optimization**: Titles are automatically truncated to TikTok's limits
- **Quality**: Clips are optimized for TikTok (vertical format works best)
- **Viral Scoring**: AI ranks clips 1-10 for engagement potential
- **Multiple Accounts**: You can login to multiple TikTok accounts with different names

## 🛠️ Managing TikTok Accounts

```bash
# Login to additional accounts
python cli.py login -n gaming_account
python cli.py login -n reaction_account

# Show all logged in accounts
python cli.py show -u

# Use different account for uploads
python process_and_upload.py "video.mp4" --tiktok-user gaming_account
```

## 🎊 You're Ready to Go Viral!

Your complete TikTok automation pipeline is ready! Just run one command and watch as it:

1. Downloads any video from the internet
2. Finds the most viral moments using AI
3. Creates perfect TikTok clips
4. Uploads them automatically to your account

**Start creating viral content now:**
```bash
python process_and_upload.py "https://www.twitch.tv/videos/YOUR_VOD_ID" --tiktok-user my_account --max-uploads 3
```

The future of content creation is here! 🚀 