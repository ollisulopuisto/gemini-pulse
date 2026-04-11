# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Calendar Versioning](https://calver.org/) (vYY.MM.DD.N).

## [v26.04.11.7] - 2026-04-11

### Fixed
- **UI Optimization:** Removed redundant "Latest Prompt" from Deep Status section as it is already displayed in the main card.
- **Deep Status Refinement:** Improved "Current Thought" extraction to fallback to the thought's description if a subject is not available.

## [v26.04.11.6] - 2026-04-11

### Fixed
- **Robust Session Parsing:** Replaced brittle string-splitting logic with a balanced brace counter to correctly extract JSON message objects from session files, even when they contain complex shell output or nested braces.

## [v26.04.11.5] - 2026-04-11

### Added
- **HTTPS Support:** Added optional HTTPS support using self-signed certificates.
    - `deploy.sh` now offers to generate certificates during setup.
    - `pulse.py` automatically detects and uses `cert.pem` and `key.pem` if present.
- **Enhanced Deployment Verification:** The `deploy.sh` script now performs a final verification check to ensure the background service is reachable.

### Fixed
- **Deployment Reliability:** 
    - Switched to modern `launchctl bootout` and `launchctl bootstrap` commands for better macOS compatibility.
    - Silenced noisy background job termination messages during deployment.
    - Moved pre-deployment logs to a project-local directory to avoid Seatbelt permission issues.
- **Deep Status Monitoring:** Fully stabilized the real-time agent state monitoring with a robust chunk-based parser.
    - **Latest Prompt:** Shows the last instruction from the user.
    - **Current Thought:** Displays the subject of the agent's current reasoning.
    - **Latest Action:** Shows the description of the active or most recent tool call.
- **General Stability:** Resolved various "Operation not permitted" and "Address already in use" errors through improved process management and unbuffered logging.

## [v26.04.09.3] - 2026-04-09

### Added
- **Deep Status Monitoring:** The dashboard now extracts and displays real-time agent state from `gemini-cli` session files:
    - **Latest Prompt:** Shows the last instruction received from the user.
    - **Current Thought:** Displays the high-level subject of the agent's current reasoning process.
    - **Latest Action:** Shows the description of the most recently completed or active tool call.
- UI Enhancements: Added a dedicated "Deep Status" section to agent cards with specialized styling for improved readability.

## [v26.04.09.2] - 2026-04-09

### Added
- Documentation: Updated README with a detailed description of the `deploy.sh` script, security architecture (salted/hashed passwords), and manual execution options.

## [v26.04.09.1] - 2026-04-09

### Added
- **Zero-Dependency Monitor:** A mobile-friendly dashboard for tracking multiple `gemini-cli` agent processes.
- **Real-time Activity Detection:** 
    - Visual "Busy" state with shimmer animations and status badges.
    - Multi-factor heuristic: CPU usage threshold (>2%), recent log modifications, and recent file changes in the project directory (`find -newermt`).
- **CPU Monitoring:** Real-time CPU usage reporting for every tracked process.
- **Secure Authentication:** 
    - Optional Basic Auth protection.
    - Credentials stored as salted PBKDF2 hashes (SHA-256) in the LaunchAgent's environment variables.
- **Easy Deployment:** `deploy.sh` script for automated macOS LaunchAgent installation, including a secure credential setup prompt.
- **Responsive UI:** Dark-mode, grid-based layout that works perfectly on both mobile and desktop.
