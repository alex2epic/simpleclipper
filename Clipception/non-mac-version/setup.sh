#!/bin/bash

echo "🎥 Clipception Setup Script"
echo "=========================="

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment is activated: $VIRTUAL_ENV"
else
    echo "❌ Virtual environment not activated. Please run:"
    echo "   source clipception_env/bin/activate"
    exit 1
fi

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "✅ Python version: $python_version"

# Check FFmpeg
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg is installed"
else
    echo "❌ FFmpeg not found. Please install it:"
    echo "   brew install ffmpeg"
    exit 1
fi

# Check OpenRouter API key
if [[ -z "$OPEN_ROUTER_KEY" ]]; then
    echo "❌ OPEN_ROUTER_KEY environment variable not set"
    echo "   Please get an API key from https://openrouter.ai/"
    echo "   Then set it with: export OPEN_ROUTER_KEY='your_key_here'"
    echo "   Or add it to your ~/.zshrc file for persistence"
    exit 1
else
    echo "✅ OpenRouter API key is set"
fi

# Test imports
echo "🔍 Testing Python imports..."
python3 -c "
import whisper
import torch
import librosa
import soundfile
import pydub
from openai import OpenAI
import pandas as pd
import numpy as np
print('✅ All required packages imported successfully')
"

if [ $? -eq 0 ]; then
    echo "🎉 Setup complete! You can now process videos with:"
    echo "   python process_vid_v4.py /path/to/your/video.mp4"
else
    echo "❌ Some imports failed. Please check the error messages above."
    exit 1
fi 