
import os
import google.generativeai as genai
from app.models import Item, Category, Brand
from sqlalchemy.orm import selectinload
from app.services.vector_service import vector_service

class AIService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def _build_system_instruction(self, user_message):
        related_items = []
        try:
            related_items = vector_service.semantic_search(user_message, limit=5)
        except Exception as db_err:
            print(f"DB CONTEXT ERROR: {str(db_err)}")
        
        catalog_snippet = ""
        if related_items:
            catalog_snippet = "العطور المتاحة:\n"
            for i in related_items:
                try:
                    price = getattr(i, 'min_price_sql', "N/A")
                    catalog_snippet += f"- {i.name} (ID: {i.id}) من براند {i.brand.name if i.brand else ''} | {price}\n"
                except:
                    continue

        return f"""
        أنت "الخبير العطري" (The Scent Connoisseur) والحارس لهوية Signature Perfumes الفاخرة. ✨🧴
        مهمتك هي تقديم تجربة استشارية راقية، مخصصة، ومنظمة للغاية.

        سياق المنتجات المتوفرة حالياً في متجرنا:
        {catalog_snippet if catalog_snippet else "مجموعتنا العطرية الفاخرة متوفرة وتشمل أرقى الماركات العالمية (Chanel, Dior, Tom Ford, YSL, Amouage)."}

        القواعد الصارمة للهوية والرد:
        1. التحية والافتتاحية: ابدأ دائماً بترحيب دافئ وراقي يليق بعالم الفخامة.
        2. التنسيق المرئي (Visual Structure):
           - استخدم العناوين العريضة (Bold) لأسماء العطور.
           - استخدم القوائم المنقطة أو المرقمة بوضوح.
           - اترك مسافات (Symmetry) بين الفقرات لسهولة القراءة.
        3. المحتوى الاحترافي:
           - اشرح "النوتات العطرية" (الأفتتاحية، القلب، القاعدة) بأسلوب وصفي جذاب.
           - اذكر "المناسبة" المناسبة لكل عطر (رسمي، يومي، سهرة).
        4. بطاقات المنتجات الذكية:
           - يجب وضع الكود [PRODUCT:ID] مباشرة بعد اسم العطر إذا كان متوفراً في السياق أعلاه.
        5. الخاتمة: اختم بسؤال تفاعلي لبق أو عرض للمساعدة الإضافية. ✨

        مثال على نمط الرد المطلوب:
        "أهلاً بك في عالم Signature Perfumes الفاخر... إليك قائمة مختارة:
        **العطر الأول**: [الوصف] [PRODUCT:ID]
        **العطر الثاني**: [الوصف] [PRODUCT:ID]"

        اللغة: العربية الفصحى الحديثة، بأسلوب "Luxury Concierge".
        """

    def get_response(self, user_message, history=None):
        try:
            system_instruction = self._build_system_instruction(user_message)

            # Fix #3: Cleanly instantiate model once without re-configuring
            chat_model = genai.GenerativeModel(
                model_name='gemini-1.5-flash',
                system_instruction=system_instruction
            )

            cleaned_history = []
            if history:
                for h in history:
                    try:
                        role = "user" if h.get('role') == "user" else "model"
                        parts = h.get('parts', [])
                        text = parts[0].get('text') if isinstance(parts[0], dict) else str(parts[0])
                        cleaned_history.append({"role": role, "parts": [text]})
                    except: continue

            chat = chat_model.start_chat(history=cleaned_history)
            response = chat.send_message(user_message)
            return response.text
        except Exception as e:
            print(f"CRITICAL AI ERROR: {str(e)}")
            return "أعتذر منك، يبدو أنني كنت غارقاً في تحليل عبير عطر استثنائي. ✨ هل يمكنك تكرار سؤالك؟"

    def stream_response(self, user_message, history=None):
        """Generator for streaming responses with Model Failover & DB Resilience."""
        # List of models to try in order of preference
        models_to_try = ['gemini-1.5-flash', 'gemini-2.0-flash', 'gemini-flash-latest']
        
        try:
            system_instruction = self._build_system_instruction(user_message)

            cleaned_history = []
            if history:
                for h in history:
                    try:
                        role = "user" if h.get('role') == "user" else "model"
                        parts = h.get('parts', [])
                        text = ""
                        if isinstance(parts, list) and len(parts) > 0:
                            p = parts[0]
                            text = p.get('text', '') if isinstance(p, dict) else str(p)
                        if text:
                            cleaned_history.append({"role": role, "parts": [text]})
                    except: continue

            # Try each model until one works
            success = False
            for model_name in models_to_try:
                try:
                    temp_model = genai.GenerativeModel(
                        model_name=model_name,
                        system_instruction=system_instruction
                    )
                    chat = temp_model.start_chat(history=cleaned_history)
                    response = chat.send_message(user_message, stream=True)
                    
                    for chunk in response:
                        if chunk.text:
                            yield chunk.text
                    success = True
                    break # Success! Exit model loop
                except Exception as model_err:
                    print(f"Model {model_name} failed: {str(model_err)}")
                    continue
            
            if not success:
                yield "أعتذر منك بشدة، جميع قنواتنا العطرية مشغولة حالياً. ✨ يرجى المحاولة بعد دقيقة واحدة."

        except Exception as e:
            print(f"CRITICAL STREAMING ERROR: {str(e)}")
            yield "حدث خطأ غير متوقع. ✨ هل يمكنك تكرار طلبك؟"

ai_service = AIService()
