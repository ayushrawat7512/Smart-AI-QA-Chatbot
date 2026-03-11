import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import re

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="AI Smart QA Tester", layout="centered")

st.title("🤖 AI Smart QA Tester")
st.write("Ask software testing questions or paste a website URL to generate test cases.")

# ---------------- GEMINI SETUP ----------------
API_KEY = st.secrets.get("GEMINI_API_KEY")

if not API_KEY:
    st.error("Gemini API key not found. Please add it in Streamlit Secrets.")
    st.stop()

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-pro")

# ---------------- SESSION STATE ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- SIDEBAR ----------------
st.sidebar.title("Chat History")

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.sidebar.write("💬", msg["content"][:40])

if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# ---------------- FUNCTIONS ----------------

def ask_ai(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Error: {str(e)}"


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

    for tag in soup.find_all(["input","textarea","select"]):

        name = tag.get("name") or tag.get("id") or "N/A"
        typ = tag.get("type") or tag.name

        inputs.append({
            "Field": name,
            "Type": typ
        })

    return inputs


# ---------------- DISPLAY CHAT ----------------

for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):

        st.markdown(msg["content"])

        if msg.get("table"):
            st.table(msg["table"])

        if msg.get("test_cases"):
            st.markdown(msg["test_cases"])


# ---------------- USER INPUT ----------------

user_input = st.chat_input("Ask QA question or paste website URL...")

if user_input:

    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):

        with st.spinner("Processing..."):

            if re.match(r'https?://', user_input):

                html = get_html(user_input)

                if html:

                    inputs = extract_inputs(html)

                    st.write("### Detected Input Fields")

                    st.table(inputs)

                    prompt = f"""
You are a senior QA engineer.

Generate detailed test cases for these fields:

{inputs}

Include:
- Positive test cases
- Negative test cases
- Boundary value cases
- Edge cases
"""

                    answer = ask_ai(prompt)

                    st.write("### AI Generated Test Cases")

                    st.markdown(answer)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "Detected form fields and generated test cases.",
                        "table": inputs,
                        "test_cases": answer
                    })

                else:
                    st.error("Unable to access this website.")

            else:

                prompt = f"""
You are a software testing expert.

Answer the following QA question clearly:

{user_input}
"""

                answer = ask_ai(prompt)

                st.markdown(answer)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

    st.rerun()
