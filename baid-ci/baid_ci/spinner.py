"""Spinner implementation for visual feedback"""

import sys
import time
import threading


class Spinner:
    """A simple spinner for providing visual feedback during long operations"""

    def __init__(self, message=""):
        """Initialize spinner with optional message prefix"""
        self.message = message
        self.spinning = False
        self.spinner_chars = "|/-\\"
        self.current = 0
        self.thread = None

    def spin(self):
        """Animation loop for spinner - runs in a separate thread"""
        while self.spinning:
            sys.stdout.write(f"\r{self.message}{self.spinner_chars[self.current]} ")
            sys.stdout.flush()
            self.current = (self.current + 1) % len(self.spinner_chars)
            time.sleep(0.1)
        # Clear the spinner line when done
        sys.stdout.write(f"\r{' ' * (len(self.message) + 2)}\r")
        sys.stdout.flush()

    def start(self):
        """Start the spinner in a background thread"""
        self.spinning = True
        self.thread = threading.Thread(target=self.spin)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """Stop the spinner"""
        self.spinning = False
        if self.thread:
            self.thread.join()