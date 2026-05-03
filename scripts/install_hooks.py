#!/usr/bin/env python3
"""
scripts/install_hooks.py
========================
Run this ONCE to install the pre-commit secrets-scanner hook.
    python scripts/install_hooks.py
"""
import shutil
import stat
from pathlib import Path

HOOK_CONTENT = """#!/usr/bin/env python3
import subprocess, sys
result = subprocess.run([sys.executable, "scripts/check_secrets.py"], capture_output=False)
sys.exit(result.returncode)
"""

def install():
    hook_path = Path(".git/hooks/pre-commit")
    hook_path.parent.mkdir(parents=True, exist_ok=True)
    hook_path.write_text(HOOK_CONTENT, encoding="utf-8")
    # Make executable (Linux/Mac). On Windows git bash picks it up automatically.
    hook_path.chmod(hook_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    print(f"[OK] Pre-commit hook installed at {hook_path}")
    print("   Every 'git commit' will now scan for exposed secrets automatically.")

if __name__ == "__main__":
    install()
