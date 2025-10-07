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
# LOAD MODELS
# -------------------
@st.cache_resource
def load_models():
    sentiment_analyzer = pipeline("sentiment-analysis")
    emotion_classifier = pipeline(
        "text-classification",
        model="j-hartmann/emotion-english-distilroberta-base",
        top_k=None
    )
    return sentiment_analyzer, emotion_classifier

sentiment_analyzer, emotion_classifier = load_models()

# -------------------
# HELPER FUNCTIONS
# -------------------
def normalize_emotions(raw_output):
    """
    Convert the output of emotion_classifier to a consistent list of dicts:
    [{"label": ..., "score": ...}, ...]
    """
    if isinstance(raw_output, dict):
        return [{"label": k, "score": v} for k, v in raw_output.items()]
    elif isinstance(raw_output, list):
        if len(raw_output) > 0 and isinstance(raw_output[0], dict) and "label" in raw_output[0]:
            return raw_output  # already list of dicts
        elif len(raw_output) > 0 and isinstance(raw_output[0], list):
            # sometimes returned as list of lists
            return [{"label": e["label"], "score": e["score"]} for e in raw_output[0]]
    return [{"label": "neutral", "score": 1.0}]  # fallback

def interpret_emotions(text):
    emotions_raw = emotion_classifier(text[:512])
    emotions = normalize_emotions(emotions_raw)
    top_emotions = sorted(emotions, key=lambda x: x['score'], reverse=True)[:3]
    labels = [e['label'].lower() for e in top_emotions]

    if "sadness" in labels:
        return "This text reflects emotional fatigue, sadness, or mild depression."
    elif "anger" in labels or "disgust" in labels:
        return "There is frustration, anger, or irritation present."
    elif "fear" in labels:
        return "The text shows signs of anxiety or worry."
    elif "joy" in labels or "love" in labels:
        return "This text reflects positive emotions and wellbeing."
    elif "neutral" in labels:
        return "The text appears calm or neutral, though subtle emotions may be present."
    else:
        return "The text has mixed emotional tones."

def detect_top_emotion(text):
    emotions_raw = emotion_classifier(text[:512])
    emotions = normalize_emotions(emotions_raw)
    if emotions:
        return max(emotions, key=lambda x: x['score'])['label'].lower()
    return "neutral"

def generate_chat_response(top_emotion):
    if top_emotion == "sadness":
        return "I hear you 💛. It sounds like you're feeling really down or tired. Do you want to talk more about it?"
    elif top_emotion in ["anger", "disgust"]:
        return "It seems something is frustrating or upsetting you 😔. I'm here to listen if you want to share."
    elif top_emotion == "fear":
        return "You might be feeling anxious or worried 😟. Would you like to talk about what's on your mind?"
    elif top_emotion in ["joy", "love"]:
        return "It's wonderful to hear that! 😊 Keep embracing those positive moments."
    elif top_emotion == "neutral":
        return "I understand. Sometimes it's hard to put feelings into words. Want to share more?"
    else:
        return "Thanks for sharing. I'm here to listen to whatever you're feeling."

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
                emotions_raw = emotion_classifier(text[:512])
                emotions = normalize_emotions(emotions_raw)
                interpretation = interpret_emotions(text)

            st.success("✅ Analysis Complete!")
            st.subheader("🧠 Wellbeing Analysis")
            st.write(f"**Overall Sentiment:** {sentiment['label']} ({sentiment['score']:.2f})")
            
            st.write("**Detected Emotions:**")
            for emo in emotions:
                st.write(f"- {emo['label']}: {emo['score']:.2f}")
            
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
            with st.spinner("Thinking..."):
                time.sleep(1.5)
                top_emotion = detect_top_emotion(user_input)
                bot_reply = generate_chat_response(top_emotion)
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
