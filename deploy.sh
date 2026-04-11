#!/bin/bash

# Gemini Pulse Deployment Script
set -e

# Configuration
PROJECT_PATH=$(pwd)
HOME_DIR=$HOME
PLIST_NAME="com.dst.gemini-pulse.plist"
PLIST_NAME_STR="com.dst.gemini-pulse"
TARGET_PLIST="$HOME/Library/LaunchAgents/$PLIST_NAME"
PYTHON_PATH=$(which python3)

echo "🚀 Deploying Gemini Pulse from $PROJECT_PATH"

# 0. SSL Setup (Optional)
if [[ ! -f "cert.pem" || ! -f "key.pem" ]]; then
    echo "🔒 HTTPS Setup (Optional)"
    echo "Generate self-signed SSL certificate for HTTPS? (y/N): "
    read SSL_INPUT
    if [[ "$SSL_INPUT" =~ ^[Yy]$ ]]; then
        echo "📝 Generating self-signed certificate..."
        openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes -subj "/CN=localhost"
        echo "✅ Certificates generated."
    fi
fi

PROTOCOL="http"
CURL_OPTS="-s -I"
if [[ -f "cert.pem" && -f "key.pem" ]]; then
    PROTOCOL="https"
    CURL_OPTS="$CURL_OPTS -k"
fi

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
        export PULSE_HASH=$(echo -n "$PASS_INPUT" | python3 -c "import hashlib, os, base64, sys; salt=os.urandom(16); pwd=sys.stdin.read().encode(); hash=hashlib.pbkdf2_hmac('sha256', pwd, salt, 100000); print(f'{base64.b64encode(salt).decode()}:{base64.b64encode(hash).decode()}')")
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
sed -e "s|{{PROJECT_PATH}}|$PROJECT_PATH|g" \
    -e "s|{{HOME_DIR}}|$HOME_DIR|g" \
    -e "s|{{PLIST_NAME_STR}}|$PLIST_NAME_STR|g" \
    -e "s|{{PYTHON_PATH}}|$PYTHON_PATH|g" \
    -e "s|{{PULSE_PY_PATH}}|$PROJECT_PATH/pulse.py|g" \
    gemini-pulse.plist.example > "$PLIST_NAME"

# Insert environment variables if configured
if [[ -n "$ENV_VARS_BLOCK" ]]; then
    sed -i '' -e "/{{ENV_VARS}}/{
        r /dev/stdin
        d
    }" "$PLIST_NAME" <<< "$ENV_VARS_BLOCK"
else
    sed -i '' -e "s|{{ENV_VARS}}||g" "$PLIST_NAME"
fi

# 2. Manual Test Phase
echo "🔍 Running pre-deployment test..."
# Kill any existing pulse.py processes first
pkill -9 -f pulse.py || true
sleep 1

# Start pulse.py in background for testing
# We use the same env vars that will be in the plist
export PULSE_USER
export PULSE_HASH
$PYTHON_PATH -u "$PROJECT_PATH/pulse.py" > "$HOME_DIR/.gemini/tmp/pulse_test.log" 2>&1 &
PULSE_PID=$!

echo "⏳ Waiting for server to start..."
MAX_RETRIES=5
COUNT=0
SUCCESS=false

while [ $COUNT -lt $MAX_RETRIES ]; do
    if curl $CURL_OPTS "$PROTOCOL://localhost:1337/" > /dev/null; then
        SUCCESS=true
        break
    fi
    echo "..."
    sleep 2
    COUNT=$((COUNT+1))
done

# Kill the test process
kill $PULSE_PID 2>/dev/null || true
wait $PULSE_PID 2>/dev/null || true

if [ "$SUCCESS" = false ]; then
    echo "❌ Pre-deployment test failed! Server did not respond on $PROTOCOL://localhost:1337"
    echo "Check $HOME_DIR/.gemini/tmp/pulse_test.log for details."    exit 1
fi

echo "✅ Pre-deployment test passed!"

# 3. Copy to LaunchAgents
echo "📂 Installing to ~/Library/LaunchAgents/..."
cp "$PLIST_NAME" "$TARGET_PLIST"

# 4. Load the service
echo "🔄 Starting background service..."
# On macOS, try to bootout/bootstrap for better reliability
launchctl bootout gui/$(id -u) "$TARGET_PLIST" 2>/dev/null || true
# Final cleanup just in case
pkill -9 -f pulse.py || true
sleep 1
launchctl bootstrap gui/$(id -u) "$TARGET_PLIST" || launchctl load -w "$TARGET_PLIST"
echo "✅ Done! Gemini Pulse is now running in the background."
echo "🔗 Access it at: $PROTOCOL://localhost:1337 (or your network IP)"

# 5. Final Verification
echo "🔍 Verifying background service..."
sleep 3
if curl $CURL_OPTS "$PROTOCOL://localhost:1337/" > /dev/null; then
    echo "✅ Service is reachable!"
else
    echo "⚠️  Service is not responding yet. It might take a few more seconds."
    echo "   Check logs: tail -f $HOME_DIR/.gemini/tmp/gemini-pulse.err"
fi

