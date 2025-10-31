import time
import csv
import os
import subprocess
import signal
import sys
import argparse
from datetime import datetime
from queue import Queue
import threading
from PIL import Image, ImageDraw
import Quartz
import mss
import numpy as np


class ScreenCaptureVideo:
    def __init__(self, capture_interval=0.1, output_dir="__cursor_data", tag="", 
                 video_quality="medium", fps=10):
        """
        Initialize screen capture system with video encoding
        
        Args:
            capture_interval: Time between captures in seconds (default: 0.1 = 10 FPS)
            output_dir: Directory to save video and CSV
            tag: Tag for naming files
            video_quality: 'low' (faster, larger), 'medium' (balanced), 'high' (slower, smaller)
            fps: Frames per second for the output video (should match 1/capture_interval)
        """
        self.capture_interval = capture_interval
        self.output_dir = output_dir
        self.tag = tag
        self.fps = fps
        self.running = False
        
        # Quality presets for H.264 encoding
        self.quality_presets = {
            'low': {'crf': 28, 'preset': 'ultrafast'},  # Fast, larger files
            'medium': {'crf': 23, 'preset': 'medium'},  # Balanced
            'high': {'crf': 18, 'preset': 'slow'}       # Slower, better compression
        }
        self.video_quality = self.quality_presets.get(video_quality, self.quality_presets['medium'])
        
        # Create output directory
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"Created output directory: {self.output_dir}")
        
        # Frame queue for video encoding
        self.frame_queue = Queue(maxsize=300)  # Buffer up to 30 seconds at 10 FPS
        
        # CSV logging
        self.mouse_positions = []
        self.csv_file_path = os.path.join(self.output_dir, f"mouse_positions_{self.tag}.csv")
        self.csv_update_interval = 0.5
        self.data_lock = threading.Lock()
        
        # Video output (use .webm for transparency support)
        self.video_file_path = os.path.join(self.output_dir, f"screen_capture_{self.tag}.webm")
        self.ffmpeg_process = None
        self.start_time = None
        self.frame_count = 0
        self.queued_frame_count = 0  # Frames queued for encoding
        
        # Initialize mss
        self.sct = mss.mss()
        self._update_screen_info()
    
    def _get_global_bounds(self):
        """Return a bounding box enclosing all physical displays"""
        err, ids, cnt = Quartz.CGGetActiveDisplayList(16, None, None)
        if err != Quartz.kCGErrorSuccess:
            raise OSError(f"CGGetActiveDisplayList failed: {err}")
        
        min_x = min_y = float("inf")
        max_x = max_y = -float("inf")
        for did in ids[:cnt]:
            r = Quartz.CGDisplayBounds(did)
            x0, y0 = r.origin.x, r.origin.y
            x1, y1 = x0 + r.size.width, y0 + r.size.height
            min_x, min_y = min(min_x, x0), min(min_y, y0)
            max_x, max_y = max(max_x, x1), max(max_y, y1)
        return min_x, min_y, max_x, max_y
    
    def _update_screen_info(self):
        """Get screen configuration using mss"""
        monitors = self.sct.monitors
        self.combined_monitor = monitors[0]
        self.width = self.combined_monitor['width'] // 2  # 50% size
        self.height = self.combined_monitor['height'] // 2
        
        print(f"Detected {len(monitors) - 1} monitor(s)")
        print(f"Combined screen area: {self.combined_monitor['width']}x{self.combined_monitor['height']}")
        print(f"Output video size: {self.width}x{self.height}")
        
        # Get global bounds for coordinate conversion
        self.min_x, self.min_y, self.max_x, self.gmax_y = self._get_global_bounds()
    
    def _draw_rounded_rectangle(self, draw, bounds, radius, outline_color, width):
        """Draw a rounded rectangle with rounded corners"""
        x0, y0, x1, y1 = bounds
        
        # Use PIL's built-in rounded_rectangle method for better rendering
        # This ensures corners and edges connect properly
        draw.rounded_rectangle(
            [x0, y0, x1, y1],
            radius=radius,
            outline=outline_color,
            width=width
        )
    
    def _capture_all_displays(self):
        """Capture all displays and return as PIL Image"""
        screenshot = self.sct.grab(self.combined_monitor)
        img = Image.frombytes("RGB", (screenshot.width, screenshot.height), screenshot.rgb)
        img = img.convert("RGBA")
        
        # Create mask for display areas with rounded corners
        mask = Image.new("L", (img.width, img.height), 0)
        mask_draw = ImageDraw.Draw(mask)
        
        monitors = self.sct.monitors
        monitor_bounds = []
        border_radius = 24
        
        for i in range(1, len(monitors)):
            mon = monitors[i]
            x = mon['left'] - self.combined_monitor['left']
            y = mon['top'] - self.combined_monitor['top']
            bounds = (x, y, x + mon['width'], y + mon['height'])
            
            # Draw rounded rectangle mask to clip content
            mask_draw.rounded_rectangle(
                [bounds[0], bounds[1], bounds[2], bounds[3]],
                radius=border_radius,
                fill=255
            )
            monitor_bounds.append(bounds)
        
        img.putalpha(mask)
        
        # Draw borders on top of the clipped content
        draw = ImageDraw.Draw(img, 'RGBA')
        border_color = (255, 255, 255)
        
        for bounds in monitor_bounds:
            self._draw_rounded_rectangle(draw, bounds, border_radius, border_color, 6)
        
        # Resize to 50% for efficiency
        new_size = (self.width, self.height)
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        return img
    
    def _get_cursor_pos(self):
        """Get current cursor position"""
        event = Quartz.CGEventCreate(None)
        cursor_location = Quartz.CGEventGetLocation(event)
        
        img_x = cursor_location.x - self.combined_monitor['left']
        img_y = cursor_location.y - self.combined_monitor['top']
        
        return {"x": img_x, "y": img_y}
    
    def _start_ffmpeg(self):
        """Start FFmpeg process for video encoding with transparency support"""
        # FFmpeg command for VP9 encoding with alpha channel (transparency)
        # Use variable frame rate (VFR) to match actual capture timing
        cmd = [
            'ffmpeg',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-s', f'{self.width}x{self.height}',
            '-pix_fmt', 'rgba',  # RGBA for transparency
            '-r', str(self.fps),  # Input frame rate
            '-i', '-',  # Read from stdin
            '-an',  # No audio
            '-vcodec', 'libvpx-vp9',  # VP9 codec supports alpha
            '-pix_fmt', 'yuva420p',  # Output with alpha channel
            '-crf', str(self.video_quality['crf']),
            '-b:v', '0',  # Use CRF rate control
            '-auto-alt-ref', '0',  # Disable alt-ref frames for transparency
            '-vsync', 'vfr',  # Variable frame rate - important!
            '-y',  # Overwrite output file
            self.video_file_path
        ]
        
        self.ffmpeg_process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=10**8
        )
        print(f"FFmpeg started, encoding to: {self.video_file_path}")
    
    def _video_encoder_worker(self):
        """Worker thread that encodes frames to video"""
        self._start_ffmpeg()
        
        while self.running:
            try:
                frame_data = self.frame_queue.get(timeout=1)
                if frame_data is None:  # Poison pill to stop
                    break
                
                # Convert PIL Image to RGBA numpy array (preserve transparency)
                img = frame_data['image']
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Convert to numpy array and write to FFmpeg
                frame = np.array(img)
                self.ffmpeg_process.stdin.write(frame.tobytes())
                self.frame_count += 1
                
                self.frame_queue.task_done()
                
            except Exception as e:
                if self.running:  # Only print errors if we're still supposed to be running
                    print(f"Error encoding frame: {e}")
                continue
        
        # Close FFmpeg stdin to signal end of input
        try:
            self.ffmpeg_process.stdin.close()
            self.ffmpeg_process.wait(timeout=10)
        except Exception as e:
            print(f"Error closing FFmpeg: {e}")
    
    def _capture_loop(self):
        """Main capture loop"""
        while self.running:
            try:
                # Capture frame
                img = self._capture_all_displays()
                cursor_pos = self._get_cursor_pos()
                timestamp = time.time()
                
                # Calculate video timestamp (seconds from start)
                video_timestamp = timestamp - self.start_time if self.start_time else 0
                
                # Queue frame for encoding
                frame_queued = False
                try:
                    frame_data = {
                        'image': img,
                        'timestamp': timestamp,
                        'video_timestamp': video_timestamp
                    }
                    self.frame_queue.put_nowait(frame_data)
                    frame_number = self.queued_frame_count
                    self.queued_frame_count += 1
                    frame_queued = True
                except:
                    print(f"Frame queue full, dropping frame at {video_timestamp:.2f}s")
                    frame_number = -1  # Mark as dropped
                
                # Store cursor position with frame number (only if frame was queued)
                if frame_queued:
                    with self.data_lock:
                        self.mouse_positions.append({
                            "frame_number": frame_number,
                            "timestamp": timestamp,
                            "video_timestamp": video_timestamp,
                            "x": cursor_pos["x"],
                            "y": cursor_pos["y"]
                        })
                
                time.sleep(self.capture_interval)
                
            except Exception as e:
                print(f"Error in capture loop: {e}")
                time.sleep(1)
    
    def _write_to_csv(self):
        """Periodically write mouse positions to CSV"""
        while self.running:
            try:
                time.sleep(self.csv_update_interval)
                
                with self.data_lock:
                    if not self.mouse_positions:
                        continue
                    data_to_write = self.mouse_positions.copy()
                    self.mouse_positions.clear()
                
                file_exists = os.path.isfile(self.csv_file_path)
                with open(self.csv_file_path, 'a', newline='') as csvfile:
                    fieldnames = ['frame_number', 'timestamp', 'datetime', 'video_timestamp', 'x', 'y']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    if not file_exists:
                        writer.writeheader()
                    
                    for pos in data_to_write:
                        writer.writerow({
                            'frame_number': pos['frame_number'],
                            'timestamp': pos['timestamp'],
                            'datetime': datetime.fromtimestamp(pos['timestamp']).strftime('%Y-%m-%d %H:%M:%S.%f'),
                            'video_timestamp': pos['video_timestamp'],
                            'x': pos['x'],
                            'y': pos['y']
                        })
                
            except Exception as e:
                print(f"Error writing to CSV: {e}")
                time.sleep(1)
    
    def start(self):
        """Start the screen capture system"""
        self.running = True
        self.start_time = time.time()
        
        # Start video encoder thread
        encoder_thread = threading.Thread(target=self._video_encoder_worker)
        encoder_thread.daemon = True
        encoder_thread.start()
        
        # Start capture thread
        capture_thread = threading.Thread(target=self._capture_loop)
        capture_thread.daemon = True
        capture_thread.start()
        
        # Start CSV writer thread
        csv_thread = threading.Thread(target=self._write_to_csv)
        csv_thread.daemon = True
        csv_thread.start()
        
        print(f"\n{'='*60}")
        print(f"Screen Capture Started (Video Mode)")
        print(f"{'='*60}")
        print(f"Capture rate: {self.fps} FPS")
        print(f"Video quality: {self.video_quality}")
        print(f"Output video: {self.video_file_path}")
        print(f"Output CSV: {self.csv_file_path}")
        print(f"Press Ctrl+C to stop")
        print(f"{'='*60}\n")
        
        try:
            while self.running:
                time.sleep(1)
                # Print status every 10 seconds
                if self.frame_count % (self.fps * 10) == 0 and self.frame_count > 0:
                    duration = time.time() - self.start_time
                    print(f"Captured {self.frame_count} frames ({duration:.1f}s)")
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the screen capture system"""
        print("\nStopping capture...")
        self.running = False
        
        # Wait for frame queue to empty
        print("Waiting for frames to finish encoding...")
        try:
            self.frame_queue.join()
        except Exception as e:
            print(f"Error waiting for frame queue: {e}")
        
        # Send poison pill to encoder
        try:
            self.frame_queue.put(None, timeout=1)
        except:
            pass
        
        # Write remaining CSV data
        with self.data_lock:
            if self.mouse_positions:
                try:
                    file_exists = os.path.isfile(self.csv_file_path)
                    with open(self.csv_file_path, 'a', newline='') as csvfile:
                        fieldnames = ['frame_number', 'timestamp', 'datetime', 'video_timestamp', 'x', 'y']
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        
                        if not file_exists:
                            writer.writeheader()
                        
                        for pos in self.mouse_positions:
                            writer.writerow({
                                'frame_number': pos['frame_number'],
                                'timestamp': pos['timestamp'],
                                'datetime': datetime.fromtimestamp(pos['timestamp']).strftime('%Y-%m-%d %H:%M:%S.%f'),
                                'video_timestamp': pos['video_timestamp'],
                                'x': pos['x'],
                                'y': pos['y']
                            })
                    print(f"Wrote final {len(self.mouse_positions)} entries to CSV")
                except Exception as e:
                    print(f"Error writing final CSV data: {e}")
        
        # Wait for FFmpeg to finish
        print("Waiting for video encoding to complete...")
        if self.ffmpeg_process:
            try:
                self.ffmpeg_process.wait(timeout=15)
                print("Video encoding completed")
            except subprocess.TimeoutExpired:
                print("FFmpeg didn't finish in time, terminating...")
                self.ffmpeg_process.terminate()
                self.ffmpeg_process.wait()
        
        # Close mss
        try:
            self.sct.close()
        except Exception as e:
            print(f"Error closing mss: {e}")
        
        print(f"\n{'='*60}")
        print(f"Screen Capture Stopped")
        print(f"{'='*60}")
        print(f"Total frames captured: {self.frame_count}")
        print(f"Total duration: {time.time() - self.start_time:.1f}s")
        print(f"Video saved to: {self.video_file_path}")
        print(f"CSV saved to: {self.csv_file_path}")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Screen capture with video encoding')
    parser.add_argument('--tag', type=str, default=None, 
                        help='Tag for naming output files (default: timestamp)')
    parser.add_argument('--fps', type=int, default=10, 
                        help='Frames per second (default: 10)')
    parser.add_argument('--quality', type=str, default='low', 
                        choices=['low', 'medium', 'high'],
                        help='Video quality preset (default: low)')
    parser.add_argument('--output-dir', type=str, default='__cursor_data',
                        help='Output directory (default: __cursor_data)')
    args = parser.parse_args()
    
    # Generate timestamp-based tag if none provided
    if args.tag is None:
        args.tag = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create capture instance
    # Quality options: 'low' (fast, larger files), 'medium' (balanced), 'high' (best compression)
    capture = ScreenCaptureVideo(
        capture_interval=1.0/args.fps,  # Calculate interval from FPS
        output_dir=args.output_dir,
        tag=args.tag,
        video_quality=args.quality,
        fps=args.fps
    )
    
    # Handle clean shutdown
    def signal_handler(sig, frame):
        capture.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    capture.start()

