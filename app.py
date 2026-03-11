import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import google.generativeai as genai

# Gemini API key
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])


model = genai.GenerativeModel("gemini-1.5-flash")

# Page
st.set_page_config(page_title="AI Smart QA Chatbot", layout="wide")

st.title("🤖 AI Smart QA Chatbot")

# Session memory
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
st.sidebar.title("Chat History")

for m in st.session_state.messages:
    if m["role"] == "user":
        preview = m["content"][:50]
        st.sidebar.write("💬", preview)

if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# Get website html
def get_html(url):
    try:
        r = requests.get(url, timeout=10)
        return r.text
    except:
        return None

# Extract inputs
def extract_inputs(html):
    soup = BeautifulSoup(html, "html.parser")
    inputs = []

    for tag in soup.find_all(["input","textarea","select"]):
        name = tag.get("name") or tag.get("id") or "N/A"
        typ = tag.get("type") or tag.name
        inputs.append({"Field":name,"Type":typ})

    return inputs

# Gemini answer
def ask_ai(prompt):

    response = model.generate_content(prompt)

    return response.text


# Show chat history
for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):

        st.markdown(msg["content"])

        if msg.get("table"):
            st.table(msg["table"])

        if msg.get("testcases"):
            st.markdown(msg["testcases"])


# Chat input
user_input = st.chat_input("Ask QA question or paste URL")

if user_input:

    st.session_state.messages.append({
        "role":"user",
        "content":user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            if re.match(r'https?://', user_input):

                html = get_html(user_input)

                if html:

                    inputs = extract_inputs(html)

                    st.table(inputs)

                    prompt = f"""
You are a senior QA engineer.

Generate detailed test cases for these input fields.

Fields:
{inputs}

Include:
Positive cases
Negative cases
Boundary value
Edge cases
"""

                    answer = ask_ai(prompt)

                    st.markdown(answer)

                    st.session_state.messages.append({
                        "role":"assistant",
                        "content":"Detected form fields",
                        "table":inputs,
                        "testcases":answer
                    })

                else:

                    st.error("Could not access website")

            else:

                prompt=f"""
You are a software testing expert.

Answer this QA question clearly:

{user_input}
"""

                answer=ask_ai(prompt)

                st.markdown(answer)

                st.session_state.messages.append({
                    "role":"assistant",
                    "content":answer
                })

    st.rerun()
