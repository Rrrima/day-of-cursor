import time
import csv
import os
from datetime import datetime
from queue import Queue
import threading
from PIL import Image, ImageDraw
import Quartz
import mss
from Cocoa import NSEvent


class ScreenCapture:
    def __init__(self, capture_interval=0.1, screenshot_dir="__cursor_data_debug_display", tag="", draw_cursor=False):
        """
        Initialize screen capture system
        
        Args:
            capture_interval: Time between captures in seconds (default: 0.1 = 10 FPS)
            screenshot_dir: Directory to save screenshots and CSV
            draw_cursor: Whether to draw a visual marker at cursor position (default: False)
        """
        self.capture_interval = capture_interval
        self.screenshot_dir = screenshot_dir
        self.draw_cursor = draw_cursor
        self.running = False
        self.tag = tag
        
        # Create screenshot directory if it doesn't exist
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)
            print(f"Created screenshot directory: {self.screenshot_dir}")
        
        # Screenshot queue for asynchronous I/O
        self.screenshot_queue = Queue(maxsize=1000)
        self.num_screenshot_workers = 3
        
        # CSV logging
        self.mouse_positions = []
        self.csv_file_path = os.path.join(self.screenshot_dir, f"mouse_positions_{self.tag}.csv")
        self.csv_update_interval = 0.5  # Write to CSV every 0.5 seconds
        self.data_lock = threading.Lock()
        
        # Last cursor position for change detection
        self.last_cursor_pos = None
        
        # Initialize mss and get monitor info
        self.sct = mss.mss()
        self._update_screen_info()
    
    def _get_global_bounds(self):
        """Return a bounding box enclosing all physical displays (Quartz coordinates)"""
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
        # Get all monitors (index 0 is the combined virtual screen)
        monitors = self.sct.monitors
        
        print(f"Detected {len(monitors) - 1} monitor(s)")
        
        # Monitor 0 is the combined virtual screen
        self.combined_monitor = monitors[0]
        print(f"Combined screen area: {self.combined_monitor['width']}x{self.combined_monitor['height']}")
        print(f"  Offset: left={self.combined_monitor['left']}, top={self.combined_monitor['top']}")
        
        # Print individual monitors
        for i in range(1, len(monitors)):
            mon = monitors[i]
            print(f"  Monitor {i}: {mon['width']}x{mon['height']} at ({mon['left']}, {mon['top']})")
        
        # Get global bounds for Y-coordinate conversion  
        self.min_x, self.min_y, self.max_x, self.gmax_y = self._get_global_bounds()
        print(f"  Quartz global bounds: min_x={self.min_x}, min_y={self.min_y}, max_x={self.max_x}, max_y={self.gmax_y}")
        print(f"  Total Quartz space: {self.max_x - self.min_x} x {self.gmax_y - self.min_y}")
    
    def _draw_rounded_rectangle(self, draw, bounds, radius, outline_color, width):
        """Draw a rounded rectangle"""
        x0, y0, x1, y1 = bounds
        
        # Draw the four corners as arcs
        draw.arc([x0, y0, x0 + radius * 2, y0 + radius * 2], 180, 270, fill=outline_color, width=width)
        draw.arc([x1 - radius * 2, y0, x1, y0 + radius * 2], 270, 360, fill=outline_color, width=width)
        draw.arc([x0, y1 - radius * 2, x0 + radius * 2, y1], 90, 180, fill=outline_color, width=width)
        draw.arc([x1 - radius * 2, y1 - radius * 2, x1, y1], 0, 90, fill=outline_color, width=width)
        
        # Draw the four sides
        draw.line([x0 + radius, y0, x1 - radius, y0], fill=outline_color, width=width)  # top
        draw.line([x0 + radius, y1, x1 - radius, y1], fill=outline_color, width=width)  # bottom
        draw.line([x0, y0 + radius, x0, y1 - radius], fill=outline_color, width=width)  # left
        draw.line([x1, y0 + radius, x1, y1 - radius], fill=outline_color, width=width)  # right

    def _capture_all_displays(self):
        """Capture all displays using mss"""
        # Monitor 0 captures all displays combined
        screenshot = self.sct.grab(self.combined_monitor)
        
        # Convert mss screenshot to PIL Image with alpha channel
        img = Image.frombytes("RGB", (screenshot.width, screenshot.height), screenshot.rgb)
        img = img.convert("RGBA")
        
        # Create a mask for actual display areas
        # Start with fully transparent image
        mask = Image.new("L", (img.width, img.height), 0)
        mask_draw = ImageDraw.Draw(mask)
        
        # Get all individual monitors (skip index 0 which is the combined screen)
        monitors = self.sct.monitors
        monitor_bounds = []
        
        for i in range(1, len(monitors)):
            mon = monitors[i]
            # Calculate position relative to combined monitor
            x = mon['left'] - self.combined_monitor['left']
            y = mon['top'] - self.combined_monitor['top']
            # Draw white rectangle for this display area
            mask_draw.rectangle(
                [x, y, x + mon['width'], y + mon['height']],
                fill=255
            )
            # Store bounds for later drawing
            monitor_bounds.append((x, y, x + mon['width'], y + mon['height']))
        
        # Apply mask to make non-display areas transparent
        img.putalpha(mask)
        
        # Draw minimalist rounded borders around each display (Apple aesthetic)
        draw = ImageDraw.Draw(img, 'RGBA')
        
        border_radius = 12  # Rounded corner radius
        shadow_offset = 3
        
        for bounds in monitor_bounds:
            x0, y0, x1, y1 = bounds
            
            # Draw subtle shadow (multiple layers for blur effect)
            # shadow_color = (0, 0, 0, 15)  # Very subtle black shadow
            # for offset in range(shadow_offset, 0, -1):
            #     shadow_bounds = (
            #         x0 + offset,
            #         y0 + offset,
            #         x1 + offset,
            #         y1 + offset
            #     )
            #     self._draw_rounded_rectangle(
            #         draw,
            #         shadow_bounds,
            #         border_radius,
            #         shadow_color,
            #         10
            #     )
            
            # Draw main border (light gray, Apple-style)
            border_color = (255, 255, 255)  # Light gray with slight transparency
            self._draw_rounded_rectangle(
                draw,
                bounds,
                border_radius,
                border_color,
                10
            )
        
        return img
    
    def _get_cursor_pos(self):
        """Get current cursor position relative to the captured screenshot"""
        # Get cursor position using Quartz CGEvent (bottom-left origin)
        event = Quartz.CGEventCreate(None)
        cursor_location = Quartz.CGEventGetLocation(event)
        
        cg_x = cursor_location.x
        cg_y = cursor_location.y

        # print(f"Cursor position: x={cg_x}, y={cg_y}")
        
        
        # Adjust for mss combined monitor offset
        # The mss screenshot starts at (combined_monitor['left'], combined_monitor['top'])
        img_x = cg_x - self.combined_monitor['left']
        img_y = cg_y - self.combined_monitor['top']

        print(f"Cursor position: x={img_x}, y={img_y}")

        
        return {"x": img_x, "y": img_y}
    
    def _process_screenshot(self, screenshot_data):
        """Process and save a screenshot (runs in worker thread)"""
        try:
            timestamp = screenshot_data['timestamp']
            cursor_x = screenshot_data['cursor_x']
            cursor_y = screenshot_data['cursor_y']
            screenshot = screenshot_data['screenshot']
            
            original_width = screenshot.width
            original_height = screenshot.height
            
            # Draw cursor marker on original size screenshot if enabled
            if self.draw_cursor:
                draw = ImageDraw.Draw(screenshot)
                marker_size = 20
                # Draw a red circle with crosshair at cursor position
                draw.ellipse(
                    [cursor_x - marker_size, cursor_y - marker_size, 
                     cursor_x + marker_size, cursor_y + marker_size],
                    outline='red', width=3
                )
                # Draw crosshair
                draw.line([cursor_x - marker_size - 10, cursor_y, 
                          cursor_x + marker_size + 10, cursor_y], 
                          fill='red', width=2)
                draw.line([cursor_x, cursor_y - marker_size - 10, 
                          cursor_x, cursor_y + marker_size + 10], 
                          fill='red', width=2)
            
            # Resize to 50% of original size for storage efficiency
            new_size = (original_width // 2, original_height // 2)
            screenshot = screenshot.resize(new_size)
            
            # Create filename using timestamp
            filename = f"{timestamp}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            
            # Save screenshot
            screenshot.save(filepath)
            return filepath
        except Exception as e:
            print(f"Error processing screenshot: {e}")
            return None
    
    def _screenshot_worker(self):
        """Worker thread that processes screenshots from the queue"""
        while self.running:
            try:
                screenshot_data = self.screenshot_queue.get(timeout=1)
                self._process_screenshot(screenshot_data)
                self.screenshot_queue.task_done()
            except:
                continue
    
    def _capture_screenshot_async(self, timestamp, cursor_x, cursor_y):
        """Capture screenshot and queue it for async processing"""
        try:
            # Capture all displays (fast, in-memory operation)
            screenshot = self._capture_all_displays()
            
            # Queue the screenshot for processing by worker thread
            screenshot_data = {
                'timestamp': timestamp,
                'cursor_x': cursor_x,
                'cursor_y': cursor_y,
                'screenshot': screenshot
            }
            
            # Non-blocking put (skip if queue is full)
            try:
                self.screenshot_queue.put_nowait(screenshot_data)
                filepath = os.path.join(self.screenshot_dir, f"{timestamp}.png")
                return filepath
            except:
                print(f"Screenshot queue full, skipping frame {timestamp}")
                return None
                
        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            return None

    def _track_and_capture(self):
        """Continuously track cursor position and capture screenshots"""
        while self.running:
            try:
                # Get cursor position and timestamp together
                cursor_pos = self._get_cursor_pos()
                timestamp = time.time()
                
                # Capture screenshot asynchronously
                screenshot_path = self._capture_screenshot_async(
                    timestamp, 
                    cursor_pos["x"], 
                    cursor_pos["y"]
                )
                
                # Store position in buffer
                with self.data_lock:
                    self.mouse_positions.append({
                        "timestamp": timestamp,
                        "x": cursor_pos["x"],
                        "y": cursor_pos["y"],
                        "screenshot": screenshot_path if screenshot_path else ""
                    })
                
                self.last_cursor_pos = cursor_pos
                time.sleep(self.capture_interval)
                
            except Exception as e:
                print(f"Error tracking cursor: {e}")
                time.sleep(1)

    def _write_to_csv(self):
        """Periodically write mouse positions to CSV file"""
        while self.running:
            try:
                time.sleep(self.csv_update_interval)
                
                # Get data from buffer
                with self.data_lock:
                    if not self.mouse_positions:
                        continue
                    data_to_write = self.mouse_positions.copy()
                    self.mouse_positions.clear()
                
                # Write to CSV file
                file_exists = os.path.isfile(self.csv_file_path)
                with open(self.csv_file_path, 'a', newline='') as csvfile:
                    fieldnames = ['timestamp', 'datetime', 'x', 'y', 'screenshot']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    # Write header if file is new
                    if not file_exists:
                        writer.writeheader()
                    
                    # Write all buffered positions
                    for pos in data_to_write:
                        writer.writerow({
                            'timestamp': pos['timestamp'],
                            'datetime': datetime.fromtimestamp(pos['timestamp']).strftime('%Y-%m-%d %H:%M:%S.%f'),
                            'x': pos['x'],
                            'y': pos['y'],
                            'screenshot': pos.get('screenshot', '')
                        })
                
                # print(f"Wrote {len(data_to_write)} entries to {self.csv_file_path}")
                
            except Exception as e:
                print(f"Error writing to CSV: {e}")
                time.sleep(1)

    def start(self):
        """Start the screen capture system"""
        self.running = True
        
        # Start screenshot worker threads
        for i in range(self.num_screenshot_workers):
            worker_thread = threading.Thread(
                target=self._screenshot_worker, 
                name=f"ScreenshotWorker-{i}"
            )
            worker_thread.daemon = True
            worker_thread.start()

        # Start cursor position tracking and screenshot capture thread
        capture_thread = threading.Thread(target=self._track_and_capture)
        capture_thread.daemon = True
        capture_thread.start()

        # Start CSV writing thread
        csv_thread = threading.Thread(target=self._write_to_csv)
        csv_thread.daemon = True
        csv_thread.start()
        
        print(f"Screen capture started")
        print(f"Capture rate: ~{int(1/self.capture_interval)} FPS")
        print(f"Screenshot workers: {self.num_screenshot_workers} threads")
        print(f"CSV write interval: {self.csv_update_interval} seconds")
        print(f"Draw cursor marker: {self.draw_cursor}")
        print(f"Output directory: {self.screenshot_dir}")
        print(f"Data saved to: {self.csv_file_path}")
        print("Press Ctrl+C to exit")
        
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop the screen capture system"""
        self.running = False
        
        # Wait for screenshot queue to finish processing
        print("\nStopping... waiting for screenshot queue to finish...")
        try:
            self.screenshot_queue.join()
            print(f"Screenshot queue processed successfully")
        except Exception as e:
            print(f"Error waiting for screenshot queue: {e}")
        
        # Write any remaining data to CSV
        with self.data_lock:
            if self.mouse_positions:
                try:
                    file_exists = os.path.isfile(self.csv_file_path)
                    with open(self.csv_file_path, 'a', newline='') as csvfile:
                        fieldnames = ['timestamp', 'datetime', 'x', 'y', 'screenshot']
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        
                        if not file_exists:
                            writer.writeheader()
                        
                        for pos in self.mouse_positions:
                            writer.writerow({
                                'timestamp': pos['timestamp'],
                                'datetime': datetime.fromtimestamp(pos['timestamp']).strftime('%Y-%m-%d %H:%M:%S.%f'),
                                'x': pos['x'],
                                'y': pos['y'],
                                'screenshot': pos.get('screenshot', '')
                            })
                    print(f"Wrote final {len(self.mouse_positions)} entries to {self.csv_file_path}")
                except Exception as e:
                    print(f"Error writing final data to CSV: {e}")
        
        # Close mss instance
        try:
            self.sct.close()
        except Exception as e:
            print(f"Error closing mss: {e}")
        
        print("Screen capture stopped")


if __name__ == "__main__":
    # Create capture instance with 10 FPS (0.1 second interval)
    # Adjust capture_interval for different frame rates:
    # - 0.1 = 10 FPS
    # - 0.05 = 20 FPS
    # - 0.033 = ~30 FPS
    # Set draw_cursor=True to draw a red marker at cursor position (useful for debugging)
    capture = ScreenCapture(
        capture_interval=0.1, 
        screenshot_dir="__cursor_data",
        tag="Literature_infospace",
        # draw_cursor=True  # Set to True to visualize cursor position on screenshots
    )
    capture.start()

