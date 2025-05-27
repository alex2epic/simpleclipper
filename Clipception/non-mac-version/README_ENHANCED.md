# 🎥 Clipception - Enhanced TikTok Auto Clipper

## ✅ FULLY INSTALLED & READY TO USE!

Your TikTok auto clipper is now fully set up with **Twitch VOD auto-download support**! 🎉

## 🚀 Two Ways to Use

### 1. Process Local Video Files
```bash
python process_vid_v4.py /path/to/your/video.mp4
```

### 2. Process Twitch VODs/URLs (NEW!)
```bash
python process_twitch_vod.py https://www.twitch.tv/videos/123456789
```

## 🌟 Supported Platforms

- ✅ **Twitch VODs** - `https://www.twitch.tv/videos/123456789`
- ✅ **YouTube Videos** - `https://youtube.com/watch?v=...`
- ✅ **Local Files** - MP4, AVI, MOV, MKV, etc.
- ✅ **Most video platforms** supported by yt-dlp

## 🔧 What's Installed

- ✅ Python 3.13.2 with virtual environment
- ✅ OpenAI Whisper for transcription
- ✅ DeepSeek AI for clip ranking
- ✅ yt-dlp for video downloading
- ✅ FFmpeg for video processing
- ✅ All audio analysis libraries
- ✅ OpenRouter API key configured

## 📁 Output Structure

```
FeatureTranscribe/
├── video_name.enhanced_transcription.json  # AI transcription with audio features
├── top_clips_one.json                      # Ranked clips by viral potential
├── video_name.mp4                          # Processed video file
└── clips/                                  # Ready-to-upload clips!
    ├── clip_1.mp4                          # Top viral moment
    ├── clip_2.mp4                          # Second best clip
    └── ...                                 # Up to 20 clips
```

## 🎯 Example Usage

```bash
# Activate environment (if not already active)
cd /Users/alexfreedman/simpleclipper/Clipception/non-mac-version
source clipception_env/bin/activate

# Process a Twitch VOD
python process_twitch_vod.py https://www.twitch.tv/videos/2345678901

# Process a local file
python process_vid_v4.py ~/Downloads/stream_recording.mp4
```

## ⚡ Features

- 🤖 **AI-Powered Clip Detection** - Finds the most viral moments
- 🔊 **Advanced Audio Analysis** - Detects excitement, laughter, reactions
- 📊 **Viral Potential Scoring** - Ranks clips 1-10 for engagement
- 🎬 **Auto Video Extraction** - Creates ready-to-upload clips
- ⬇️ **Auto Download** - Works directly with Twitch VOD links
- 🎯 **TikTok Optimized** - 20-120 second clips perfect for social media

## 📝 Processing Time

- **Short videos (< 1 hour)**: 5-10 minutes
- **Medium videos (1-3 hours)**: 15-25 minutes  
- **Long streams (4+ hours)**: 30-45 minutes

## 🎬 Ready to Go Viral!

Your auto clipper is ready! Just paste any Twitch VOD link or point it at a video file, and it will automatically:

1. Download the video (if URL)
2. Transcribe all speech with timestamps
3. Analyze audio for excitement/engagement
4. Use AI to rank the most viral moments
5. Extract clips ready for TikTok/YouTube Shorts

**Start creating viral content now:**
```bash
python process_twitch_vod.py https://www.twitch.tv/videos/YOUR_VOD_ID
```

The clips will be in `FeatureTranscribe/clips/` ready to upload! 🚀 