import streamlit as st

# הגדרות עיצוב לדף
st.set_page_config(
    page_title="פרויקטי AI - שנה רביעית",
    page_icon="🤖",
)

# כותרת ראשית
st.title("🤖 פרויקטי בינה מלאכותית")
st.subheader("שנה רביעית - חוג פייתון מתקדם")

st.markdown("---")



st.markdown("---")

# רשימת הפרויקטים
st.header("📚 הפרויקטים")

# יצירת 2 עמודות לתצוגה מסודרת
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 🎮 1. משחק אליאס
    משחק ניחושים אינטראקטיבי עם AI  
    **טכנולוגיות:** Gemini API, Streamlit  
    **מה לומדים:** ניהול שיחה, Session State
    """)

    st.markdown("""
    ### 📝 2. מחולל שיעורי בית
    מערכת חכמה ליצירת תרגילים מותאמים אישית  
    **טכנולוגיות:** Gemini API, Prompt Engineering  
    **מה לומדים:** Few-shot Learning, בקרת איכות
    """)

    st.markdown("""
    ### 💡 3. מערכת המלצות (RAG)
    מנוע חיפוש חכם והמלצות מבוססות AI  
    **טכנולוגיות:** Vector DB, Embeddings  
    **מה לומדים:** Semantic Search, RAG
    """)

with col2:
    st.markdown("""
    ### 📊 4. אתגר Kaggle
    ניתוח נתונים ובניית מודל חיזוי  
    **טכנולוגיות:** Pandas, NumPy, Matplotlib  
    **מה לומדים:** Data Science, Machine Learning
    """)

    st.markdown("""
    ### 🎯 5. AI שמשחק במשחק
    AI שלומד לשחק משחק באופן עצמאי  
    **טכנולוגיות:** OpenAI Gym, Q-Learning  
    **מה לומדים:** Reinforcement Learning
    """)

    st.markdown("""
    ### 💻 6. סוכן קוד
    AI שכותב ומריץ קוד באופן אוטונומי  
    **טכנולוגיות:** LLM, Code Generation  
    **מה לומדים:** Autonomous Agents
    """)

st.markdown("---")

# מידע נוסף
st.info("""
💡 **טיפ:** השתמשו בתפריט בצד שמאל כדי לנווט בין הפרויקטים השונים.  
כל פרויקט הוא אפליקציה עצמאית ומלאה!
""")

# פוטר
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>פותח במסגרת חוג פייתון לבני נוער - שנה רביעית 🚀</p>
</div>
""", unsafe_allow_html=True)