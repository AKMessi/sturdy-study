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

def handle_api_error(response):
    """Checks for HTTP errors and raises a detailed exception."""
    response.raise_for_status() # This will raise an HTTPError for 4xx/5xx

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

tabs = st.tabs([
    "**💬 Chat with Docs**", 
    "**🔎 Find Practice Problems**",
    "**📝 Test Yourself (MCQs)**",
    "**👩‍🏫 Guided Session**",
    "**🗺️ Concept Map**"
])

with tabs[0]:
    st.subheader("Your AI Assistant")
    if "messages" not in st.session_state: st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]): st.markdown(message["content"])
    if prompt := st.chat_input("Ask a question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Agent is thinking..."):
                try:
                    payload = {"question": prompt, "user_id": user_id}
                    response = requests.post(f"{API_URL}/chat", json=payload)
                    handle_api_error(response)
                    data = response.json()
                    content = data.get("answer", data.get("quiz", "Sorry, I had a problem."))
                    st.markdown(content)
                    st.session_state.messages.append({"role": "assistant", "content": content})
                except Exception as e: st.error(f"Error: {e}")

with tabs[1]:
    st.subheader("Find Practice Problems on the Web")
    topic = st.text_input("Enter your topic", key="problem_topic")
    if st.button("Search for Problems", type="primary", key="search_problems"):
        with st.spinner(f"Searching..."):
            try:
                payload = {"topic": topic, "user_id": user_id}
                response = requests.post(f"{API_URL}/find-problems", json=payload)
                handle_api_error(response)
                st.markdown(response.json().get("results", "No results."))
            except Exception as e: st.error(f"Error: {e}")

with tabs[2]:
    st.subheader("Generate a Practice Exam (PDF)")
    num_q = st.number_input("How many questions?", 5, 50, 10)
    if st.button("Generate Exam", type="primary", key="gen_exam"):
        with st.spinner("Starting exam generation... (This can take 1-2 minutes)"):
            try:
                payload = {"user_id": user_id, "num_questions": num_q}
                response = requests.post(f"{API_URL}/generate-test", json=payload)
                handle_api_error(response)
                job_id = response.json().get("job_id")
                status = "running"
                while status == "running" or status == "pending":
                    time.sleep(5)
                    status_response = requests.get(f"{API_URL}/generate-test/status/{job_id}")
                    handle_api_error(status_response)
                    job = status_response.json()
                    status = job.get("status")
                if status == "complete":
                    st.success("✅ Exam Generated!")
                    full_download_url = f"{BASE_URL}{job.get('download_url')}"
                    st.markdown(f"➡️ [**Download Your Exam PDF**]({full_download_url})", unsafe_allow_html=True)
                else:
                    st.error(f"Job failed: {job.get('error')}")
            except Exception as e: st.error(f"Error: {e}")

with tabs[3]:
    st.subheader("👩‍🏫 AI-Guided Socratic Session")
    if "guided_messages" not in st.session_state: st.session_state.guided_messages = []
    if "guided_topic" not in st.session_state: st.session_state.guided_topic = None
    if st.session_state.guided_topic is None:
        topic = st.text_input("What topic do you want to master today?", key="guided_topic_input")
        if st.button("Start Guided Session", type="primary", key="start_guided"):
            if topic:
                st.session_state.guided_topic = topic
                st.rerun()
    else:
        st.info(f"**Current Topic:** {st.session_state.guided_topic} | [End Session](?end_session=true)", icon="🧠")
        if st.query_params.get("end_session") == "true":
            st.session_state.guided_topic = None
            st.session_state.guided_messages = []
            st.query_params.clear()
            st.rerun()
        for message in st.session_state.guided_messages:
            with st.chat_message(message["role"]): st.markdown(message["content"])
        if prompt := st.chat_input("Answer the tutor..."):
            pass

with tabs[4]:
    st.subheader("🗺️ Concept Map Visualizer")
    st.caption("Get a 'big picture' overview of your course materials.")
    
    if "dot_string" not in st.session_state:
        st.session_state.dot_string = ""
        
    if st.button("Generate Concept Map", type="primary"):
        if not user_id:
            st.error("Please enter a User/Course ID in the sidebar first.")
        else:
            with st.spinner("Analyzing your entire course to build a map... (This can take 1-2 minutes)"):
                try:
                    payload = {"user_id": user_id}
                    response = requests.post(f"{API_URL}/generate-map", json=payload)
                    handle_api_error(response)
                    
                    data = response.json()
                    st.session_state.dot_string = data.get("dot_string")
                    
                except requests.exceptions.HTTPError as e:
                    st.error(f"Error from server: {e.response.text}")
                except Exception as e:
                    st.error(f"Connection Error: {e}")

    if st.session_state.dot_string:
        st.graphviz_chart(st.session_state.dot_string)