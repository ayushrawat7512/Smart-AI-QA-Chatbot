import streamlit as st
import ollama
import requests
from bs4 import BeautifulSoup
import re

# --- Page Config ---
st.set_page_config(page_title="AI Smart QA Chatbot", layout="wide")

# --- Custom CSS ---
st.markdown("""
<style>
.centered-container {
    max-width: 800px;
    margin-left: auto;
    margin-right: auto;
}
button.open-website {
    padding:8px 16px; 
    background-color:#4CAF50; 
    color:white; 
    border:none; 
    border-radius:4px; 
    cursor:pointer;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Sidebar ---
st.sidebar.title("Chat History")
if st.session_state.messages:
    for m in st.session_state.messages:
        if m["role"] == "user":
            content = m["content"]
            # If it's a URL
            if content.startswith("http"):
                st.sidebar.markdown(f"[🌐 {content}]({content})", unsafe_allow_html=True)
            else:
                # Show first 50 chars of question
                preview = content if len(content) <= 50 else content[:47] + "..."
                st.sidebar.markdown(f"💬 {preview}")
else:
    st.sidebar.write("No chats yet.")

if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# --- Helper Functions ---
def get_html(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        return r.text
    except:
        return None

def extract_inputs(html):
    soup = BeautifulSoup(html, "html.parser")
    inputs = []
    for tag in soup.find_all(["input", "select", "textarea"]):
        name = tag.get("name") or tag.get("id") or "N/A"
        typ = tag.get("type") or tag.name
        inputs.append({"Field": name, "Type": typ})
    return inputs

def generate_tests(inputs):
    prompt = f"You are a senior QA engineer. Based on these form fields: {inputs}, generate: Positive/Negative cases, Edge cases, BVA, and Equivalence Partitioning."
    try:
        response = ollama.chat(
            model="llama3",
            messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"]
    except Exception as e:
        return f"Error connecting to Ollama: {str(e)}"

# --- Main UI ---
st.markdown('<div class="centered-container">', unsafe_allow_html=True)

st.title("🤖 AI Smart QA Chatbot")
st.markdown("Ask any Software Testing related question below OR paste a website URL to analyze and generate test cases.")

# --- Display Chat History ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("table") and msg.get("url"):
            st.markdown(f"""
            <a href="{msg['url']}" target="_blank">
                <button class="open-website">Open Website</button>
            </a>
            """, unsafe_allow_html=True)
            st.table(msg["table"])
        st.markdown(msg["content"])
        if msg.get("test_cases"):
            st.markdown(msg["test_cases"])

# --- Chat Input ---
if user_input := st.chat_input("Ask a software testing question or Paste URL..."):
    # Store user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Assistant response
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            # --- URL Handling ---
            if re.match(r'https?://', user_input):
                html = get_html(user_input)
                if html:
                    inputs = extract_inputs(html)
                    if inputs:
                        st.markdown(f"""
                        <a href="{user_input}" target="_blank">
                            <button class="open-website">Open Website</button>
                        </a>
                        """, unsafe_allow_html=True)
                        st.table(inputs)
                        loaded_msg = f"✅ **Loaded {user_input}**. Detected input fields:"
                        st.markdown(loaded_msg)
                        test_cases = generate_tests(inputs)
                        st.markdown("### AI Generated Test Cases")
                        st.markdown(test_cases)
                        # Store assistant message
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": loaded_msg,
                            "table": inputs,
                            "url": user_input,
                            "test_cases": test_cases
                        })
                    else:
                        msg = "No standard input fields found on this page."
                        st.warning(msg)
                        st.session_state.messages.append({"role": "assistant", "content": msg})
                else:
                    msg = "Couldn't reach the URL. Check if it's correct."
                    st.error(msg)
                    st.session_state.messages.append({"role": "assistant", "content": msg})

            # --- General QA Question Handling ---
            else:
                prompt = f"You are a senior QA engineer. Answer this software testing question clearly:\n\n{user_input}"
                try:
                    response = ollama.chat(
                        model="llama3",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    answer = response["message"]["content"]
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as e:
                    msg = f"Error connecting to Ollama: {str(e)}"
                    st.error(msg)
                    st.session_state.messages.append({"role": "assistant", "content": msg})

    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)
