# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Calendar Versioning](https://calver.org/) (vYY.MM.DD.N).

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
