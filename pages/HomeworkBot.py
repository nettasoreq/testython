import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import streamlit as st
import requests
from bs4 import BeautifulSoup

# הגדרות עמוד
st.set_page_config(
    page_title="עוזר שיעורי בית חכם",
    page_icon="📚",
    layout="wide"
)

# טעינת API Key
load_dotenv()
API_KEY = os.getenv("API_KEY") or st.secrets.get("API_KEY")

# כותרת
st.title("📚 עוזר שיעורי בית עם חיפוש באינטרנט")
st.markdown("---")


# ===== פונקציות עזר =====

def search_web(query):
    """
    פונקציה שמחפשת באינטרנט ומחזירה תוצאות
    משתמשת ב-DuckDuckGo HTML (חינמי לגמרי!)
    """
    try:
        # DuckDuckGo HTML search (לא דורש API key)
        url = f"https://html.duckduckgo.com/html/?q={query}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # חילוץ תוצאות
        results = []
        for result in soup.find_all('div', class_='result')[:5]:  # 5 תוצאות ראשונות
            title_elem = result.find('a', class_='result__a')
            snippet_elem = result.find('a', class_='result__snippet')

            if title_elem and snippet_elem:
                title = title_elem.get_text()
                snippet = snippet_elem.get_text()
                link = title_elem.get('href', '')

                results.append({
                    'title': title,
                    'snippet': snippet,
                    'link': link
                })

        # עיצוב התוצאות לטקסט
        if results:
            formatted = f"תוצאות חיפוש עבור '{query}':\n\n"
            for i, result in enumerate(results, 1):
                formatted += f"{i}. {result['title']}\n"
                formatted += f"   {result['snippet']}\n"
                formatted += f"   {result['link']}\n\n"
            return formatted
        else:
            return f"לא נמצאו תוצאות עבור '{query}'"

    except Exception as e:
        return f"שגיאה בחיפוש: {str(e)}"


# הגדרת הפונקציה ל-Gemini
search_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="search_web",
            description="חפש מידע באינטרנט. השתמש בפונקציה הזו כאשר אתה צריך מידע עדכני או מידע שאתה לא בטוח בו.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "query": types.Schema(
                        type=types.Type.STRING,
                        description="מה לחפש באינטרנט (באנגלית)"
                    )
                },
                required=["query"]
            )
        )
    ]
)

# System instruction
SYSTEM_INSTRUCTION = """
אתה עוזר שיעורי בית חכם ומועיל לתלמידים.

חוקים חשובים:
1. תמיד הסבר צעד אחר צעד
2. השתמש בדוגמאות ברורות
3. היה סבלני ומעודד
4. אל תיתן את התשובה המלאה - תוביל את התלמיד לפתרון
5. אם התלמיד תקוע, תן רמז קטן
6. כתוב בעברית ברורה

כלים זמינים:
- יש לך גישה לפונקציית search_web לחיפוש מידע באינטרנט
- השתמש בה כאשר אתה צריך מידע עדכני או מידע שאתה לא בטוח בו
- תמיד חפש באנגלית (לדוגמה: "photosynthesis process" ולא "תהליך הפוטוסינתזה")

המטרה שלך: לעזור לתלמיד ללמוד ולהבין, לא רק לתת תשובות!
"""

# רשימת מודלים זמינים
AVAILABLE_MODELS = {
    "Gemini 2.5 Flash ": "gemini-2.5-flash",
    "Gemini 2.0 Flash": "gemini-2.0-flash",
}


def create_chat_with_model(model_name):
    """יוצר chat session חדש עם מודל מסוים"""
    client = genai.Client(api_key=API_KEY)

    chat = client.chats.create(
        model=model_name,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.7,
            tools=[search_tool],
        )
    )

    return client, chat


def rebuild_chat_with_history(model_name, history):
    """
    בונה chat session חדש עם מודל חדש ומשחזר את ההיסטוריה
    """
    client = genai.Client(api_key=API_KEY)

    chat = client.chats.create(
        model=model_name,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.7,
            tools=[search_tool],
        )
    )

    # משחזר את ההיסטוריה - שולח כל הודעה מחדש
    for msg in history:
        if msg["role"] == "user":
            # שולח הודעת משתמש
            try:
                chat.send_message(msg["content"])
            except:
                pass  # אם יש שגיאה, ממשיכים הלאה
        elif msg["role"] == "assistant" and not msg.get("is_function"):
            # לא צריך לשלוח את תשובות הבוט - הן נוצרות אוטומטית
            pass

    return client, chat


# ===== אתחול הבוט =====

def initialize_bot():
    """אתחול הבוט"""
    if "client" not in st.session_state:
        st.session_state.current_model = "gemini-2.0-flash"
        client, chat = create_chat_with_model(st.session_state.current_model)
        st.session_state.client = client
        st.session_state.chat = chat
        st.session_state.messages = []


def switch_model(new_model):
    """מחליף מודל תוך שמירת ההיסטוריה"""
    if new_model != st.session_state.current_model:
        with st.spinner(f"מחליף למודל {new_model}..."):
            try:
                # בונה chat חדש עם ההיסטוריה
                client, chat = rebuild_chat_with_history(new_model, st.session_state.messages)

                st.session_state.client = client
                st.session_state.chat = chat
                st.session_state.current_model = new_model

                st.success(f"✅ עברת למודל: {new_model}")
                return True
            except Exception as e:
                st.error(f"❌ שגיאה בהחלפת מודל: {str(e)}")
                return False


def send_message_with_tools(user_message):
    """שליחת הודעה עם טיפול ב-function calling וניסיון מודלים חלופיים"""

    models_to_try = [
        st.session_state.current_model,
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
    ]

    # מסיר כפילויות ושומר על הסדר
    models_to_try = list(dict.fromkeys(models_to_try))

    for attempt, model in enumerate(models_to_try):
        try:
            # אם זה לא המודל הראשון, מחליף מודל
            if attempt > 0:
                st.warning(f"⚠️ עומס על {models_to_try[0]}, מנסה {model}...")
                switch_model(model)

            # שמירת הודעת המשתמש
            if attempt == 0:  # רק בפעם הראשונה
                st.session_state.messages.append({
                    "role": "user",
                    "content": user_message
                })

            # שליחת ההודעה
            response = st.session_state.chat.send_message(user_message)

            # בדיקה אם יש function call
            has_function_call = False
            if response.candidates and len(response.candidates) > 0:
                parts = response.candidates[0].content.parts
                for part in parts:
                    if part.function_call:
                        has_function_call = True
                        function_call = part.function_call

                        # הצגת מה המודל רוצה לחפש
                        with st.status("🔍 מחפש באינטרנט...", expanded=True) as status:
                            query = function_call.args['query']
                            st.write(f"מחפש: **{query}**")

                            # ביצוע החיפוש
                            search_results = search_web(query)
                            st.write("✅ מצאתי מידע!")
                            status.update(label="✅ החיפוש הושלם", state="complete")

                        # שמירת בקשת ה-function
                        if attempt == 0:
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": f"[חיפש באינטרנט: {query}]",
                                "is_function": True
                            })

                        # שליחת התוצאות חזרה למודל
                        function_response_part = types.Part(
                            function_response=types.FunctionResponse(
                                name="search_web",
                                response={"result": search_results}
                            )
                        )

                        final_response = st.session_state.chat.send_message(function_response_part)

                        # שמירת התשובה הסופית
                        if attempt == 0:
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": final_response.text
                            })

                        return final_response.text

            # אם אין function call - תשובה רגילה
            if not has_function_call:
                if attempt == 0:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response.text
                    })
                return response.text

        except Exception as e:
            error_message = str(e)

            # בדיקה אם זו שגיאת עומס (429 או RESOURCE_EXHAUSTED)
            if "429" in error_message or "RESOURCE_EXHAUSTED" in error_message or "quota" in error_message.lower():
                if attempt < len(models_to_try) - 1:
                    # יש עוד מודלים לנסות
                    continue
                else:
                    # נגמרו המודלים
                    error_msg = "❌ כל המודלים עמוסים כרגע. נסה שוב בעוד כמה שניות."
            else:
                # שגיאה אחרת
                error_msg = f"❌ שגיאה: {error_message}"

            if attempt == 0:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })
            return error_msg

    # אם הגענו לכאן - נכשלו כל הניסיונות
    error_msg = "❌ לא הצלחתי לקבל תשובה מאף מודל. נסה שוב מאוחר יותר."
    st.session_state.messages.append({
        "role": "assistant",
        "content": error_msg
    })
    return error_msg


# ===== אתחול =====
initialize_bot()

# ===== Sidebar - בחירת מודל =====
with st.sidebar:
    st.header("⚙️ הגדרות מודל")

    # מציג את המודל הנוכחי
    current_model_display = None
    for display_name, model_id in AVAILABLE_MODELS.items():
        if model_id == st.session_state.current_model:
            current_model_display = display_name
            break

    st.info(f"**מודל נוכחי:** {current_model_display}")

    # בחירת מודל חדש
    selected_model_display = st.selectbox(
        "החלף מודל:",
        list(AVAILABLE_MODELS.keys()),
        index=list(AVAILABLE_MODELS.values()).index(st.session_state.current_model),
        key="model_selector"
    )

    selected_model = AVAILABLE_MODELS[selected_model_display]

    if st.button("🔄 החלף מודל", use_container_width=True):
        if selected_model != st.session_state.current_model:
            switch_model(selected_model)
            st.rerun()
        else:
            st.info("כבר משתמש במודל הזה")

    st.markdown("---")

    st.header("ℹ️ איך זה עובד?")

    st.markdown("""
    ### 🔄 החלפת מודלים
    אם מודל עמוס, אפשר להחליף למודל אחר!
    **כל ההיסטוריה נשמרת** ✅

    ### 🤖 System Prompt
    הבוט מוגדר לעזור לך ללמוד!

    ### 💬 היסטוריית שיחה
    נשמרת ועוברת בין מודלים

    ### 🔍 חיפוש באינטרנט
    חיפוש אוטומטי כשצריך מידע עדכני
    """)

    st.markdown("---")

    # סטטיסטיקות
    st.subheader("📊 סטטיסטיקות")
    user_messages = len([m for m in st.session_state.messages if m["role"] == "user"])
    bot_messages = len([m for m in st.session_state.messages if m["role"] == "assistant" and not m.get("is_function")])
    searches = len([m for m in st.session_state.messages if m.get("is_function")])

    st.metric("הודעות שלך", user_messages)
    st.metric("תשובות הבוט", bot_messages)
    st.metric("חיפושים באינטרנט", searches)

    st.markdown("---")

    # איפוס
    if st.button("🗑️ התחל שיחה חדשה", use_container_width=True):
        client, chat = create_chat_with_model(st.session_state.current_model)
        st.session_state.client = client
        st.session_state.chat = chat
        st.session_state.messages = []
        st.rerun()

# ===== תצוגת השיחה =====
st.subheader("💬 שיחה עם העוזר")

# הצגת ההיסטוריה
if len(st.session_state.messages) > 0:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="🧑‍🎓"):
                st.write(msg["content"])
        else:  # assistant
            if msg.get("is_function"):
                with st.chat_message("assistant", avatar="🔍"):
                    st.info(msg["content"])
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.write(msg["content"])
else:
    st.info("👋 שלום! אני כאן לעזור לך עם שיעורי הבית. אני יכול גם לחפש מידע באינטרנט אם צריך!")

# ===== קלט מהמשתמש =====
user_input = st.chat_input("כתוב את השאלה שלך כאן...")

if user_input:
    # הצגת השאלה
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.write(user_input)

    # קבלת תשובה
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("חושב..."):
            response = send_message_with_tools(user_input)
            st.write(response)

    st.rerun()

