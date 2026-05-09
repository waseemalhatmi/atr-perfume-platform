"""
scripts/get_aliexpress_token.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
سكريبت للحصول على Access Token من AliExpress
يستخدم IOP SDK الرسمي (نسخة مدمجة داخلياً)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import sys
import os
import json

# إضافة مجلد scripts للمسار
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.dirname(__file__))
import iop

# ══════════════════════════════════════════════════════════════
# تحميل الإعدادات من متغيرات البيئة فقط (لا تضع المفاتيح في الكود!)
# ══════════════════════════════════════════════════════════════
# قبل التشغيل، اضبط المتغيرات في PowerShell:
#   $env:ALIEXPRESS_APP_KEY    = "533828"
#   $env:ALIEXPRESS_APP_SECRET = "YOUR_APP_SECRET"
#   $env:ALIEXPRESS_AUTH_CODE  = "3_533828_XXXXXXXXXX"
# ثم شغّل: python scripts/get_aliexpress_token.py
# ══════════════════════════════════════════════════════════════
APP_KEY    = os.environ.get("ALIEXPRESS_APP_KEY", "")
APP_SECRET = os.environ.get("ALIEXPRESS_APP_SECRET", "")
AUTH_CODE  = os.environ.get("ALIEXPRESS_AUTH_CODE", "")

# التحقق من وجود المتغيرات الضرورية
_missing = [name for name, val in [
    ("ALIEXPRESS_APP_KEY",    APP_KEY),
    ("ALIEXPRESS_APP_SECRET", APP_SECRET),
    ("ALIEXPRESS_AUTH_CODE",  AUTH_CODE),
] if not val]
if _missing:
    print(f"❌ متغيرات البيئة الآتية غير مضبوطة: {', '.join(_missing)}")
    print("   اضبطها في PowerShell ثم أعد التشغيل:")
    for m in _missing:
        print(f"   $env:{m} = \"YOUR_VALUE\"")
    sys.exit(1)
# ══════════════════════════════════════════════════════════════

def get_token():
    print("=" * 55)
    print("AliExpress Token Exchange (IOP SDK)")
    print("=" * 55)

    url = "https://api-sg.aliexpress.com"
    client = iop.IopClient(url, APP_KEY, APP_SECRET)

    # استخدام نفس الـ Endpoint الرسمي من التوثيق
    request = iop.IopRequest('/auth/token/security/create')
    request.add_api_param('code', AUTH_CODE)
    request.add_api_param('uuid', 'atr-perfume-platform')  # معرف فريد لتطبيقك

    print(f"Sending request to: {url}/sync")
    print(f"API method: /auth/token/security/create")
    print(f"Code: {AUTH_CODE[:20]}...")
    print()

    response = client.execute(request)

    print(f"HTTP Status: {response.http_status}")
    print(f"Response type: {response.type}")
    print(f"Raw body (first 500 chars):")
    print(response.body[:500])
    print()

    # تحليل النتيجة
    try:
        data = json.loads(response.body)
    except Exception:
        print("ERROR: Could not parse response as JSON")
        return

    # البحث عن التوكن في هيكل الرد
    # AliExpress يضع البيانات في مستوى مختلف أحياناً
    access_token = (
        data.get("access_token") or
        data.get("result", {}).get("access_token") or
        data.get("data", {}).get("access_token")
    )

    refresh_token = (
        data.get("refresh_token") or
        data.get("result", {}).get("refresh_token") or
        data.get("data", {}).get("refresh_token")
    )

    expires = (
        data.get("expires_in") or
        data.get("result", {}).get("expires_in") or
        0
    )

    if access_token:
        print("=" * 55)
        print("SUCCESS! Got Access Token")
        print("=" * 55)
        print(f"\nACCESS TOKEN:\n   {access_token}")
        print(f"\nREFRESH TOKEN:\n   {refresh_token}")
        print(f"\nExpires in: {int(expires)//86400} days")
        print("\n" + "=" * 55)
        print("Next Step:")
        print("   GitHub > Settings > Secrets > Actions > New Secret")
        print(f"   Name:  ALIEXPRESS_ACCESS_TOKEN")
        print(f"   Value: {access_token}")
        print("=" * 55)
    else:
        print("=" * 55)
        print("FAILED - Full response:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print()
        error_msg = (
            data.get("error_description") or
            data.get("msg") or
            data.get("message") or
            data.get("error_response", {}).get("msg") or
            "Unknown error"
        )
        print(f"Error: {error_msg}")
        print()
        print("Possible causes:")
        print("  1. Code expired (must be used within 10 minutes)")
        print("  2. Code already used once (cannot reuse)")
        print("  3. App Key/Secret mismatch")
        print()
        print("Solution: Get a new authorization code by visiting:")
        print(f"  https://api-sg.aliexpress.com/oauth/authorize?response_type=code&client_id={APP_KEY}&redirect_uri=https://atr-perfume-platform-d4jr.onrender.com")
        print("=" * 55)


if __name__ == "__main__":
    get_token()
