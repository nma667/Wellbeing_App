import streamlit as st
from textblob import TextBlob
import json
import os
from datetime import datetime

# -------------------- CONFIG --------------------
st.set_page_config(page_title="AI Wellbeing System", layout="centered")
st.title("🌿 Bilingual AI Wellbeing Support System")

# -------------------- HELPER FUNCTIONS --------------------
def analyze_assignment_local(text):
    """Offline AI simulation: analyze student text for emotional risk."""
    text_lower = text.lower()
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity

    # Keyword detection
    high_keywords = ["suicide", "die", "hopeless", "worthless", "end it", "tired of life", "kill myself"]
    medium_keywords = ["sad", "tired", "alone", "empty", "don’t care", "anxious", "depressed", "stressed"]

    # Logic for risk detection
    if any(word in text_lower for word in high_keywords):
        risk = "⚠️ High Risk - urgent concern detected"
    elif any(word in text_lower for word in medium_keywords) or sentiment < -0.2:
        risk = "🟠 Medium Risk - signs of low mood or stress"
    else:
        risk = "🟢 Low Risk - text seems generally positive"

    # Save result
    save_analysis(text, risk)
    return risk


def save_analysis(text, risk):
    """Save the analysis locally to data.json"""
    data = {"text": text, "risk": risk, "timestamp": datetime.now().isoformat()}
    try:
        if os.path.exists("data.json"):
            with open("data.json", "r") as f:
                existing = json.load(f)
        else:
            existing = []
        existing.append(data)
        with open("data.json", "w") as f:
            json.dump(existing, f, indent=4)
    except Exception as e:
        st.error(f"Error saving data: {e}")


def chat_reply_local(user_input):
    """Simulated wellbeing chat assistant"""
    text = user_input.lower()
    if any(word in text for word in ["sad", "upset", "tired", "anxious", "lonely"]):
        return "I'm really sorry you're feeling this way 💛. Do you want to tell me more about what’s been bothering you?"
    elif "okay" in text or "fine" in text:
        return "It’s okay to just feel ‘okay.’ Some days are like that. How has your week been going?"
    elif "happy" in text or "good" in text:
        return "That’s great to hear 😊! What’s been making you feel better lately?"
    elif "school" in text or "homework" in text:
        return "School can definitely be stressful. Are you managing okay with your classes?"
    else:
        return "I’m here to listen 💬. You can tell me anything that’s on your mind."


# -------------------- MAIN APP --------------------
tabs = st.tabs(["📄 Assignment Analyzer", "💬 Wellbeing Chatbox", "📊 Counselor Dashboard"])

# --- TAB 1: Assignment Analyzer ---
with tabs[0]:
    st.header("📄 Analyze Student Assignment")
    st.write("Paste or upload a student’s text to detect emotional wellbeing signals.")

    uploaded_file = st.file_uploader("Upload a .txt file", type=["txt"])
    text_input = st.text_area("Or paste the student's writing here:")

    if st.button("🔍 Analyze"):
        if uploaded_file:
            text = uploaded_file.read().decode("utf-8")
        elif text_input.strip():
            text = text_input
        else:
            st.warning("Please upload a file or paste text first.")
            st.stop()

        with st.spinner("Analyzing..."):
            result = analyze_assignment_local(text)

        st.success("✅ Analysis Complete!")
        st.subheader("AI Wellbeing Analysis:")
        st.info(result)

# --- TAB 2: Chatbox ---
with tabs[1]:
    st.header("💬 Wellbeing Chat Support")
    st.write("A private space for students to chat and receive supportive responses.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display previous chat messages
    for msg in st.session_state.chat_history:
        if msg["sender"] == "user":
            st.markdown(f"<div style='text-align: right; background-color:#DCF8C6; padding:8px; border-radius:10px; margin:5px 0; max-width:80%; float:right;'>{msg['message']}</div><div style='clear:both;'></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='text-align: left; background-color:#EAEAEA; padding:8px; border-radius:10px; margin:5px 0; max-width:80%; float:left;'>{msg['message']}</div><div style='clear:both;'></div>", unsafe_allow_html=True)

    user_input = st.text_input("Type your message here...")

    if st.button("Send"):
        if user_input.strip():
            st.session_state.chat_history.append({"sender": "user", "message": user_input})
            reply = chat_reply_local(user_input)
            st.session_state.chat_history.append({"sender": "bot", "message": reply})
            st.experimental_rerun()

# --- TAB 3: Counselor Dashboard ---
with tabs[2]:
    st.header("📊 Counselor Dashboard")
    st.write("View past analyses of uploaded student work.")

    if os.path.exists("data.json"):
        with open("data.json", "r") as f:
            data = json.load(f)
        for entry in reversed(data[-5:]):  # show latest 5
            st.markdown(f"""
            **Date:** {entry['timestamp']}  
            **Risk Level:** {entry['risk']}  
            **Excerpt:** {entry['text'][:200]}...
            ---
            """)
    else:
        st.info("No analysis data available yet.")
