import rumps
import subprocess
import threading
import webbrowser
import os
import signal
import sys
from datetime import datetime
from AppKit import (
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSImage,
    NSColor,
    NSImageSymbolConfiguration,
)
from capture_server_video import (
    create_capture_session,
    DEFAULT_FPS,
    DEFAULT_QUALITY,
    DEFAULT_OUTPUT_DIR,
)

class DayOfCursorApp(rumps.App):
    def __init__(self):
        super(DayOfCursorApp, self).__init__("DayOfCursor", title="", quit_button=None)
        
        self.menu = [
            rumps.MenuItem("Start Recording", callback=self.toggle_recording),
            rumps.MenuItem("View Sessions", callback=self.view_sessions),
            None,  # Separator
            rumps.MenuItem("Quit", callback=self.clean_quit),
        ]
        
        self.capture = None
        self.is_recording = False
        self.webpack_process = None
        
        # Set the initial idle icon (White Circle) using a timer
        # to ensure the app is fully initialized before we touch native components
        rumps.Timer(self.initialize_ui, 0.1).start()
        
        # Start the web app automatically on launch
        self.start_web_app()

    def initialize_ui(self, timer):
        """Ensure the initial native icon is set once the status item is ready."""
        if self.set_status_icon():
            timer.stop()

    def set_status_icon(self, color=None):
        """Set the menu bar icon using the SF Symbols circle."""
        try:
            nsapp = getattr(self, "_nsapp", None)
            status_item = getattr(nsapp, "nsstatusitem", None) if nsapp else None
            if status_item is None:
                return False

            image = NSImage.imageWithSystemSymbolName_accessibilityDescription_("circle.fill", None)
            if image is None:
                return False

            desired_color = color or NSColor.labelColor()
            config = NSImageSymbolConfiguration.configurationWithHierarchicalColor_(desired_color)
            colored_image = image.imageWithSymbolConfiguration_(config)

            button = status_item.button()
            button.setImage_(colored_image)
            button.setTitle_("")
            self.title = None
            return True
        except Exception as e:
            print(f"Failed to set status icon: {e}")
            return False

    def start_web_app(self):
        """Starts the webpack dev server in the background as a process group."""
        print("Starting Webpack dev server...")
        try:
            # Using os.setsid to create a new process group so we can kill it all later
            self.webpack_process = subprocess.Popen(
                ["npm", "run", "dev"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            print(f"Webpack server started with PID {self.webpack_process.pid}")
        except Exception as e:
            rumps.alert("Error", f"Failed to start web server: {e}")

    def toggle_recording(self, sender):
        if not self.is_recording:
            # Start Recording
            tag = None
            default_tag = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            while True:
                response = rumps.Window(
                    message="Enter a tag name for this session:",
                    title="Start Recording",
                    default_text=default_tag,
                    ok="Start",
                    cancel="Cancel"
                ).run()
                
                if not response.clicked:
                    return  # User cancelled
                
                tag = response.text.strip()
                if not tag:
                    rumps.alert("Error", "Tag name cannot be empty.")
                    continue  # reprompt
                break  # Valid tag found
            
            # Create capture session via shared helper (handles tag collisions)
            self.capture = create_capture_session(
                tag=tag,
                fps=DEFAULT_FPS,
                quality=DEFAULT_QUALITY,
                output_dir=DEFAULT_OUTPUT_DIR,
            )
            final_tag = getattr(self.capture, "tag", tag)
            
            # Run the capture in a separate thread so it doesn't freeze the menu bar UI
            self.recording_thread = threading.Thread(
                target=self.capture.start,
                daemon=True,
            )
            self.recording_thread.start()
            
            self.is_recording = True
            # Update to purple circle for recording mode
            self.set_status_icon(NSColor.systemPurpleColor())
            sender.title = "Stop Recording"
            rumps.notification("Day of Cursor", "Recording Started", f"Session: {final_tag}")
        else:
            # Stop Recording
            if self.capture:
                self.capture.stop()
                self.capture = None
            
            self.is_recording = False
            # Switch back to plain circle for idle mode
            self.set_status_icon()
            sender.title = "Start Recording"
            rumps.notification("Day of Cursor", "Recording Saved", "Your session has been saved to __cursor_data.")

    def view_sessions(self, _):
        """Opens the session viewer in the default web browser."""
        # The port 3001 is hardcoded in webpack.config.js
        webbrowser.open("http://localhost:3001")

    def clean_quit(self, _):
        """Ensures all child processes and recording threads are cleaned up on exit."""
        print("\nQuitting and cleaning up...")
        
        # Stop recording if active
        if self.is_recording and self.capture:
            self.capture.stop()
            
        # Kill the webpack process group
        if self.webpack_process:
            try:
                # Send SIGTERM to the entire process group
                os.killpg(os.getpgid(self.webpack_process.pid), signal.SIGTERM)
                print("Webpack server stopped.")
            except ProcessLookupError:
                # Process already exited; treat as success
                print("Webpack server already stopped.")
            except Exception as e:
                print(f"Unexpected issue stopping webpack server: {e}")
                
        rumps.quit_application()

if __name__ == "__main__":
    # Hide Dock icon by setting activation policy to accessory
    ns_app = NSApplication.sharedApplication()
    ns_app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    
    # Ensure we are in the project root
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    app = DayOfCursorApp()
    app.run()

