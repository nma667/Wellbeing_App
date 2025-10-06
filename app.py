import streamlit as st
from openai import OpenAI
import time

# Initialize client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="Wellbeing Assistant", layout="wide")

# --- Style ---
st.markdown("""
<style>
.chat-bubble-user {
    background-color: #DCF8C6;
    color: black;
    padding: 10px 15px;
    border-radius: 20px;
    margin: 5px 0;
    text-align: right;
    width: fit-content;
    max-width: 80%;
    align-self: flex-end;
}
.chat-bubble-ai {
    background-color: #F1F0F0;
    color: black;
    padding: 10px 15px;
    border-radius: 20px;
    margin: 5px 0;
    text-align: left;
    width: fit-content;
    max-width: 80%;
    align-self: flex-start;
}
.chat-container {
    display: flex;
    flex-direction: column;
}
</style>
""", unsafe_allow_html=True)

# --- Retry logic for OpenAI ---
def call_openai_with_retry(prompt, model="gpt-3.5-turbo", retries=3, delay=5):
    for i in range(retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": "You are a helpful educational assistant."},
                          {"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            if "RateLimitError" in str(type(e)) or "429" in str(e):
                if i < retries - 1:
                    st.warning(f"Rate limit reached. Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    st.error("OpenAI rate limit reached. Please try again later.")
            else:
                st.error(f"Error: {e}")
                break

# --- Sidebar ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["📄 Assignment Analyzer", "💬 Wellbeing Chatbox"])

# --- Assignment Analyzer ---
if page == "📄 Assignment Analyzer":
    st.title("📄 Student Assignment Analyzer")
    st.write("Upload a student's short assignment *or* paste the text below to get a wellbeing risk score.")

    tab1, tab2 = st.tabs(["📁 Upload File", "📝 Paste Text"])

    text_content = ""

    with tab1:
        uploaded_file = st.file_uploader("Upload a .txt or .docx file", type=["txt", "docx"])
        if uploaded_file:
            if uploaded_file.name.endswith(".txt"):
                text_content = uploaded_file.read().decode("utf-8")
            else:
                from docx import Document
                doc = Document(uploaded_file)
                text_content = "\n".join([p.text for p in doc.paragraphs])
            st.success("File uploaded successfully!")

    with tab2:
        pasted_text = st.text_area("Paste student’s writing here:", height=200)
        if pasted_text.strip():
            text_content = pasted_text

    if text_content:
        st.subheader("🔍 Analyzing...")
        with st.spinner("Analyzing emotional tone..."):
            analysis_prompt = f"""
            Analyze the following student's writing for emotional wellbeing risk:
            - Determine if the tone suggests Low, Medium, or High wellbeing risk.
            - Provide a one-sentence summary explaining your reasoning.

            Student writing:
            {text_content}
            """
            result = call_openai_with_retry(analysis_prompt)
        st.success("✅ Analysis Complete!")
        st.markdown(f"**AI Wellbeing Analysis:** {result}")

# --- Wellbeing Chatbox ---
if page == "💬 Wellbeing Chatbox":
    st.title("💬 Wellbeing Chat Support")

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    user_input = st.chat_input("Type your message...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        ai_response = call_openai_with_retry(user_input)
        st.session_state.messages.append({"role": "assistant", "content": ai_response})

    # Display messages as bubbles
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-bubble-user">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-bubble-ai">{msg["content"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
