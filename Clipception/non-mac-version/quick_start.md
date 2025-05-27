# 🚀 Quick Start Guide

## You're All Set! 🎉

Clipception is now fully installed and configured on your macOS system. Here's how to use it:

## 📹 Processing Your First Video

1. **Make sure you're in the right directory:**
   ```bash
   cd /Users/alexfreedman/simpleclipper/Clipception/non-mac-version
   source clipception_env/bin/activate
   ```

2. **Process a video (local file):**
   ```bash
   python process_vid_v4.py /path/to/your/video.mp4
   ```

   **Or process a Twitch VOD directly (auto-download):**
   ```bash
   python process_twitch_vod.py https://www.twitch.tv/videos/123456789
   ```

   Examples:
   ```bash
   # Local file
   python process_vid_v4.py ~/Downloads/my_stream.mp4
   
   # Twitch VOD (auto-downloads)
   python process_twitch_vod.py https://www.twitch.tv/videos/2345678901
   
   # YouTube video (also works!)
   python process_twitch_vod.py https://youtube.com/watch?v=dQw4w9WgXcQ
   ```

## 🔄 What Happens During Processing

**For Twitch VODs/URLs:**
1. **Auto-Download** - Downloads the video from Twitch/YouTube using yt-dlp
2. **Audio Extraction** - Extracts audio from your video
3. **Transcription** - Uses OpenAI Whisper to transcribe speech with timestamps
4. **Audio Analysis** - Analyzes volume, intensity, and emotional characteristics
5. **AI Ranking** - Uses DeepSeek AI to rank clips by viral potential
6. **Clip Extraction** - Creates actual video clips ready for upload

**For Local Files:**
1. **Audio Extraction** - Extracts audio from your video
2. **Transcription** - Uses OpenAI Whisper to transcribe speech with timestamps
3. **Audio Analysis** - Analyzes volume, intensity, and emotional characteristics
4. **AI Ranking** - Uses DeepSeek AI to rank clips by viral potential
5. **Clip Extraction** - Creates actual video clips ready for upload

## 📁 Output Structure

After processing, you'll find:
```
FeatureTranscribe/
├── your_video.enhanced_transcription.json  # Detailed transcription
├── top_clips_one.json                      # Ranked clips metadata
├── your_video.mp4                          # Copy of original video
└── clips/                                  # Extracted video clips
    ├── clip_1.mp4
    ├── clip_2.mp4
    └── ...
```

## ⚡ Pro Tips

- **Best Results**: Use videos with clear speech and varied audio (reactions, excitement)
- **File Formats**: MP4, AVI, MOV, MKV all supported
- **Processing Time**: ~30 minutes for 4+ hour 1080p videos
- **Clip Length**: Default 20-120 seconds, optimized for TikTok/YouTube Shorts

## 🎯 Ready to Go Viral!

Your TikTok auto clipper is ready! Just point it at any video file and it will automatically find and extract the most engaging moments.

**Example command to get started:**
```bash
python process_vid_v4.py ~/Downloads/your_video.mp4
```

The clips will be saved in the `FeatureTranscribe/clips/` directory, ready to upload to TikTok, YouTube Shorts, or any other platform! 