import streamlit as st
import requests
import json
import time

API_URL = "http://127.0.0.1:8000/v1/study"
BASE_URL = "http://127.0.0.1:8000"

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
                try:
                    files = {"file": (uploaded_pdf.name, uploaded_pdf, "application/pdf")}
                    response = requests.post(f"{API_URL}/upload", files=files, data={"user_id": user_id})
                    if response.status_code == 200:
                        status.update(label="PDF Indexed Successfully!", state="complete", expanded=False)
                    else:
                        st.error(response.text)
                except Exception as e:
                    st.error(f"Connection Error: {e}")

    st.markdown("---")
    uploaded_audio = st.file_uploader("Upload Lecture Audio", type=["mp3", "m4a", "wav"])
    if uploaded_audio:
        if st.button("Transcribe & Index Audio"):
            with st.status("Listening & Transcribing...", expanded=True) as status:
                try:
                    files = {"file": (uploaded_audio.name, uploaded_audio, uploaded_audio.type)}
                    response = requests.post(f"{API_URL}/upload-audio", files=files, data={"user_id": user_id})
                    if response.status_code == 200:
                        status.update(label="Audio Transcribed!", state="complete", expanded=False)
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
    "**📝 Test Yourself (MCQs)**"
])

with tab1:
    st.subheader("Your AI Tutor")
    st.caption("Ask questions, summarize topics, or ask for a quick quiz.")
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
                            st.markdown("### 📝 Pop Quiz!")
                            st.session_state.messages.append({"role": "assistant", "content": "I've generated a quiz for you above!"})
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
    st.subheader("Generate a Practice Exam (PDF)")
    st.caption("This agent will analyze all your course materials to create a unique exam.")
    
    num_q = st.number_input(
        "How many questions?", 
        min_value=5, 
        max_value=50, 
        value=10
    )
    
    if st.button("Generate Exam", type="primary"):
        if not user_id:
            st.error("Please enter a User/Course ID in the sidebar first.")
        else:
            with st.spinner("Starting exam generation... This may take 1-2 minutes."):
                try:
                    payload = {"user_id": user_id, "num_questions": num_q}
                    response = requests.post(f"{API_URL}/generate-test", json=payload)
                    
                    if response.status_code != 200:
                        st.error(f"Error starting job: {response.text}")
                    else:
                        job_id = response.json().get("job_id")
                        st.success(f"Job started! Job ID: {job_id}")
                        
                        with st.spinner(f"Generating {num_q} questions... This is a heavy task, please wait."):
                            status = "running"
                            while status == "running" or status == "pending":
                                time.sleep(5)
                                status_response = requests.get(f"{API_URL}/generate-test/status/{job_id}")
                                if status_response.status_code == 200:
                                    job = status_response.json()
                                    status = job.get("status")
                                    if status == "complete":
                                        st.success("✅ Exam Generated!")
                                        download_url = job.get("download_url")
                                        full_download_url = f"{BASE_URL}{download_url}"
                                        
                                        st.markdown(f"Your exam is ready to download:")
                                        st.markdown(f"➡️ [**Download Your Exam PDF**]({full_download_url})", unsafe_allow_html=True)
                                        
                                    elif status == "error":
                                        st.error(f"Job failed: {job.get('error')}")
                                else:
                                    st.error("Failed to get job status.")
                                    break
            
                except Exception as e:
                    st.error(f"Connection Error: {e}")