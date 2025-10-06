import streamlit as st
import json
import os
from deep_translator import GoogleTranslator
from textblob import TextBlob
from openai import OpenAI

# --- Initialize OpenAI client ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

DATA_FILE = "data.json"

# ---------- TRANSLATION HELPERS ----------
def detect_language(text):
    try:
        if any('\u0600' <= c <= '\u06FF' for c in text):
            return "ar"
        else:
            return "en"
    except Exception:
        return "en"

def translate_to_en(text):
    lang = detect_language(text)
    if lang != "en":
        try:
            return GoogleTranslator(source='auto', target='en').translate(text)
        except Exception:
            return text
    return text

def translate_from_en(text, target_lang):
    if target_lang != "en":
        try:
            return GoogleTranslator(source='en', target=target_lang).translate(text)
        except Exception:
            return text
    return text

# ---------- HELPER FUNCTIONS ----------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"assignments": [], "chats": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def analyze_text(text):
    # Simple AI wellbeing classifier
    prompt = f"""Classify this student's emotional state as Low, Medium, or High wellbeing risk.
    Text: {text}
    Respond only with one of these: Low, Medium, or High."""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def chat_with_ai(user_message, lang="en"):
    translated = translate_to_en(user_message)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a friendly school wellbeing chatbot that gives comforting and simple responses."},
            {"role": "user", "content": translated}
        ]
    )
    reply_en = response.choices[0].message.content.strip()
    return translate_from_en(reply_en, lang)

# ---------- STREAMLIT APP ----------
st.set_page_config(page_title="AI Wellbeing System", layout="wide")
st.title("💬 Bilingual AI Wellbeing System")

tabs = st.tabs(["📄 Analyze Student Assignment", "💭 Therapy Chatbox"])

# --- TAB 1: Analyze Assignment ---
with tabs[0]:
    st.header("📄 Upload and Analyze Assignment")
    uploaded = st.file_uploader("Upload a student’s text file (.txt)", type=["txt"])
    
    if uploaded is not None:
        text = uploaded.read().decode("utf-8")
        st.subheader("Uploaded Text:")
        st.text_area("Student’s Assignment", text, height=200)
        
        detected_lang = detect_language(text)
        translated_text = translate_to_en(text)
        
        if st.button("🔍 Analyze Wellbeing Risk"):
            result = analyze_text(translated_text)
            
            data = load_data()
            data["assignments"].append({
                "text": text,
                "language": detected_lang,
                "risk": result
            })
            save_data(data)
            
            st.success(f"AI Wellbeing Risk: **{result}**")

# --- TAB 2: Chatbox ---
with tabs[1]:
    st.header("💭 Therapy Chatbox")
    user_input = st.text_input("Type your message here...")
    
    if st.button("Send"):
        if user_input.strip():
            lang = detect_language(user_input)
            ai_reply = chat_with_ai(user_input, lang)
            
            data = load_data()
            data["chats"].append({"user": user_input, "ai": ai_reply})
            save_data(data)
            
            st.markdown(f"**🧍You:** {user_input}")
            st.markdown(f"**🤖 AI:** {ai_reply}")
        else:
            st.warning("Please enter a message before sending.")

