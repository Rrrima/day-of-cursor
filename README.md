# 🖱️ Day of a Cursor

Watch your cursor's journey through time! Record your screen and cursor movements, then replay them as a bird's-eye view or experience it from your cursor's POV 👁️

## Recording Your Screen

### Setup (First Time)

```bash
# Create a virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Start Recording

```bash
python capture_server_video.py --tag <your_tag>
```

Examples:

```bash
python capture_server_video.py --tag lit_review
python capture_server_video.py --tag debugging_session
```

### Stop Recording

Press **Ctrl+C** to stop recording

Your files will be saved in `__cursor_data/`:

- `screen_capture_<your_tag>.webm` - Your screen recording
- `mouse_positions_<your_tag>.csv` - Cursor position data

## Viewing Your Recording

### Launch the Frontend

```bash
# Install frontend dependencies (first time only)
npm install

# Start the development server
npm start
```

The app will open at `http://localhost:3000`

### Configure Your Tag

Before viewing, update the tag name in `src/AppVideo.jsx`:

```javascript
const TAG = "your_tag"; // Change this to match your recording tag
```

Then enjoy your cursor's replay!

## PNG Mode (Deprecated)

> Warning: This mode saves individual PNG screenshots and will eat your disk space fast!

If you still want to use it:

1. Use `capture_server.py` instead of `capture_server_video.py`
2. Update `src/index.js` to render `<App />` instead of `<AppVideo />`

## Advanced Options

### Recording Options

```bash
python capture_server_video.py \
  --tag my_session \
  --fps 10 \                    # Frames per second (default: 10)
  --quality low \               # low/medium/high (default: low)
  --output-dir __cursor_data    # Output directory
```

## Requirements

- Python 3.7+
- Node.js and npm
- FFmpeg (for video encoding)
- macOS (uses Quartz for screen capture)

---

Made with ✨ for tracking every pixel of your cursor's adventure
