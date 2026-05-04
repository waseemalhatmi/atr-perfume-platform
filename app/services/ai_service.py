"""
ai_service.py — Gemini AI chatbot service for ATR Perfume Platform.

Compatible with google-generativeai >= 0.5.x
"""
import os
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            logger.info("Gemini AI configured successfully.")
        else:
            logger.warning("GEMINI_API_KEY is not set — AI chat will be disabled.")

        # Models in order of preference (most capable → fastest fallback)
        self._model_priority = [
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-1.0-pro",
        ]

    # ── System Instruction ────────────────────────────────────────────────────

    def _build_system_instruction(self, user_message: str) -> str:
        """
        Build the AI persona + product context.
        Falls back gracefully if the DB / vector service is unavailable.
        """
        catalog_snippet = ""
        try:
            from app.services.vector_service import vector_service
            if user_message:
                related = vector_service.semantic_search(user_message, limit=5)
                if related:
                    catalog_snippet = "العطور المتاحة:\n"
                    for i in related:
                        try:
                            price = getattr(i, "min_price_sql", "N/A")
                            brand = i.brand.name if i.brand else ""
                            catalog_snippet += f"- {i.name} (ID: {i.id}) من براند {brand} | {price}\n"
                        except Exception:
                            continue
        except Exception as e:
            logger.warning(f"Could not build product context: {e}")

        return (
            "أنت «الخبير العطري» (The Scent Connoisseur) — مستشار عطور فاخر لمنصة ATR. ✨🧴\n\n"
            "مهمتك تقديم تجربة استشارية راقية ومنظمة.\n\n"
            f"{catalog_snippet if catalog_snippet else 'مجموعتنا تشمل أرقى الماركات: Chanel, Dior, Tom Ford, YSL, Amouage.'}\n\n"
            "القواعد:\n"
            "1. ابدأ بترحيب دافئ يليق بعالم الفخامة.\n"
            "2. استخدم **Bold** لأسماء العطور، وقوائم منظمة.\n"
            "3. اشرح النوتات العطرية (أفتتاحية، قلب، قاعدة) بوصف جذاب.\n"
            "4. أذكر [PRODUCT:ID] مباشرة بعد اسم العطر إذا كان متوفراً في السياق.\n"
            "5. اختم بسؤال تفاعلي أو عرض مساعدة. ✨\n"
            "اللغة: العربية الفصحى الحديثة بأسلوب Luxury Concierge."
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _clean_history(self, history: list) -> list:
        cleaned = []
        for h in (history or []):
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

    def _make_model(self, model_name: str, system_instruction: str):
        """
        Instantiate a GenerativeModel.
        Handles both old SDK (no system_instruction) and new SDK (>= 0.5).
        """
        try:
            return genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction,
            )
        except TypeError:
            # Older SDK version: system_instruction not yet supported
            logger.warning(f"SDK does not support system_instruction; using bare model {model_name}")
            return genai.GenerativeModel(model_name=model_name)

    # ── Public API ────────────────────────────────────────────────────────────

    def get_response(self, user_message: str, history=None) -> str:
        """Single-shot response with automatic model failover."""
        if not self.api_key:
            return "⚠️ خدمة الذكاء الاصطناعي غير مفعّلة — يرجى إضافة GEMINI_API_KEY."

        system_instruction = self._build_system_instruction(user_message)
        cleaned_history = self._clean_history(history)

        for model_name in self._model_priority:
            try:
                model = self._make_model(model_name, system_instruction)
                chat = model.start_chat(history=cleaned_history)
                response = chat.send_message(user_message)
                logger.info(f"AI response generated using {model_name}")
                return response.text
            except Exception as e:
                logger.warning(f"Model {model_name} failed: {e}")
                continue

        logger.error("All Gemini models failed in get_response.")
        return "أعتذر، خدمة الذكاء الاصطناعي غير متاحة مؤقتاً. يرجى المحاولة بعد قليل."

    def stream_response(self, user_message: str, history=None):
        """Streaming response generator with automatic model failover."""
        if not self.api_key:
            yield "⚠️ خدمة الذكاء الاصطناعي غير مفعّلة — يرجى إضافة GEMINI_API_KEY."
            return

        system_instruction = self._build_system_instruction(user_message)
        cleaned_history = self._clean_history(history)

        for model_name in self._model_priority:
            try:
                model = self._make_model(model_name, system_instruction)
                chat = model.start_chat(history=cleaned_history)
                response = chat.send_message(user_message, stream=True)
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
                logger.info(f"AI stream completed using {model_name}")
                return  # ✅ success — stop iterating models
            except Exception as e:
                logger.warning(f"Model {model_name} failed in stream: {e}")
                continue

        logger.error("All Gemini models failed in stream_response.")
        yield "أعتذر، خدمة الذكاء الاصطناعي غير متاحة مؤقتاً. يرجى المحاولة بعد قليل."


ai_service = AIService()
