
import os
import logging
import google.generativeai as genai
from app.models import Item
from app.services.vector_service import vector_service

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
        # Prefer stable flash model; fallback list for resilience
        self._model_priority = [
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-pro",
        ]

    def _build_system_instruction(self, user_message: str) -> str:
        related_items = []
        try:
            related_items = vector_service.semantic_search(user_message, limit=5)
        except Exception as db_err:
            logger.warning(f"AI context fetch error: {db_err}")

        catalog_snippet = ""
        if related_items:
            catalog_snippet = "العطور المتاحة:\n"
            for i in related_items:
                try:
                    price = getattr(i, "min_price_sql", "N/A")
                    brand_name = i.brand.name if i.brand else ""
                    catalog_snippet += f"- {i.name} (ID: {i.id}) من براند {brand_name} | {price}\n"
                except Exception:
                    continue

        return f"""
        أنت "الخبير العطري" (The Scent Connoisseur) والحارس لهوية ATR Perfumes الفاخرة. ✨🧴
        مهمتك هي تقديم تجربة استشارية راقية، مخصصة، ومنظمة للغاية.

        سياق المنتجات المتوفرة حالياً في متجرنا:
        {catalog_snippet if catalog_snippet else "مجموعتنا العطرية الفاخرة متوفرة وتشمل أرقى الماركات العالمية (Chanel, Dior, Tom Ford, YSL, Amouage)."}

        القواعد الصارمة للهوية والرد:
        1. التحية والافتتاحية: ابدأ دائماً بترحيب دافئ وراقي يليق بعالم الفخامة.
        2. التنسيق المرئي: استخدم العناوين العريضة (Bold) لأسماء العطور، والقوائم المنقطة.
        3. المحتوى الاحترافي: اشرح "النوتات العطرية" بأسلوب وصفي جذاب، واذكر المناسبة المناسبة.
        4. بطاقات المنتجات الذكية: ضع الكود [PRODUCT:ID] مباشرة بعد اسم العطر إذا كان متوفراً.
        5. الخاتمة: اختم بسؤال تفاعلي لبق أو عرض للمساعدة الإضافية. ✨

        اللغة: العربية الفصحى الحديثة، بأسلوب "Luxury Concierge".
        """

    def _get_model(self, model_name: str):
        """Instantiate a Gemini model. system_instruction supported in genai>=0.5."""
        system_instruction = None
        try:
            # Build system instruction text (may fail if DB is down)
            system_instruction = self._build_system_instruction("")
        except Exception:
            pass

        try:
            # New SDK (>=0.5): system_instruction is a top-level kwarg
            return genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction,
            )
        except TypeError:
            # Old SDK (<0.5): system_instruction not supported — use bare model
            logger.warning(
                f"SDK version does not support system_instruction. Using bare model: {model_name}"
            )
            return genai.GenerativeModel(model_name=model_name)

    def _clean_history(self, history: list) -> list:
        cleaned = []
        if not history:
            return cleaned
        for h in history:
            try:
                role = "user" if h.get("role") == "user" else "model"
                parts = h.get("parts", [])
                if not parts:
                    continue
                p = parts[0]
                text = p.get("text", "") if isinstance(p, dict) else str(p)
                if text.strip():
                    cleaned.append({"role": role, "parts": [text]})
            except Exception:
                continue
        return cleaned

    def get_response(self, user_message: str, history=None) -> str:
        """Single-shot response with model failover."""
        if not self.api_key:
            return "⚠️ خدمة الذكاء الاصطناعي غير مفعّلة حالياً."

        cleaned_history = self._clean_history(history or [])

        for model_name in self._model_priority:
            try:
                model = self._get_model(model_name)
                chat = model.start_chat(history=cleaned_history)
                response = chat.send_message(user_message)
                return response.text
            except Exception as e:
                logger.warning(f"Model {model_name} failed in get_response: {e}")
                continue

        return "أعتذر منك، جميع قنواتنا العطرية مشغولة حالياً. ✨ يرجى المحاولة بعد دقيقة."

    def stream_response(self, user_message: str, history=None):
        """Streaming response generator with model failover."""
        if not self.api_key:
            yield "⚠️ خدمة الذكاء الاصطناعي غير مفعّلة حالياً."
            return

        cleaned_history = self._clean_history(history or [])

        for model_name in self._model_priority:
            try:
                model = self._get_model(model_name)
                chat = model.start_chat(history=cleaned_history)
                response = chat.send_message(user_message, stream=True)
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
                return  # Success — exit generator
            except Exception as e:
                logger.warning(f"Model {model_name} failed in stream_response: {e}")
                continue

        yield "أعتذر منك بشدة، جميع قنواتنا العطرية مشغولة حالياً. ✨ يرجى المحاولة بعد دقيقة."


ai_service = AIService()
