"""
scripts/iop.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
نسخة Python بسيطة من IOP SDK الرسمي لـ AliExpress
مبنية داخلياً دون الحاجة لأي مكتبة خارجية.
مرجع: https://open.aliexpress.com/doc/api.htm
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import hashlib
import hmac
import time
import json
import requests


class IopRequest:
    def __init__(self, api_name: str):
        self.api_name = api_name
        self._params = {}

    def add_api_param(self, key: str, value: str):
        self._params[key] = str(value)

    @property
    def params(self):
        return self._params


class IopResponse:
    def __init__(self, raw_text: str, http_status: int):
        self.http_status = http_status
        self.body = raw_text
        self.type = "nil"
        self._data = {}

        try:
            self._data = json.loads(raw_text)
            # AliExpress wraps errors in {"error_response": {...}}
            if "error_response" in self._data:
                self.type = "ISP"
            else:
                self.type = "nil"  # success
        except Exception:
            self.type = "ISP"

    def get(self, key, default=None):
        return self._data.get(key, default)

    def __repr__(self):
        return f"IopResponse(status={self.http_status}, type={self.type})"


class IopClient:
    def __init__(self, url: str, app_key: str, app_secret: str):
        self.url = url.rstrip("/")
        self.app_key = app_key
        self.app_secret = app_secret

    def _sign(self, params: dict, api_name: str = "") -> str:
        """
        AliExpress Official MD5 Signing Algorithm:
        secret + sorted(key+value pairs) + secret → MD5 uppercase
        NOTE: method name is NOT included in the sign string
        """
        # استبعاد حقل sign نفسه من عملية الحساب
        sign_params = {k: v for k, v in params.items() if k != "sign"}
        sorted_items = sorted(sign_params.items())
        base_string = self.app_secret + "".join(f"{k}{v}" for k, v in sorted_items) + self.app_secret
        return hashlib.md5(base_string.encode("utf-8")).hexdigest().upper()

    def execute(self, request: IopRequest, access_token: str = "") -> IopResponse:
        """تنفيذ طلب API وإرجاع IopResponse."""
        params = {
            "app_key":    self.app_key,
            "method":     request.api_name,
            "timestamp":  str(int(time.time() * 1000)),
            "sign_method": "md5",
            "v":          "2.0",
        }
        if access_token:
            params["session"] = access_token

        # دمج معلمات الطلب
        params.update(request.params)

        # بناء التوقيع مع اسم الـ API
        params["sign"] = self._sign(params, request.api_name)

        try:
            response = requests.post(
                f"{self.url}/sync",
                data=params,
                timeout=30
            )
            return IopResponse(response.text, response.status_code)
        except requests.exceptions.RequestException as e:
            return IopResponse(json.dumps({"error": str(e)}), 0)
