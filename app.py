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
    # Sentiment analysis (general)
    sentiment_analyzer = pipeline("sentiment-analysis")
    # Mental health tuned emotion model
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
def interpret_emotions(text):
    """
    Generate human-readable wellbeing summary from text.
    """
    emotions = emotion_classifier(text[:512])
    top_emotions = sorted(emotions, key=lambda x: x['score'], reverse=True)[:3]
    labels = [e['label'].lower() for e in top_emotions]

    # Check for nuanced states
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
                # Detect emotion from user message
                emotions = emotion_classifier(user_input[:512])
                top_emotion = max(emotions, key=lambda x: x['score'])['label'].lower()

                # Generate empathetic response
                if top_emotion == "sadness":
                    bot_reply = "I hear you 💛. It sounds like you're feeling really down or tired. Do you want to talk more about it?"
                elif top_emotion in ["anger", "disgust"]:
                    bot_reply = "It seems something is frustrating or upsetting you 😔. I'm here to listen if you want to share."
                elif top_emotion == "fear":
                    bot_reply = "You might be feeling anxious or worried 😟. Would you like to talk about what's on your mind?"
                elif top_emotion in ["joy", "love"]:
                    bot_reply = "It's wonderful to hear that! 😊 Keep embracing those positive moments."
                elif top_emotion == "neutral":
                    bot_reply = "I understand. Sometimes it's hard to put feelings into words. Want to share more?"
                else:
                    bot_reply = "Thanks for sharing. I'm here to listen to whatever you're feeling."

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
