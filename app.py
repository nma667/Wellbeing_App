# app.py
import streamlit as st
import openai
from deep_translator import GoogleTranslator
from textblob import TextBlob
import json
import os
from datetime import datetime

# ---------- CONFIG ----------
openai.api_key = os.getenv("OPENAI_API_KEY")
DATA_FILE = "data.json"

translator = Translator()

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
    
# ---------- SIMPLE PERSISTENCE ----------
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"assignments": [], "chats": []}
    else:
        return {"assignments": [], "chats": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

# ---------- HELPERS ----------
def analyze_assignment_openai(text):
    urgent_keywords = [
        "kill myself", "end my life", "suicide", "want to die",
        "give up", "i can't go on", "life is pointless",
        "i wish i was dead", "self harm", "cut myself"
    ]
    for word in urgent_keywords:
        if word in text.lower():
            return {
                "risk": "high",
                "reason": f"Detected urgent phrase: '{word}'",
                "summary": "The text contains explicit signs of severe distress."
            }

    concerning_keywords = [
        "don’t feel much", "don't feel much", "don’t feel anything", "don't feel anything",
        "tired of people", "nothing excites me", "same thing every day",
        "no motivation", "just okay", "don’t care", "don't care",
        "feel empty", "numb", "pointless", "hopeless"
    ]
    for word in concerning_keywords:
        if word in text.lower():
            return {
                "risk": "high",
                "reason": f"Detected depressive pattern: '{word}'",
                "summary": "The text shows signs of depression or emotional withdrawal."
            }

    prompt = f"""
    You are analyzing a student's assignment for signs of emotional distress.

    Text: {text}

    Return a JSON object with:
    - risk: one of ["low","medium","high"]
    - reason: short explanation
    - summary: a one-sentence summary of emotional state

    IMPORTANT:
    - If the text shows emotional numbness, social withdrawal, or loss of interest, set risk = "high".
    - If the text is clearly healthy and positive, set risk = "low".
    - Otherwise, set risk = "medium".
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        result_text = response.choices[0].message["content"].strip()
        try:
            analysis = json.loads(result_text)
        except:
            analysis = {"risk": "medium", "reason": "Could not parse output", "summary": result_text}
        return analysis
    except Exception as e:
        return {"risk": "medium", "reason": f"Error: {e}", "summary": "Fallback analysis"}

def get_supportive_reply_openai(user_text_en):
    system_prompt = (
        "You are a compassionate school counselor. Respond in a calm, supportive, "
        "non-judgmental way. Offer brief validation, one or two small coping steps, "
        "and encourage seeking help if needed. If the user mentions self-harm or "
        "suicidal thoughts, include an urgent escalation recommendation."
    )
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text_en}
            ],
            max_tokens=250,
            temperature=0.7,
        )
        return resp.choices[0].message["content"].strip()
    except Exception:
        return "I'm sorry, I'm having trouble right now. Please try again or contact a counselor."

def detect_suicidal_ideation(text_en):
    words = text_en.lower()
    triggers = ["kill myself", "end my life", "suicide", "want to die", "give up", "i can't go on"]
    return any(t in words for t in triggers)

# ---------- STREAMLIT UI ----------
st.set_page_config(page_title="Bilingual AI Wellbeing Prototype", layout="wide")
st.title("Bilingual AI Wellbeing — Prototype")
tab = st.tabs(["Teacher: Assignment Analyzer", "Student: Therapy Chatbox", "Counselor Dashboard"])

# ---------------- Teacher Analyzer ----------------
with tab[0]:
    st.header("Teacher — Assignment Analyzer")
    st.write("Paste a student assignment (or upload a .txt) and click Analyze.")
    col1, col2 = st.columns([3,1])

    with col1:
        uploaded = st.file_uploader("Upload a .txt file (optional)", type=["txt"])
        if uploaded:
            raw_text = uploaded.read().decode("utf-8")
        else:
            raw_text = st.text_area("Or paste assignment text here:", height=300)

        if st.button("Analyze Assignment"):
            if not raw_text or raw_text.strip() == "":
                st.warning("Please paste or upload the assignment text first.")
            else:
                try:
                    detected = translator.detect(raw_text).lang
                except Exception:
                    detected = "en"
                text_for_analysis = raw_text
                if detected != "en":
                    try:
                        text_for_analysis = translator.translate(raw_text, src=detected, dest="en").text
                    except Exception:
                        text_for_analysis = raw_text
                with st.spinner("Analyzing with AI..."):
                    analysis = analyze_assignment_openai(text_for_analysis)

                st.subheader("AI Analysis")
                st.markdown(f"**Risk level:** `{analysis.get('risk','unknown')}`  ")
                st.markdown("**Summary:**")
                st.write(analysis.get("summary", ""))

                entry = {
                    "id": f"A{len(data['assignments'])+1}",
                    "timestamp": datetime.utcnow().isoformat(),
                    "original_text": raw_text,
                    "detected_language": detected,
                    "analysis": analysis
                }
                data["assignments"].append(entry)
                save_data(data)
                st.success("Saved analysis to prototype datastore (data.json).")

# ---------------- Student Chatbox ----------------
with tab[1]:
    st.header("Student — Private Therapy Chatbox")
    if "chat_input" not in st.session_state:
        st.session_state.chat_input = ""

    user_text = st.text_input("Type how you feel (English or Arabic)", key="chat_text")
    if st.button("Send Message"):
        if not user_text or user_text.strip() == "":
            st.warning("Please type something first.")
        else:
            try:
                detected = translator.detect(user_text).lang
            except Exception:
                detected = "en"
            text_en = user_text
            if detected != "en":
                try:
                    text_en = translator.translate(user_text, src=detected, dest="en").text
                except Exception:
                    text_en = user_text

            urgent = detect_suicidal_ideation(text_en)
            reply_en = get_supportive_reply_openai(text_en)

            if urgent:
                reply_en = (
                    "I hear you and I'm really sorry you're feeling this way. "
                    "This sounds urgent — please contact local emergency services or a trusted adult right now."
                )

            reply = reply_en
            if detected != "en":
                try:
                    reply = translator.translate(reply_en, src="en", dest=detected).text
                except Exception:
                    reply = reply_en

            chat_entry = {
                "id": f"C{len(data['chats'])+1}",
                "timestamp": datetime.utcnow().isoformat(),
                "detected_language": detected,
                "message_original": user_text,
                "message_en": text_en,
                "reply_en": reply_en,
                "reply_local": reply,
                "urgent_flag": urgent
            }
            data["chats"].append(chat_entry)
            save_data(data)

            st.markdown("**You:**")
            st.write(user_text)
            st.markdown("**Counselor (AI):**")
            st.write(reply)
            if urgent:
                st.error("⚠️ Urgent content detected. Please notify appropriate staff in a real deployment.")
