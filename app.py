import streamlit as st
from transformers import pipeline
import time

# -------------------
# PAGE CONFIG
# -------------------
st.set_page_config(
    page_title="AI Wellbeing Assistant",
    layout="wide",
    page_icon="💬"
)

# -------------------
# LOAD LOCAL MODELS
# -------------------
@st.cache_resource
def load_models():
    sentiment_analyzer = pipeline("sentiment-analysis")
    # Mental-health tuned emotion model
    emotion_classifier = pipeline(
        "text-classification", 
        model="j-hartmann/emotion-english-distilroberta-base", 
        top_k=None
    )
    return sentiment_analyzer, emotion_classifier

sentiment_analyzer, emotion_classifier = load_models()

# -------------------
# WELLBEING INTERPRETER
# -------------------
def interpret_emotions(sentiment, emotions):
    """
    Generate a human-readable wellbeing summary from sentiment and emotions.
    """
    top_emotions = sorted(emotions, key=lambda x: x['score'], reverse=True)[:3]
    labels = [e['label'].lower() for e in top_emotions]
    
    # Basic interpretation rules
    if "sadness" in labels or "anger" in labels or "fear" in labels:
        mood = "This text shows signs of emotional fatigue, stress, or mild depression."
    elif "joy" in labels or "love" in labels:
        mood = "This text reflects positive emotions and wellbeing."
    elif "neutral" in labels:
        if sentiment['label'] == "NEGATIVE":
            mood = "Even though it seems neutral, there's a subtle negative tone indicating possible low mood."
        else:
            mood = "The text appears neutral in tone."
    else:
        mood = "The text has mixed emotional tones."

    return mood

# -------------------
# SIDEBAR
# -------------------
st.sidebar.title("🧭 Navigation")
page = st.sidebar.radio("Go to", ["📄 Assignment Analyzer", "💬 Wellbeing Chatbox"])

# -------------------
# ASSIGNMENT ANALYZER
# -------------------
if page == "📄 Assignment Analyzer":
    st.title("📘 Assignment Analyzer")
    st.write("Upload or paste a student's work below to analyze its wellbeing tone and emotions.")

    upload_option = st.radio("Choose input method:", ["📤 Upload file", "✏️ Paste text"])
    text = ""

    if upload_option == "📤 Upload file":
        uploaded_file = st.file_uploader("Upload a .txt file", type=["txt"])
        if uploaded_file:
            text = uploaded_file.read().decode("utf-8")
    else:
        text = st.text_area("Paste the student's text here", height=200)

    if st.button("🔍 Analyze"):
        if text.strip() == "":
            st.warning("Please upload or paste some text to analyze.")
        else:
            with st.spinner("Analyzing..."):
                time.sleep(2)
                sentiment = sentiment_analyzer(text[:512])[0]
                emotions = emotion_classifier(text[:512])

            st.success("✅ Analysis Complete!")
            st.subheader("🧠 Wellbeing Analysis")
            st.write(f"**Overall Sentiment:** {sentiment['label']} ({sentiment['score']:.2f})")
            
            st.write("**Detected Emotions:**")
            for emo in emotions:
                st.write(f"- {emo['label']}: {emo['score']:.2f}")
            
            interpretation = interpret_emotions(sentiment, emotions)
            st.markdown(f"**💡 Wellbeing Interpretation:** {interpretation}")

# -------------------
# WELLBEING CHATBOX
# -------------------
elif page == "💬 Wellbeing Chatbox":
    st.title("💬 Wellbeing Chat Support")
    st.write("Chat safely — this assistant offers empathetic, wellbeing-focused support.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.text_input("Type your message...", key="chat_input")

    if st.button("Send"):
        if user_input.strip():
            st.session_state.chat_history.append(("user", user_input))
            # Simulate AI response (offline)
            with st.spinner("Thinking..."):
                time.sleep(1.5)
                sentiment = sentiment_analyzer(user_input[:512])[0]["label"]
                if sentiment == "NEGATIVE":
                    bot_reply = "I'm sorry you're feeling this way 💛. Want to talk more about what's making you feel down?"
                elif sentiment == "POSITIVE":
                    bot_reply = "That's great to hear! 😊 Keep up the positive energy."
                else:
                    bot_reply = "I understand. Would you like to share more about that?"
            st.session_state.chat_history.append(("bot", bot_reply))
        else:
            st.warning("Please enter a message before sending.")

    # Display chat
    st.markdown("### 💬 Chat History")
    for sender, msg in st.session_state.chat_history:
        if sender == "user":
            st.markdown(
                f"<div style='background-color:#d4edda; padding:10px; border-radius:10px; margin-bottom:5px; text-align:right;'>{msg}</div>", 
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div style='background-color:#f8f9fa; padding:10px; border-radius:10px; margin-bottom:5px;'>{msg}</div>", 
                unsafe_allow_html=True
            )
