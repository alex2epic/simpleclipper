# 🎥 Clipception Setup Guide for macOS

This guide will help you set up Clipception on macOS to automatically generate viral clips from your videos.

## ✅ Prerequisites Check

All of these are already installed and working:
- ✅ Python 3.13.2 (requirement: 3.10+)
- ✅ FFmpeg (for video processing)
- ✅ Virtual environment created and activated
- ✅ All Python dependencies installed

## 🔑 Required: OpenRouter API Key

You need to get an API key from OpenRouter to use the AI clip ranking feature:

1. Go to [https://openrouter.ai/](https://openrouter.ai/)
2. Sign up for an account
3. Get your API key from the dashboard
4. Set the environment variable:

```bash
export OPEN_ROUTER_KEY='your_api_key_here'
```

To make this permanent, add it to your `~/.zshrc` file:
```bash
echo 'export OPEN_ROUTER_KEY="your_api_key_here"' >> ~/.zshrc
source ~/.zshrc
```

## 🚀 Usage

Once you have your API key set up, you can process videos:

```bash
# Make sure you're in the right directory and virtual environment is active
cd /Users/alexfreedman/simpleclipper/Clipception/non-mac-version
source clipception_env/bin/activate

# Process a video
python process_vid_v4.py /path/to/your/video.mp4
```

## 📁 Output

The script will create a `FeatureTranscribe/` directory with:
- `[video_name].enhanced_transcription.json` - Detailed transcription with audio features
- `top_clips_one.json` - Ranked clips with engagement metrics  
- `clips/` - Directory containing extracted video segments ready for upload

## 🔧 Testing Setup

Run the setup checker:
```bash
./setup.sh
```

## 📝 Notes

- **Processing Time**: For a 1080p video that is 4+ hours long, expect approximately 30 minutes processing time
- **GPU**: This version works on macOS with CPU processing (CUDA not available on Mac)
- **Models**: Uses OpenAI Whisper for transcription and DeepSeek for clip ranking
- **Audio Features**: Analyzes volume, intensity, and spectral characteristics for better clip selection

## 🎯 Supported Video Formats

- MP4, AVI, MOV, MKV, and other FFmpeg-supported formats
- Recommended: 1080p or higher resolution for best results

## 🆘 Troubleshooting

If you encounter issues:

1. **Import errors**: Make sure virtual environment is activated
2. **FFmpeg errors**: Ensure FFmpeg is properly installed with `brew install ffmpeg`
3. **API errors**: Check that your OpenRouter API key is correctly set
4. **Memory issues**: For very long videos, consider using a smaller Whisper model (add `--model base` to transcription.py)

## 🎬 Ready to Create Viral Clips!

Once everything is set up, you can start processing your videos and automatically extract the most engaging moments for TikTok, YouTube Shorts, and other platforms! 