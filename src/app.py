import streamlit as st
import requests
import json
import time

API_URL = "http://127.0.0.1:8000/v1/study"

st.set_page_config(
    page_title="Sturdy Study AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stChatMessage {font-family: 'Inter', sans-serif;}
    h1 {color: #2E86C1;}
    .stButton button {width: 100%; border-radius: 5px;}
    div[data-testid="stTabs"] {margin-top: -40px;}
</style>
""", unsafe_allow_html=True)

st.title("🎓 Sturdy Study: The Agentic Tutor")

with st.sidebar:
    st.header("⚙️ Course Setup")
    user_id = st.text_input("User/Course ID", value="demo_course_101", help="Unique ID for your vector store")
    
    st.divider()
    
    st.subheader("📂 1. Upload Materials")
    
    uploaded_pdf = st.file_uploader("Upload PDF Slides", type=["pdf"])
    if uploaded_pdf:
        if st.button("Process PDF", type="primary"):
            with st.status("Ingesting PDF...", expanded=True) as status:
                st.write("Uploading to server...")
                files = {"file": (uploaded_pdf.name, uploaded_pdf, "application/pdf")}
                try:
                    response = requests.post(f"{API_URL}/upload", files=files, data={"user_id": user_id})
                    if response.status_code == 200:
                        status.update(label="PDF Indexed Successfully!", state="complete", expanded=False)
                        st.success(f"Added {response.json()['documents_added']} chunks to memory.")
                    else:
                        status.update(label="Error", state="error")
                        st.error(response.text)
                except Exception as e:
                    st.error(f"Connection Error: {e}")

    st.markdown("---")
    uploaded_audio = st.file_uploader("Upload Lecture Audio", type=["mp3", "m4a", "wav"])
    if uploaded_audio:
        if st.button("Transcribe & Index Audio"):
            with st.status("Listening & Transcribing...", expanded=True) as status:
                st.write("Sending to Whisper model...")
                files = {"file": (uploaded_audio.name, uploaded_audio, uploaded_audio.type)}
                try:
                    response = requests.post(f"{API_URL}/upload-audio", files=files, data={"user_id": user_id})
                    if response.status_code == 200:
                        status.update(label="Audio Transcribed!", state="complete", expanded=False)
                        st.success("Lecture audio added to knowledge base.")
                    else:
                        st.error(response.text)
                except Exception as e:
                    st.error(f"Connection Error: {e}")
    
    st.divider()
    if st.button("Clear Chat History"):
        if "messages" in st.session_state:
            st.session_state.messages = []
        st.rerun()

tab1, tab2, tab3 = st.tabs([
    "**💬 Chat with Docs**", 
    "**🔎 Find Practice Problems**", 
    "**📖 Word-for-Word Definitions**"
])

with tab1:
    st.subheader("Your AI Tutor")
    st.caption("Ask questions, summarize topics, or ask for a quiz based on your uploaded materials.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a question about your documents..."):
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Agent is thinking..."):
                try:
                    payload = {"question": prompt, "user_id": user_id}
                    response = requests.post(f"{API_URL}/chat", json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if data.get("quiz"):
                            content = "I've generated a quiz for you! See below."
                            st.session_state.messages.append({"role": "assistant", "content": content})
                            st.markdown("### 📝 Pop Quiz Generated")
                            try:
                                quiz_json = json.loads(data["quiz"])
                                for i, q in enumerate(quiz_json.get("questions", [])):
                                    st.markdown(f"**{i+1}. {q['question_text']}**")
                                    st.radio(f"Options for Q{i+1}", q["options"], key=f"q_{i}", label_visibility="collapsed")
                                    with st.expander(f"Reveal Answer {i+1}"):
                                        st.success(f"Correct: {q['correct_answer']}")
                            except Exception as e:
                                st.error(f"Failed to parse quiz JSON: {e}")
                                st.markdown(data["quiz"])
                        
                        elif data.get("answer"):
                            content = data["answer"]
                            st.markdown(content)
                            st.session_state.messages.append({"role": "assistant", "content": content})

                    else:
                        st.error(f"Error {response.status_code}: {response.text}")
                
                except Exception as e:
                    st.error(f"Connection Error: {e}")

with tab2:
    st.subheader("Find Practice Problems on the Web")
    st.caption("This tool uses your course context to find *relevant* external problems.")
    
    topic = st.text_input("Enter your topic (e.g., 'gradient descent')", key="problem_topic")
    
    if st.button("Search for Problems", type="primary"):
        if not topic:
            st.error("Please enter a topic.")
        else:
            with st.spinner(f"Searching the web for '{topic}' problems..."):
                try:
                    payload = {"topic": topic, "user_id": user_id}
                    response = requests.post(f"{API_URL}/find-problems", json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.markdown(data.get("results", "No results found."))
                    else:
                        st.error(f"Error {response.status_code}: {response.text}")
                
                except Exception as e:
                    st.error(f"Connection Error: {e}")

with tab3:
    st.subheader("Word-for-Word Definitions")
    st.caption("Look up exact definitions from your uploaded documents.")
    
    term = st.text_input("Enter a term (e.g., 'linear regression')", key="define_term")
    
    if st.button("Find Definition"):
        if not term:
            st.error("Please enter a term.")
        else:
            with st.spinner(f"Searching your docs for '{term}'..."):
                try:
                    payload = {"term": term, "user_id": user_id}
                    response = requests.post(f"{API_URL}/define", json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.markdown(f"### Definition for **{term}**")
                        st.info(data.get("definition", "Definition not found."))
                    else:
                        st.error(f"Error {response.status_code}: {response.text}")
                
                except Exception as e:
                    st.error(f"Connection Error: {e}")