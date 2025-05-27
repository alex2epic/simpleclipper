#!/bin/bash

echo "🚀 Starting TikTok Auto Clipper Web Interface..."
echo "================================================"

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment is activated: $VIRTUAL_ENV"
else
    echo "🔄 Activating virtual environment..."
    source clipception_env/bin/activate
fi

# Check for OpenRouter API key
if [[ -z "$OPEN_ROUTER_KEY" ]]; then
    echo "⚠️  Warning: OPEN_ROUTER_KEY not set"
    echo "   The system will still work for TikTok login, but video processing requires the API key"
fi

echo ""
echo "🌐 Starting web server..."
echo "📱 Open your browser to: http://localhost:8080"
echo ""
echo "💡 Features available:"
echo "   • Paste video URLs (Twitch, YouTube, etc.)"
echo "   • Monitor processing status in real-time"
echo "   • Login to TikTok accounts via popup"
echo "   • Auto-upload clips to TikTok"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python web_app.py 