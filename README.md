# Gemini Pulse

A zero-dependency, mobile-friendly dashboard for monitoring `gemini-cli` agents.

## Features

- **Mobile First**: Designed for quick status checks on an iPhone or Android device.
- **Real-Time Busy State**: Visual shimmer and badges indicate if an agent is active (thinking, running tools, or modifying project files).
- **CPU Monitoring**: See real-time CPU usage for every tracked process.
- **Zero Dependencies**: Only uses the Python Standard Library.
- **Auto-Refresh**: Every 3 seconds for a "live" feel.
- **Secure Authentication**: Optional Basic Auth with salted PBKDF2 hashing.
- **Background Service**: Built-in support for running as a macOS LaunchAgent.

## Deployment

The easiest way to install Gemini Pulse on macOS is using the included deployment script:

```bash
./deploy.sh
```

The script will:
1. Detect your local project paths and Python installation.
2. Prompt for optional Basic Authentication credentials.
3. Generate a tailored `.plist` configuration with salted/hashed passwords.
4. Install and start the background service via `launchctl`.

## Authentication (Optional)

If you configure a username and password during deployment, the script will securely hash them using PBKDF2-SHA256. The plain-text password is **never stored** on disk; only the salt and the hash are saved in the LaunchAgent's environment variables.

## Manual Run

```bash
# Run with default settings (port 1337)
python3 pulse.py

# Run with custom port and credentials
PORT=1340 PULSE_USER=admin PULSE_HASH="salt:hash" python3 pulse.py
```

Access the dashboard at `http://localhost:1337` (or your network IP).

## Requirements

- macOS (for `launchctl` support)
- Python 3.9+
- `gemini-cli` (active agents will be detected automatically)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
