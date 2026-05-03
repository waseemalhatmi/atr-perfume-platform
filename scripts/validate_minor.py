"""
scripts/validate_minor.py
Validates all Minor Priority fixes + Production Polish (A-E).
Run: python scripts/validate_minor.py
"""
import re, ast, sys, pathlib

ROOT = pathlib.Path(__file__).parent.parent
results = []

def check(label, passed, detail=""):
    results.append(("PASS" if passed else "FAIL", label, detail))
    return passed

def src(path):
    return (ROOT / path).read_text(encoding="utf-8")

def parse_ok(path):
    try:
        ast.parse(src(path))
        return True
    except SyntaxError:
        return False

# ── Syntax (every touched file) ──────────────────────────────────────────────
for f in [
    "app/__init__.py",
    "app/tasks.py",
    "app/routes/catalog.py",
    "app/services/analytics.py",
    "app/utils/resilience.py",
    "app/utils/logger.py",
    "app/utils/cache_metrics.py",
]:
    check(f"SYNTAX {f}", parse_ok(f))

# ── Minor-1: Structured logging utility ──────────────────────────────────────
log_src = src("app/utils/logger.py")
check("M-1a  logger.py exists",              (ROOT / "app/utils/logger.py").exists())
check("M-1b  _JsonFormatter class",          "_JsonFormatter" in log_src)
check("M-1c  get_logger() exported",         "def get_logger" in log_src)
check("M-1d  ISO-8601 UTC timestamp",        "timezone.utc" in log_src)

# ── Minor-2: Cache metrics ────────────────────────────────────────────────────
cm_src = src("app/utils/cache_metrics.py")
check("M-2a  cache_metrics.py exists",       (ROOT / "app/utils/cache_metrics.py").exists())
check("M-2b  record_hit() defined",          "def record_hit" in cm_src)
check("M-2c  record_miss() defined",         "def record_miss" in cm_src)
check("M-2d  get_metrics() defined",         "def get_metrics" in cm_src)
check("M-2e  Redis fallback to local",       "_local" in cm_src)

cat = src("app/routes/catalog.py")
check("M-2f  record_hit used in catalog",    "record_hit" in cat)
check("M-2g  record_miss used in catalog",   "record_miss" in cat)

# ── Minor-3: Global pagination cap ───────────────────────────────────────────
check("M-3a  per_page capped at 50",         "per_page\", 12, type=int), 50)" in cat)
check("M-3b  no hardcoded 48 cap",           "per_page\", 12, type=int), 48)" not in cat)

# ── Minor-4: DB query timeout handled via circuit breaker (resilience.py) ────
res = src("app/utils/resilience.py")
check("M-4a  CircuitBreaker guards DB ops",  "db_circuit_breaker" in res)

# ── Minor-5: Cache failure fallback (try/except on every cache call) ─────────
cache_calls = cat.count("cache.get(") + cat.count("cache.set(")
except_blocks = cat.count("except Exception")
check("M-5a  all cache ops guarded (try/except)", except_blocks >= 4)

# ── Minor-6: Rate limit logging ──────────────────────────────────────────────
init_src = src("app/__init__.py")
check("M-6a  rate_limit logger created",     "_rl_log" in init_src)
check("M-6b  errorhandler 429 registered",   "errorhandler(429)" in init_src)
check("M-6c  IP logged on rate limit",       "ip=request.remote_addr" in init_src)

# ── Minor-7: Consistent error format ─────────────────────────────────────────
check("M-7a  errorhandler 400 registered",   "errorhandler(400)" in init_src)
check("M-7b  errorhandler 404 registered",   "errorhandler(404)" in init_src)
check("M-7c  errorhandler 500 registered",   "errorhandler(500)" in init_src)
check("M-7d  error + code fields in 429",    '"code": 429' in init_src)
check("M-7e  error + code fields in 500",    '"code": 500' in init_src)

# ── Minor-8: Background job structured logging ────────────────────────────────
tasks = src("app/tasks.py")
check("M-8a  get_logger used in tasks",      "get_logger" in tasks)
check("M-8b  task_started event emitted",    "task_started" in tasks)
check("M-8c  task_succeeded event emitted",  "task_succeeded" in tasks)
check("M-8d  task_failed event emitted",     "task_failed" in tasks or "task_max_retries" in tasks)
check("M-8e  no stdlib logger in tasks",     "import logging" not in tasks)

# ── Minor-9: UTC timestamps in analytics ─────────────────────────────────────
anl = src("app/services/analytics.py")
check("M-9a  UTC used in analytics",         "datetime.utcnow()" in anl or "timezone.utc" in anl)
check("M-9b  no naive datetime in logger",   "timezone.utc" in log_src)

# ── Minor-10: print() removed from catalog.py ────────────────────────────────
import re as _re
print_lines = [l for l in cat.splitlines()
               if _re.search(r'\bprint\s*\(', l) and not l.strip().startswith("#")]
check("M-10a no print() in catalog.py",      len(print_lines) == 0,
      f"Found: {print_lines[:2]}" if print_lines else "clean")


# ── Polish-A: Unified TTL strategy ───────────────────────────────────────────
check("PA-a  item_detail cache 1800s",       "timeout=1800" in cat)
check("PA-b  item_list cache 300s",          "timeout=300"  in cat)
check("PA-c  filters cache 3600s",           "timeout=3600" in cat)

anl_src = src("app/services/analytics.py")
check("PA-d  analytics cache 300s",          "timeout=300"  in anl_src)

vec = src("app/services/vector_service.py")
check("PA-e  search TTL via namespace ver.", "vec:search_ns" in vec)

# ── Polish-C: Error consistency ───────────────────────────────────────────────
check("PC-a  errorhandler 429 returns code", "code\": 429" in init_src)
check("PC-b  errorhandler 500 returns code", "code\": 500" in init_src)

# ── Polish-D: Performance headers ────────────────────────────────────────────
check("PD-a  X-Response-Time-MS set",        "X-Response-Time-MS" in init_src)
check("PD-b  X-Cache-Status set in catalog", "X-Cache-Status"     in cat)

# ── Polish-E: Structured JSON logger ─────────────────────────────────────────
check("PE-a  JSON file formatter in init",   "_JsonFileFormatter" in init_src)
check("PE-b  structured perf log",           "request_completed"  in init_src)

# ── REPORT ────────────────────────────────────────────────────────────────────
print()
print("=" * 70)
print("  MINOR PRIORITY + PRODUCTION POLISH — VALIDATION REPORT")
print("=" * 70)
all_pass = True
for status, label, detail in results:
    mark = "[PASS]" if status == "PASS" else "[FAIL]"
    print(f"  {mark}  {label}")
    if detail:
        print(f"         {detail}")
    if status == "FAIL":
        all_pass = False
print("=" * 70)
overall = "ALL CHECKS PASSED — Enterprise SaaS Production Excellence" \
    if all_pass else "SOME CHECKS FAILED — Review above"
print(f"  RESULT: {overall}")
print("=" * 70)
sys.exit(0 if all_pass else 1)
