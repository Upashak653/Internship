import streamlit as st
import openai
import os
import re
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("OpenAI API key not found. Please set it in your environment variables or Streamlit secrets.")
    st.stop()

openai.api_key = OPENAI_API_KEY

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = [
        {"role": "system", "content": "You are a helpful hiring assistant. Ask the user for candidate information step by step."},
        {"role": "assistant", "content": "Hello! I'm the TalentScout Hiring Assistant. Let's get started. What is your full name?"}
    ]

if 'candidate_info' not in st.session_state:
    st.session_state.candidate_info = {
        'name': None,
        'email': None,
        'phone': None,
        'experience': None,
        'position': None,
        'current_position': None,
        'tech_stack': None
    }

if 'conversation_stage' not in st.session_state:
    st.session_state.conversation_stage = 'get_name'


def generate_questions_prompt(tech_stack):
    return (
        f"You are a hiring manager. The candidate's tech stack is: {tech_stack}. "
        f"Generate 3-5 intermediate-level technical questions specific to this tech stack. "
        f"Format them as a numbered list. Do not include conversational text."
    )

def get_llm_response(prompt, chat_history):
    """
    Sends a prompt to OpenAI and returns the response.
    """
    try:
        messages = chat_history + [{"role": "user", "content": prompt}]
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"I'm sorry, I encountered an error: {e}. Please try again."

st.title("TalentScout Hiring Assistant")
st.sidebar.title("TalentScout Assistant")
st.sidebar.info(
    """
    Welcome to the TalentScout Hiring Assistant!
    
    Steps:
    1. Chat with the assistant to provide your info.
    2. Receive technical questions based on your tech stack.
    3. Review your collected information.
    """
)

st.sidebar.title("TalentScout Assistant")

st.markdown("---")
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if user_input := st.chat_input("Type here..."):
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    response_text = ""

    if any(keyword in user_input.lower() for keyword in ["bye", "goodbye", "thanks", "thank you", "stop", "exit"]):
        response_text = "Thank you for your time! Your information has been collected. A hiring manager will review it and get back to you."
        st.session_state.conversation_stage = 'finished'
    elif st.session_state.conversation_stage == 'get_name':
        st.session_state.candidate_info['name'] = user_input
        response_text = "Great! What is your email address?"
        st.session_state.conversation_stage = 'get_email'

    elif st.session_state.conversation_stage == 'get_email':
        if re.match(r"[^@]+@[^@]+\.[^@]+", user_input):
            st.session_state.candidate_info['email'] = user_input
            response_text = "Got it. What is your phone number?"
            st.session_state.conversation_stage = 'get_phone'
        else:
            response_text = "That doesn't look like a valid email. Please enter a valid email address."

    elif st.session_state.conversation_stage == 'get_phone':
        st.session_state.candidate_info['phone'] = user_input
        response_text = "Thanks! How many years of professional experience do you have?"
        st.session_state.conversation_stage = 'get_experience'

    elif st.session_state.conversation_stage == 'get_experience':
        try:
            st.session_state.candidate_info['experience'] = int(user_input)
            response_text = "Years of experience noted. What is your desired position?"
            st.session_state.conversation_stage = 'get_position'
        except ValueError:
            response_text = "Please enter a valid number for years of experience."

    elif st.session_state.conversation_stage == 'get_position':
        st.session_state.candidate_info['position'] = user_input
        response_text = "Please enter your current location."
        st.session_state.conversation_stage = 'get_location'

    elif st.session_state.conversation_stage == 'get_location':
        st.session_state.candidate_info['location'] = user_input
        response_text = "Lastly, please list your tech stack (e.g., Python, Django, React, SQL)."
        st.session_state.conversation_stage = 'get_tech_stack'

    elif st.session_state.conversation_stage == 'get_tech_stack':
        st.session_state.candidate_info['tech_stack'] = user_input
        st.session_state.conversation_stage = 'generating_questions'

        with st.spinner("Generating technical questions..."):
            prompt = generate_questions_prompt(user_input)
            questions_response = get_llm_response(prompt, st.session_state.chat_history)

        response_text = f"Perfect! Here are some technical questions based on your tech stack:\n\n{questions_response}"
        if any(keyword in user_input.lower() for keyword in ["bye", "goodbye", "thanks", "thank you", "stop", "exit"]):
           st.session_state.conversation_stage = 'finished'

    if response_text:
        with st.chat_message("assistant"):
            st.write(response_text)
        st.session_state.chat_history.append({"role": "assistant", "content": response_text})
    if st.session_state.conversation_stage == 'finished':
        st.markdown("### Candidate Information Collected:")
        st.warning("Conversation has ended. Refresh the page to start a new one.")
