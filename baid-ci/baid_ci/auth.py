"""Authentication module for BAID-CI

This module handles Google OAuth authentication and token management.
"""

import json
import os
import time
import webbrowser
import secrets
from urllib.parse import parse_qs, urlparse, quote
import requests
from cryptography.fernet import Fernet

# Constants
BASE_URL = "https://core.baid.dev"
GOOGLE_CLIENT_ID = "742371152853-usfgd7l7ccp3mkekku8ql3iol5m3d7oi.apps.googleusercontent.com"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
REDIRECT_URI = f"{BASE_URL}/api/auth/google-login"
CONFIG_DIR = os.path.expanduser("~/.baid-ci")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


# Encryption key generation (unique per installation)
def get_encryption_key():
    """Get or create encryption key for token storage"""
    key_file = os.path.join(CONFIG_DIR, ".key")
    if not os.path.exists(key_file):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        key = Fernet.generate_key()
        with open(key_file, "wb") as f:
            f.write(key)
        os.chmod(key_file, 0o600)  # Secure permissions
    else:
        with open(key_file, "rb") as f:
            key = f.read()
    return key


class Config:
    """Configuration manager for baid-ci"""

    def __init__(self):
        self.token = None
        self.token_expiry = 0
        self.user_email = None
        self.user_name = None
        self.session_id = None
        self.cipher = Fernet(get_encryption_key())
        self.load()

    def load(self):
        """Load configuration from file"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)

                    # Decrypt token if present
                    if "token" in data and data["token"]:
                        encrypted_token = data["token"].encode()
                        self.token = self.cipher.decrypt(encrypted_token).decode()
                    else:
                        self.token = None

                    self.token_expiry = data.get("token_expiry", 0)
                    self.user_email = data.get("user_email")
                    self.user_name = data.get("user_name")
                    self.session_id = data.get("session_id")
            except Exception as e:
                print(f"Error loading config: {e}")
                self.reset()
        else:
            self.reset()

    def save(self):
        """Save configuration to file"""
        os.makedirs(CONFIG_DIR, exist_ok=True)
        try:
            # Encrypt the token before saving
            encrypted_token = self.cipher.encrypt(self.token.encode()).decode() if self.token else None

            with open(CONFIG_FILE, "w") as f:
                json.dump({
                    "token": encrypted_token,
                    "token_expiry": self.token_expiry,
                    "user_email": self.user_email,
                    "user_name": self.user_name,
                    "session_id": self.session_id
                }, f)

            # Set appropriate permissions
            os.chmod(CONFIG_FILE, 0o600)

        except Exception as e:
            print(f"Error saving config: {e}")

    def reset(self):
        """Reset configuration"""
        self.token = None
        self.token_expiry = 0
        self.user_email = None
        self.user_name = None
        self.session_id = None

        # Remove config file if it exists
        if os.path.exists(CONFIG_FILE):
            try:
                os.remove(CONFIG_FILE)
            except:
                pass


def build_auth_url(state):
    """Build the Google OAuth URL with BAID.dev as the redirect URI"""
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent"
    }

    query_string = "&".join([f"{k}={quote(v)}" for k, v in params.items()])
    return f"{GOOGLE_AUTH_URL}?{query_string}"


def poll_for_session(state, max_attempts=60):
    """Poll the session endpoint to get the token after successful authentication"""
    print(f"Polling for session with state: {state}")
    print(f"Session polling URL: {BASE_URL}/api/auth/session?state={state}")
    print("Waiting for you to complete the authentication in your browser...")
    print("You can close the browser tab once you see the success message.")

    delay_seconds = 2

    for attempt in range(max_attempts):
        try:
            print(f"Poll attempt {attempt + 1}/{max_attempts}...", end="\r")
            session_url = f"{BASE_URL}/api/auth/session?state={state}"

            response = requests.get(
                session_url,
                timeout=10
            )

            if response.status_code != 200:
                time.sleep(delay_seconds)
                continue

            try:
                session_data = response.json()

                # Check for error
                if "error" in session_data and session_data["error"]:
                    time.sleep(delay_seconds)
                    continue

                # Check if we have the access token
                if "access_token" in session_data:
                    print("\nSuccessfully retrieved access token!")
                    return {
                        "token": session_data.get("access_token"),
                        "expires_in": session_data.get("expires_in", 28800),
                        "user_email": session_data.get("email"),
                        "user_name": session_data.get("name")
                    }
                else:
                    # No access token yet
                    pass
            except ValueError:
                # Not JSON or invalid JSON
                pass

        except Exception as e:
            print(f"\nError during polling: {e}")

        # Wait before next attempt
        time.sleep(delay_seconds)

    print("\nPolling for session timed out after 2 minutes")
    return None


def authenticate_with_google():
    """Complete Google OAuth flow and exchange code with BAID.dev"""
    # Generate a state parameter for CSRF protection
    state = secrets.token_hex(16)

    print(f"Starting OAuth flow with state: {state}")

    try:
        # Build and open the Google OAuth URL
        auth_url = build_auth_url(state)
        print(f"Opening browser for Google authentication...")
        webbrowser.open(auth_url)

        # Now we just poll for the session token
        print("Browser opened. Please complete the authentication process.")
        token_info = poll_for_session(state)

        if not token_info:
            print("Failed to retrieve authentication token.")
            return None

        print(f"Successfully authenticated as {token_info.get('user_email', 'unknown')}")
        return token_info

    except Exception as e:
        print(f"Authentication error: {e}")
        return None


def ensure_authenticated(config):
    """Ensure user is authenticated, refresh token if needed"""
    # Check if token exists and is valid
    if not config.token or time.time() >= config.token_expiry:
        # Token is missing or expired, need to authenticate
        auth_result = authenticate_with_google()
        if auth_result:
            config.token = auth_result["token"]
            config.token_expiry = time.time() + auth_result["expires_in"]
            config.user_email = auth_result["user_email"]
            config.user_name = auth_result["user_name"]
            config.save()
            return True
        return False
    return True