"""
MetroGuard AI - Persistent Public Tunnel Daemon with Auto-Reconnect Keepalive
"""

import subprocess
import time
import sys

def run_tunnel():
    cmd = "npx localtunnel --port 8000 --subdomain metroguard-ai"
    while True:
        print("[KeepAlive Tunnel] Launching public HTTPS tunnel on https://metroguard-ai.loca.lt ...")
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            for line in proc.stdout:
                print(line, end="")
                sys.stdout.flush()
        except Exception as e:
            print(f"[KeepAlive Tunnel] Error: {e}")
        finally:
            try:
                proc.kill()
            except Exception:
                pass
        print("[KeepAlive Tunnel] Tunnel disconnected. Reconnecting in 3 seconds...")
        time.sleep(3)

if __name__ == "__main__":
    run_tunnel()
