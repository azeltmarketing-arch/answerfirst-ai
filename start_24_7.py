import subprocess
import time
import os
import sys

BASE = r"C:\Users\azelt\answerfirst-ai"
commands = [
    ("CRM", [sys.executable, os.path.join(BASE, "crm", "app.py")]),
    ("Dashboard", [sys.executable, "-m", "http.server", "8080"], os.path.join(BASE, "dashboard")),
    ("Portal", [sys.executable, os.path.join(BASE, "portal", "app.py")]),
    ("Unified", [sys.executable, os.path.join(BASE, "unified", "app.py")]),
]

processes = []
try:
    while True:
        print("[*] Starting AnswerFirst AI servers...")
        for name, cmd, *rest in commands:
            cwd = rest[0] if rest else None
            p = subprocess.Popen(cmd, cwd=cwd, creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
            processes.append((name, p))
            print(f"[+] {name} started (PID {p.pid})")
        print("[+] All servers running. Monitoring for crashes...")
        time.sleep(30)
except KeyboardInterrupt:
    print("\n[*] Shutting down...")
    for name, p in processes:
        p.terminate()
        print(f"[-] {name} stopped")
