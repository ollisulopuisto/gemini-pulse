#!/usr/bin/env python3
"""
Gemini Pulse - A zero-dependency mobile-friendly monitor for gemini-cli.
Version: v26.04.11.8
License: GNU General Public License v3


Features:
- Responsive Grid Layout (Mobile/Desktop).
- Deduplication of processes by Project CWD.
...
- "Busy" state detection based on log heuristics and file modification time.
"""
import http.server
import socketserver
import subprocess
import json
import re
import os
import datetime
import time
import base64
import hashlib
import hmac
import sys
import ssl
from pathlib import Path

# --- BOOTSTRAP ---
print("--- Pulse Process Starting ---", flush=True)

# --- CONFIGURATION ---
PORT = 1337
GEMINI_TMP_ROOT = Path(os.path.expanduser("~/.gemini/tmp"))

# Authentication (optional)
AUTH_USER = os.getenv("PULSE_USER")
AUTH_HASH = os.getenv("PULSE_HASH") # Format: salt:hash (base64)

# SSL (optional, for HTTPS)
CERT_FILE = Path(__file__).parent / "cert.pem"
KEY_FILE = Path(__file__).parent / "key.pem"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>Gemini Pulse</title>
    <style>
        :root {
            --bg: #0d1117;
            --card-bg: #161b22;
            --border: #30363d;
            --text: #c9d1d9;
            --text-muted: #8b949e;
            --blue: #58a6ff;
            --green: #3fb950;
            --red: #f85149;
            --purple: #d2a8ff;
            --orange: #d29922;
        }
        body {
            background-color: var(--bg);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            color: var(--text);
            margin: 0;
            padding: 0;
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
        }
        nav {
            background-color: rgba(22, 27, 34, 0.8);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            padding: 1rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        .container { 
            padding: 1rem; 
            max-width: 1400px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 1.25rem;
        }
        @media (max-width: 400px) {
            .container { grid-template-columns: 1fr; }
        }
        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.25rem;
            box-shadow: 0 8px 24px rgba(0,0,0,0.2);
            transition: transform 0.2s ease;
            display: flex;
            flex-direction: column;
            position: relative;
            overflow: hidden;
        }
        .busy-indicator {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--blue), var(--purple), var(--blue));
            background-size: 200% 100%;
            animation: shimmer 2s infinite linear;
            display: none;
        }
        .deep-status {
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px dashed var(--border);
            font-size: 0.85rem;
        }
        .deep-row {
            margin-bottom: 0.5rem;
        }
        .deep-label {
            color: var(--text-muted);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.7rem;
            letter-spacing: 0.05em;
            margin-bottom: 0.2rem;
        }
        .deep-content {
            color: var(--text);
            line-height: 1.4;
        }
        .thought-subject {
            color: var(--purple);
            font-weight: 600;
        }
        .action-desc {
            color: var(--blue);
        }
        .is-busy .busy-indicator { display: block; }
        @keyframes shimmer {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }

        .title-row {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 0.5rem;
        }
        .project-name {
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--blue);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .status-badge {
            font-size: 0.65rem;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 800;
            text-transform: uppercase;
        }
        .status-busy { background: var(--orange); color: #000; }
        .status-idle { background: var(--border); color: var(--text-muted); }

        .cwd {
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-bottom: 1rem;
            word-break: break-all;
            opacity: 0.8;
        }
        .msg-box {
            background-color: var(--bg);
            border-radius: 12px;
            padding: 1rem;
            font-size: 0.95rem;
            line-height: 1.5;
            white-space: pre-wrap;
            max-height: 250px;
            overflow-y: auto;
            border: 1px solid var(--border);
            font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace;
        }
        .meta-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 1rem;
        }
        .badge {
            font-size: 0.7rem;
            padding: 3px 8px;
            border-radius: 6px;
            text-transform: uppercase;
            font-weight: 800;
        }
        .type-user { color: var(--blue); border: 1px solid var(--blue); }
        .type-model { color: var(--green); border: 1px solid var(--green); }
        .type-tool { color: var(--purple); border: 1px solid var(--purple); }
        .type-none { color: var(--text-muted); border: 1px solid var(--border); }

        .time-info {
            font-size: 0.8rem;
            text-align: right;
        }
        .rel-time { font-weight: 700; color: var(--text); }
        
        button {
            background: var(--blue);
            border: none;
            color: white;
            padding: 0.6rem 1.2rem;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <nav>
        <div style="font-weight: 800; font-size: 1.3rem; letter-spacing: -0.02em;">Gemini Pulse</div>
        <button onclick="refresh()" id="refresh-btn">Refresh</button>
    </nav>
    <div class="container" id="list">
        <div class="empty">Scanning for active agents...</div>
    </div>
    <script>
        async function refresh() {
            try {
                const res = await fetch('/api');
                const agents = await res.json();
                render(agents);
            } catch (e) {
                document.getElementById('list').innerHTML = '<div class="empty">Connection Lost</div>';
            }
        }
        function esc(s) {
            return String(s)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;');
        }
        function render(agents) {
            const list = document.getElementById('list');
            if (!agents || agents.length === 0) {
                list.innerHTML = '<div class="empty">No active Gemini agents found</div>';
                return;
            }
            list.innerHTML = agents.map(a => {
                const now = Math.floor(Date.now() / 1000);
                const diff = now - a.unix;
                let rel = '---';
                if (a.unix > 0) {
                    if (diff < 60) rel = diff + 's ago';
                    else if (diff < 3600) rel = Math.floor(diff/60) + 'm ago';
                    else rel = Math.floor(diff/3600) + 'h ago';
                }
                const busyClass = a.busy ? 'is-busy' : '';
                const statusLabel = a.busy ? 'Busy' : 'Idle';
                const statusBadgeClass = a.busy ? 'status-busy' : 'status-idle';

                return `
                <div class="card ${busyClass}">
                    <div class="busy-indicator"></div>
                    <div class="title-row">
                        <span class="project-name">${esc(a.project)}</span>
                        <span class="status-badge ${statusBadgeClass}">${statusLabel}</span>
                    </div>
                    <div class="cwd">${esc(a.cwd)}</div>
                    <div class="msg-box">${esc(a.msg)}</div>
                    
                    <div class="deep-status">
                        ${a.current_thought !== "---" ? `
                        <div class="deep-row">
                            <div class="deep-label">Current Thought</div>
                            <div class="deep-content thought-subject">${esc(a.current_thought)}</div>
                        </div>` : ''}
                        ${a.latest_action !== "---" ? `
                        <div class="deep-row">
                            <div class="deep-label">Latest Action</div>
                            <div class="deep-content action-desc">${esc(a.latest_action)}</div>
                        </div>` : ''}
                    </div>

                    <div class="meta-row">
                        <div>
                            <span class="badge type-${a.type}">${esc(a.type)}</span>
                            <span class="badge" style="background: var(--border); color: var(--text-muted);">${a.cpu.toFixed(1)}% CPU</span>
                        </div>
                        <div class="time-info">
                            <span class="rel-time">${rel}</span>
                            <span style="color: var(--text-muted); margin-left: 4px;">${esc(a.time)}</span>
                        </div>
                    </div>
                </div>
            `}).join('');
        }
        refresh();
        setInterval(refresh, 3000);
    </script>
</body>
</html>
"""

class PulseHandler(http.server.BaseHTTPRequestHandler):
    def check_auth(self):
        """Checks if the request is authorized using Basic Auth."""
        if not AUTH_USER or not AUTH_HASH:
            return True # Auth not configured
            
        auth_header = self.headers.get('Authorization')
        if auth_header is None:
            return False
            
        if not auth_header.startswith('Basic '):
            return False
            
        try:
            # Decode the base64 credentials from client
            encoded_creds = auth_header.split(' ')[1]
            decoded_creds = base64.b64decode(encoded_creds).decode('utf-8')
            user, password = decoded_creds.split(':', 1)
            
            if user != AUTH_USER:
                return False

            # Verify against salted hash: salt_b64:hash_b64
            salt_b64, stored_hash_b64 = AUTH_HASH.split(':', 1)
            salt = base64.b64decode(salt_b64)
            stored_hash = base64.b64decode(stored_hash_b64)
            
            # Recompute PBKDF2 hash using the same salt
            computed_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
            return hmac.compare_digest(computed_hash, stored_hash)
        except Exception:
            return False

    def do_GET(self):
        if not self.check_auth():
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Gemini Pulse"')
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Unauthorized')
            return

        if self.path == "/api":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(self.get_agents()).encode())
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode())

    def get_agents(self):
        agents = {}
        try:
            output = subprocess.check_output(["pgrep", "-f", "gemini"], text=True).strip()
            pids = set(output.split("\n"))
        except:
            return []

        for pid in pids:
            try:
                # Get CPU usage
                cpu_output = subprocess.check_output(["ps", "-p", pid, "-o", "%cpu"], text=True).strip()
                # Handle locale-specific decimals (e.g., 0,0 instead of 0.0)
                cpu_usage = float(cpu_output.split("\n")[-1].replace(",", "."))
                
                cwd_output = subprocess.check_output(["lsof", "-a", "-p", pid, "-d", "cwd", "-Fn"], text=True).strip()
                match = re.search(r"n(/.*)", cwd_output)
                if not match: continue
                cwd = Path(match.group(1))
                project_name = cwd.name
                
                if str(cwd) in agents: continue

                log_file = None
                if (GEMINI_TMP_ROOT / project_name / "logs.json").exists():
                    log_file = GEMINI_TMP_ROOT / project_name / "logs.json"
                else:
                    for item in GEMINI_TMP_ROOT.glob("*/.project_root"):
                        if item.read_text().strip() == str(cwd):
                            log_file = item.parent / "logs.json"
                            break
                
                msg, mtype, mtime, munix, busy = "No active logs", "none", "---", 0, False
                latest_prompt, current_thought, latest_action = "---", "---", "---"
                
                # Busy Heuristic 1: CPU usage > 2%
                if cpu_usage > 2.0:
                    busy = True

                # Try to extract Deep Status from session JSON
                try:
                    chat_dir = (log_file.parent if log_file else (GEMINI_TMP_ROOT / project_name)) / "chats"
                    if chat_dir.exists():
                        session_files = list(chat_dir.glob("session-*.json"))
                        if session_files:
                            newest_session = max(session_files, key=os.path.getmtime)
                            # Efficiently read only the end of the file for the latest state
                            with open(newest_session, "rb") as f:
                                f.seek(0, os.SEEK_END)
                                size = f.tell()
                                read_size = min(size, 131072)
                                f.seek(size - read_size)
                                tail = f.read().decode('utf-8', errors='replace')
                                
                                # Extract messages using a more robust brace-balancing approach
                                chunks = tail.split('"id":')
                                if len(chunks) > 1:
                                    parsed_messages = []
                                    # Take last 8 potential messages to ensure we get user/gemini pairs
                                    for chunk in reversed(chunks[-9:]):
                                        try:
                                            # Reconstruct a parsable JSON snippet
                                            m_str = '{"id":' + chunk
                                            # Find the balanced end of the object
                                            balance = 0
                                            in_string = False
                                            escape = False
                                            end_pos = -1
                                            for i, char in enumerate(m_str):
                                                if char == '"' and not escape:
                                                    in_string = not in_string
                                                if not in_string:
                                                    if char == '{': balance += 1
                                                    elif char == '}':
                                                        balance -= 1
                                                        if balance == 0:
                                                            end_pos = i + 1
                                                            break
                                                elif char == '\\':
                                                    escape = not escape
                                                else:
                                                    escape = False
                                            
                                            if end_pos != -1:
                                                m_obj = json.loads(m_str[:end_pos])
                                                parsed_messages.append(m_obj)
                                        except: continue
                                    
                                    # Extract latest prompt
                                    for m in parsed_messages:
                                        if m.get("type") == "user":
                                            content = m.get("content", [])
                                            if isinstance(content, list) and content:
                                                latest_prompt = str(content[0].get("text", "---"))[:200]
                                            elif isinstance(content, str):
                                                latest_prompt = content[:200]
                                            break
                                    
                                    # Extract current thought and action
                                    for m in parsed_messages:
                                        if m.get("type") == "gemini":
                                            thoughts = m.get("thoughts", [])
                                            if thoughts:
                                                # Use subject if available, otherwise description (truncated)
                                                t = thoughts[-1]
                                                current_thought = str(t.get("subject") or t.get("description") or "---")[:200]
                                            
                                            tool_calls = m.get("toolCalls", [])
                                            if tool_calls:
                                                latest_action = str(tool_calls[-1].get("description", "---"))[:200]
                                            else:
                                                content = m.get("content")
                                                if content:
                                                    latest_action = str(content[0].get("text", content) if isinstance(content, list) else content)[:200]
                                            break
                except Exception:
                    pass

                if log_file and log_file.exists():
                    # Busy Heuristic 2: Log file modified in last 60s
                    mtime_stat = os.path.getmtime(log_file)
                    now = time.time()
                    if (now - mtime_stat) < 60:
                        busy = True

                    with open(log_file, "r") as f:
                        try:
                            f.seek(0, os.SEEK_END)
                            size = f.tell()
                            # Read last 16KB to find the last valid JSON object
                            read_size = min(size, 16384)
                            f.seek(size - read_size)
                            tail = f.read()
                            
                            # Find the last { ... } that contains "message"
                            matches = re.findall(r'\{[^{}]*?"message"[^{}]*?\}', tail, re.DOTALL)
                            if matches:
                                latest = json.loads(matches[-1])
                                msg = latest.get("message", "---")[:1000]
                                mtype = latest.get("type", "unknown")
                                ts = latest.get("timestamp", "---")
                                mtime = ts.split("T")[-1][:8]
                                try:
                                    dt = datetime.datetime.fromisoformat(ts.replace('Z', '+00:00'))
                                    munix = int(dt.timestamp())
                                except: pass

                                # Busy Heuristic 3: Type is 'user' or 'tool' (waiting)
                                # Only if recent
                                if (now - munix) < 600:
                                    if mtype == "user":
                                        busy = True
                                    elif mtype == "tool" and "call_id" in str(latest) and "result" not in str(latest):
                                        busy = True
                        except:
                            msg = "Parsing error"

                # Busy Heuristic 4: Any file in CWD (excluding hidden) modified in last 30s
                try:
                    # Look for any recently modified file in the project directory
                    recent_files = subprocess.check_output(
                        ["find", str(cwd), "-maxdepth", "2", "-not", "-path", "*/.*", "-newermt", "30 seconds ago"], 
                        text=True, stderr=subprocess.DEVNULL, timeout=2
                    ).strip()
                    if recent_files:
                        busy = True
                except:
                    pass

                agents[str(cwd)] = {
                    "pid": pid, "project": project_name, "cwd": str(cwd),
                    "msg": msg, "type": mtype, "time": mtime, "unix": munix, "busy": busy,
                    "cpu": cpu_usage,
                    "latest_prompt": latest_prompt,
                    "current_thought": current_thought,
                    "latest_action": latest_action
                }
            except:
                continue
        
        return sorted(agents.values(), key=lambda x: x['unix'], reverse=True)

    def log_message(self, format, *args): return 

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("0.0.0.0", PORT), PulseHandler) as httpd:
            protocol = "http"
            if CERT_FILE.exists() and KEY_FILE.exists():
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
                httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
                protocol = "https"
            
            print(f"Gemini Pulse (v26.04.11.8) [GPLv3] active at {protocol}://localhost:{PORT}", flush=True)
            httpd.serve_forever()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr, flush=True)
        sys.exit(1)

