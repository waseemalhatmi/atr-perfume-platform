#!/usr/bin/env python3
"""
scripts/check_secrets.py
========================
Pre-commit secrets scanner.
Scans all git-tracked files for patterns that look like real credentials.

Usage (manual):   python scripts/check_secrets.py
Usage (auto):     Installed as .git/hooks/pre-commit via  scripts/install_hooks.py
"""

import subprocess
import re
import sys
from pathlib import Path

# ── Patterns that indicate a REAL secret (not a placeholder) ─────────────────
SECRET_PATTERNS = [
    # Gemini / Google AI keys
    (r"AIzaSy[A-Za-z0-9_-]{33}", "Google/Gemini API Key"),
    # Google OAuth client secrets
    (r"GOCSPX-[A-Za-z0-9_-]{28}", "Google OAuth Client Secret"),
    # Generic long hex secrets (>= 40 chars) assigned to known var names
    (r'(?:SECRET_KEY|secret_key)\s*=\s*["\']?[a-f0-9]{40,}', "Flask SECRET_KEY hardcoded"),
    # Supabase service role / anon keys
    (r"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "JWT / Supabase key"),
    # PostgreSQL connection strings with embedded passwords
    (r"postgresql://[^:]+:[^@]{6,}@", "PostgreSQL connection string with password"),
    # Generic high-entropy strings assigned to API key variables
    (r'(?:API_KEY|api_key)\s*=\s*["\'][A-Za-z0-9/+]{32,}["\']', "Hardcoded API Key"),
]

# ── Files / extensions to skip ────────────────────────────────────────────────
SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".eot",
    ".lock", ".map", ".min.js",
}
SKIP_PATHS = {
    "node_modules", ".git", "venv", "__pycache__",
    "dist", ".pytest_cache", "instance",
}


def get_staged_files() -> list[Path]:
    """Return list of files currently staged for commit."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True, text=True
    )
    return [Path(f) for f in result.stdout.strip().splitlines() if f]


def get_all_tracked_files() -> list[Path]:
    """Return all files tracked by git."""
    result = subprocess.run(
        ["git", "ls-files"],
        capture_output=True, text=True
    )
    return [Path(f) for f in result.stdout.strip().splitlines() if f]


def should_skip(path: Path) -> bool:
    if path.suffix.lower() in SKIP_EXTENSIONS:
        return True
    for part in path.parts:
        if part in SKIP_PATHS:
            return True
    return False


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    """Returns list of (line_num, matched_text, pattern_name)."""
    hits = []
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        for line_num, line in enumerate(content.splitlines(), 1):
            for pattern, name in SECRET_PATTERNS:
                if re.search(pattern, line):
                    hits.append((line_num, line.strip()[:120], name))
    except (OSError, PermissionError):
        pass
    return hits


def main(scan_staged_only: bool = True) -> int:
    files = get_staged_files() if scan_staged_only else get_all_tracked_files()
    found_secrets = False

    for path in files:
        if should_skip(path) or not path.exists():
            continue
        hits = scan_file(path)
        for line_num, line_text, pattern_name in hits:
            print(f"[SECRET DETECTED] {pattern_name}")
            print(f"   File : {path}")
            print(f"   Line : {line_num}")
            print(f"   Match: {line_text}")
            found_secrets = True

    if found_secrets:
        print("\n" + "=" * 60)
        print("[BLOCKED] COMMIT BLOCKED: Real secrets found in tracked files.")
        print("   Move them to .env and reference via os.environ.get()")
        print("=" * 60)
        return 1

    print("[OK] No secrets detected in tracked files.")
    return 0


if __name__ == "__main__":
    scan_all = "--all" in sys.argv
    sys.exit(main(scan_staged_only=not scan_all))
