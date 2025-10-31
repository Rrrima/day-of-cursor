#!/bin/bash
# Setup script for video-based screen capture

echo "=========================================="
echo "Video Mode Setup for Screen Capture"
echo "=========================================="
echo ""

# Check if FFmpeg is installed
echo "Checking for FFmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "✓ FFmpeg is installed"
    ffmpeg -version | head -n 1
else
    echo "✗ FFmpeg is not installed"
    echo ""
    echo "Please install FFmpeg using Homebrew:"
    echo "  brew install ffmpeg"
    echo ""
    exit 1
fi

echo ""

# Check Python version
echo "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✓ $PYTHON_VERSION"
else
    echo "✗ Python 3 is not installed"
    exit 1
fi

echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements_video.txt

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To start capturing:"
echo "  python3 capture_server_video.py"
echo ""
echo "To use the video viewer frontend:"
echo "  1. Update your entry point to use AppVideo.jsx"
echo "  2. Run your webpack dev server"
echo ""
echo "See VIDEO_OPTIMIZATION.md for more details"
echo ""

