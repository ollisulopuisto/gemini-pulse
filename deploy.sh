#!/bin/bash

# Gemini Pulse Deployment Script
# 
# This script automates the installation and configuration of the Gemini Pulse
# LaunchAgent on macOS with optional Basic Authentication support.

set -e

# Configuration
PROJECT_PATH=$(pwd)
HOME_DIR=$HOME
PLIST_NAME="com.dst.gemini-pulse.plist"
PLIST_NAME_STR="com.dst.gemini-pulse"
TARGET_PLIST="$HOME/Library/LaunchAgents/$PLIST_NAME"
PYTHON_PATH=$(which python3)

echo "🚀 Deploying Gemini Pulse from $PROJECT_PATH"

# Check for Auth Configuration
if [[ -z "$PULSE_USER" || -z "$PULSE_HASH" ]]; then
    echo "🔐 Security Setup (Optional)"
    echo "If you want to protect your dashboard with Basic Auth, enter credentials below."
    echo "Leave blank to skip authentication."
    read -p "Username: " USER_INPUT
    read -s -p "Password: " PASS_INPUT
    echo ""
    
    if [[ -n "$USER_INPUT" && -n "$PASS_INPUT" ]]; then
        export PULSE_USER="$USER_INPUT"
        # Generate salted PBKDF2 hash using Python (zero dependency)
        export PULSE_HASH=$(python3 -c "import hashlib, os, base64; salt=os.urandom(16); hash=hashlib.pbkdf2_hmac('sha256', '$PASS_INPUT'.encode(), salt, 100000); print(f'{base64.b64encode(salt).decode()}:{base64.b64encode(hash).decode()}')")
    fi
fi

ENV_VARS_BLOCK=""
if [[ -n "$PULSE_USER" && -n "$PULSE_HASH" ]]; then
    echo "✅ Authentication will be enabled (Salted PBKDF2)."
    ENV_VARS_BLOCK="    <key>EnvironmentVariables</key>
    <dict>
        <key>PULSE_USER</key>
        <string>$PULSE_USER</string>
        <key>PULSE_HASH</key>
        <string>$PULSE_HASH</string>
    </dict>"
else
    echo "⚠️  No authentication configured. Dashboard will be public on your local network."
fi

# 1. Generate the actual .plist from the template
echo "📝 Generating $PLIST_NAME..."
# Using a temporary file for sed to handle multiline block correctly
cat gemini-pulse.plist.example | \
    sed -e "s|{{PROJECT_PATH}}|$PROJECT_PATH|g" \
        -e "s|{{HOME_DIR}}|$HOME_DIR|g" \
        -e "s|com.user.gemini-pulse|$PLIST_NAME_STR|g" \
        -e "s|/usr/bin/python3|$PYTHON_PATH|g" > "$PLIST_NAME"

# Insert environment variables if configured
if [[ -n "$ENV_VARS_BLOCK" ]]; then
    # Insert before the last </dict>
    sed -i '' -e "/{{ENV_VARS}}/{
        r /dev/stdin
        d
    }" "$PLIST_NAME" <<< "$ENV_VARS_BLOCK"
else
    sed -i '' -e "s|{{ENV_VARS}}||g" "$PLIST_NAME"
fi

# 2. Copy to LaunchAgents
echo "📂 Installing to ~/Library/LaunchAgents/..."
cp "$PLIST_NAME" "$TARGET_PLIST"

# 3. Load the service
echo "🔄 Restarting service..."
launchctl unload "$TARGET_PLIST" 2>/dev/null || true
launchctl load "$TARGET_PLIST"

echo "✅ Done! Gemini Pulse is now running in the background."
echo "🔗 Access it at: http://localhost:1337 (or your network IP)"
