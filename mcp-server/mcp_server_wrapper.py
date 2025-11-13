#!/usr/bin/env python3
"""
Windows-compatible wrapper for MCP server.
Fixes stdio buffering issues on Windows by acting as a transparent proxy.
"""
import sys
import os
import subprocess
import threading
import traceback

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_SCRIPT = os.path.join(SCRIPT_DIR, "mcp_server.py")
ERROR_LOG = os.path.join(SCRIPT_DIR, "wrapper_errors.txt")

def log_error(msg):
    """Log errors to file"""
    with open(ERROR_LOG, "a") as f:
        f.write(f"{msg}\n")

def main():
    """Start MCP server with proper stdio handling."""
    
    # Clear error log
    with open(ERROR_LOG, "w") as f:
        f.write("=== Wrapper Session Started ===\n")
    
    # Start the actual MCP server
    proc = subprocess.Popen(
        [sys.executable, "-u", SERVER_SCRIPT],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
        env=os.environ.copy()
    )
    
    log_error(f"Server started with PID: {proc.pid}")
    
    def forward_stdin():
        """Forward stdin to server"""
        try:
            log_error("stdin forwarder started")
            while True:
                line = sys.stdin.buffer.readline()
                if not line:
                    log_error("stdin: EOF received")
                    break
                log_error(f"stdin->server: {len(line)} bytes")
                proc.stdin.write(line)
                proc.stdin.flush()
        except Exception as e:
            log_error(f"stdin error: {e}")
            log_error(traceback.format_exc())
    
    def forward_stdout():
        """Forward server output to stdout"""
        try:
            log_error("stdout forwarder started")
            while True:
                line = proc.stdout.readline()
                if not line:
                    log_error("stdout: EOF received")
                    break
                log_error(f"server->stdout: {len(line)} bytes")
                sys.stdout.buffer.write(line)
                sys.stdout.buffer.flush()
        except Exception as e:
            log_error(f"stdout error: {e}")
            log_error(traceback.format_exc())
    
    def forward_stderr():
        """Forward server stderr to stderr"""
        try:
            log_error("stderr forwarder started")
            while True:
                line = proc.stderr.readline()
                if not line:
                    log_error("stderr: EOF received")
                    break
                # Don't log stderr content to avoid recursion, just forward it
                sys.stderr.buffer.write(line)
                sys.stderr.buffer.flush()
        except Exception as e:
            log_error(f"stderr error: {e}")
            log_error(traceback.format_exc())
    
    # Start forwarding threads
    threading.Thread(target=forward_stdin, daemon=True).start()
    threading.Thread(target=forward_stdout, daemon=True).start()
    threading.Thread(target=forward_stderr, daemon=True).start()
    
    log_error("All threads started, waiting for process...")
    
    # Wait for process
    returncode = proc.wait()
    log_error(f"Server exited with code: {returncode}")
    sys.exit(returncode)

if __name__ == "__main__":
    main()
