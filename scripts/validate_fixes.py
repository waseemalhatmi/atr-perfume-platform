"""
scripts/validate_fixes.py
Validates all 5 critical fixes applied to the project.
Run: python scripts/validate_fixes.py
"""
import sys
import re
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
results = []


def check(label, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results.append((status, label, detail))
    return passed


# ─── FIX 1: Secrets Protection ───────────────────────────────────────────────
gi = (ROOT / ".gitignore").read_text(encoding="utf-8")
check("FIX-1a .env in gitignore",    ".env"   in gi,   ".env line present")
check("FIX-1b .env.* in gitignore",  ".env.*" in gi,   ".env.* wildcard present")
check("FIX-1c *.pem in gitignore",   "*.pem"  in gi,   "cert/key files excluded")
check("FIX-1d secrets scanner",      (ROOT / "scripts" / "check_secrets.py").exists())
check("FIX-1e pre-commit hook",      (ROOT / ".git" / "hooks" / "pre-commit").exists())

# ─── FIX 2: start_timer duplicate ────────────────────────────────────────────
init_src = (ROOT / "app" / "__init__.py").read_text(encoding="utf-8")
timer_count = len(re.findall(
    r"@app\.before_request\s*\n\s*def start_timer", init_src
))
check("FIX-2  start_timer registered once", timer_count == 1, f"count={timer_count}")

# log_performance uses g.start_time (not request._start_time)
check(
    "FIX-2  log_performance uses g.start_time",
    "g.start_time" in init_src and "request._start_time" not in init_src,
    "g.start_time found, request._start_time absent",
)

# ─── FIX 3: SQLAlchemy commit safety ─────────────────────────────────────────
disc = (ROOT / "app" / "services" / "discovery_service.py").read_text(encoding="utf-8")
# Isolate only the refresh_item_recommendations function body
func_start = disc.find("def refresh_item_recommendations")
func_end   = disc.find("\ndef ", func_start + 1)
func_body  = disc[func_start:func_end]

check("FIX-3a no commit() in refresh func", "db.session.commit()" not in func_body)
check("FIX-3b flush() in refresh func",     "db.session.flush()"  in func_body)

tasks = (ROOT / "app" / "tasks.py").read_text(encoding="utf-8")
check("FIX-3c task has explicit commit",    "db.session.commit()" in tasks)

# Fallback in get_similar_fragrances commits after refresh
fallback_idx  = disc.find("def get_similar_fragrances")
fallback_end  = disc.find("\ndef ", fallback_idx + 1)
fallback_body = disc[fallback_idx:fallback_end]
check(
    "FIX-3d fallback commits after refresh",
    "db.session.commit()" in fallback_body,
    "explicit commit after refresh_item_recommendations in route fallback",
)

# ─── FIX 4: FTS dictionary ───────────────────────────────────────────────────
search = (ROOT / "app" / "services" / "search_service.py").read_text(encoding="utf-8")
# Extract actual function-call arguments (not comments)
vec_calls = re.findall(r"to_tsvector\((['\"])(.*?)\1", search)
qry_calls = re.findall(r"plainto_tsquery\((['\"])(.*?)\1", search)

vec_ok = all(arg == "simple" for _, arg in vec_calls)
qry_ok = all(arg == "simple" for _, arg in qry_calls)
check("FIX-4a to_tsvector uses 'simple'",    vec_ok, str(vec_calls))
check("FIX-4b plainto_tsquery uses 'simple'", qry_ok, str(qry_calls))

ilike_fallback = "Item.name.ilike(term)" in search
check("FIX-4c ilike fallback present", ilike_fallback)

# ─── FIX 5: Newsletter URLSearchParams ───────────────────────────────────────
api_ts = (ROOT / "frontend" / "src" / "lib" / "api.ts").read_text(encoding="utf-8")
check("FIX-5a URLSearchParams used",       "URLSearchParams" in api_ts)
check("FIX-5b plain object removed",       "{ email, mode: 'guest' }" not in api_ts)

# ─── PRINT REPORT ─────────────────────────────────────────────────────────────
print()
print("=" * 65)
print("  FINAL VALIDATION REPORT — Critical Fixes")
print("=" * 65)
all_pass = True
for status, label, detail in results:
    mark = "[PASS]" if status == "PASS" else "[FAIL]"
    print(f"  {mark}  {label}")
    if detail:
        print(f"         {detail}")
    if status == "FAIL":
        all_pass = False

print("=" * 65)
overall = "ALL 5 FIXES VERIFIED — System is clean" if all_pass else "SOME CHECKS FAILED — Review above"
print(f"  RESULT: {overall}")
print("=" * 65)
sys.exit(0 if all_pass else 1)
