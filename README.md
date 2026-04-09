# Gemini Pulse

A zero-dependency, mobile-friendly dashboard for monitoring `gemini-cli` agents.

## Features

- **Mobile First**: Designed for quick status checks on an iPhone or Android device.
- **Zero Dependencies**: Only uses the Python Standard Library.
- **Auto-Refresh**: Every 5 seconds.
- **Relative Timestamps**: Displays how long ago an agent was active (e.g., "15s ago").
- **Background Support**: Can run as a macOS LaunchAgent.

## Setup

1. Clone this repository.
2. Edit `com.dst.gemini-pulse.plist.example` (renaming it as needed) and replace `{{PROJECT_PATH}}` and `{{HOME_DIR}}` with your local paths.
3. Link or copy the `.plist` file to `~/Library/LaunchAgents/`.
4. Run `launchctl load ~/Library/LaunchAgents/com.dst.gemini-pulse.plist` to start the background service.

## Manual Run

```bash
python3 pulse.py
```

Access the dashboard at `http://<your-ip>:1337`
